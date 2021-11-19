# Copyright 2017, 2018, 2021 Stefan Richthofer
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

# Created on 29.04.2017

"""
pytypes.typelogger is a module for automatic creation of
PEP 484 stubfiles based on runtime observations.

Also allows creation of Python 2.7 compatible stubfiles.
"""

import sys
import os
import abc
import datetime
import atexit
from typing import Union, Any, Tuple
from inspect import getmembers, isclass, ismodule, getsourcelines, \
        findsource, isfunction, ismethod, ismethoddescriptor

try:
    import pkg_resources
except ImportError:
    pass

import pytypes
from .type_util import deep_type, type_str, get_Tuple_params, \
        Empty, simplify_for_Union, _get_types, _has_type_hints, \
        _preprocess_typecheck, get_Union_params, is_Union, \
        get_Generic_itemtype, TypeAgent, _implicit_globals, \
        _check_as_func, is_Tuple
from .util import getargspecs, getargnames
from .typechecker import _typeinspect_func
from . import util

_member_cache = {}
_fully_typelogged_modules = {}
silent = True
use_NoneType = False
simplify = True
_module_file_map = {} # cache module filenames for use atexit
_member_line_map = {} # cache line numbers for use atexit
# (for some reason, module.__file__ does not exist any more when atexit performs)


def _print(line):
    if not silent:
        print(line)


def log_type(args_kw, ret, func, slf=False, prop_getter=False, clss=None, argspecs=None,
            args_kw_type=None, ret_type = None):
    """Stores information of a function or method call into a cache, so pytypes can
    create a PEP 484 stubfile from this information later on (see dump_cache).
    """
    if args_kw_type is None:
        args_kw_type = deep_type(args_kw)
    if ret_type is None:
        ret_type = deep_type(ret)
    if argspecs is None:
        argspecs = getargspecs(func)
    node = _register_logged_func(func, slf, prop_getter, clss, argspecs)
    node.add_observation(args_kw_type, ret_type)
    
    md = util.getmodule_for_member(func, prop_getter)
    if not md.__name__ in _module_file_map:
        _module_file_map[md.__name__] = md.__file__

    if clss is None:
        try:
            clss = util.get_class_that_defined_method(func)
        except ValueError:
            pass
    if not clss is None and not clss in _member_line_map:
        _member_line_map[clss] = findsource(clss)[1]


def _register_logged_func(func, slf, prop_getter, clss, argspecs):
    if isinstance(func, property):
        func_key = func.fget if prop_getter else func.fset
    else:
        func_key = func
    if func_key in _member_cache:
        node = _member_cache[func_key]
    else:
        node = _typed_member(func, slf, prop_getter, clss, argspecs)
        _member_cache[func_key] = node
    return node


def register_all_members_in_class(clss):
    mb = getmembers(clss, lambda t: isclass(t) or _check_as_func(t))
    # todo: Care for overload-decorator
    for elem in mb:
        if elem[0] in clss.__dict__:
            el = clss.__dict__[elem[0]]
            if isfunction(el) and _has_type_hints(el):
                _register_logged_func(el, True, False, clss, util.getargspecs(el))
            elif isclass(el):
                register_all_members_in_class(el)
            elif ismethoddescriptor(el) and type(el) is staticmethod and \
                    _has_type_hints(el):
                _register_logged_func(el, False, False, clss, util.getargspecs(el))
            elif isinstance(el, property):
                if not el.fget is None and _has_type_hints(el.fget, clss):
                    _register_logged_func(el, True, True, clss, util.getargspecs(el))
                if not el.fset is None and _has_type_hints(el.fset, clss):
                    _register_logged_func(el, True, False, clss, util.getargspecs(el))
    # classmethods are not obtained via inspect.getmembers.
    # We have to look into __dict__ for that.
    for key in clss.__dict__:
        attr = getattr(clss, key)
        if ismethod(attr):
            _register_logged_func(attr, True, False, clss, util.getargspecs(el))


def register_all_members_in_module(md):
    funcs = [func[1] for func in getmembers(md, isfunction)]
    cls = [cl[1] for cl in getmembers(md, isclass)]
    for func in funcs:
        _register_logged_func(func, False, False, None, util.getargspecs(func))
    for cl in cls:
        if sys.modules[cl.__module__] is md:
            register_all_members_in_class(cl)


