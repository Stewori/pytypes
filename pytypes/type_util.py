# Copyright 2017 Stefan Richthofer
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Created on 13.12.2016

import random
import sys
import types
import threading
import typing
from inspect import isfunction, ismethod, isclass, ismodule
try:
    from backports.typing import Tuple, Dict, List, Set, Union, Any, TupleMeta, \
        GenericMeta, CallableMeta, Sequence, Mapping, TypeVar, Container, Generic
except ImportError:
    from typing import Tuple, Dict, List, Set, Union, Any, TupleMeta, Optional, \
        GenericMeta, CallableMeta, Sequence, Mapping, TypeVar, Container, Generic
from warnings import warn, warn_explicit

import pytypes
from .stubfile_manager import _match_stub_type, as_stub_func_if_any
from .typecomment_parser import _get_typestrings, _funcsigtypesfromstring
from . import util

_annotated_modules = {}
_extra_dict = {}
_saved_profilers = {}

for tp in typing.__all__:
    tpa = getattr(typing, tp)
    try:
        _extra_dict[tpa.__extra__] = tpa
    except AttributeError:
        pass
if not tuple in _extra_dict:
    _extra_dict[tuple] = Tuple

if sys.version_info.major >= 3:
    _basestring = str
else:
    _basestring = basestring

EMPTY = TypeVar('EMPTY', bound=Container, covariant=True)


class Empty(Generic[EMPTY]):
    """pytypes-specific type to represent empty lists, sets, dictionaries
    and other empty containers.
    """
    pass


def get_generator_yield_type(genr):
    """Obtains the yield type of a generator object.
    """
    return get_generator_type(genr).__args__[0]


def get_generator_type(genr):
    """Obtains PEP 484 style type of a generator object, i.e. returns a
    typing.Generator object.
    """
    if 'gen_type' in genr.gi_frame.f_locals:
        return genr.gi_frame.f_locals['gen_type']
    else:
        return _funcsigtypes(genr.gi_code, False, None, genr.gi_frame.f_globals)[1]


def get_iterable_itemtype(obj):
    """Attempts to get an iterable's itemtype without iterating over it,
    not even partly. Note that iterating over an iterable might modify
    its inner state, e.g. if it is an iterator.
    Note that obj is expected to be an iterable, not a typing.Iterable.
    This function leverages various alternative ways to obtain that
    info, e.g. by looking for type annotations of '__iter__' or '__getitem__'.
    It is intended for (unknown) iterables, where the type cannot be obtained
    via sampling without the risk of modifying inner state.
    """
    # support further specific iterables on demand
    try:
        if isinstance(obj, range):
            tpl = tuple(deep_type(obj.start), deep_type(obj.stop), deep_type(obj.step))
            return Union[tpl]
    except TypeError:
        # We're running Python 2
        pass
    if type(obj) is tuple:
        tpl = tuple(deep_type(t) for t in obj)
        return Union[tpl]
    elif type(obj) is types.GeneratorType:
        return get_generator_yield_type(obj)
    else:
        tp = deep_type(obj)
        if isinstance(tp, GenericMeta):
            if issubclass(tp.__origin__, typing.Iterable):
                if len(tp.__args__) == 1:
                    return tp.__args__[0]
                return _select_Generic_superclass_parameters(tp, typing.Iterable)[0]
    if is_iterable(obj):
        if type(obj) is str:
            return str
        if hasattr(obj, '__iter__'):
            if has_type_hints(obj.__iter__):
                itrator = _funcsigtypes(obj.__iter__, True, obj.__class__)[1]
                if isinstance(itrator, GenericMeta) and itrator.__origin__ is typing.Iterator:
                    return itrator.__args__[0]
        if hasattr(obj, '__getitem__'):
            if has_type_hints(obj.__getitem__):
                itrator =  _funcsigtypes(obj.__getitem__, True, obj.__class__)[1]
                if isinstance(itrator, GenericMeta) and itrator.__origin__ is typing.Iterator:
                    return itrator.__args__[0]
        return None # means that type is unknown
    else:
        raise TypeError('Not an iterable: '+str(type(obj)))


def get_Generic_itemtype(sq, simplify = True):
    """sq must be a typing.Tuple or subclass of typing.Iterable or typing.Container.
    """
    if isinstance(sq, TupleMeta):
        if simplify:
            itm_tps = [x for x in get_Tuple_params(sq)]
            simplify_for_Union(itm_tps)
            return Union[tuple(itm_tps)]
        else:
            return Union[get_Tuple_params(sq)]
    else:
        try:
            return _select_Generic_superclass_parameters(sq, typing.Container)[0]
        except TypeError:
            try:
                return _select_Generic_superclass_parameters(sq, typing.Iterable)[0]
            except TypeError:
                raise TypeError("Has no itemtype: "+str(sq))


def get_Tuple_params(tpl):
    """Python version independent function to obtain the parameters
    of a typing.Tuple object.
    Tested with CPython 2.7, 3.5, 3.6 and Jython 2.7.1.
    """
    try:
        return tpl.__tuple_params__
    except AttributeError:
        try:
            if tpl.__args__ is None:
                return None
            # Python 3.6
            return () if tpl.__args__[0] == () else tpl.__args__
        except AttributeError:
            return None


def get_Union_params(un):
    """Python version independent function to obtain the parameters
    of a typing.Union object.
    Tested with CPython 2.7, 3.5, 3.6 and Jython 2.7.1.
    """
    try:
        return un.__union_params__
    except AttributeError:
        # Python 3.6
        return un.__args__


def get_Callable_args_res(clb):
    """Python version independent function to obtain the parameters
    of a typing.Callable object. Returns as tuple: args, result.
    Tested with CPython 2.7, 3.5, 3.6 and Jython 2.7.1.
    """
    try:
        return clb.__args__, clb.__result__
    except AttributeError:
        # Python 3.6
        return clb.__args__[:-1], clb.__args__[-1]


def is_iterable(obj):
    """Tests if an object implements the iterable protocol.
    This function is intentionally not capitalized, because
    it does not check w.r.t. (capital) Iterable class from
    typing or collections.
    """
    try:
        itr = iter(obj)
        del itr
        return True
    except:
        return False


def is_Union(tp):
    """Python version independent check if a type is typing.Union.
    Tested with CPython 2.7, 3.5, 3.6 and Jython 2.7.1.
    """
    if tp is Union:
        return True
    try:
        # Python 3.6
        return tp.__origin__ is Union
    except AttributeError:
        try:
            return isinstance(tp, typing.UnionMeta)
        except AttributeError:
            return False


def deep_type(obj, depth = None, max_sample = None):
    """Tries to construct a type for a given value. In contrast to type(...),
    deep_type does its best to fit structured types from typing as close as
    possible to the given value.
    E.g. deep_type((1, 2, 'a')) will return Tuple[int, int, str] rather than
    just tuple.
    Supports various types from typing, but not yet all.
    Also detects nesting up to given depth (uses pytypes.default_typecheck_depth
    if no value is given).
    If a value for max_sample is given, this number of elements is probed
    from lists, sets and dictionaries to determine the element type. By default,
    all elements are probed. If there are fewer elements than max_sample, all
    existing elements are probed.
    """
    return _deep_type(obj, [], depth, max_sample)


