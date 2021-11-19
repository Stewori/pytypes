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

# Created on 25.10.2016

"""
Creates Python 2.7-style stubfiles from Python 3.5-style stubfiles.
Conversion process needs Python 3.5, but resulting files can be
distributed for use with Python 2.7.
Only works if no Python 3.5 specific code was used to construct
type variables and such.

So far the conversion is somewhat naive and a hand-crafted
Python 2.7. stub-file might be required for advanced use-cases.
Such a file should be stored like the usual stub-file, but
using the suffix 'pyi2'. If such a file exists, pytypes will take
it as override of the pyi-file when running on Python 2.7.
"""

import sys
import imp
import inspect
import os
import datetime

sys.path.append('/data/workspace/linux/pytypes')

try:
    import pkg_resources
except ImportError:
    pass

import pytypes
from pytypes import util, typelogger, type_util

from typing import Any, TypeVar


py3 = False
force = False
silent = False
indent = '    '
stub_open_mode = "U"
stub_descr = (".pyi", stub_open_mode, imp.PY_SOURCE)
_implicit_globals = set()
# This behavior changed with Python 3.6:
_tpvar_is_class = inspect.isclass(TypeVar('_test'))


def _print(line):
    if not silent:
        print(line)


def _typestring(_types, argspecs, slf_or_clsm=False, assumed_globals=None):
    if _types[0] is Any:
        argstr = '...'
    else:
        args = type_util._preprocess_typecheck(_types[0], argspecs, slf_or_clsm)
        argstr = typelogger._prepare_arg_types_str(args, argspecs, slf_or_clsm,
                assumed_globals=assumed_globals, update_assumed_globals=True,
                implicit_globals=_implicit_globals)
    retstr = type_util.type_str(_types[1], assumed_globals, True, _implicit_globals)
    res = (argstr+' -> '+retstr)
    res = res.replace('NoneType', 'None')
    return res


def _typecomment(_types, argspec, slf_or_clsm=False, assumed_globals=None):
    return '# type: '+_typestring(_types, argspec, slf_or_clsm, assumed_globals)


def typecomment(func, argspec=None, slf_or_clsm=False, assumed_globals=None):
    if argspec is None:
        argspec = util.getargspecs(func)
    return _typecomment(type_util.get_types(func), argspec, slf_or_clsm, assumed_globals)


def signature(func):
    argstr = ', '.join(util.getargnames(util.getargspecs(func), True))
    return 'def '+func.__name__+'('+argstr+'):'


def annotated_signature(func, argspec=None, slf_or_clsm=False, assumed_globals=None):
    # inspect.formatargspec would only work in Python 3 with annotations
    if argspec is None:
        argspec = util.getargspecs(func)
    _types = type_util.get_types(func)
    sig_lst = []
    tp_lst = typelogger._prepare_arg_types_list(_types[0], argspec, slf_or_clsm, sig_lst)
    for i in range(len(sig_lst)):
        sig_lst[i] += ': '+type_util.type_str(tp_lst[i], assumed_globals, True, _implicit_globals)
    if slf_or_clsm:
        sig_lst.insert(0, argspec.args[0])
    res_tp = type_util.type_str(_types[1], assumed_globals, True, _implicit_globals)
    res = ''.join(('(', ', '.join(sig_lst), ') -> ', res_tp))
    return ''.join(('def ', func.__name__, res.replace('NoneType', 'None'), ':'))


def _write_func(func, lines, inc=0, decorators=None, slf_or_clsm=False, assumed_globals=None):
    if type_util.has_type_hints(func):
        if not decorators is None:
            for dec in decorators:
                lines.append(inc*indent+'@'+dec)
        if py3:
            lines.append(inc*indent+ \
                    annotated_signature(func, slf_or_clsm=slf_or_clsm,
                    assumed_globals=assumed_globals)+' ...')
        else:
            lines.append(inc*indent+signature(func))
            lines.append((inc+1)*indent+typecomment(func, slf_or_clsm=slf_or_clsm,
                    assumed_globals=assumed_globals))
            lines.append((inc+1)*indent+'pass')