def combine_argtype(observations):
    """Combines a list of Tuple types into one.
    Basically these are combined element wise into a Union with some
    additional unification effort (e.g. can apply PEP 484 style numeric tower).
    """
    assert len(observations) > 0
    assert is_Tuple(observations[0])
    if len(observations) > 1:
        prms = [get_Tuple_params(observations[0])]
        ln = len(prms[0])
        for obs in observations[1:]:
            assert is_Tuple(obs)
            prms.append(get_Tuple_params(obs))
            assert len(prms[-1]) == ln
        if simplify:
            prms = map(list, zip(*prms))
            if not isinstance(prms, list):
                # special care for Python 3
                prms = list(prms)
            for type_list in prms:
                simplify_for_Union(type_list)
            prms = map(tuple, prms)
        else:
            prms = map(tuple, zip(*prms))
        prms = map(Union.__getitem__, prms)
        return Tuple[tuple(prms)]
    else:
        return observations[0]


def combine_type(observations):
    """Combines a list of types into one.
    Basically these are combined into a Union with some
    additional unification effort (e.g. can apply PEP 484 style numeric tower).
    """
    assert len(observations) > 0
    if len(observations) == 1:
        return observations[0]
    else:
        if simplify:
            simplify_for_Union(observations)
        return Union[tuple(observations)]


def _print_cache():
    for key in _member_cache:
        node = _member_cache[key]
        print (node)


def _imp_name(obj):
    try:
        nlst = util._get_class_nesting_list(obj, sys.modules[obj.__module__])
        if len(nlst) > 0:
            return nlst[0].__name__
        return obj.__name__
    except:
        # For some reason, Any and Union don't have __name__.
        if is_Union(obj):
            return 'Union'
        elif obj is Any:
            return 'Any'
    return str(obj)


def _module_name(md):
    if md.__name__ in _module_file_map:
        return _module_file_map[md.__name__].rsplit(os.sep, 1)[-1].split('.', 1)[0]
    if md.__name__ == '__main__':
        return md.__file__.rsplit(os.sep, 1)[-1].split('.', 1)[0]
    else:
        return md.__name__


def _make_import_section(required_globals, typevars, implicit_globals):
    mdict = {}
    for obj in required_globals:
        if obj.__module__ in mdict:
            mdict[obj.__module__].append(_imp_name(obj))
        else:
            mdict[obj.__module__] = [_imp_name(obj)]
    if len(typevars) > 0:
        for tpv in typevars:
            tpvmd = util.search_class_module(tpv)
            if not tpvmd is None and not tpvmd in _implicit_globals \
                    and not tpvmd in implicit_globals:
                if tpvmd.__name__ in mdict:
                    mdict[tpvmd.__name__].append(tpv.__name__)
                else:
                    mdict[tpvmd.__name__] = [tpv.__name__]
            elif tpvmd in implicit_globals:
                if 'typing' in mdict:
                    mdict['typing'].append('TypeVar')
                else:
                    mdict['typing'] = ['TypeVar']
    lines = []
    mnames = [mn for mn in mdict]
    mnames.sort()
    for mname in mnames:
        pck = sys.modules[mname].__package__
        name = _module_name(sys.modules[mname])
        if not pck is None and not pck == '' and not name.startswith(pck+'.'):
            name = pck+'.'+name
        lst = mdict[mname]
        lst.sort()
        lines.append('from %s import %s'%(name, ', '.join(lst)))
    return lines


