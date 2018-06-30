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
import collections
import weakref
from inspect import isfunction, ismethod, isclass, ismodule
try:
    from backports.typing import Tuple, Dict, List, Set, FrozenSet, Union, Any, \
            Sequence, Mapping, TypeVar, Container, Generic, Sized, Iterable, Generator
except ImportError:
    from typing import Tuple, Dict, List, Set, FrozenSet, Union, Any, \
            Sequence, Mapping, TypeVar, Container, Generic, Sized, Iterable, Generator
try:
    # Python 3.7
    from typing import ForwardRef
    _typing_3_7 = True
except ImportError:
    from typing import _ForwardRef as ForwardRef
    _typing_3_7 = False
from warnings import warn, warn_explicit

import pytypes
from .stubfile_manager import _match_stub_type, as_stub_func_if_any
from .typecomment_parser import _get_typestrings, _funcsigtypesfromstring
from . import util

_annotated_modules = {}
_extra_dict = {}
_saved_profilers = {}
_fw_resolve_cache = {}
_checked_generator_types = weakref.WeakKeyDictionary()

for tp in typing.__all__:
    tpa = getattr(typing, tp)
    try:
        _extra_dict[tpa.__extra__] = tpa
    except AttributeError:
        try:
            _extra_dict[tpa.__origin__] = tpa
        except: pass
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
    See https://github.com/python/typing/issues/157 for details on why this
    is necessary.
    """
    pass


def _origin(tp):
    if _typing_3_7:
        res = tp.__origin__
        try:
            return _extra_dict[res]
        except KeyError:
            return res
    else:
        return tp.__origin__


def _extra(tp):
    #return tp.__extra__
    try:
        return tp.__extra__
    except AttributeError:
        pass
    try:
        return tp.__origin__
    except AttributeError:
        pass
    return None


def get_generator_yield_type(genr):
    """Obtains the yield type of a generator object.
    """
    return get_generator_type(genr).__args__[0]


def get_generator_type(genr):
    """Obtains PEP 484 style type of a generator object, i.e. returns a
    typing.Generator object.
    """
    if genr in _checked_generator_types:
        return _checked_generator_types[genr]
    if not genr.gi_frame is None and 'gen_type' in genr.gi_frame.f_locals:
        return genr.gi_frame.f_locals['gen_type']
    else:
        cllble, nesting, slf = util.get_callable_fq_for_code(genr.gi_code)
        if cllble is None:
            return Generator
        return _funcsigtypes(cllble, slf, nesting[-1] if slf else None,
                genr.gi_frame.f_globals if not genr.gi_frame is None else None)[1]


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
        if is_Generic(tp):
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
                if is_Generic(itrator) and itrator.__origin__ is typing.Iterator:
                    return itrator.__args__[0]
        if hasattr(obj, '__getitem__'):
            if has_type_hints(obj.__getitem__):
                itrator =  _funcsigtypes(obj.__getitem__, True, obj.__class__)[1]
                if is_Generic(itrator) and itrator.__origin__ is typing.Iterator:
                    return itrator.__args__[0]
        return None # means that type is unknown
    else:
        raise TypeError('Not an iterable: '+str(type(obj)))


def get_Generic_itemtype(sq, simplify=True):
    """Retrieves the item type from a PEP 484 generic or subclass of such.
    sq must be a typing.Tuple or (subclass of) typing.Iterable or typing.Container.
    Consequently this also works with typing.List, typing.Set and typing.Dict.
    Note that for typing.Dict and mapping types in general, the key type is regarded as item type.
    For typing.Tuple all contained types are returned as a typing.Union.
    If simplify == True some effort is taken to eliminate redundancies in such a union.
    """
    if is_Tuple(sq):
        if simplify:
            itm_tps = [x for x in get_Tuple_params(sq)]
            simplify_for_Union(itm_tps)
            return Union[tuple(itm_tps)]
        else:
            return Union[get_Tuple_params(sq)]
    else:
        try:
            res = _select_Generic_superclass_parameters(sq, typing.Container)
        except TypeError:
            res = None
        if res is None:
            try:
                res = _select_Generic_superclass_parameters(sq, typing.Iterable)
            except TypeError:
                pass
        if res is None:
            raise TypeError("Has no itemtype: "+type_str(sq))
        else:
            return res[0]


def get_Mapping_key_value(mp):
    """Retrieves the key and value types from a PEP 484 mapping or subclass of such.
    mp must be a (subclass of) typing.Mapping.
    """
    try:
        res = _select_Generic_superclass_parameters(mp, typing.Mapping)
    except TypeError:
        res = None
    if res is None:
        raise TypeError("Has no key/value types: "+type_str(mp))
    else:
        return tuple(res)


def get_Generic_parameters(tp, generic_supertype):
    """tp must be a subclass of generic_supertype.
    Retrieves the type values from tp that correspond to parameters
    defined by generic_supertype.

    E.g. get_Generic_parameters(tp, typing.Mapping) is equivalent
    to get_Mapping_key_value(tp) except for the error message.

    Note that get_Generic_itemtype(tp) is not exactly equal to
    get_Generic_parameters(tp, typing.Container), as that method
    additionally contains treatment for typing.Tuple and typing.Iterable.
    """
    try:
        res = _select_Generic_superclass_parameters(tp, generic_supertype)
    except TypeError:
        res = None
    if res is None:
        raise TypeError("%s has no proper parameters defined by %s."%
                (type_str(tp), type_str(generic_supertype)))
    else:
        return tuple(res)


def get_Tuple_params(tpl):
    """Python version independent function to obtain the parameters
    of a typing.Tuple object.
    Omits the ellipsis argument if present. Use is_Tuple_ellipsis for that.
    Tested with CPython 2.7, 3.5, 3.6 and Jython 2.7.1.
    """
    try:
        return tpl.__tuple_params__
    except AttributeError:
        try:
            if tpl.__args__ is None:
                return None
            # Python 3.6
            if tpl.__args__[0] == ():
                return ()
            else:
                if tpl.__args__[-1] is Ellipsis:
                    return tpl.__args__[:-1] if len(tpl.__args__) > 1 else None
                else:
                    return tpl.__args__
        except AttributeError:
            return None


def is_Tuple_ellipsis(tpl):
    """Python version independent function to check if a typing.Tuple object
    contains an ellipsis."""
    try:
        return tpl.__tuple_use_ellipsis__
    except AttributeError:
        try:
            if tpl.__args__ is None:
                return False
            # Python 3.6
            if tpl.__args__[-1] is Ellipsis:
                return True
        except AttributeError:
            pass
        return False


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


def is_Type(tp):
    """Python version independent check if an object is a type.
    For Python 3.7 onwards(?) this is not equivalent to
    ``isinstance(tp, type)`` any more, as that call would return
    ``False`` for PEP 484 types.
    Tested with CPython 2.7, 3.5, 3.6, 3.7 and Jython 2.7.1.
    """
    if isinstance(tp, type):
        return True
    try:
        typing._type_check(tp, '')
        return True
    except TypeError:
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


def is_Tuple(tp):
    try:
        return isinstance(tp, typing.TupleMeta)
    except AttributeError:
        try:
            return isinstance(tp, typing._GenericAlias) and \
                    tp.__origin__ is tuple
        except AttributeError:
            return False


def is_Generic(tp):
    try:
        return isinstance(tp, typing.GenericMeta)
    except AttributeError:
        try:
            return issubclass(tp, typing.Generic)
# 			return isinstance(tp, typing._VariadicGenericAlias) and \
# 					tp.__origin__ is tuple
        except AttributeError:
            return False
        except TypeError:
            # Shall we accept _GenericAlias, i.e. Tuple, Union, etc?
            return isinstance(tp, typing._GenericAlias)


def is_Callable(tp):
    try:
        return isinstance(tp, typing.CallableMeta)
    except AttributeError:
        try:
            return isinstance(tp, typing._VariadicGenericAlias) and \
                    tp.__origin__ is collections.abc.Callable
        except AttributeError:
            return False


def deep_type(obj, depth = None, max_sample = None, get_type = None):
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
    Optionally, a custom get_type function can be provided to further
    customize how types are resolved. By default it uses type function.
    """
    return _deep_type(obj, [], 0, depth, max_sample, get_type)