def _write_property(prop, lines, inc=0, decorators=None, assumed_globals=None):
    if not decorators is None:
        for dec in decorators:
            lines.append(inc*indent+'@'+dec)
    if not prop.fget is None:
        _write_func(prop.fget, lines, inc, ['property'], True, assumed_globals)
    if not prop.fset is None:
        if not prop.fget is None:
            lines.append('')
        _write_func(prop.fset, lines, inc, ['%s.setter'%prop.fget.__name__], True,
                assumed_globals)


def _write_TypeVar(tpv, lines, inc=0):
    args = [tpv.__name__]
    if not tpv.__bound__ is None:
        args.append('bound='+type_util.type_str(tpv.__bound__))
    if tpv.__covariant__:
        args.append('covariant=True')
    if tpv.__contravariant__:
        args.append('contravariant=True')
    lines.append("%s%s = TypeVar('%s')"%(inc*indent, tpv.__name__, ', '.join(args)))


def _write_class(clss, lines, inc = 0, assumed_globals=None, implicit_globals=None,
            assumed_typevars=None):
    _print("write class: "+str(clss))
    anyElement = False
    lines.append(inc*indent+typelogger._signature_class(clss,
            assumed_globals, implicit_globals, assumed_typevars))
    mb = inspect.getmembers(clss, lambda t: inspect.isclass(t) or type_util._check_as_func(t))
    # todo: Care for overload-decorator
    for elem in mb:
        if elem[0] in clss.__dict__:
            el = clss.__dict__[elem[0]]
            if inspect.isfunction(el):
                lines.append('')
                _write_func(el, lines, inc+1, slf_or_clsm=True,
                        assumed_globals=assumed_globals)
                anyElement = True
            elif inspect.isclass(el):
                lines.append('')
                if isinstance(el, TypeVar):
                    _write_TypeVar(el, lines, inc+1)
                else:
                    _write_class(el, lines, inc+1, assumed_globals, implicit_globals,
                            assumed_typevars)
                anyElement = True
            elif inspect.ismethoddescriptor(el) and type(el) is staticmethod:
                lines.append('')
                _write_func(el.__func__, lines, inc+1, ['staticmethod'],
                        assumed_globals=assumed_globals)
                anyElement = True
            elif isinstance(el, property):
                lines.append('')
                _write_property(el, lines, inc+1, assumed_globals=assumed_globals)
                anyElement = True

    # classmethods are not obtained via inspect.getmembers.
    # We have to look into __dict__ for that.
    for key in clss.__dict__:
        attr = getattr(clss, key)
        if util.is_classmethod(attr):
            lines.append('')
            _write_func(attr, lines, inc+1, ['classmethod'], True, assumed_globals)
            anyElement = True

    if not anyElement:
        lines.append((inc+1)*indent+'pass')


def _func_get_line(func):
    try:
        return func.__code__.co_firstlineno
    except:
        pass
    if isinstance(func, property):
        return func.fget.__code__.co_firstlineno if not func.fget is None \
                else func.fset.__code__.co_firstlineno
    else:
        return func.__func__.__code__.co_firstlineno


def _class_get_line(clss):
    return inspect.findsource(clss)[1]