def _dump_module(module_node, path=None, python2=False, suffix=None):
    if suffix is None:
        suffix = 'pyi2' if python2 else 'pyi'
    if path is None:
        path = pytypes.default_typelogger_path
    basic_name = module_node.get_basic_filename()
    if module_node.module.__name__ in _module_file_map:
        src_fname = _module_file_map[module_node.module.__name__]
    else:
        src_fname = module_node.module.__file__
    if src_fname is None:
        src_fname = 'unknown file'
    pck_path = module_node.get_pck_path()
    try:
        checksum = util._md5(src_fname)
    except:
        checksum = 'unknown checksum'
    pck_path = path if pck_path is None else os.sep.join((path, pck_path))
    #indent = module_node._indent()
    stubpath = ''.join((pck_path, os.sep, basic_name, '.', suffix))
    if not os.path.exists(pck_path):
        os.makedirs(pck_path)
    nw = datetime.datetime.now()
    try:
        exec_info_lst = [sys.executable]
        if len(sys.argv) > 0:
            exec_info_lst.append(sys.argv[0])
            if len(sys.argv) > 1:
                exec_info_lst.append(' '.join(sys.argv[1:]))
        exec_info = ('\n'+pytypes.default_indent).join(exec_info_lst)
    except:
        exec_info = 'unknown call'
    with open(stubpath, 'w') as stub_handle:
        try:
            version = pkg_resources.get_distribution('pytypes').version
        except NameError:
            version = pytypes._version
        lines = ['"""',
                'Automatically generated Python 2.7-compliant stubfile of ' if python2 
                        else 'Automatically generated stubfile of \n',
                src_fname,
                'MD5-Checksum: '+checksum,
                '\nThis file was generated by pytypes.typelogger v'+version,
                'at '+nw.isoformat()+'.\n',
                'Type information is based on runtime observations while running',
                util._python_version_string(),
                exec_info,
                '\nWARNING:',
                'If you edit this file, be aware that it was automatically generated.',
                'Save your customized version to a distinct place;',
                'this file might be overwritten without notice.',
                '"""',
                '',
                '', # import section later goes here; don't forget to track in imp_index
                '']
        imp_index = 15

        for i in range(len(lines)):
            lines[i] = lines[i]+'\n'
        lines.append('\n')
        assumed_glbls = set()
        assumed_typevars = set()
        implicit_globals = set()
        module_node.dump(lines, 0, python2, None,
                assumed_glbls, implicit_globals, assumed_typevars)
        imp_lines = _make_import_section(assumed_glbls, assumed_typevars, implicit_globals)
        lines.insert(imp_index, '\n'.join(imp_lines))
        if not python2:
            lines.append('\n')
        _print(''.join(lines))
        stub_handle.writelines(lines)


def dump_cache(path=None, python2=False, suffix=None):
    """Writes cached observations by @typelogged into stubfiles.
    Files will be created in the directory provided as 'path'; overwrites
    existing files without notice.
    Uses 'pyi2' suffix if 'python2' flag is given else 'pyi'. Resulting
    files will be Python 2.7 compilant accordingly.
    """
    typelogging_enabled_tmp = pytypes.typelogging_enabled
    pytypes.typelogging_enabled = False
    if suffix is None:
        suffix = 'pyi2' if python2 else 'pyi'
    if path is None:
        path = pytypes.default_typelogger_path
    modules = {}
    for key in _member_cache:
        node = _member_cache[key]
        mname = node.get_modulename()
        if not mname in modules:
            mnode = _module_node(mname)
            modules[mname] = mnode
        else:
            mnode = modules[mname]
        mnode.append(node)
    for module in modules:
        _dump_module(modules[module], path, python2, suffix)
    pytypes.typelogging_enabled = typelogging_enabled_tmp


def _dump_at_exit():
    pytypes.typelogging_enabled = False
    if len(_member_cache) > 0:
        if pytypes.dump_typelog_at_exit:
            dump_cache()
        if pytypes.dump_typelog_at_exit_python2:
            dump_cache(python2=True)
        _print('dumped at exit: '+str(len(_member_cache)))
atexit.register(_dump_at_exit)