def _deep_type(obj, checked, depth = None, max_sample = None):
    if depth is None:
        depth = pytypes.default_typecheck_depth
    if max_sample is None:
        max_sample = pytypes.deep_type_samplesize
    if -1 != max_sample < 2:
        max_sample = 2
    try:
        res = obj.__orig_class__
    except AttributeError:
        res = type(obj)
    if depth == 0 or obj in checked:
        return res
    else:
        checked.append(obj)
    if res == tuple:
        res = Tuple[tuple(_deep_type(t, checked, depth-1) for t in obj)]
    elif res == list:
        if len(obj) == 0:
            return Empty[List]
        if max_sample == -1 or max_sample >= len(obj)-1 or len(obj) <= 2:
            tpl = tuple(_deep_type(t, checked, depth-1) for t in obj)
        else:
            # In case of lists I somehow feel it's better to ensure that
            # first and last element are part of the sample
            sample = [0, len(obj)-1]
            try:
                rsmp = random.sample(xrange(1, len(obj)-1), max_sample-2)
            except NameError:
                rsmp = random.sample(range(1, len(obj)-1), max_sample-2)
            sample.extend(rsmp)
            tpl = tuple(_deep_type(obj[t], checked, depth-1) for t in sample)
        res = List[Union[tpl]]
    elif res == dict:
        if len(obj) == 0:
            return Empty[Dict]
        if max_sample == -1 or max_sample >= len(obj)-1 or len(obj) <= 2:
            try:
                # We prefer a view (avoid copy)
                tpl1 = tuple(_deep_type(t, checked, depth-1) for t in obj.viewkeys())
                tpl2 = tuple(_deep_type(t, checked, depth-1) for t in obj.viewvalues())
            except AttributeError:
                # Python 3 gives views like this:
                tpl1 = tuple(_deep_type(t, checked, depth-1) for t in obj.keys())
                tpl2 = tuple(_deep_type(t, checked, depth-1) for t in obj.values())
        else:
            try:
                kitr = iter(obj.viewkeys())
                vitr = iter(obj.viewvalues())
            except AttributeError:
                kitr = iter(obj.keys())
                vitr = iter(obj.values())
            ksmpl = []
            vsmpl = []
            block = (len(obj) // max_sample)-1
            # I know this method has some bias towards beginning of iteration
            # sequence, but it's still more random than just taking the
            # initial sample and better than O(n) random.sample.
            while len(ksmpl) < max_sample:
                if block > 0:
                    j = random.randint(0, block)
                    k = random.randint(0, block)
                    while j > 0:
                        next(vitr) # discard
                        j -= 1
                    while k > 0:
                        next(kitr) # discard
                        k -= 1
                ksmpl.append(next(kitr))
                vsmpl.append(next(vitr))
            tpl1 = tuple(_deep_type(t, checked, depth-1) for t in ksmpl)
            tpl2 = tuple(_deep_type(t, checked, depth-1) for t in vsmpl)
        res = Dict[Union[tpl1], Union[tpl2]]
    elif res == set:
        if len(obj) == 0:
            return Empty[Set]
        if max_sample == -1 or max_sample >= len(obj)-1 or len(obj) <= 2:
            tpl = tuple(_deep_type(t, checked, depth-1) for t in obj)
        else:
            itr = iter(obj)
            smpl = []
            block = (len(obj) // max_sample)-1
            # I know this method has some bias towards beginning of iteration
            # sequence, but it's still more random than just taking the
            # initial sample and better than O(n) random.sample.
            while len(smpl) < max_sample:
                if block > 0:
                    j = random.randint(0, block)
                    while j > 0:
                        next(itr) # discard
                        j -= 1
                smpl.append(next(itr))
            tpl = tuple(_deep_type(t, checked, depth-1) for t in smpl)
        res = Set[Union[tpl]]
    elif res == types.GeneratorType:
        res = get_generator_type(obj)
    elif sys.version_info.major == 2 and isinstance(obj, types.InstanceType):
        # For old-style instances return the actual class:
        return obj.__class__
    elif _issubclass_2(res, Container) and len(obj) == 0:
        return Empty[res]
    elif hasattr(res, '__origin__') and \
            _issubclass_2(res.__origin__, Container) and len(obj) == 0:
        return Empty[res.__origin__]
    return res


def is_builtin_type(tp):
    """Checks if the given type is a builtin one.
    """
    return hasattr(__builtins__, tp.__name__) and tp is getattr(__builtins__, tp.__name__)


def has_type_hints(func0):
    """Detects if the given function or method has type annotations.
    Also considers typecomments and stubfiles.
    """
    return _has_type_hints(func0)


def _check_as_func(memb):
    return isfunction(memb) or ismethod(memb) or \
            isinstance(memb, classmethod) or isinstance(memb, staticmethod) or \
            isinstance(memb, property)


def _has_type_hints(func0, func_class = None, nesting = None):
    actual_func = util._actualfunc(func0)
    func = as_stub_func_if_any(actual_func, func0, func_class, nesting)
    stub_func = func
    func = util._actualfunc(func)
    tpHints = _tpHints_from_annotations(func0, actual_func, stub_func, func)
    if not tpHints is None:
        return True
    try:
        tpHints = typing.get_type_hints(func)
    except NameError:
        # Some typehint caused this NameError, so typhints are present in some form
        return True
    except TypeError:
        # func seems to be not suitable to have type hints
        return False
    except AttributeError:
        # func seems to be not suitable to have type hints
        return False
    try:
        tpStr = _get_typestrings(func, False)
        return not ((tpStr is None or tpStr[0] is None) and (tpHints is None or not tpHints))
    except TypeError:
        return False


_implicit_globals = set()
try:
    _implicit_globals.add(sys.modules['__builtin__'])
except:
    _implicit_globals.add(sys.modules['builtins'])
def _tp_relfq_name(tp, tp_name=None, assumed_globals=None, update_assumed_globals=None,
            implicit_globals=None):
    # _type: (type, Optional[Union[Set[Union[type, types.ModuleType]], Mapping[Union[type, types.ModuleType], str]]], Optional[bool]) -> str
    """Provides the fully qualified name of a type relative to a set of
    modules and types that is assumed as globally available.
    If assumed_globals is None this always returns the fully qualified name.
    If update_assumed_globals is True, this will return the plain type name,
    but will add the type to assumed_globals (expected to be a set).
    This way a caller can query how to generate an appropriate import section.
    If update_assumed_globals is False, assumed_globals can alternatively be
    a mapping rather than a set. In that case the mapping is expected to be
    an alias table, mapping modules or types to their alias names desired for
    displaying.
    update_assumed_globals can be None (default). In that case this will return the
    plain type name if assumed_globals is None as well (default).
    This mode is there to have a less involved default behavior.
    """
    if tp_name is None:
        tp_name = util.get_class_qualname(tp)
    if implicit_globals is None:
        implicit_globals = _implicit_globals
    else:
        implicit_globals = implicit_globals.copy()
        implicit_globals.update(_implicit_globals)
    if assumed_globals is None:
        if update_assumed_globals is None:
            return tp_name
        md = sys.modules[tp.__module__]
        if md in implicit_globals:
            return tp_name
        name = tp.__module__+'.'+tp_name
        pck = None
        if not (md.__package__ is None or md.__package__ == ''
                or name.startswith(md.__package__)):
            pck = md.__package__
        return name if pck is None else pck+'.'+name
    if tp in assumed_globals:
        try:
            return assumed_globals[tp]
        except:
            return tp_name
    elif hasattr(tp, '__origin__') and tp.__origin__ in assumed_globals:
        try:
            return assumed_globals[tp.__origin__]
        except:
            return tp_name
    # For some reason Callable does not have __origin__, so we special-case
    # it here. Todo: Find a cleaner solution.
    elif isinstance(tp, CallableMeta) and typing.Callable in assumed_globals:
        try:
            return assumed_globals[typing.Callable]
        except:
            return tp_name
    elif update_assumed_globals == True:
        if not assumed_globals is None:
            if hasattr(tp, '__origin__') and not tp.__origin__ is None:
                toadd = tp.__origin__
            elif isinstance(tp, CallableMeta):
                toadd = typing.Callable
            else:
                toadd = tp
            if not sys.modules[toadd.__module__] in implicit_globals:
                assumed_globals.add(toadd)
        return tp_name
    else:
        md = sys.modules[tp.__module__]
        if md in implicit_globals:
            return tp_name
        md_name = tp.__module__
        if md in assumed_globals:
            try:
                md_name = assumed_globals[md]
            except:
                pass
        else:
            if not (md.__package__ is None or md.__package__ == ''
                    or md_name.startswith(md.__package__)):
                md_name = md.__package__+'.'+tp.__module__
        return md_name+'.'+tp_name


def type_str(tp, assumed_globals=None, update_assumed_globals=None,
            implicit_globals=None):
    """Generates a nicely readable string representation of the given type.
    The returned representation is workable as a source code string and would
    reconstruct the given type if handed to eval, provided that globals/locals
    are configured appropriately (e.g. assumes that various types from typing
    have been imported).
    Used as type-formatting backend of ptypes' code generator abilities
    in modules typelogger and stubfile_2_converter.
    
    For semantics of assumed_globals and update_assumed_globals see
    _tp_relfq_name. Its doc applies to every argument or result contained in
    tp (recursively) and to tp itself.
    """
    if assumed_globals is None and update_assumed_globals is None:
        if implicit_globals is None:
            implicit_globals = set()
        else:
            implicit_globals = implicit_globals.copy()
        implicit_globals.add(sys.modules['typing'])
        implicit_globals.add(sys.modules['__main__'])
    if isinstance(tp, tuple):
        return '('+', '.join([type_str(tp0, assumed_globals, update_assumed_globals,
                implicit_globals) for tp0 in tp])+')'
    try:
        return type_str(tp.__orig_class__, assumed_globals, update_assumed_globals,
                implicit_globals)
    except AttributeError:
        pass
    tp = _match_stub_type(tp)
    if isinstance(tp, TypeVar):
        return tp.__name__
    elif isclass(tp) and not isinstance(tp, GenericMeta) \
            and not hasattr(typing, tp.__name__):
        tp_name = _tp_relfq_name(tp, None, assumed_globals, update_assumed_globals,
                implicit_globals)
        prm = ''
        if hasattr(tp, '__args__') and not tp.__args__ is None:
            params = [type_str(param, assumed_globals, update_assumed_globals,
                    implicit_globals) for param in tp.__args__]
            prm = '[%s]'%', '.join(params)
        return tp_name+prm
    elif is_Union(tp):
        prms = get_Union_params(tp)
        params = [type_str(param, assumed_globals, update_assumed_globals,
                implicit_globals) for param in prms]
        return '%s[%s]'%(_tp_relfq_name(Union, 'Union', assumed_globals,
                update_assumed_globals, implicit_globals), ', '.join(params))
    elif isinstance(tp, TupleMeta):
        prms = get_Tuple_params(tp)
        tpl_params = [type_str(param, assumed_globals, update_assumed_globals,
                implicit_globals) for param in prms]
        return '%s[%s]'%(_tp_relfq_name(Tuple, 'Tuple', assumed_globals,
                update_assumed_globals, implicit_globals), ', '.join(tpl_params))
    elif hasattr(tp, '__args__'):
        tp_name = _tp_relfq_name(tp, None, assumed_globals, update_assumed_globals,
                implicit_globals)
        if tp.__args__ is None:
            if hasattr(tp, '__parameters__') and \
                    hasattr(tp, '__origin__') and tp.__origin__ is Generic and \
                    not tp.__parameters__ is None and len(tp.__parameters__) > 0:
                args = tp.__parameters__
            else:
                return tp_name
        else:
            args = tp.__args__
        params = [type_str(param, assumed_globals, update_assumed_globals, implicit_globals)
                for param in args]
        if hasattr(tp, '__result__'):
            return '%s[[%s], %s]'%(tp_name, ', '.join(params),
                    type_str(tp.__result__, assumed_globals, update_assumed_globals,
                    implicit_globals))
        elif isinstance(tp, CallableMeta):
            return '%s[[%s], %s]'%(tp_name, ', '.join(params[:-1]),
                    type_str(params[-1], assumed_globals, update_assumed_globals,
                    implicit_globals))
        else:
            return '%s[%s]'%(tp_name, ', '.join(params))
    elif hasattr(tp, '__name__'):
        result = _tp_relfq_name(tp, None, assumed_globals, update_assumed_globals,
                implicit_globals)
    elif tp is Any:
        # In Python 3.6 Any does not have __name__.
        result = _tp_relfq_name(tp, 'Any', assumed_globals, update_assumed_globals,
                implicit_globals)
    else:
        # Todo: Care for other special types from typing where necessary.
        result = str(tp)
    if not implicit_globals is None:
        for s in implicit_globals:
            result = result.replace(s.__name__+'.', '')
    return result


def get_types(func):
    """Works like get_type_hints, but returns types as a sequence rather than a
    dictionary. Types are returned in declaration order of the corresponding arguments.
    """
    return _get_types(func, util.is_classmethod(func), util.is_method(func))


def get_member_types(obj, member_name, prop_getter = False):
    """Still experimental, incomplete and hardly tested.
    Works like get_types, but is also applicable to descriptors.
    """
    cls = obj.__class__
    member = getattr(cls, member_name)
    slf = not (isinstance(member, staticmethod) or isinstance(member, classmethod))
    clsm = isinstance(member, classmethod)
    return _get_types(member, clsm, slf, cls, prop_getter)


def _get_types(func, clsm, slf, clss = None, prop_getter = False,
            unspecified_type = Any, infer_defaults = None):
    """Helper for get_types and get_member_types.
    """
    func0 = util._actualfunc(func, prop_getter)
    # check consistency regarding special case with 'self'-keyword
    if not slf:
        argNames = util.getargnames(util.getargspecs(func0))
        if len(argNames) > 0:
            if clsm:
                if argNames[0] != 'cls':
                    print('Warning: classmethod using non-idiomatic argname '+func0.__name__)
    if clss is None and (slf or clsm):
        if slf:
            assert util.is_method(func) or isinstance(func, property)
        if clsm:
            assert util.is_classmethod(func)
        clss = util.get_class_that_defined_method(func)
        assert hasattr(clss, func.__name__)
    args, res = _funcsigtypes(func, slf or clsm, clss, None, prop_getter,
            unspecified_type = unspecified_type, infer_defaults = infer_defaults)
    return _match_stub_type(args), _match_stub_type(res)


def get_type_hints(func):
    """Resembles typing.get_type_hints, but is also workable on Python 2.7 and
    searches stubfiles for type information.
    Also on Python 3, this takes type comments
    (python.org/dev/peps/pep-0484/#suggested-syntax-for-python-2-7-and-straddling-code)
    into account if present.
    """
    if not has_type_hints(func):
        # What about defaults?
        return {}
    return _get_type_hints(func)


def _get_type_hints(func, args = None, res = None, infer_defaults = None):
    """Helper for get_type_hints.
    """
    if args is None or res is None:
        args2, res2 = _get_types(func, util.is_classmethod(func),
                util.is_method(func), unspecified_type = type(NotImplemented),
                infer_defaults = infer_defaults)
        if args is None:
            args = args2
        if res is None:
            res = res2
    slf = 1 if util.is_method(func) else 0
    argNames = util.getargnames(util.getargspecs(util._actualfunc(func)))
    result = {}
    if not args is Any:
        prms = get_Tuple_params(args)
        for i in range(slf, len(argNames)):
            if not prms[i-slf] is type(NotImplemented):
                result[argNames[i]] = prms[i-slf]
    result['return'] = res
    return result


def _make_invalid_type_msg(descr, func_name, tp):
    msg = 'Invalid %s in %s:\n    %s is not a type.' % (descr, func_name, str(tp))
    if isinstance(tp, tuple):
        mask = '\n  You might rather want to use typing.Tuple:\n      Tuple[%s]'
        try:
            msg += mask % (', '.join(type_str(t) for t in tp))
        except:
            msg += mask % (', '.join(str(t) for t in tp))
    return msg


def _tpHints_from_annotations(*args):
    for func in args:
        if not func is None and hasattr(func, '__annotations__'):
            res = func.__annotations__
            if not res is None and len(res) > 0:
                return res
    return None


# Only intended for use with __annotations__.
# For typestrings, _funcsigtypesfromstring can directly insert defaults
def _handle_defaults(sig_types, arg_specs, unspecified_indices = None):
    if arg_specs.defaults is None:
        return sig_types
    prms = get_Tuple_params(sig_types[0])
    if len(prms) < len(arg_specs.args):
        # infer missing types from defaults...
        df = len(arg_specs.args)-len(prms)
        if df <= len(arg_specs.defaults):
            resType = [prm for prm in prms]
            for obj in arg_specs.defaults[-df:]:
                resType.append(deep_type(obj))
            if unspecified_indices is None:
                res = Tuple[tuple(resType)], sig_types[1]
                return res
        elif not unspecified_indices is None:
            resType = [prm for prm in prms]
    elif not unspecified_indices is None:
        resType = [prm for prm in prms]
    if not unspecified_indices is None and len(unspecified_indices) > 0:
        off = len(arg_specs.args)-len(arg_specs.defaults)
        for i in unspecified_indices:
            if i >= off:
                resType[i] = deep_type(arg_specs.defaults[i-off])
        res = Tuple[tuple(resType)], sig_types[1]
        return res
    return sig_types


def _funcsigtypes(func0, slf, func_class = None, globs = None, prop_getter = False,
        unspecified_type = Any, infer_defaults = None):
    if infer_defaults is None:
        infer_defaults = pytypes.infer_default_value_types
    # Check for stubfile
    actual_func = util._actualfunc(func0, prop_getter)
    func = as_stub_func_if_any(actual_func, func0, func_class)
    stub_func = None
    if isinstance(func, property):
        stub_func = func
        func = util._actualfunc(func, prop_getter)
    try:
        tpHints = typing.get_type_hints(func)
    except AttributeError:
        tpHints = None
    tpStr = _get_typestrings(func, slf)
    argSpecs = util.getargspecs(actual_func)
    hints_from_annotations = False
    if tpHints is None or not tpHints:
        tpHints = _tpHints_from_annotations(func0, actual_func, stub_func, func)
        hints_from_annotations = True
    if (tpStr is None or tpStr[0] is None) and tpHints is None:
        # What about defaults?
        return Any, Any
    if not (tpStr is None or tpStr[0] is None) and tpStr[0].find('...') != -1:
        numArgs = len(argSpecs.args) - 1 if slf else 0
        while len(tpStr[1]) < numArgs:
            tpStr[1].append(None)
    if globs is None:
        if func.__module__.endswith('.pyi') or func.__module__.endswith('.pyi2'):
            globs = {}
            globs.update(sys.modules[func.__module__].__dict__)
            try:
                # In case of something like stubfile_2_converter a stub without module
                # might be present, which would cause KeyError here.
                globs.update(sys.modules[func.__module__.rsplit('.', 1)[0]].__dict__)
            except KeyError:
                pass
        else:
            globs = sys.modules[func.__module__].__dict__
    argNames = util.getargnames(argSpecs)
    if slf:
        if not tpHints is None and tpHints and not func_class is None and \
                argNames[0] in tpHints:
            # cls or self was type-annotated
            if not util.is_classmethod(func) and not _issubclass(tpHints[argNames[0]], func_class):
                # todo: What about classmethods?
                str_args = (func.__module__, func_class.__name__, func.__name__,
                        'self' if argNames[0] == 'self' else "self-arg '"+argNames[0]+"'",
                        type_str(func_class), type_str(tpHints[argNames[0]]),
                        "\nCalling the self-arg '"+
                        argNames[0]+"' is not recommended." if argNames[0] != 'self' else '')
                msg = ('%s.%s.%s declares invalid type for %s:\n'+
                        'Expected: %s\nDeclared: %s'+
                        "\nAnnotating the self-arg with a type is not recommended.%s") % str_args
                if pytypes.checking_enabled and not pytypes.warning_mode:
                    raise TypeError(msg)
                else:
                    import traceback
                    tb = traceback.extract_stack()
                    off = util._calc_traceback_list_offset(tb)
                    warn_explicit(msg, pytypes.TypeWarning, tb[off][0], tb[off][1])
        argNames = argNames[1:]
    if not tpHints is None and tpHints:
        if hints_from_annotations:
            tmp = tpHints
            tpHints = {}
            for key in tmp:
                val = tmp[key]
                if val is None:
                    val = type(None)
                elif isinstance(val, _basestring):
                    val = eval(val, globs)
                tpHints[key] = val
        # We're running Python 3 or have custom __annotations__ in Python 2.7
        retTp = tpHints['return'] if 'return' in tpHints else Any
        unspecIndices = []
        for i in range(len(argNames)):
            if not argNames[i] in tpHints:
                unspecIndices.append(i)
        resType = (Tuple[tuple((tpHints[t] if t in tpHints else unspecified_type) \
                for t in argNames)], retTp if not retTp is None else type(None))
        if infer_defaults:
            resType = _handle_defaults(resType, argSpecs, unspecIndices)
        if not pytypes.annotations_override_typestring and not (tpStr is None or tpStr[0] is None):
            if pytypes.strict_annotation_collision_check:
                raise TypeError('%s.%s has multiple type declarations.'
                        % (func.__module__, func.__name__))
            else:
                resType2 = _funcsigtypesfromstring(*tpStr, argspec = argSpecs, globals = globs,
                        argCount = len(argNames), unspecified_type = unspecified_type,
                        defaults = argSpecs.defaults if infer_defaults else None,
                        func = actual_func, func_class = func_class, slf = slf)
                if resType != resType2:
                    raise TypeError('%s.%s declares incompatible types:\n'
                            % (func.__module__, func.__name__)
                            + 'Via hints:   %s\nVia comment: %s'
                            % (type_str(resType), type_str(resType2)))
        try:
            typing._type_check(resType[0], '') # arg types
        except TypeError:
            raise TypeError(_make_invalid_type_msg('arg types',
                    util._fully_qualified_func_name(func, slf, func_class), resType[0]))
        try:
            typing._type_check(resType[1], '') # return type
        except TypeError:
            raise TypeError(_make_invalid_type_msg('return type',
                    util._fully_qualified_func_name(func, slf, func_class), resType[1]))
        return resType
    res = _funcsigtypesfromstring(*tpStr, globals = globs, argspec = argSpecs,
            argCount = len(argNames),
            defaults = argSpecs.defaults if infer_defaults else None,
            unspecified_type = unspecified_type, func = actual_func,
            func_class = func_class, slf = slf)
    try:
        typing._type_check(res[0], '') # arg types
    except TypeError:
        raise TypeError(_make_invalid_type_msg('arg types',
                util._fully_qualified_func_name(func, slf, func_class), res[0]))
    try:
        typing._type_check(res[1], '') # return type
    except TypeError:
        raise TypeError(_make_invalid_type_msg('return type',
                util._fully_qualified_func_name(func, slf, func_class), res[1]))
    if pytypes.annotations_from_typestring:
        if not hasattr(func0, '__annotations__') or len(func0.__annotations__) == 0:
            if not infer_defaults:
                func0.__annotations__ = _get_type_hints(func0, res[0], res[1])
            else:
                res2 = _funcsigtypesfromstring(*tpStr, argspec = argSpecs, globals = globs,
                        argCount = len(argNames), unspecified_type = unspecified_type,
                        func = actual_func, func_class = func_class, slf = slf)
                func0.__annotations__ = _get_type_hints(func0, res2[0], res2[1])
    return res


def _issubclass_Mapping_covariant(subclass, superclass):
    """Helper for _issubclass, a.k.a pytypes.issubtype.
    """
    # This subclass-check treats Mapping-values as covariant
    if isinstance(subclass, GenericMeta):
        if not issubclass(subclass.__origin__, Mapping):
            return False
        if not _issubclass(subclass.__args__[0], superclass.__args__[0]):
            return False
        if not _issubclass(subclass.__args__[1], superclass.__args__[1]):
            return False
        return True
    return issubclass(subclass, superclass)


def _find_Generic_super_origin(subclass, superclass_origin):
    """Helper for _issubclass_Generic.
    """
    stack = [subclass]
    param_map = {}
    while len(stack) > 0:
        bs = stack.pop()
        if isinstance(bs, GenericMeta):
            if (bs.__origin__ is superclass_origin or \
                    (bs.__origin__ is None and bs is superclass_origin)):
                prms = []
                prms.extend(bs.__parameters__)
                for i in range(len(prms)):
                    while prms[i] in param_map:
                        prms[i] = param_map[prms[i]]
                return prms
            if not bs.__origin__ is None and len(bs.__origin__.__parameters__) > 0:
                for i in range(len(bs.__parameters__)):
                    ors = bs.__origin__.__parameters__[i]
                    if bs.__parameters__[i] != ors:
                        param_map[ors] = bs.__parameters__[i]
            try:
                stack.extend(bs.__orig_bases__)
            except AttributeError:
                stack.extend(bs.__bases__)
    return None


def _select_Generic_superclass_parameters(subclass, superclass_origin):
    """Helper for _issubclass_Generic.
    """
    if subclass.__origin__ is superclass_origin:
        return subclass.__args__
    prms = _find_Generic_super_origin(subclass, superclass_origin)
    return [subclass.__args__[subclass.__origin__.__parameters__.index(prm)] \
            for prm in prms]


def _issubclass_Generic(subclass, superclass):
    """Helper for _issubclass, a.k.a pytypes.issubtype.
    """
    # this function is partly based on code from typing module 3.5.2.2
    if subclass is None:
        return False
    if subclass in _extra_dict:
        subclass = _extra_dict[subclass]
    if isinstance(subclass, TupleMeta):
        tpl_prms = get_Tuple_params(subclass)
        if not tpl_prms is None and len(tpl_prms) == 0:
            # (This section is required because Empty shall not be
            # used on Tuples.)
            # an empty Tuple is any Sequence, regardless of type
            # note that we needn't consider superclass beeing a tuple,
            # because that should have been checked in _issubclass_Tuple
            return issubclass(typing.Sequence, superclass.__origin__)
        subclass = Sequence[Union[tpl_prms]]
    if isinstance(subclass, GenericMeta):
        # For a class C(Generic[T]) where T is co-variant,
        # C[X] is a subclass of C[Y] iff X is a subclass of Y.
        origin = superclass.__origin__
        #Formerly: if origin is not None and origin is subclass.__origin__:
        if origin is not None and _issubclass(subclass.__origin__, origin):
            assert len(superclass.__args__) == len(origin.__parameters__)
            if len(subclass.__args__) == len(origin.__parameters__):
                sub_args = subclass.__args__
            else:
                # We select the relevant subset of args by TypeVar-matching
                sub_args = _select_Generic_superclass_parameters(subclass, superclass.__origin__)
                assert len(sub_args) == len(origin.__parameters__)
            for p_self, p_cls, p_origin in zip(superclass.__args__,
                                            sub_args,
                                            origin.__parameters__):
                if isinstance(p_origin, TypeVar):
                    if p_origin.__covariant__:
                        # Covariant -- p_cls must be a subclass of p_self.
                        if not _issubclass(p_cls, p_self):
                            break
                    elif p_origin.__contravariant__:
                        # Contravariant.  I think it's the opposite. :-)
                        if not _issubclass(p_self, p_cls):
                            break
                    else:
                        # Invariant -- p_cls and p_self must equal.
                        if p_self != p_cls:
                            break
                else:
                    # If the origin's parameter is not a typevar,
                    # insist on invariance.
                    if p_self != p_cls:
                        break
            else:
                return True
            # If we break out of the loop, the superclass gets a chance.

        # I.e.: origin is None or not _issubclass(subclass.__origin__, origin)
        # In this case we must consider origin or subclass.__origin__ to be None
        # We treat param-values as unknown in the following sense:
        #   for covariant params: treat unknown more-or-equal specific than Any
        #   for contravariant param: Any more-or-equal specific than Unknown
        #   for invariant param: unknown never passes
        # if both are unknown:
        #   return False (?) (or NotImplemented? Or let a flag decide behavior?)
        if origin is None:
            if not pytypes.check_unbound_types:
                raise TypeError("Attempted to check unbound type(superclass: "+str(superclass))
            if not subclass.__origin__ is None:
                if not type.__subclasscheck__(superclass, subclass.__origin__):
                    return False
                prms = _find_Generic_super_origin(subclass.__origin__, superclass)
                args = _select_Generic_superclass_parameters(subclass, superclass)
                for i in range(len(prms)):
                    if prms[i].__covariant__:
                        if pytypes.strict_unknown_check:
                            return False
                    elif prms[i].__contravariant__:
                        # Subclass-value must be wider than or equal to Any, i.e. must be Any:
                        if not args[i] is Any:
                            return False
                    else:
                        return False
                return True
            #else:
                # nothing to do here... (?)
        elif subclass.__origin__ is None:
            if not pytypes.check_unbound_types:
                raise TypeError("Attempted to check unbound type (subclass): "+str(subclass))
            if not type.__subclasscheck__(superclass.__origin__, subclass):
                return False
            prms = superclass.__origin__.__parameters__
            for i in range(len(prms)):
                if prms[i].__covariant__:
                    # subclass-arg here is unknown, so in superclass only Any can pass:
                    if not superclass.__args__[i] is Any:
                        return False
                elif prms[i].__contravariant__:
                    if pytypes.strict_unknown_check:
                        return False
                else:
                    return False
            return True
# 	Formerly: if super(GenericMeta, superclass).__subclasscheck__(subclass):
    if type.__subclasscheck__(superclass, subclass):
        return True
    if superclass.__extra__ is None or isinstance(subclass, GenericMeta):
        return False
    return _issubclass_2(subclass, superclass.__extra__)


def _issubclass_Tuple(subclass, superclass):
    """Helper for _issubclass, a.k.a pytypes.issubtype.
    """
    # this function is partly based on code from typing module 3.5.2.2
    if subclass in _extra_dict:
        subclass = _extra_dict[subclass]
    if not isinstance(subclass, type):
        # To TypeError.
        return False
    if not isinstance(subclass, TupleMeta):
        if isinstance(subclass, GenericMeta):
            try:
                return _issubclass_Generic(subclass, superclass)
            except:
                pass
        elif is_Union(subclass):
            return all(_issubclass_Tuple(t, superclass)
                    for t in get_Union_params(subclass))
        else:
            return False
    super_args = get_Tuple_params(superclass)
    if super_args is None:
        return True
    sub_args = get_Tuple_params(subclass)
    if sub_args is None:
        return False  # ???
    # Covariance.
    return (len(super_args) == len(sub_args) and
            all(_issubclass(x, p)
                for x, p in zip(sub_args, super_args)))


def _issubclass_Union(subclass, superclass):
    """Helper for _issubclass, a.k.a pytypes.issubtype.
    """
    # this function is partly based on code from typing module 3.5.2.2
    super_args = get_Union_params(superclass)
    if super_args is None:
        return is_Union(subclass)
    elif is_Union(subclass):
        sub_args = get_Union_params(subclass)
        if sub_args is None:
            return False
        return all(_issubclass(c, superclass) for c in (sub_args))
    elif isinstance(subclass, TypeVar):
        if subclass in super_args:
            return True
        if subclass.__constraints__:
            return _issubclass(Union[subclass.__constraints__], superclass)
        return False
    else:
        return any(_issubclass(subclass, t) for t in super_args)


# This is just a crutch, because issubclass sometimes tries to be too smart.
# Note that this doesn't consider __subclasshook__ etc, so use with care!
def _has_base(cls, base):
    """Helper for _issubclass, a.k.a pytypes.issubtype.
    """
    if cls is base:
        return True
    elif cls is None:
        return False
    for bs in cls.__bases__:
        if _has_base(bs, base):
            return True
    return False


def _issubclass(subclass, superclass):
    """Access this via pytypes.is_subtype.
    Works like issubclass, but supports PEP 484 style types from typing module.
    """
    if superclass is Any:
        return True
    if subclass is Any:
        return superclass is Any
    if pytypes.apply_numeric_tower:
        if superclass is float and subclass is int:
            return True
        elif superclass is complex and \
                (subclass is int or subclass is float):
            return True
    if superclass in _extra_dict:
        superclass = _extra_dict[superclass]
    try:
        if _issubclass_2(subclass, Empty):
            if _issubclass_2(superclass, Container):
                return _issubclass_2(subclass.__args__[0], superclass)
            try:
                if _issubclass_2(superclass.__origin__, Container):
                    return _issubclass_2(subclass.__args__[0], superclass.__origin__)
            except TypeError:
                pass
    except TypeError:
        pass
    return _issubclass_2(subclass, superclass)


def _issubclass_2(subclass, superclass):
    """Helper for _issubclass, a.k.a pytypes.issubtype.
    """
    if isinstance(superclass, TupleMeta):
        return _issubclass_Tuple(subclass, superclass)
    if isinstance(superclass, GenericMeta):
        # We would rather use issubclass(superclass.__origin__, Mapping), but that's somehow erroneous
        if pytypes.covariant_Mapping and _has_base(superclass.__origin__, Mapping):
            return _issubclass_Mapping_covariant(subclass, superclass)
        else:
            return _issubclass_Generic(subclass, superclass)
    if is_Union(superclass):
        return _issubclass_Union(subclass, superclass)
    if is_Union(subclass):
        return all(_issubclass(t, superclass) for t in get_Union_params(subclass))
    if subclass in _extra_dict:
        subclass = _extra_dict[subclass]
    try:
        return issubclass(subclass, superclass)
    except TypeError:
        raise TypeError("Invalid type declaration: %s, %s" %
                (type_str(subclass), type_str(superclass)))


def _isinstance_Callable(obj, cls, check_callables = True):
    # todo: Let pytypes somehow create a Callable-scoped error message,
    # e.g. instead of
    #	Expected: Tuple[Callable[[str, int], str], str]
    #	Received: Tuple[function, str]
    # make
    #	Expected: Tuple[Callable[[str, int], str], str]
    #	Received: Tuple[Callable[[str, str], str], str]
    if not hasattr(obj, '__call__'):
        return False
    if has_type_hints(obj):
        slf_or_cls = util.is_method(obj) or util.is_classmethod(obj)
        parent_cls = util.get_class_that_defined_method(obj) if slf_or_cls else None
        argSig, resSig = _funcsigtypes(obj, slf_or_cls, parent_cls)
        argSig = _match_stub_type(argSig)
        resSig = _match_stub_type(resSig)
        clb_args, clb_res = get_Callable_args_res(cls)
        if not _issubclass(Tuple[clb_args], argSig):
            return False
        if not _issubclass(resSig, clb_res):
            return False
        return True
    return not check_callables


def _isinstance(obj, cls):
    """Access this via pytypes.is_of_type.
    Works like isinstance, but supports PEP 484 style types from typing module.
    """
    # Special treatment if cls is Iterable[...]
    if isinstance(cls, GenericMeta) and cls.__origin__ is typing.Iterable:
        if not is_iterable(obj):
            return False
        itp = get_iterable_itemtype(obj)
        if itp is None:
            return not pytypes.check_iterables
        else:
            return _issubclass(itp, cls.__args__[0])
    if isinstance(cls, CallableMeta):
        return _isinstance_Callable(obj, cls)
    if obj == {}:
        return issubclass(typing.Dict, cls.__origin__)
    return _issubclass(deep_type(obj), cls)


def _make_generator_error_message(tp, gen, expected_tp, incomp_text):
    _cmp_msg_format = 'Expected: %s\nReceived: %s'
    # todo: obtain fully qualified generator name
    return gen.__name__+' '+incomp_text+':\n'+_cmp_msg_format \
                % (type_str(expected_tp), type_str(tp))


def generator_checker_py3(gen, gen_type):
    """Builds a typechecking wrapper around a Python 3 style generator object.
    """
    initialized = False
    sn = None
    try:
        while True:
            a = gen.send(sn)
            if initialized or not a is None:
                if not gen_type.__args__[0] is Any and not _isinstance(a, gen_type.__args__[0]):
                    tpa = deep_type(a)
                    msg = _make_generator_error_message(deep_type(a), gen, gen_type.__args__[0],
                            'has incompatible yield type')
                    _raise_typecheck_error(msg, True, a, tpa, gen_type.__args__[0])
# 					raise pytypes.ReturnTypeError(_make_generator_error_message(deep_type(a), gen,
# 							gen_type.__args__[0], 'has incompatible yield type'))
            initialized = True
            sn = yield a
            if not gen_type.__args__[1] is Any and not _isinstance(sn, gen_type.__args__[1]):
                tpsn = deep_type(sn)
                msg = _make_generator_error_message(tpsn, gen, gen_type.__args__[1],
                        'has incompatible send type')
                _raise_typecheck_error(msg, False, sn, tpsn, gen_type.__args__[1])
# 				raise pytypes.InputTypeError(_make_generator_error_message(deep_type(sn), gen,
# 						gen_type.__args__[1], 'has incompatible send type'))
    except StopIteration as st:
        # Python 3:
        # todo: Check if st.value is always defined (i.e. as None if not present)
        if not gen_type.__args__[2] is Any and not _isinstance(st.value, gen_type.__args__[2]):
                tpst = deep_type(st.value)
                msg = _make_generator_error_message(tpst, gen, gen_type.__args__[2],
                        'has incompatible return type')
                _raise_typecheck_error(msg, True, st.value, tpst, gen_type.__args__[2])
# 				raise pytypes.ReturnTypeError(_make_generator_error_message(sttp, gen,
# 						gen_type.__args__[2], 'has incompatible return type'))
        raise st


def generator_checker_py2(gen, gen_type):
    """Builds a typechecking wrapper around a Python 2 style generator object.
    """
    initialized = False
    sn = None
    while True:
        a = gen.send(sn)
        if initialized or not a is None:
            if not gen_type.__args__[0] is Any and not _isinstance(a, gen_type.__args__[0]):
                tpa = deep_type(a)
                msg = _make_generator_error_message(tpa, gen, gen_type.__args__[0],
                        'has incompatible yield type')
                _raise_typecheck_error(msg, True, a, tpa, gen_type.__args__[0])
# 				raise pytypes.ReturnTypeError(_make_generator_error_message(tpa, gen,
# 						gen_type.__args__[0], 'has incompatible yield type'))
        initialized  = True
        sn = yield a
        if not gen_type.__args__[1] is Any and not _isinstance(sn, gen_type.__args__[1]):
            tpsn = deep_type(sn)
            msg = _make_generator_error_message(tpsn, gen, gen_type.__args__[1],
                    'has incompatible send type')
            _raise_typecheck_error(msg, False, sn, tpsn, gen_type.__args__[1])
# 			raise pytypes.InputTypeError(_make_generator_error_message(tpsn, gen,
# 					gen_type.__args__[1], 'has incompatible send type'))


def _find_typed_base_method(meth, cls):
    meth0 = util._actualfunc(meth)
    for cls1 in util.mro(cls):
        if hasattr(cls1, meth0.__name__):
            fmeth = getattr(cls1, meth0.__name__)
            if has_type_hints(util._actualfunc(fmeth)):
                return fmeth, cls1
    return None, None


def annotations_func(func):
    """Works like annotations, but is only applicable to functions,
    methods and properties.
    """
    if not has_type_hints(func):
        # What about defaults?
        func.__annotations__ =  {}
    func.__annotations__ = _get_type_hints(func,
            infer_defaults = False)
    return func


def annotations_class(cls):
    """Works like annotations, but is only applicable to classes.
    """
    assert(isclass(cls))
    # To play it safe we avoid to modify the dict while iterating over it,
    # so we previously cache keys.
    # For this we don't use keys() because of Python 3.
    # Todo: Better use inspect.getmembers here
    keys = [key for key in cls.__dict__]
    for key in keys:
        memb = cls.__dict__[key]
        if _check_as_func(memb):
            annotations_func(memb)
        elif isclass(memb):
            annotations_class(memb)
    return cls


def annotations_module(md):
    """Works like annotations, but is only applicable to modules (by explicit call).
    md must be a module or a module name contained in sys.modules.
    """
    if isinstance(md, str):
        if md in sys.modules:
            md = sys.modules[md]
            if md is None:
                return md
        elif md in pytypes.typechecker._pending_modules:
            # if import is pending, we just store this call for later
            pytypes.typechecker._pending_modules[md].append(annotations_module)
            return md
    assert(ismodule(md))
    if md.__name__ in pytypes.typechecker._pending_modules:
            # if import is pending, we just store this call for later
            pytypes.typechecker._pending_modules[md.__name__].append(annotations_module)
            # we already process the module now as far as possible for its internal use
            # todo: Issue warning here that not the whole module might be covered yet
    if md.__name__ in _annotated_modules and \
            _annotated_modules[md.__name__] == len(md.__dict__):
        return md
    # To play it safe we avoid to modify the dict while iterating over it,
    # so we previously cache keys.
    # For this we don't use keys() because of Python 3.
    # Todo: Better use inspect.getmembers here
    keys = [key for key in md.__dict__]
    for key in keys:
        memb = md.__dict__[key]
        if _check_as_func(memb) and memb.__module__ == md.__name__:
            annotations_func(memb)
        elif isclass(memb) and memb.__module__ == md.__name__:
            annotations_class(memb)
    if not md.__name__ in pytypes.typechecker._pending_modules:
        _annotated_modules[md.__name__] = len(md.__dict__)
    return md


def annotations(memb):
    """Decorator applicable to functions, methods, properties,
    classes or modules (by explicit call).
    If applied on a module, memb must be a module or a module name contained in sys.modules.
    See pytypes.set_global_annotations_decorator to apply this on all modules.
    Methods with type comment will have type hints parsed from that
    string and get them attached as __annotations__ attribute.
    Methods with either a type comment or ordinary type annotations in
    a stubfile will get that information attached as __annotations__
    attribute (also a relevant use case in Python 3).
    Behavior in case of collision with previously (manually)
    attached __annotations__ can be controlled using the flags
    pytypes.annotations_override_typestring and pytypes.annotations_from_typestring.
    """
    if _check_as_func(memb):
        return annotations_func(memb)
    if isclass(memb):
        return annotations_class(memb)
    if ismodule(memb):
        return annotations_module(memb)
    if memb in sys.modules or memb in pytypes.typechecker._pending_modules:
        return annotations_module(memb)
    return memb


def _catch_up_global_annotations_decorator():
    for mod_name in sys.modules:
        if not mod_name in _annotated_modules:
            try:
                md = sys.modules[mod_name]
            except KeyError:
                md = None
            if not md is None and ismodule(md):
                annotations_module(mod_name)


def simplify_for_Union(type_list):
    """Removes types that are subtypes of other elements in the list.
    Does not return a copy, but instead modifies the given list.
    Intended for preprocessing of types to be combined into a typing.Union.
    Subtypecheck is backed by pytypes.is_subtype, so this differs from
    typing.Union's own simplification efforts.
    E.g. this also considers numeric tower like described in
    https://www.python.org/dev/peps/pep-0484/#the-numeric-tower
    (treats int as subtype of float as subtype of complex)
    Use pytypes.apply_numeric_tower flag to switch off numeric tower support.
    """
    i = 0
    while i < len(type_list):
        j = 0
        while j < i:
            if _issubclass(type_list[j], type_list[i]):
                del type_list[j]
                i -= 1
            else:
                j += 1
        j = i+1
        while j < len(type_list):
            if _issubclass(type_list[j], type_list[i]):
                del type_list[j]
            else:
                j += 1
        i += 1


def _preprocess_typecheck(argSig, argspecs, slf_or_clsm = False):
    """From a PEP 484 style type-tuple with types for *varargs and/or **kw
    this returns a type-tuple containing Tuple[tp, ...] and Dict[str, kw-tp]
    instead.
    """
    # todo: Maybe move also slf-logic here
    vargs = argspecs.varargs
    try:
        kw = argspecs.keywords
    except AttributeError:
        kw = argspecs.varkw
    try:
        kwonly = argspecs.kwonlyargs
    except AttributeError:
        kwonly = None
    if not vargs is None or not kw is None:
        arg_type_lst = list(get_Tuple_params(argSig))
        if not vargs is None:
            vargs_pos = (len(argspecs.args)-1) \
                    if slf_or_clsm else len(argspecs.args)
            # IndexErrors in this section indicate that a child-method was
            # checked against a parent's type-info with the child featuring
            # a more wider type on signature level (e.g. adding vargs)
            try:
                vargs_type = typing.Sequence[arg_type_lst[vargs_pos]]
            except IndexError:
                vargs_type = typing.Sequence[typing.Any]
            try:
                arg_type_lst[vargs_pos] = vargs_type
            except IndexError:
                arg_type_lst.append(vargs_type)
        if not kw is None:
            kw_pos = len(argspecs.args)
            if slf_or_clsm:
                kw_pos -= 1
            if not vargs is None:
                kw_pos += 1
            if not kwonly is None:
                kw_pos += len(kwonly)
            try:
                kw_type = typing.Dict[str, arg_type_lst[kw_pos]]
            except IndexError:
                kw_type = typing.Dict[str, typing.Any]
            try:
                arg_type_lst[kw_pos] = kw_type
            except IndexError:
                arg_type_lst.append(kw_type)
        return typing.Tuple[tuple(arg_type_lst)]
    else:
        return argSig


def _raise_typecheck_error(msg, is_return=False, value=None, received_type=None,
            expected_type=None, func=None):
    if pytypes.warning_mode:
        import traceback
        tb = traceback.extract_stack()
        off = util._calc_traceback_list_offset(tb)
        cat = pytypes.ReturnTypeWarning if is_return else pytypes.InputTypeWarning
        warn_explicit(msg, cat, tb[off][0], tb[off][1])
# 		if not func is None:
# 			warn_explicit(msg, cat, func.__code__.co_filename,
# 					func.__code__.co_firstlineno, func.__module__)
# 		else:
# 			warn(msg, pytypes.ReturnTypeWarning)
    else:
        if is_return:
            raise pytypes.ReturnTypeError(msg)
        else:
            raise pytypes.InputTypeError(msg)


def _get_current_call_info(clss = None, caller_level = 0):
    prop = None
    prop_getter = False
    fq, code = util._get_current_function_fq(caller_level+1)
    if isinstance(fq[0], property):
        prop = fq[0]
        if fq[0].fget.__code__ is code:
            cllable = fq[0].fget
            prop_getter = True
        elif not fq[0].fset is None and fq[0].fset.__code__ is code:
            cllable = fq[0].fset
    else:
        cllable = fq[0]
    if cllable is None:
        raise RuntimeError("Couldn't determine caller.")
    slf = fq[2]
    clsm = pytypes.is_classmethod(fq[0])
    if clss is None and len(fq[1]) > 0:
        clss = fq[1][-1]
    return cllable, clss, slf, clsm, prop, prop_getter


def _check_caller_type(return_type, cllable = None, call_args = None, clss = None, caller_level = 0):
    prop = None
    prop_getter = False
    if cllable is None:
        cllable, clss, slf, clsm, prop, prop_getter = _get_current_call_info(clss, caller_level+1)
    else:
        clsm = pytypes.is_classmethod(cllable)
        slf = ismethod(cllable)
        if clss is None:
            clss = util.get_class_that_defined_method(cllable) if slf or clsm else None
    act_func = util._actualfunc(cllable)
    has_hints = has_type_hints(cllable)
    if not has_hints and not slf:
        return
    if not return_type:
        specs = util.getargspecs(act_func)
        if call_args is None:
            call_args = util.get_current_args(caller_level+1, cllable, util.getargnames(specs))
        if slf or clsm:
            call_args = call_args[1:]
    if not prop is None:
        argSig, retSig = _get_types(prop, clsm, slf, clss, prop_getter)
        try:
            if return_type:
                pytypes._checkfuncresult(retSig, call_args, act_func, slf or clsm, clss,
                        prop_getter, force_exception=True)
            else:
                pytypes._checkfunctype(argSig, call_args, act_func, slf or clsm, clss,
                        False, False, specs, force_exception=True)
        except pytypes.TypeCheckError:
            if not pytypes.warning_mode:
                raise
            else:
                return False
    else:
        if slf:
            check_parent = pytypes.always_check_parent_types
            if not check_parent:
                try:
                    check_parent = act_func.override_checked
                except AttributeError:
                    pass
            if not check_parent:
                try:
                    check_parent = cllable.override_checked
                except AttributeError:
                    pass
            if check_parent:
                cllable, clss = _find_typed_base_method(cllable, clss)
                if cllable is None:
                    return
                act_func = util._actualfunc(cllable)
                if not return_type:
                    specs = util.getargspecs(act_func)
            elif not has_hints:
                return
        argSig, retSig = _get_types(cllable, clsm, slf, clss)
        try:
            if return_type:
                pytypes._checkfuncresult(retSig, call_args, act_func, slf or clsm, clss,
                        prop_getter, force_exception=True)
            else:
                pytypes._checkfunctype(argSig, call_args, act_func, slf or clsm, clss,
                        False, False, specs, force_exception=True)
        except pytypes.TypeCheckError:
            if not pytypes.warning_mode:
                raise
            else:
                return False
        return True


def restore_profiler():
    """If a typechecking profiler is active, e.g. created by
    pytypes.set_global_typechecked_profiler(), such a profiler
    must be restored whenever a TypeCheckError is caught.
    The call must stem from the thread that raised the error.
    Otherwise the typechecking profiler is implicitly disabled.
    Alternatively one can turn pytypes into warning mode. In that
    mode no calls to this function are required (unless one uses
    filterwarnings("error") or likewise).
    """
    idn = threading.current_thread().ident
    if not sys.getprofile() is None:
        warn("restore_profiler: Current profile is not None!")
    if not idn in _saved_profilers:
        warn("restore_profiler: No saved profiler for calling thread!")
    else:
        sys.setprofile(_saved_profilers[idn])
        del _saved_profilers[idn]


class TypeAgent(object):

    def __init__(self, all_threads = True):
        self.all_threads = all_threads
        self._previous_profiler = None
        self._previous_thread_profiler = None
        self._active = False
        self._pending = False
        self._cleared = False
        self._checking_enabled = False
        self._logging_enabled = False
        self._caller_level_shift = 0

    def _is_checking(self):
        if not pytypes.checking_enabled:
            return False
        if pytypes.global_typechecked_profiler:
            # a global checker is already doing the job
            # So return true only if self is this global checker.
            return self is pytypes._global_type_agent
        else:
            return self._checking_enabled

    def _is_logging(self):
        if not pytypes.typelogging_enabled:
            return False
        if pytypes.global_typelogged_profiler:
            # a global checker is already doing the job
            # So return true only if self is this global checker.
            return self is pytypes._global_type_agent
        else:
            return self._logging_enabled

    @property
    def active(self):
        return self._active

    def _set_caller_level_shift(self, shift):
        self._caller_level_shift = shift
        if not self._previous_profiler is None and \
                isinstance(self._previous_profiler, TypeAgent):
            self._previous_profiler._set_caller_level_shift(shift+1)

    def start(self):
        if self._active:
            raise RuntimeError('type checker already running')
        elif self._pending:
            raise RuntimeError('type checker already starting up')
        self._pending = True
        # Install this instance as the current profiler
        self._previous_profiler = sys.getprofile()
        self._set_caller_level_shift(0)
        sys.setprofile(self)

        # If requested, set this instance as the default profiler for all future threads
        # (does not affect existing threads)
        if self.all_threads:
            self._previous_thread_profiler = threading._profile_hook
            threading.setprofile(self)
        self._active, self._pending = True, False

    def stop(self):
        if self._active and not self._pending:
            self._pending = True
            if sys.getprofile() is self:
                sys.setprofile(self._previous_profiler)
                if not self._previous_profiler is None and \
                        isinstance(self._previous_profiler, TypeAgent):
                    self._previous_profiler._set_caller_level_shift(0)
            else:
                if not (sys.getprofile() is None and self._cleared):
                    warn('the system profiling hook has changed unexpectedly')
            if self.all_threads:
                if threading._profile_hook is self:
                    threading.setprofile(self._previous_thread_profiler)
                else:  # pragma: no cover
                    warn('the threading profiling hook has changed unexpectedly')
            self._active, self._pending = False, False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def __call__(self, frame, event, arg):
        if not self._active and not self._pending:
            # This happens if all_threads was enabled and a thread was created when the checker was
            # running but was then stopped. The thread's profiler callback can't be reset any other
            # way but this.
            sys.setprofile(self._previous_thread_profiler)
            return
        if self._pending:
            if self._previous_profiler is not None:
                self._previous_profiler(frame, event, arg)
        else:
            # If an actual profiler is running, don't include the type checking times in its results
            if event == 'call':
                if self._is_checking():
                    try:
                        #check_argument_types(caller_level=self._caller_level_shift+1)
                        _check_caller_type(False, caller_level=self._caller_level_shift+1)
                    except RuntimeError:
                        # Caller could not be determined.
                        pass
                    except pytypes.TypeCheckError:
                        _saved_profilers[threading.current_thread().ident] = self
                        self._cleared = True
                        raise
                if self._previous_profiler is not None:
                    self._previous_profiler(frame, event, arg)
            elif event == 'return':
                if self._previous_profiler is not None:
                    self._previous_profiler(frame, event, arg)
                if self._is_checking():
                    try:
                        #check_return_type(arg, caller_level=self._caller_level_shift+1)
                        _check_caller_type(True, None, arg, caller_level=self._caller_level_shift+1)
                    except RuntimeError:
                        # Caller could not be determined.
                        pass
                    except pytypes.TypeCheckError:
                        _saved_profilers[threading.current_thread().ident] = self
                        self._cleared = True
                        raise
                if self._is_logging():
                    try:
                        cllable, clss, slf, clsm, prop, prop_getter = \
                                _get_current_call_info(caller_level=self._caller_level_shift+1)
                        act_func = util._actualfunc(cllable)
                        specs = util.getargspecs(act_func)
                        call_args = util.get_current_args(self._caller_level_shift+1, cllable,
                                util.getargnames(specs))
                        if slf or clsm:
                            call_args = call_args[1:]
                        pytypes.log_type(call_args, arg, cllable if prop is None else prop,
                                slf, prop_getter, clss, specs)
                    except:
                        pass
            else:
                if self._previous_profiler is not None:
                    self._previous_profiler(frame, event, arg)