def convert(in_file, out_file = None):
    global _implicit_globals
    _print('in_file: '+in_file)
    assert(os.path.isfile(in_file))
    checksum = util._md5(in_file)
    if out_file is None:
        if in_file.endswith('py'):
            if py3:
                out_file = in_file+'i'
            else:
                out_file = in_file+'i2'
        elif in_file.endswith('pyi'):
            if py3:
                out_file = in_file
            else:
                out_file = in_file+'2'
        else:
            out_file = in_file+'2'
        if os.path.exists(out_file) and not force:
            _print("File already exists: "+str(out_file))
            _print("Run with --force to force overwriting.")
            sys.exit(os.EX_CANTCREAT)
    _print('out_file: '+out_file)

    with open(in_file, stub_open_mode) as module_file:
        module_name = os.path.basename(in_file)
        stub_module = imp.load_module(
                module_name, module_file, in_file, stub_descr)
        if module_name in sys.modules:
            _implicit_globals.add(sys.modules[module_name])
        module_basename = module_name.rsplit('.')[0]
        if module_basename in sys.modules:
            _implicit_globals.add(sys.modules[module_basename])

    funcs = [func[1] for func in inspect.getmembers(stub_module, inspect.isfunction)]
    cls = [cl[1] for cl in inspect.getmembers(stub_module, inspect.isclass)]
    tpvs = set()
    i = 0
    if _tpvar_is_class:
        while i < len(cls):
            if isinstance(cls[i], TypeVar):
                tpvs.add(cls[i])
                del cls[i]
            else:
                i += 1
    else:
        # Python 3.6
        for tpv in inspect.getmembers(stub_module, lambda t: isinstance(t, TypeVar)):
            tpvs.add(tpv[1])

    funcs.sort(key=_func_get_line)
    cls.sort(key=_class_get_line)

    directory = os.path.dirname(out_file)
    if directory == '':
        directory = '.'
    if not os.path.exists(directory):
        os.makedirs(directory)
    assumed_glbls = set()
    assumed_typevars = set()
    nw = datetime.datetime.now()
    with open(out_file, 'w') as out_file_handle:
        try:
            version = pkg_resources.get_distribution('pytypes').version
        except:
            version = pytypes._version
        lines = ['"""',
                'Python 2.7-compliant stubfile of ',
                in_file,
                'MD5-Checksum: '+checksum,
                '\nThis file was generated by pytypes.stubfile_2_converter v'+version,
                'at '+nw.isoformat(),
                'running on '+util._python_version_string()+'.\n',
                'WARNING:',
                'If you edit this file, be aware that it was automatically generated.',
                'Save your customized version to a distinct place;',
                'this file might be overwritten without notice.',
                '"""',
                '',
                ''] # import section later goes here; don't forget to track in imp_index
        imp_index = 13
        any_tpv = False
        for tpv in tpvs:
            if util.search_class_module(tpv) is stub_module:
                if not any_tpv:
                    lines.append('')
                _write_TypeVar(tpv, lines)
                any_tpv = True

        for func in funcs:
            lines.append('')
            _write_func(func, lines, assumed_globals=assumed_glbls)

        for cl in cls:
            if sys.modules[cl.__module__] in _implicit_globals:
                lines.append('\n')
                _write_class(cl, lines, assumed_globals=assumed_glbls,
                        implicit_globals=_implicit_globals,
                        assumed_typevars=assumed_typevars)

        for el in tpvs:
            assumed_typevars.add(el)

        imp_lines = typelogger._make_import_section(assumed_glbls, assumed_typevars,
                _implicit_globals)
        lines.insert(imp_index, '\n'.join(imp_lines))
        for i in range(len(lines)):
            _print(lines[i])
            lines[i] = lines[i]+'\n'
        lines.append('\n')
        out_file_handle.writelines(lines)


def err_no_in_file():
    print("Error: No in_file given! Use -h for help.")
    sys.exit(os.EX_USAGE)


def print_usage():
    print("stubfile_2_converter usage:")
    print("python3 -m pytypes.stubfile_2_converter [options/flags] [in_file]")
    print("Supported options/flags:")
    print(" -o [out_file] : custom output-file")
    print(" -s            : silent mode")
    print("--py3          : write Python 3 stubfile")
    print(" -t            : indent with tabs")
    print(" -h            : usage")


def main():
    global silent, py3, in_file, out_file, indent, force

    if '-h' in sys.argv:
        print_usage()
        sys.exit(0)
    in_file = sys.argv[-1]
    if len(sys.argv) < 2 or in_file.startswith('-'):
        err_no_in_file()
    out_file = None
    if '-s' in sys.argv:
        silent = True
    if '--py3' in sys.argv:
        py3 = True
    if '--force' in sys.argv:
        force = True
    if '-t' in sys.argv:
        indent = '\t'
    try:
        index_o = sys.argv.index('-o')
        if index_o == len(sys.argv)-2:
            err_no_in_file()
        out_file = sys.argv[index_o+1]
    except ValueError:
        pass
    convert(in_file, out_file)


if __name__ == '__main__':
    main()