def _prepare_arg_types(arg_Tuple, argspecs, slf_or_clsm = False, names = None):
    tps = get_Tuple_params(arg_Tuple)
    arg_tps = []
    off = 1 if slf_or_clsm else 0
    i = off-1
    if names is None:
        for i in range(off, len(argspecs.args)):
            arg_tps.append(tps[i-off])
        if slf_or_clsm:
            i -= 1
    else:
        for i in range(off, len(argspecs.args)):
            arg_tps.append(tps[i-off])
            names.append(argspecs.args[i])
        if slf_or_clsm:
            i -= 1
    vararg_tp = None
    if not argspecs.varargs is None:
        i += 1
        if is_Union(tps[i]):
            itm_tps = []
            uprms = get_Union_params(tps[i])
            for uprm in uprms:
                itm_tp = get_Generic_itemtype(uprm, simplify)
                if not itm_tp is None:
                    itm_tps.append(itm_tp)
            simplify_for_Union(itm_tps)
            vararg_tp = Union[tuple(itm_tps)]
        else:
            vararg_tp = get_Generic_itemtype(tps[i], simplify)
            if vararg_tp is None:
                vararg_tp = Any
        if not names is None:
            names.append('*'+argspecs.varargs)

    kwonly_tps = None
    try:
        if not argspecs.kwonlyargs is None:
            kwonly_tps = []
            if names is None:
                for _ in range(len(argspecs.kwonlyargs)):
                    i += 1
                    kwonly_tps.append(tps[i])
            else:
                for j in range(len(argspecs.kwonlyargs)):
                    i += 1
                    kwonly_tps.append(tps[i])
                    names.append(argspecs.kwonlyargs[j])
    except AttributeError:
        pass

    try:
        kw = argspecs.keywords
    except AttributeError:
        kw = argspecs.varkw
    kw_tp = None
    if not kw is None:
        i += 1
        if is_Union(tps[i]):
            itm_tps = []
            uprms = get_Union_params(tps[i])
            for uprm in uprms:
                itm_tp = uprm.__args__[-1]
                if not itm_tp is None:
                    itm_tps.append(itm_tp)
            simplify_for_Union(itm_tps)
            kw_tp = Union[tuple(itm_tps)]
        else:
            kw_tp = Any if issubclass(tps[i], Empty) else tps[i].__args__[-1]
        if not names is None:
            names.append('**'+kw)
    return arg_tps, vararg_tp, kw_tp, kwonly_tps


def _prepare_arg_types_list(arg_Tuple, argspecs, slf_or_clsm = False, names=None):
    arg_tps, vararg_tp, kw_tp, kwonly_tps = _prepare_arg_types(
            arg_Tuple, argspecs, slf_or_clsm, names)
    res = []
    res.extend(arg_tps)
    if not vararg_tp is None:
        res.append(vararg_tp)
    if not kwonly_tps is None:
        res.extend(kwonly_tps)
    if not kw_tp is None:
        res.append(kw_tp)
    return res


def _prepare_arg_types_str(arg_Tuple, argspecs, slf_or_clsm = False, names=None,
            assumed_globals=None, update_assumed_globals=None, implicit_globals=None):
    arg_tps, vararg_tp, kw_tp, kwonly_tps = _prepare_arg_types(
            arg_Tuple, argspecs, slf_or_clsm, names)
    res = []
    res.extend(type_str(tp, assumed_globals, update_assumed_globals, implicit_globals)
            for tp in arg_tps)
    if not vararg_tp is None:
        res.append('*'+type_str(vararg_tp, assumed_globals, update_assumed_globals,
                implicit_globals))
    if not kwonly_tps is None:
        res.extend(type_str(tp, assumed_globals, update_assumed_globals, implicit_globals)
                for tp in kwonly_tps)
    if not kw_tp is None:
        res.append('**'+type_str(kw_tp, assumed_globals, update_assumed_globals,
                implicit_globals))
    return ''.join(('(', ', '.join(res), ')'))


def _signature_class(clss, assumed_globals=None, implicit_globals=None,
            assumed_typevars=None):
    if implicit_globals is None:
        implicit_globals = _implicit_globals
    else:
        implicit_globals = implicit_globals.copy()
        implicit_globals.update(_implicit_globals)
    for bs in clss.__bases__:
        if not sys.modules[bs.__module__] in implicit_globals:
            if hasattr(bs, '__origin__') and not bs.__origin__ is None:
                assumed_globals.add(bs.__origin__)
            else:
                assumed_globals.add(bs)
    try:
        bases = clss.__orig_bases__
    except AttributeError:
        bases = clss.__bases__
    if not assumed_typevars is None:
        for base in bases:
            if hasattr(base, '__parameters__') and len(base.__parameters__) > 0:
                for prm in base.__parameters__:
                    assumed_typevars.add(prm)
    base_names = [type_str(base, assumed_globals, True, implicit_globals) for base in bases]
    return 'class '+clss.__name__+'('+', '.join(base_names)+'):'