def _deep_type(obj, checked, checked_len, depth = None, max_sample = None, get_type = None):
    """checked_len allows to operate with a fake length for checked.
    This is necessary to ensure that each depth level operates based
    on the same checked list subset. Otherwise our recursion detection
    mechanism can fall into false-positives.
    """
    if depth is None:
        depth = pytypes.default_typecheck_depth
    if max_sample is None:
        max_sample = pytypes.deep_type_samplesize
    if -1 != max_sample < 2:
        max_sample = 2
    if get_type is None:
        get_type = type
    try:
        res = obj.__orig_class__
    except AttributeError:
        res = get_type(obj)
    if depth == 0 or util._is_in(obj, checked[:checked_len]):
        return res
    elif not util._is_in(obj, checked[checked_len:]):
        checked.append(obj)
    # We must operate with a consistent checked list for one certain depth level
    # to avoid issues with a list, tuple, dict, etc containing the same element
    # multiple times. This could otherwise be misconcepted as a recursion.
    # Using a fake len checked_len2 ensures this. Each depth level operates with
    # a common fake length of checked list:
    checked_len2 = len(checked)
    if res == tuple:
        res = Tuple[tuple(_deep_type(t, checked, checked_len2, depth-1, None, get_type) for t in obj)]
    elif res == list:
        if len(obj) == 0:
            return Empty[List]
        if max_sample == -1 or max_sample >= len(obj)-1 or len(obj) <= 2:
            tpl = tuple(_deep_type(t, checked, checked_len2, depth-1, None, get_type) for t in obj)
        else:
            # In case of lists I somehow feel it's better to ensure that
            # first and last element are part of the sample
            sample = [0, len(obj)-1]
            try:
                rsmp = random.sample(xrange(1, len(obj)-1), max_sample-2)
            except NameError:
                rsmp = random.sample(range(1, len(obj)-1), max_sample-2)
            sample.extend(rsmp)
            tpl = tuple(_deep_type(obj[t], checked, checked_len2, depth-1, None, get_type) for t in sample)
        res = List[Union[tpl]]
    elif res == dict:
        if len(obj) == 0:
            return Empty[Dict]
        if max_sample == -1 or max_sample >= len(obj)-1 or len(obj) <= 2:
            try:
                # We prefer a view (avoid copy)
                tpl1 = tuple(_deep_type(t, checked, checked_len2, depth-1, None, get_type) \
                        for t in obj.viewkeys())
                tpl2 = tuple(_deep_type(t, checked, checked_len2, depth-1, None, get_type) \
                        for t in obj.viewvalues())
            except AttributeError:
                # Python 3 gives views like this:
                tpl1 = tuple(_deep_type(t, checked, checked_len2, depth-1, None, get_type) for t in obj.keys())
                tpl2 = tuple(_deep_type(t, checked, checked_len2, depth-1, None, get_type) for t in obj.values())
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
            tpl1 = tuple(_deep_type(t, checked, checked_len2, depth-1, None, get_type) for t in ksmpl)
            tpl2 = tuple(_deep_type(t, checked, checked_len2, depth-1, None, get_type) for t in vsmpl)
        res = Dict[Union[tpl1], Union[tpl2]]
    elif res == set or res == frozenset:
        if res == set:
            typ = Set
        else:
            typ = FrozenSet
        if len(obj) == 0:
            return Empty[typ]
        if max_sample == -1 or max_sample >= len(obj)-1 or len(obj) <= 2:
            tpl = tuple(_deep_type(t, checked, depth-1, None, None, get_type) for t in obj)
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
            tpl = tuple(_deep_type(t, checked, depth-1, None, None, get_type) for t in smpl)
        res = typ[Union[tpl]]
    elif res == types.GeneratorType:
        res = get_generator_type(obj)
    elif sys.version_info.major == 2 and isinstance(obj, types.InstanceType):
        # For old-style instances return the actual class:
        return obj.__class__
    elif _has_base(res, Container) and len(obj) == 0:
        return Empty[res]
    elif hasattr(res, '__origin__') and _has_base(res.__origin__, Container) and len(obj) == 0:
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
    elif is_Callable(tp) and typing.Callable in assumed_globals:
        try:
            return assumed_globals[typing.Callable]
        except:
            return tp_name
    elif update_assumed_globals == True:
        if not assumed_globals is None:
            if hasattr(tp, '__origin__') and not tp.__origin__ is None:
                toadd = tp.__origin__
            elif is_Callable(tp):
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
            implicit_globals=None, bound_Generic=None, bound_typevars=None):
    """Generates a nicely readable string representation of the given type.
    The returned representation is workable as a source code string and would
    reconstruct the given type if handed to eval, provided that globals/locals
    are configured appropriately (e.g. assumes that various types from typing
    have been imported).
    Used as type-formatting backend of ptypes' code generator abilities
    in modules typelogger and stubfile_2_converter.

    If tp contains unbound TypeVars and bound_Generic is provided, this
    function attempts to retrieve corresponding values for the unbound TypeVars
    from bound_Generic.

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
                implicit_globals, bound_Generic, bound_typevars) for tp0 in tp])+')'
    try:
        return type_str(tp.__orig_class__, assumed_globals, update_assumed_globals,
                implicit_globals, bound_Generic, bound_typevars)
    except AttributeError:
        pass
    tp = _match_stub_type(tp)
    if isinstance(tp, TypeVar):
        prm = None
        if not bound_typevars is None:
            try:
                prm = bound_typevars[tp]
            except:
                pass
        if prm is None and not bound_typevars is None and tp in bound_typevars:
            prm = bound_typevars[tp]
        if prm is None and not bound_Generic is None:
            prm = get_arg_for_TypeVar(tp, bound_Generic)
        if not prm is None:
            return type_str(prm, assumed_globals, update_assumed_globals,
                    implicit_globals, bound_Generic, bound_typevars)
        return tp.__name__
    elif isinstance(tp, ForwardRef):
        return "'%s'" % tp.__forward_arg__
    elif isclass(tp) and not is_Generic(tp) \
            and not hasattr(typing, tp.__name__):
        tp_name = _tp_relfq_name(tp, None, assumed_globals, update_assumed_globals,
                implicit_globals)
        prm = ''
        if hasattr(tp, '__args__') and not tp.__args__ is None:
            params = [type_str(param, assumed_globals, update_assumed_globals,
                    implicit_globals, bound_Generic, bound_typevars) for param in tp.__args__]
            prm = '[%s]'%', '.join(params)
        return tp_name+prm
    elif is_Union(tp):
        prms = get_Union_params(tp)
        params = [type_str(param, assumed_globals, update_assumed_globals,
                implicit_globals, bound_Generic, bound_typevars) for param in prms]
        # See: https://github.com/Stewori/pytypes/issues/44
        if pytypes.canonical_type_str:
            params = sorted(params)
        return '%s[%s]'%(_tp_relfq_name(Union, 'Union', assumed_globals,
                update_assumed_globals, implicit_globals), ', '.join(params))
    elif is_Tuple(tp):
        prms = get_Tuple_params(tp)
        tpl_params = [type_str(param, assumed_globals, update_assumed_globals,
                implicit_globals, bound_Generic, bound_typevars) for param in prms]
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
        params = [type_str(param, assumed_globals, update_assumed_globals,
                implicit_globals, bound_Generic, bound_typevars) for param in args]
        if hasattr(tp, '__result__'):
            return '%s[[%s], %s]'%(tp_name, ', '.join(params),
                    type_str(tp.__result__, assumed_globals, update_assumed_globals,
                    implicit_globals, bound_Generic, bound_typevars))
        elif is_Callable(tp):
            return '%s[[%s], %s]'%(tp_name, ', '.join(params[:-1]),
                    type_str(params[-1], assumed_globals, update_assumed_globals,
                    implicit_globals, bound_Generic, bound_typevars))
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
                    util._warn_argname('classmethod using non-idiomatic cls argname',
                            func0, slf, clsm, clss)
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


def resolve_fw_decl(in_type, module_name=None, globs=None, level=0,
        search_stack_depth=2):
    '''Resolves forward references in ``in_type``, see
    https://www.python.org/dev/peps/pep-0484/#forward-references.


    Note:

    ``globs`` should be a dictionary containing values for the names
    that must be resolved in ``in_type``. If ``globs`` is not provided, it
    will be created by ``__globals__`` from the module named ``module_name``,
    plus ``__locals__`` from the last ``search_stack_depth`` stack frames (Default: 2),
    beginning at the calling function. This is to resolve cases where ``in_type`` and/or
    types it fw-references are defined inside a function.

    To prevent walking the stack, set ``search_stack_depth=0``.
    Ideally provide a proper ``globs`` for best efficiency.
    See ``util.get_function_perspective_globals`` for obtaining a ``globs`` that can be
    cached. ``util.get_function_perspective_globals`` works like described above.
    '''
    # Also see discussion at https://github.com/Stewori/pytypes/pull/43
    if in_type in _fw_resolve_cache:
        return _fw_resolve_cache[in_type], True
    if globs is None:
        #if not module_name is None:
        globs = util.get_function_perspective_globals(module_name, level+1,
                level+1+search_stack_depth)
    if isinstance(in_type, _basestring):
        # For the case that a pure forward ref is given as string
        out_type = eval(in_type, globs)
        _fw_resolve_cache[in_type] = out_type
        return out_type, True
    elif isinstance(in_type, typing._ForwardRef):
        # Todo: Mabe somehow get globs from in_type.__forward_code__
        if not in_type.__forward_evaluated__:
            in_type.__forward_value__ = eval(in_type.__forward_arg__, globs)
            in_type.__forward_evaluated__ = True
            return in_type, True
    elif is_Tuple(in_type):
        return in_type, any([resolve_fw_decl(in_tp, None, globs)[1] \
                for in_tp in get_Tuple_params(in_type)])
    elif is_Union(in_type):
        return in_type, any([resolve_fw_decl(in_tp, None, globs)[1] \
                for in_tp in get_Union_params(in_type)])
    elif is_Callable(in_type):
        args, res = get_Callable_args_res(in_type)
        ret = any([resolve_fw_decl(in_tp, None, globs)[1] \
                for in_tp in args])
        ret = resolve_fw_decl(res, None, globs)[1] or ret
        return in_type, ret
    elif hasattr(in_type, '__args__') and in_type.__args__ is not None:
        return in_type, any([resolve_fw_decl(in_tp, None, globs)[1] \
                for in_tp in in_type.__args__])
    return in_type, False


def _funcsigtypes(func0, slf, func_class=None, globs=None, prop_getter=False,
        unspecified_type=Any, infer_defaults=None):
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
                else:
                    # We manually create globals here for resolve_fw_decl, because globals
                    # might be needed again later. Usually resolve_fw_decl can create
                    # globals internally.
                    if globs is None:
                        globs = util.get_function_perspective_globals(func.__module__, 3)
                    val = resolve_fw_decl(val, func.__module__, globs, 3)[0]
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
        if not pytypes.annotations_override_typestring and not \
                (tpStr is None or tpStr[0] is None or tpStr[0] == 'ignore'):
            if pytypes.strict_annotation_collision_check:
                raise TypeError('%s.%s has multiple type declarations.'
                        % (func.__module__, func.__name__))
            else:
                if globs is None:
                    globs = util.get_function_perspective_globals(func.__module__, 3)
                resType2 = _funcsigtypesfromstring(*tpStr, argspec=argSpecs, glbls=globs,
                        argCount=len(argNames), unspecified_type=unspecified_type,
                        defaults=argSpecs.defaults if infer_defaults else None,
                        func=actual_func, func_class=func_class, slf=slf)
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
    if globs is None:
        globs = util.get_function_perspective_globals(func.__module__, 3)
    res = _funcsigtypesfromstring(*tpStr, glbls=globs, argspec=argSpecs,
            argCount=len(argNames),
            defaults = argSpecs.defaults if infer_defaults else None,
            unspecified_type=unspecified_type, func=actual_func,
            func_class=func_class, slf=slf)
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
                res2 = _funcsigtypesfromstring(*tpStr, argspec = argSpecs, glbls = globs,
                        argCount = len(argNames), unspecified_type = unspecified_type,
                        func = actual_func, func_class = func_class, slf = slf)
                func0.__annotations__ = _get_type_hints(func0, res2[0], res2[1])
    return res


def _issubclass_Mapping_covariant(subclass, superclass, bound_Generic, bound_typevars,
            bound_typevars_readonly, follow_fwd_refs, _recursion_check):
    """Helper for _issubclass, a.k.a pytypes.issubtype.
    This subclass-check treats Mapping-values as covariant.
    """
    if is_Generic(subclass):
        if subclass.__origin__ is None or not issubclass(subclass.__origin__, Mapping):
            return _issubclass_Generic(subclass, superclass, bound_Generic, bound_typevars,
                    bound_typevars_readonly, follow_fwd_refs, _recursion_check)
        if superclass.__args__ is None:
            if not pytypes.check_unbound_types:
                raise TypeError("Attempted to check unbound mapping type(superclass): "+
                        str(superclass))
            if pytypes.strict_unknown_check:
                # Nothing is subtype of unknown type
                return False
            super_args = (Any, Any)
        else:
            super_args = superclass.__args__
        if subclass.__args__ is None:
            if not pytypes.check_unbound_types:
                raise TypeError("Attempted to check unbound mapping type(subclass): "+
                        str(subclass))
            if pytypes.strict_unknown_check:
                # Nothing can subclass unknown type
                # For value type it would be okay if superclass had Any as value type,
                # as unknown type is subtype of Any. However, since key type is invariant
                # and also unknown, it cannot pass.
                return False
            sub_args = (Any, Any)
        else:
            sub_args = subclass.__args__
        if not _issubclass(sub_args[0], super_args[0],
                bound_Generic, bound_typevars,
                bound_typevars_readonly, follow_fwd_refs, _recursion_check):
            return False
        if not _issubclass(sub_args[1], super_args[1],
                bound_Generic, bound_typevars,
                bound_typevars_readonly, follow_fwd_refs, _recursion_check):
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
        if is_Generic(bs):
            if not bs.__origin__ is None and len(bs.__origin__.__parameters__) > 0:
                for i in range(len(bs.__args__)):
                    ors = bs.__origin__.__parameters__[i]
                    if bs.__args__[i] != ors and isinstance(bs.__args__[i], TypeVar):
                        param_map[ors] = bs.__args__[i]
            if (bs.__origin__ is superclass_origin or \
                    (bs.__origin__ is None and bs is superclass_origin)):
                prms = []
                try:
                    if len(bs.__origin__.__parameters__) > len(bs.__parameters__):
                        prms.extend(bs.__origin__.__parameters__)
                    else:
                        prms.extend(bs.__parameters__)
                except:
                    prms.extend(bs.__parameters__)
                for i in range(len(prms)):
                    while prms[i] in param_map:
                        prms[i] = param_map[prms[i]]
                return prms
            try:
                stack.extend(bs.__orig_bases__)
            except AttributeError:
                stack.extend(bs.__bases__)
    return None


def _find_base_with_origin(subclass, superclass_origin):
    try:
        if not subclass.__origin__ is None and issubclass(subclass.__origin__, superclass_origin):
            return subclass
    except AttributeError:
        return None
    try:
        orig_bases = subclass.__orig_bases__
    except AttributeError:
        orig_bases = subclass.__bases__
    for bs in orig_bases:
        try:
            if not bs.__origin__ is None and issubclass(bs.__origin__, superclass_origin):
                return bs
        except AttributeError:
            return None
    for bs in orig_bases:
        res = _find_base_with_origin(bs, superclass_origin)
        if not res is None:
            return res


def _select_Generic_superclass_parameters(subclass, superclass_origin):
    """Helper for _issubclass_Generic.
    """
    subclass = _find_base_with_origin(subclass, superclass_origin)
    if subclass is None:
        return None
    if subclass.__origin__ is superclass_origin:
        return subclass.__args__
    prms = _find_Generic_super_origin(subclass, superclass_origin)
    res = []
    for prm in prms:
        sub_search = subclass
        while not sub_search is None:
            try:
                res.append(sub_search.__args__[sub_search.__origin__.__parameters__.index(prm)])
                break
            except ValueError:
                # We search the closest base that actually contains the parameter
                sub_search = _find_base_with_origin(
                        sub_search.__origin__, superclass_origin)
        else:
            return None
    return res


def get_arg_for_TypeVar(typevar, generic):
    """Retrieves the parameter value of a given TypeVar from a Generic.
    Returns None if the generic does not contain an appropriate value.
    Note that the TypeVar is compared by instance and not by name.
    E.g. using a local TypeVar T would yield different results than
    using typing.T despite the equal name.
    """
    return _get_arg_for_TypeVar(typevar, generic, generic)


def _get_arg_for_TypeVar(typevar, generic, arg_holder):
    try:
        if arg_holder.__args__ is None:
            try:
                bases = generic.__orig_bases__
            except AttributeError:
                bases = generic.__bases__
            for i in range(len(bases)):
                res = _get_arg_for_TypeVar(typevar, generic.__bases__[i], bases[i])
                if not res is None:
                    return res
    except AttributeError:
        return None
    try:
        if typevar in generic.__parameters__:
            idx = generic.__parameters__.index(typevar)
            res = _select_Generic_superclass_parameters(arg_holder, generic)
            return res[idx]
    except (AttributeError, TypeError):
        return None
    try:
        # typing-3.5.3.0 special treatment:
        # It does not contain __origin__ in __bases__.
        if not generic.__bases__[0] == generic.__origin__:
            res = _get_arg_for_TypeVar(typevar, generic.__origin__, arg_holder)
            if not res is None:
                return res
    except:
        pass
    for base in generic.__bases__:
        res = _get_arg_for_TypeVar(typevar, base, arg_holder)
        if not res is None:
            return res


def _issubclass_Generic(subclass, superclass, bound_Generic, bound_typevars,
            bound_typevars_readonly, follow_fwd_refs, _recursion_check):
    """Helper for _issubclass, a.k.a pytypes.issubtype.
    """
    # this function is partly based on code from typing module 3.5.2.2
    if subclass is None:
        return False
    if subclass in _extra_dict:
        subclass = _extra_dict[subclass]
    if is_Tuple(subclass):
        tpl_prms = get_Tuple_params(subclass)
        if not tpl_prms is None and len(tpl_prms) == 0:
            # (This section is required because Empty shall not be
            # used on Tuples.)
            # an empty Tuple is any Sequence, regardless of type
            # note that we needn't consider superclass beeing a tuple,
            # because that should have been checked in _issubclass_Tuple
            return issubclass(typing.Sequence,
                    superclass if superclass.__origin__ is None else superclass.__origin__)
        subclass = Sequence[Union[tpl_prms]]
    if is_Generic(subclass):
        # For a class C(Generic[T]) where T is co-variant,
        # C[X] is a subclass of C[Y] iff X is a subclass of Y.
        origin = _origin(superclass) #superclass.__origin__
        if subclass.__origin__ is None:
            try:
                orig_bases = subclass.__orig_bases__
            except AttributeError:
                # Before typing 3.5.3.0 __bases__ used to contain all info that later
                # became reserved for __orig_bases__. So we can use it as a fallback:
                orig_bases = subclass.__bases__
            for scls in orig_bases:
                if is_Generic(scls):
                    if _issubclass_Generic(scls, superclass, bound_Generic, bound_typevars,
                            bound_typevars_readonly, follow_fwd_refs,
                            _recursion_check):
                        return True
        #Formerly: if origin is not None and origin is subclass.__origin__:
        elif origin is not None and \
                _issubclass(_origin(subclass), origin, bound_Generic, bound_typevars,
                        # In Python 3.7 this can currently cause infinite recursion.
                        bound_typevars_readonly, follow_fwd_refs, _recursion_check):
# 				_issubclass(subclass.__origin__, origin, bound_Generic, bound_typevars,
# 						bound_typevars_readonly, follow_fwd_refs, _recursion_check):
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
                        if not _issubclass(p_cls, p_self, bound_Generic, bound_typevars,
                                bound_typevars_readonly, follow_fwd_refs,
                                _recursion_check):
                            break
                    elif p_origin.__contravariant__:
                        # Contravariant.  I think it's the opposite. :-)
                        if not _issubclass(p_self, p_cls, bound_Generic, bound_typevars,
                                bound_typevars_readonly, follow_fwd_refs,
                                _recursion_check):
                            break
                    else:
                        # Invariant -- p_cls and p_self must equal.
                        if p_self != p_cls:
                            if not _issubclass(p_cls, p_self, bound_Generic, bound_typevars,
                                    bound_typevars_readonly, follow_fwd_refs,
                                    _recursion_check):
                                break
                            if not _issubclass(p_self, p_cls, bound_Generic, bound_typevars,
                                    bound_typevars_readonly, follow_fwd_refs,
                                    _recursion_check):
                                break
                else:
                    # If the origin's parameter is not a typevar,
                    # insist on invariance.
                    if p_self != p_cls:
                        if not _issubclass(p_cls, p_self, bound_Generic, bound_typevars,
                                    bound_typevars_readonly, follow_fwd_refs,
                                    _recursion_check):
                            break
                        if not _issubclass(p_self, p_cls, bound_Generic, bound_typevars,
                                    bound_typevars_readonly, follow_fwd_refs,
                                    _recursion_check):
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
                raise TypeError("Attempted to check unbound type(superclass): "+str(superclass))
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
    try:
        if type.__subclasscheck__(superclass, subclass):
            return True
    except TypeError: pass
    if _extra(superclass) is None or is_Generic(subclass):
        return False
    return _issubclass_2(subclass, _extra(superclass), bound_Generic, bound_typevars,
            bound_typevars_readonly, follow_fwd_refs, _recursion_check)


def _issubclass_Tuple(subclass, superclass, bound_Generic, bound_typevars,
            bound_typevars_readonly, follow_fwd_refs, _recursion_check):
    """Helper for _issubclass, a.k.a pytypes.issubtype.
    """
    # this function is partly based on code from typing module 3.5.2.2
    if subclass in _extra_dict:
        subclass = _extra_dict[subclass]
    if not is_Type(subclass):
        # To TypeError.
        return False
    if not is_Tuple(subclass):
        if is_Generic(subclass):
            try:
                return _issubclass_Generic(subclass, superclass,
                        bound_Generic, bound_typevars,
                        bound_typevars_readonly, follow_fwd_refs,
                        _recursion_check)
            except:
                pass
        elif is_Union(subclass):
            return all(_issubclass_Tuple(t, superclass, bound_Generic, bound_typevars,
                    bound_typevars_readonly, follow_fwd_refs, _recursion_check)
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
    # For now we check ellipsis in most explicit manner.
    # Todo: Compactify and Pythonify ellipsis branches (tests required before this).
    if is_Tuple_ellipsis(subclass):
        if is_Tuple_ellipsis(superclass):
            # both are ellipsis, so no length check
            common = min(len(super_args), len(sub_args))
            for i in range(common):
                if not _issubclass(sub_args[i], super_args[i], bound_Generic, bound_typevars,
                        bound_typevars_readonly, follow_fwd_refs, _recursion_check):
                    return False
            if len(super_args) < len(sub_args):
                for i in range(len(super_args), len(sub_args)):
                    # Check remaining super args against the ellipsis type
                    if not _issubclass(sub_args[i], super_args[-1], bound_Generic, bound_typevars,
                            bound_typevars_readonly, follow_fwd_refs, _recursion_check):
                        return False
            elif len(super_args) > len(sub_args):
                for i in range(len(sub_args), len(super_args)):
                    # Check remaining super args against the ellipsis type
                    if not _issubclass(sub_args[-1], super_args[i], bound_Generic, bound_typevars,
                            bound_typevars_readonly, follow_fwd_refs, _recursion_check):
                        return False
            return True
        else:
            # only subclass has ellipsis
            if len(super_args) < len(sub_args)-1:
                return False
            for i in range(len(sub_args)-1):
                if not _issubclass(sub_args[i], super_args[i], bound_Generic, bound_typevars,
                        bound_typevars_readonly, follow_fwd_refs, _recursion_check):
                    return False
            for i in range(len(sub_args), len(super_args)):
                # Check remaining super args against the ellipsis type
                if not _issubclass(sub_args[-1], super_args[i], bound_Generic, bound_typevars,
                        bound_typevars_readonly, follow_fwd_refs, _recursion_check):
                    return False
            return True
    elif is_Tuple_ellipsis(superclass):
        # only superclass has ellipsis
        if len(super_args)-1 > len(sub_args):
            return False
        for i in range(len(super_args)-1):
            if not _issubclass(sub_args[i], super_args[i], bound_Generic, bound_typevars,
                    bound_typevars_readonly, follow_fwd_refs, _recursion_check):
                return False
        for i in range(len(super_args), len(sub_args)):
            # Check remaining sub args against the ellipsis type
            if not _issubclass(sub_args[i], super_args[-1], bound_Generic, bound_typevars,
                    bound_typevars_readonly, follow_fwd_refs, _recursion_check):
                return False
        return True
    else:
        # none has ellipsis, so strict length check
        return (len(super_args) == len(sub_args) and
                all(_issubclass(x, p, bound_Generic, bound_typevars,
                bound_typevars_readonly, follow_fwd_refs, _recursion_check)
                for x, p in zip(sub_args, super_args)))


def _issubclass_Union(subclass, superclass, bound_Generic, bound_typevars,
            bound_typevars_readonly, follow_fwd_refs, _recursion_check):
    """Helper for _issubclass, a.k.a pytypes.issubtype.
    """
    if not follow_fwd_refs:
        return _issubclass_Union_rec(subclass, superclass, bound_Generic, bound_typevars,
            bound_typevars_readonly, follow_fwd_refs, _recursion_check)
    try:
        # try to succeed fast, before we go the expensive way involving recursion checks
        return _issubclass_Union_rec(subclass, superclass, bound_Generic, bound_typevars,
            bound_typevars_readonly, False, _recursion_check)
    except pytypes.ForwardRefError:
        return _issubclass_Union_rec(subclass, superclass, bound_Generic, bound_typevars,
            bound_typevars_readonly, follow_fwd_refs, _recursion_check)


def _issubclass_Union_rec(subclass, superclass, bound_Generic, bound_typevars,
            bound_typevars_readonly, follow_fwd_refs, _recursion_check):
    """Helper for _issubclass_Union.
    """
    # this function is partly based on code from typing module 3.5.2.2
    super_args = get_Union_params(superclass)
    if super_args is None:
        return is_Union(subclass)
    elif is_Union(subclass):
        sub_args = get_Union_params(subclass)
        if sub_args is None:
            return False
        return all(_issubclass(c, superclass, bound_Generic, bound_typevars,
                bound_typevars_readonly, follow_fwd_refs, _recursion_check) \
                for c in (sub_args))
    elif isinstance(subclass, TypeVar):
        if subclass in super_args:
            return True
        if subclass.__constraints__:
            return _issubclass(Union[subclass.__constraints__],
                    superclass, bound_Generic, bound_typevars,
                    bound_typevars_readonly, follow_fwd_refs, _recursion_check)
        return False
    else:
        return any(_issubclass(subclass, t, bound_Generic, bound_typevars,
                bound_typevars_readonly, follow_fwd_refs, _recursion_check) \
                for t in super_args)


# This is just a crutch, because issubclass sometimes tries to be too smart.
# Note that this doesn't consider __subclasshook__ etc, so use with care!
def _has_base(cls, base):
    """Helper for _issubclass, a.k.a pytypes.issubtype.
    """
    if cls is base:
        return True
    elif cls is None:
        return False
    try:
        for bs in cls.__bases__:
            if _has_base(bs, base):
                return True
    except:
        pass
    return False


def _issubclass(subclass, superclass, bound_Generic=None, bound_typevars=None,
            bound_typevars_readonly=False, follow_fwd_refs=True, _recursion_check=None):
    """Access this via ``pytypes.is_subtype``.
    Works like ``issubclass``, but supports PEP 484 style types from ``typing`` module.

    subclass : type
    The type to check for being a subtype of ``superclass``.

    superclass : type
    The type to check for being a supertype of ``subclass``.

    bound_Generic : Optional[Generic]
    A type object holding values for unbound typevars occurring in ``subclass`` or ``superclass``.
    Default: None
    If subclass or superclass contains unbound ``TypeVar``s and ``bound_Generic`` is
    provided, this function attempts to retrieve corresponding values for the
    unbound ``TypeVar``s from ``bound_Generic``.
    In collision case with ``bound_typevars`` the value from ``bound_Generic`` if preferred.

    bound_typevars : Optional[Dict[typing.TypeVar, type]]
    A dictionary holding values for unbound typevars occurring in ``subclass`` or ``superclass``.
    Default: {}
    Depending on ``bound_typevars_readonly`` pytypes can also bind values to typevars as needed.
    This is done by inserting according mappings into this dictionary. This can e.g. be useful to
    infer values for ``TypeVar``s or to consistently check a set of ``TypeVar``s across multiple
    calls, e.g. when checking all arguments of a function call.
    In collision case with ``bound_Generic`` the value from ``bound_Generic`` if preferred.

    bound_typevars_readonly : bool
    Defines if pytypes is allowed to write into the ``bound_typevars`` dictionary.
    Default: True
    If set to False, pytypes cannot assign values to ``TypeVar``s, but only checks regarding
    values already present in ``bound_typevars`` or ``bound_Generic``.

    follow_fwd_refs : bool
    Defines if ``_ForwardRef``s should be explored.
    Default: True
    If this is set to ``False`` and a ``_ForwardRef`` is encountered, pytypes aborts the check
    raising a ForwardRefError.

    _recursion_check : Optional[Dict[type, Set[type]]]
    Internally used for recursion checks.
    Default: None
    If ``Union``s and ``_ForwardRef``s occur in the same type, recursions can occur. As soon as
    a ``_ForwardRef`` is encountered, pytypes automatically creates this dictionary and
    continues in recursion-proof manner.
    """
    if bound_typevars is None:
        bound_typevars = {}
    if superclass is Any:
        return True
    if subclass == superclass:
        return True
    if subclass is Any:
        return superclass is Any
    if isinstance(subclass, ForwardRef) or isinstance(superclass, ForwardRef):
        if not follow_fwd_refs:
            raise pytypes.ForwardRefError(
                    "ForwardRef encountered, but follow_fwd_refs is False: '%s'\n%s"%
                    ((subclass if isinstance(subclass, ForwardRef) else superclass)
                    .__forward_arg__,
                    "Retry with follow_fwd_refs=True."))
        # Now that forward refs are in the game, we must continue in recursion-proof manner:
        if _recursion_check is None:
            _recursion_check = {superclass: {subclass}}
        elif superclass in _recursion_check:
            if subclass in _recursion_check[superclass]:
                # recursion detected
                return False
            else:
                _recursion_check[superclass].add(subclass)
        else:
            _recursion_check[superclass] = {subclass}
        if isinstance(subclass, ForwardRef):
            if not subclass.__forward_evaluated__:
                raise pytypes.ForwardRefError("ForwardRef in subclass not evaluated: '%s'\n%s"%
                        (subclass.__forward_arg__, "Use pytypes.resolve_fw_decl"))
            else:
                return _issubclass(subclass.__forward_value__, superclass,
                        bound_Generic, bound_typevars,
                        bound_typevars_readonly, follow_fwd_refs, _recursion_check)
        else: # isinstance(superclass, ForwardRef)
            if not superclass.__forward_evaluated__:
                raise pytypes.ForwardRefError("ForwardRef in superclass not evaluated: '%s'\n%s"%
                        (superclass.__forward_arg__, "Use pytypes.resolve_fw_decl"))
            else:
                return _issubclass(subclass, superclass.__forward_value__,
                        bound_Generic, bound_typevars,
                        bound_typevars_readonly, follow_fwd_refs, _recursion_check)
    if pytypes.apply_numeric_tower:
        if superclass is float and subclass is int:
            return True
        elif superclass is complex and \
                (subclass is int or subclass is float):
            return True
    if superclass in _extra_dict:
        superclass = _extra_dict[superclass]
    try:
        if _issubclass_2(subclass, Empty, bound_Generic, bound_typevars,
                    bound_typevars_readonly, follow_fwd_refs, _recursion_check):
            for empty_target in [Container, Sized, Iterable]:
                # We cannot simply use Union[Container, Sized, Iterable] as empty_target
                # because of implementation detail behavior of _issubclass_2.
                # It would e.g. cause false negative result of
                # is_subtype(Empty[Dict], Empty[Container])
                try:
                    if _issubclass_2(superclass.__origin__, empty_target,
                            bound_Generic, bound_typevars,
                            bound_typevars_readonly, follow_fwd_refs, _recursion_check):
                        return _issubclass_2(subclass.__args__[0], superclass.__origin__,
                                bound_Generic, bound_typevars,
                                bound_typevars_readonly, follow_fwd_refs, _recursion_check)
                except: pass
                if _issubclass_2(superclass, empty_target,
                        bound_Generic, bound_typevars,
                        bound_typevars_readonly, follow_fwd_refs, _recursion_check):
                    return _issubclass_2(subclass.__args__[0], superclass,
                            bound_Generic, bound_typevars,
                            bound_typevars_readonly, follow_fwd_refs, _recursion_check)
    except: pass
    try:
        if _issubclass_2(superclass, Empty, bound_Generic, bound_typevars,
                    bound_typevars_readonly, follow_fwd_refs, _recursion_check):
            for empty_target in [Container, Sized, Iterable]:
                # We cannot simply use Union[Container, Sized, Iterable] as empty_target
                # because of implementation detail behavior of _issubclass_2.
                try:
                    if _issubclass_2(subclass.__origin__, empty_target,
                            bound_Generic, bound_typevars,
                            bound_typevars_readonly, follow_fwd_refs, _recursion_check):
                        return _issubclass_2(subclass.__origin__, superclass.__args__[0],
                                bound_Generic, bound_typevars,
                                bound_typevars_readonly, follow_fwd_refs, _recursion_check)
                except: pass
                if _issubclass_2(subclass, empty_target, bound_Generic, bound_typevars,
                            bound_typevars_readonly, follow_fwd_refs, _recursion_check):
                    return _issubclass_2(subclass, superclass.__args__[0],
                            bound_Generic, bound_typevars,
                            bound_typevars_readonly, follow_fwd_refs, _recursion_check)
    except: pass
    if isinstance(superclass, TypeVar):
        if not superclass.__bound__ is None:
            if not _issubclass(subclass, superclass.__bound__, bound_Generic, bound_typevars,
                        bound_typevars_readonly, follow_fwd_refs, _recursion_check):
                return False
        if not bound_typevars is None:
            try:
                if superclass.__contravariant__:
                    return _issubclass(bound_typevars[superclass], subclass, bound_Generic,
                            bound_typevars, bound_typevars_readonly, follow_fwd_refs,
                            _recursion_check)
                elif superclass.__covariant__:
                    return _issubclass(subclass, bound_typevars[superclass], bound_Generic,
                            bound_typevars, bound_typevars_readonly, follow_fwd_refs,
                            _recursion_check)
                else:
                    return _issubclass(bound_typevars[superclass], subclass, bound_Generic,
                            bound_typevars, bound_typevars_readonly, follow_fwd_refs,
                            _recursion_check) and \
                            _issubclass(subclass, bound_typevars[superclass], bound_Generic,
                            bound_typevars, bound_typevars_readonly, follow_fwd_refs,
                            _recursion_check)
            except:
                pass
        if not bound_Generic is None:
            superclass = get_arg_for_TypeVar(superclass, bound_Generic)
            if not superclass is None:
                return _issubclass(subclass, superclass, bound_Generic, bound_typevars,
                        bound_typevars_readonly, follow_fwd_refs, _recursion_check)
        if not bound_typevars is None:
            if bound_typevars_readonly:
                return False
            else:
                # bind it...
                bound_typevars[superclass] = subclass
                return True
        return False
    if isinstance(subclass, TypeVar):
        if not bound_typevars is None:
            try:
                return _issubclass(bound_typevars[subclass], superclass, bound_Generic,
                        bound_typevars, bound_typevars_readonly, follow_fwd_refs,
                        _recursion_check)
            except:
                pass
        if not bound_Generic is None:
            subclass = get_arg_for_TypeVar(subclass, bound_Generic)
            if not subclass is None:
                return _issubclass(subclass, superclass, bound_Generic, bound_typevars,
                        bound_typevars_readonly, follow_fwd_refs, _recursion_check)
        if not subclass.__bound__ is None:
            return _issubclass(subclass.__bound__, superclass, bound_Generic, bound_typevars,
                    bound_typevars_readonly, follow_fwd_refs, _recursion_check)
        return False
    res = _issubclass_2(subclass, superclass, bound_Generic, bound_typevars,
            bound_typevars_readonly, follow_fwd_refs, _recursion_check)
    return res


def _issubclass_2(subclass, superclass, bound_Generic, bound_typevars,
            bound_typevars_readonly, follow_fwd_refs, _recursion_check):
    """Helper for _issubclass, a.k.a pytypes.issubtype.
    """
    if is_Tuple(superclass):
        return _issubclass_Tuple(subclass, superclass, bound_Generic, bound_typevars,
                bound_typevars_readonly, follow_fwd_refs, _recursion_check)
    if is_Union(superclass):
        return _issubclass_Union(subclass, superclass, bound_Generic, bound_typevars,
                bound_typevars_readonly, follow_fwd_refs, _recursion_check)
    if is_Union(subclass):
        return all(_issubclass(t, superclass, bound_Generic, bound_typevars,
                bound_typevars_readonly, follow_fwd_refs, _recursion_check) \
                for t in get_Union_params(subclass))
    if is_Generic(superclass):
        cls = superclass.__origin__ if not superclass.__origin__ is None else superclass
        # We would rather use issubclass(superclass.__origin__, Mapping), but that's somehow erroneous
        if pytypes.covariant_Mapping and (_has_base(cls, Mapping) or
                    # Python 3.7 maps everything to collections.abc:
                    (cls in _extra_dict and issubclass(cls, collections.abc.Mapping))):
            return _issubclass_Mapping_covariant(subclass, superclass,
                    bound_Generic, bound_typevars,
                    bound_typevars_readonly, follow_fwd_refs,
                    _recursion_check)
        else:
            return _issubclass_Generic(subclass, superclass, bound_Generic, bound_typevars,
                    bound_typevars_readonly, follow_fwd_refs, _recursion_check)
    if subclass in _extra_dict:
        subclass = _extra_dict[subclass]
    try:
        return issubclass(subclass, superclass)
    except TypeError:
        if not is_Type(subclass):
            # For Python 3.7, types from typing are not types.
            # So issubclass emits TypeError: issubclass() arg 1 must be a class
            raise TypeError("Invalid type declaration: %s, %s" %
                        (type_str(subclass), type_str(superclass)))
        return False


def _isinstance_Callable(obj, cls, bound_Generic, bound_typevars,
            bound_typevars_readonly, follow_fwd_refs, _recursion_check,
            check_callables = True):
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
        if not _issubclass(Tuple[clb_args], argSig, bound_Generic, bound_typevars,
                bound_typevars_readonly, follow_fwd_refs, _recursion_check):
            return False
        if not _issubclass(resSig, clb_res, bound_Generic, bound_typevars,
                bound_typevars_readonly, follow_fwd_refs, _recursion_check):
            return False
        return True
    return not check_callables


def _isinstance(obj, cls, bound_Generic=None, bound_typevars=None,
            bound_typevars_readonly=False, follow_fwd_refs=True, _recursion_check=None):
    """Access this via ``pytypes.is_of_type``.
    Works like ``isinstance``, but supports PEP 484 style types from ``typing`` module.

    obj : Any
    The object to check for being an instance of ``cls``.

    cls : type
    The type to check for ``obj`` being an instance of.

    bound_Generic : Optional[Generic]
    A type object holding values for unbound typevars occurring in ``cls``.
    Default: None
    If ``cls`` contains unbound ``TypeVar``s and ``bound_Generic`` is provided, this function
    attempts to retrieve corresponding values for the unbound ``TypeVar``s from ``bound_Generic``.
    In collision case with ``bound_typevars`` the value from ``bound_Generic`` if preferred.

    bound_typevars : Optional[Dict[typing.TypeVar, type]]
    A dictionary holding values for unbound typevars occurring in ``cls``.
    Default: {}
    Depending on ``bound_typevars_readonly`` pytypes can also bind values to typevars as needed.
    This is done by inserting according mappings into this dictionary. This can e.g. be useful to
    infer values for ``TypeVar``s or to consistently check a set of ``TypeVar``s across multiple
    calls, e.g. when checking all arguments of a function call.
    In collision case with ``bound_Generic`` the value from ``bound_Generic`` if preferred.

    bound_typevars_readonly : bool
    Defines if pytypes is allowed to write into the ``bound_typevars`` dictionary.
    Default: True
    If set to False, pytypes cannot assign values to ``TypeVar``s, but only checks regarding
    values already present in ``bound_typevars`` or ``bound_Generic``.

    follow_fwd_refs : bool
    Defines if ``ForwardRef``s should be explored.
    Default: True
    If this is set to ``False`` and a ``ForwardRef`` is encountered, pytypes aborts the check
    raising a ForwardRefError.

    _recursion_check : Optional[Dict[type, Set[type]]]
    Internally used for recursion checks.
    Default: None
    If ``Union``s and ``ForwardRef``s occur in the same type, recursions can occur. As soon as
    a ``ForwardRef`` is encountered, pytypes automatically creates this dictionary and
    continues in recursion-proof manner.
    """
    if bound_typevars is None:
        bound_typevars = {}
    # Special treatment if cls is Iterable[...]
    if is_Generic(cls) and cls.__origin__ is typing.Iterable:
        if not is_iterable(obj):
            return False
        itp = get_iterable_itemtype(obj)
        if itp is None:
            return not pytypes.check_iterables
        else:
            return _issubclass(itp, cls.__args__[0], bound_Generic, bound_typevars,
                    bound_typevars_readonly, follow_fwd_refs, _recursion_check)
    if is_Callable(cls):
        return _isinstance_Callable(obj, cls, bound_Generic, bound_typevars,
                bound_typevars_readonly, follow_fwd_refs, _recursion_check)
    return _issubclass(deep_type(obj), cls, bound_Generic, bound_typevars,
            bound_typevars_readonly, follow_fwd_refs, _recursion_check)


def _make_generator_error_message(tp, gen, expected_tp, incomp_text):
    _cmp_msg_format = 'Expected: %s\nReceived: %s'
    # todo: obtain fully qualified generator name
    return gen.__name__+' '+incomp_text+':\n'+_cmp_msg_format \
                % (type_str(expected_tp), type_str(tp))


def generator_checker_py3(gen, gen_type, bound_Generic, bound_typevars,
            bound_typevars_readonly, follow_fwd_refs, _recursion_check):
    """Builds a typechecking wrapper around a Python 3 style generator object.
    """
    initialized = False
    sn = None
    try:
        while True:
            a = gen.send(sn)
            if initialized or not a is None:
                if not gen_type.__args__[0] is Any and \
                        not _isinstance(a, gen_type.__args__[0], bound_Generic, bound_typevars,
                                bound_typevars_readonly, follow_fwd_refs,
                                _recursion_check):
                    tpa = deep_type(a)
                    msg = _make_generator_error_message(deep_type(a), gen, gen_type.__args__[0],
                            'has incompatible yield type')
                    _raise_typecheck_error(msg, True, a, tpa, gen_type.__args__[0])
# 					raise pytypes.ReturnTypeError(_make_generator_error_message(deep_type(a), gen,
# 							gen_type.__args__[0], 'has incompatible yield type'))
            initialized = True
            sn = yield a
            if not gen_type.__args__[1] is Any and \
                    not _isinstance(sn, gen_type.__args__[1], bound_Generic, bound_typevars,
                            bound_typevars_readonly, follow_fwd_refs, _recursion_check):
                tpsn = deep_type(sn)
                msg = _make_generator_error_message(tpsn, gen, gen_type.__args__[1],
                        'has incompatible send type')
                _raise_typecheck_error(msg, False, sn, tpsn, gen_type.__args__[1])
# 				raise pytypes.InputTypeError(_make_generator_error_message(deep_type(sn), gen,
# 						gen_type.__args__[1], 'has incompatible send type'))
    except StopIteration as st:
        # Python 3:
        # todo: Check if st.value is always defined (i.e. as None if not present)
        if not gen_type.__args__[2] is Any and \
                not _isinstance(st.value, gen_type.__args__[2], bound_Generic, bound_typevars,
                        bound_typevars_readonly, follow_fwd_refs, _recursion_check):
            tpst = deep_type(st.value)
            msg = _make_generator_error_message(tpst, gen, gen_type.__args__[2],
                    'has incompatible return type')
            _raise_typecheck_error(msg, True, st.value, tpst, gen_type.__args__[2])
# 			raise pytypes.ReturnTypeError(_make_generator_error_message(sttp, gen,
# 					gen_type.__args__[2], 'has incompatible return type'))
        raise st


def generator_checker_py2(gen, gen_type, bound_Generic, bound_typevars,
            bound_typevars_readonly, follow_fwd_refs, _recursion_check):
    """Builds a typechecking wrapper around a Python 2 style generator object.
    """
    initialized = False
    sn = None
    while True:
        a = gen.send(sn)
        if initialized or not a is None:
            if not gen_type.__args__[0] is Any and \
                    not _isinstance(a, gen_type.__args__[0], bound_Generic, bound_typevars,
                            bound_typevars_readonly, follow_fwd_refs, _recursion_check):
                tpa = deep_type(a)
                msg = _make_generator_error_message(tpa, gen, gen_type.__args__[0],
                        'has incompatible yield type')
                _raise_typecheck_error(msg, True, a, tpa, gen_type.__args__[0])
# 				raise pytypes.ReturnTypeError(_make_generator_error_message(tpa, gen,
# 						gen_type.__args__[0], 'has incompatible yield type'))
        initialized  = True
        sn = yield a
        if not gen_type.__args__[1] is Any and \
                not _isinstance(sn, gen_type.__args__[1], bound_Generic, bound_typevars,
                        bound_typevars_readonly, follow_fwd_refs, _recursion_check):
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
    specs = util.getargspecs(act_func)
    if call_args is None:
        call_args = util.get_current_args(caller_level+1, cllable, util.getargnames(specs))
    if slf:
        try:
            orig_clss = call_args[0].__orig_class__
        except AttributeError:
            orig_clss = call_args[0].__class__
        call_args = call_args[1:]
    elif clsm:
        orig_clss = call_args[0]
        call_args = call_args[1:]
    else:
        orig_clss = clss
    if not prop is None:
        argSig, retSig = _get_types(prop, clsm, slf, clss, prop_getter)
        try:
            if return_type:
                pytypes._checkfuncresult(retSig, call_args, act_func, slf or clsm, orig_clss,
                        prop_getter, force_exception=True)
            else:
                pytypes._checkfunctype(argSig, call_args, act_func, slf or clsm, orig_clss,
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
                pytypes._checkfuncresult(retSig, call_args, act_func, slf or clsm, orig_clss,
                        prop_getter, force_exception=True)
            else:
                pytypes._checkfunctype(argSig, call_args, act_func, slf or clsm, orig_clss,
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
                    except TypeError:
                        # Caller could not be determined.
                        pass
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