# currently not used; kept here as potential future feature
def get_indentation(func):
    """Extracts a function's indentation as a string,
    In contrast to an inspect.indentsize based implementation,
    this function preserves tabs if present.
    """
    src_lines = getsourcelines(func)[0]
    for line in src_lines:
        if not (line.startswith('@') or line.startswith('def') or line.lstrip().startswith('#')):
            return line[:len(line) - len(line.lstrip())]
    return pytypes.default_indent


def _node_get_line(node):
    return node.get_line()


class _base_node(object):
    __metaclass__  = abc.ABCMeta

    def _indent(self):
        idn = self._idn
        if not idn is None:
            return idn
        idn = pytypes.default_indent
        self._idn = idn
        return idn

    @abc.abstractmethod
    def dump(self, dest, indents = 0, python2 = False, props = None,
            assumed_globals=None, implicit_globals=None, assumed_typevars=None):
        pass

    def is_property(self):
        return False

    def append(self, node):
        raise ValueError('append is not supported by %s.' % self.__class__.__name__)

    def get_line(self):
        return 0


class _typed_member(_base_node):
    def __init__(self, member, slf=False, prop_getter=False, clss=None, argspecs=None):
        try:
            self.member = clss.__dict__[member.__name__]
        except:
            self.member = member
        clsm = isinstance(self.member, classmethod)
        stat = isinstance(self.member, staticmethod)
        prop = isinstance(self.member, property)
        if prop:
            self.name = self.member.fget.__name__  if prop_getter else self.member.fset.__name__
        else:
            self.name = self.member.__func__.__name__ if clsm or stat else self.member.__name__
        self.argspecs = argspecs
        self.clss = clss
        self.arg_type_observations = []
        self.ret_type_observations = []
        self._idn = None
        self.slf = slf
        self.clsm = clsm
        self.stat = stat
        self.prop = prop
        self.prop_getter = prop_getter
        self._added_type_hints = False

    def add_observation(self, args_kw_type, ret_type):
        self.arg_type_observations.append(args_kw_type)
        self.ret_type_observations.append(ret_type)

    def _add_observation_from_type_info(self):
        if pytypes.typelogger_include_typehint and \
                _has_type_hints(self.member, self.clss, nesting = None):
            self._added_type_hints = True
            args, ret = _get_types(self.member, self.clsm, self.slf, self.clss,
                    self.prop_getter)
            args = _preprocess_typecheck(args, self.argspecs, self.slf or self.clsm)
            self.add_observation(args, ret)

    def _type_str(self, assumed_globals=None, implicit_globals=None):
        arg_str =  _prepare_arg_types_str(combine_argtype(self.arg_type_observations),
                self.argspecs, self.slf or self.clsm, None,
                assumed_globals, True, implicit_globals)
        return ''.join((arg_str, ' -> ', type_str(combine_type(self.ret_type_observations),
                assumed_globals, True, implicit_globals)))

    def _type_comment(self, assumed_globals=None, implicit_globals=None):
        return '# type: '+self._type_str(assumed_globals, implicit_globals)

    def _signature(self):
        # For now we prefer getargnames over inspect.formatargspec, because of easier
        # bridging of Python 2 and 3.
        arg_names = getargnames(self.argspecs, True)
        return ''.join(('(', ', '.join(arg_names), ')'))

    def _annotated_signature(self, assumed_globals=None, implicit_globals=None):
        # inspect.formatargspec would only work in Python 3 with annotations
        sig_lst = []
        tp_lst = _prepare_arg_types_list(combine_argtype(self.arg_type_observations),
                self.argspecs, self.slf or self.clsm, sig_lst)
        if not use_NoneType:
            ntp = type(None)
            for i in range(len(sig_lst)):
                sig_lst[i] += ': '+('None' if tp_lst[i] == ntp else
                        type_str(tp_lst[i], assumed_globals, True, implicit_globals))
        else:
            for i in range(len(sig_lst)):
                sig_lst[i] += ': '+type_str(tp_lst[i], assumed_globals, True, implicit_globals)
        if self.slf:
            sig_lst.insert(0, 'self')
        elif self.clsm:
            sig_lst.insert(0, 'cls')
        rtp = combine_type(self.ret_type_observations)
        if not use_NoneType:
            ntp = type(None)
            res_tp = 'None' if rtp == ntp else \
                    type_str(rtp, assumed_globals, True, implicit_globals)
        else:
            res_tp = type_str(rtp, assumed_globals, True, implicit_globals)
        return ''.join(('(', ', '.join(sig_lst), ') -> ', res_tp))

    def _declaration(self, indents = 0, annotated=False,
            assumed_globals=None, implicit_globals=None):
        base_idn = self._indent()*indents
        return ''.join((base_idn, 'def ', self.name,
                self._annotated_signature(assumed_globals, implicit_globals)
                if annotated else self._signature(), ':'))

    def _stub_src_tpypestring(self, indents = 0, props = None,
            assumed_globals=None, implicit_globals=None):
        idn = self._indent()
        bs = '\n'+idn*(indents+1)
        elements = [self._declaration(indents, False, assumed_globals, implicit_globals),
                bs, self._type_comment(assumed_globals, implicit_globals), bs, 'pass']
        if self.clsm:
            elements.insert(0, idn*indents+'@classmethod\n')
        elif self.stat:
            elements.insert(0, idn*indents+'@staticmethod\n')
        elif self.prop:
            idn = self._indent()
            if self.prop_getter:
                elements.insert(0, idn*indents+'@property\n')
            else:
                elements.insert(0, idn*indents+'@%s.setter\n' % self.member.fget.__name__)
                if not self.member in props:
                    elements.insert(0, idn*(indents+1)+'pass\n')
                    elements.insert(0, idn*indents+'def '+self.name+'(self):\n')
                    elements.insert(0, idn*indents+'@property\n')
        res = ''.join(elements)
        return res if use_NoneType else res.replace('NoneType', 'None')

    def _stub_src_annotations(self, indents = 0, props = None,
            assumed_globals=None, implicit_globals=None):
        elements = [self._declaration(indents, True,
                assumed_globals, implicit_globals), ' ...']
        if self.clsm:
            idn = self._indent()
            elements.insert(0, idn*indents+'@classmethod\n')
        elif self.stat:
            idn = self._indent()
            elements.insert(0, idn*indents+'@staticmethod\n')
        elif self.prop:
            idn = self._indent()
            if self.prop_getter:
                elements.insert(0, idn*indents+'@property\n')
            else:
                elements.insert(0, idn*indents+'@%s.setter\n' % self.member.fget.__name__)
                if not self.member in props:
                    elements.insert(0, idn*indents+'def '+self.name+'(self): ...\n')
                    elements.insert(0, idn*indents+'@property\n')
        return ''.join(elements)

    def dump(self, dest, indents = 0, python2 = False, props = None,
            assumed_globals=None, implicit_globals=None, assumed_typevars=None):
        if not self._added_type_hints:
            self._add_observation_from_type_info()
        if python2:
            dest.append(self._stub_src_tpypestring(indents, props,
                    assumed_globals, implicit_globals))
        else:
            dest.append(self._stub_src_annotations(indents, props,
                    assumed_globals, implicit_globals))
        dest.append('\n\n' if python2 else '\n')

    def __str__(self):
        return ''.join((self.member.__str__(), ': ',
                type_str(combine_argtype(self.arg_type_observations)),
                ' -> ', type_str(combine_type(self.ret_type_observations))))

    def get_key(self):
        if self.prop:
            return ''.join((self.name, '/getter' if self.prop_getter else '/setter'))
        else:
            return self.name

    def get_modulename(self):
        if self.prop:
            return self.member.fget.__module__ if self.prop_getter \
                    else self.member.fset.__module__
        else:
            return self.member.__func__.__module__ if self.clsm or self.stat else \
                    self.member.__module__

    def is_property(self):
        return self.prop_getter

    def get_line(self):
        try:
            return self.member.__code__.co_firstlineno
        except:
            pass
        if self.prop:
            return self.member.fget.__code__.co_firstlineno if self.prop_getter \
                    else self.member.fset.__code__.co_firstlineno
        else:
            return self.member.__func__.__code__.co_firstlineno


class _module_node(_base_node):
    def __init__(self, mname):
        self.name = mname
        self.module = sys.modules[mname]
        self.classes = {}
        self.others = {}
        self._idn = None

    def get_basic_filename(self):
        if self.name == '__main__':
            try:
                if self.module.__name__ in _module_file_map:
                    return _module_file_map[
                            self.module.__name__].rsplit(os.sep, 1)[-1].split('.', 1)[0]
                else:
                    return self.module.__file__.rsplit(os.sep, 1)[-1].split('.', 1)[0]
            except:
                return self.name
        else:
            return self.name

    def get_pck_path(self):
        if self.module.__package__ is None:
            return None
        else:
            return self.module.__package__.replace('.', os.sep)

    def get_filename(self):
        return self.module.__file__.rsplit(os.sep, 1)[-1]

    def dump(self, dest, indents = 0, python2 = False, props=None,
            assumed_globals=None, implicit_globals=None, assumed_typevars=None):
        dump_lst = []
        dump_lst.extend(self.classes.values())
        dump_lst.extend(self.others.values())
        dump_lst.sort(key=_node_get_line)
        for elm in dump_lst:
            elm.dump(dest, indents, python2, props,
                    assumed_globals, implicit_globals, assumed_typevars)
        if not assumed_globals is None:
            for clsn in self.classes.values():
                if clsn.clss in assumed_globals:
                    assumed_globals.remove(clsn.clss)
                clsn.clean_assumed_globals(assumed_globals)

    def append(self, typed_member):
        if typed_member.clss is None and not typed_member.stat:
            typed_member._idn = self._indent()
            self.others[typed_member.get_key()] = typed_member
        else:
            if not typed_member.stat:
                nst_lst = util._get_class_nesting_list(typed_member.clss, self.module)
                tp_cls = typed_member.clss
            else:
                nst_lst = util._get_class_nesting_list_for_staticmethod(
                        typed_member.member, self.module, [], set())
                tp_cls = nst_lst[0]
                nst_lst = nst_lst[1:]
            clss_node = self
            for cls in nst_lst:
                if cls.__name__ in clss_node.classes:
                    clss_node = clss_node.classes[cls.__name__]
                else:
                    clss_node1 = _class_node(cls)
                    clss_node1._idn = self._indent()
                    clss_node.classes[cls.__name__] = clss_node1
                    clss_node = clss_node1
            if tp_cls.__name__ in clss_node.classes:
                clss_node = clss_node.classes[tp_cls.__name__]
            else:
                clss_node1 = _class_node(tp_cls)
                clss_node1._idn = self._indent()
                clss_node.classes[clss_node1.name] = clss_node1
                clss_node = clss_node1
            clss_node.append(typed_member)


class _class_node(_base_node):
    def __init__(self, clss):
        self.name = clss.__name__
        self.clss = clss
        self.classes = {}
        self.others = {}
        self._idn = None

    def dump(self, dest, indents = 0, python2 = False, props=None,
            assumed_globals=None, implicit_globals=None, assumed_typevars=None):
        dest.append('\n')
        idn = self._indent()
        dest.append(indents*idn + _signature_class(self.clss,
                assumed_globals, implicit_globals, assumed_typevars))
        dest.append('\n\n')
        dump_lst = []
        dump_lst.extend(self.classes.values())
        dump_lst.extend(self.others.values())
        dump_lst.sort(key=_node_get_line)
        props = set()
        for elm in dump_lst:
            if elm.is_property():
                props.add(elm.member)
            elm.dump(dest, indents+1, python2, props, assumed_globals, implicit_globals)

    def clean_assumed_globals(self, assumed_globals):
        if not assumed_globals is None:
            for clsn in self.classes.values():
                if clsn.clss in assumed_globals:
                    assumed_globals.remove(clsn.clss)
                clsn.clean_assumed_globals(assumed_globals)

    def append(self, member):
        member._idn = self._indent()
        self.others[member.get_key()] = member

    def get_line(self):
        if self.clss in _member_line_map:
            return _member_line_map[self.clss]
        else:
            return findsource(self.clss)[1]


def typelogged_func(func):
    """Works like typelogged, but is only applicable to functions,
    methods and properties.
    """
    if not pytypes.typelogging_enabled:
        return func
    if hasattr(func, 'do_logging'):
        func.do_logging = True
        return func
    elif hasattr(func, 'do_typecheck'):
        # actually shouldn't happen
        return _typeinspect_func(func, func.do_typecheck, True)
    else:
        return _typeinspect_func(func, False, True)


def typelogged_class(cls):
    """Works like typelogged, but is only applicable to classes.
    """
    if not pytypes.typelogging_enabled:
        return cls
    assert(isclass(cls))
    # To play it safe we avoid to modify the dict while iterating over it,
    # so we previously cache keys.
    # For this we don't use keys() because of Python 3.
    # Todo: Better use inspect.getmembers here
    keys = [key for key in cls.__dict__]
    for key in keys:
        memb = cls.__dict__[key]
        if _check_as_func(memb):
            setattr(cls, key, typelogged_func(memb))
        elif isclass(memb):
            typelogged_class(memb)
    return cls


def typelogged_module(md):
    """Works like typelogged, but is only applicable to modules by explicit call).
    md must be a module or a module name contained in sys.modules.
    """
    if not pytypes.typelogging_enabled:
        return md
    if isinstance(md, str):
        if md in sys.modules:
            md = sys.modules[md]
            if md is None:
                return md
        elif md in pytypes.typechecker._pending_modules:
            # if import is pending, we just store this call for later
            pytypes.typechecker._pending_modules[md].append(typelogged_module)
            return md
    assert(ismodule(md))
    if md.__name__ in pytypes.typechecker._pending_modules:
            # if import is pending, we just store this call for later
            pytypes.typechecker._pending_modules[md.__name__].append(typelogged_module)
            # we already process the module now as far as possible for its internal use
            # todo: Issue warning here that not the whole module might be covered yet
    assert(ismodule(md))
    if md.__name__ in _fully_typelogged_modules and \
            _fully_typelogged_modules[md.__name__] == len(md.__dict__):
        return md
    # To play it safe we avoid to modify the dict while iterating over it,
    # so we previously cache keys.
    # For this we don't use keys() because of Python 3.
    # Todo: Better use inspect.getmembers here
    keys = [key for key in md.__dict__]
    for key in keys:
        memb = md.__dict__[key]
        if _check_as_func(memb) and memb.__module__ == md.__name__:
            setattr(md, key, typelogged_func(memb))
        elif isclass(memb) and memb.__module__ == md.__name__:
            typelogged_class(memb)
    if not md.__name__ in pytypes.typechecker._pending_modules:
        _fully_typelogged_modules[md.__name__] = len(md.__dict__)
    return md


def typelogged(memb):
    """Decorator applicable to functions, methods, properties,
    classes or modules (by explicit call).
    If applied on a module, memb must be a module or a module name contained in sys.modules.
    See pytypes.set_global_typelogged_decorator to apply this on all modules.
    Observes function and method calls at runtime and allows pytypes to generate stubfiles
    from the acquired type information.
    Use dump_cache to write a stubfile in this manner.
    """
    if not pytypes.typelogging_enabled:
        return memb
    if _check_as_func(memb):
        return typelogged_func(memb)
    if isclass(memb):
        return typelogged_class(memb)
    if ismodule(memb):
        return typelogged_module(memb)
    if memb in sys.modules or memb in pytypes.typechecker._pending_modules:
        return typelogged_module(memb)
    return memb


def _catch_up_global_typelogged_decorator():
    for mod_name in sys.modules:
        if not mod_name in _fully_typelogged_modules:
            try:
                md = sys.modules[mod_name]
            except KeyError:
                md = None
            if not md is None and ismodule(md):
                typelogged_module(mod_name)


class TypeLogger(TypeAgent):

    def __init__(self, all_threads = True):
        TypeAgent.__init__(self, all_threads)
        self._logging_enabled = True
