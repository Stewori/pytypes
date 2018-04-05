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

import atexit
import imp
import inspect
import os
import subprocess
import sys
import tempfile
import warnings
from inspect import isclass, ismodule, ismethod
try:
    from backports.typing import Union, Tuple, Callable
except ImportError:
    from typing import Union, Tuple, Callable

import pytypes
from pytypes import util

stub_descr = ('.pyi', 'r', imp.PY_SOURCE)
stub_modules = {}
if sys.version_info.major >= 3:
    _stub_modules_loading = {}
else:
    _stub_modules_loading = stub_modules

if os.name == 'java':
    module_filename_delim = '$'
else:
    module_filename_delim = '.'


def _create_Python_2_stub(module_filepath, out_file = None):
    if out_file is None:
        out_file = _gen_stub2_filename(module_filepath)
    dirname = os.path.dirname(__file__)
    sep = __file__[len(dirname)]
    conv_script = dirname+sep+'stubfile_2_converter.py'
    # env = {} is required to prevent pydev from crashing
    subprocess.call([pytypes.python3_5_executable, conv_script,
            '-s', '-o', out_file, module_filepath], env = {})


def _match_classes(stub_module_or_class, original_module_or_class, original_module_name):
    classes = [cl[1] for cl in inspect.getmembers(original_module_or_class, isclass)]
    for cl in classes:
        if cl.__module__ == original_module_name and hasattr(stub_module_or_class, cl.__name__):
            # Todo: What if stub_file uses slots? (unlikely (?))
            stub_class = getattr(stub_module_or_class, cl.__name__)
            # Maybe we should assert that stub_class.__module__ is really the stub module.
            # However that might prevent some import tricks and modularity management in
            # a smarter stubfile hierarchy. So we leave it like this for now.
            stub_class._match_type = cl
            _match_classes(stub_class, cl, original_module_name)


def _match_module(stub_module, original_module):
    return _match_classes(stub_module, original_module, original_module.__name__)


def _re_match_module(module_name, final = False):
    if sys.version_info.major >= 3:
        module = sys.modules[module_name]
        assert(ismodule(module))
        m_name = module.__name__

        if m_name.endswith('.pyi') or m_name.endswith('.pyi2'):
            return
        m_key = m_name+str(id(module))
        if m_key in _stub_modules_loading:
            stub_m = _stub_modules_loading[m_key]
            _match_module(stub_m, module)
            if final:
                stub_modules[m_key] = stub_m
                del _stub_modules_loading[m_key]


def _get_stub_module(module_filepath, original_module):
    module_name = os.path.basename(module_filepath)
    pck = original_module.__name__.rsplit('.', 1)[0]
    try:
        with open(module_filepath) as module_file:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                stub_module = imp.load_module(pck+'.'+module_name, module_file, module_filepath, stub_descr)
                if sys.version_info.major >= 3:
                    _match_module(stub_module, original_module)
                return stub_module
    except SyntaxError:
        return None


def _find_stub_files(module_name):
    full_name = util._full_module_file_name_nosuffix(module_name)
    file_name = full_name+'.pyi'
    file_name2 = _plain_stub2_filename(file_name)
    return util._find_files(file_name, pytypes.stub_path), util._find_files(
            file_name2, pytypes.stub_path)


def _plain_stub2_filename(stub_file):
    return stub_file.rpartition(module_filename_delim)[0]+'.pyi2'


def _gen_stub2_filename(stub_file, base_module):
    if os.path.isfile(stub_file):
        bn = os.path.basename(stub_file).rpartition(module_filename_delim)[0]
        if pytypes.stub_gen_dir is None:
            checksum = util._md5(stub_file)
            return tempfile.gettempdir()+os.sep+bn+'__'+checksum+'.pyi2'
        else:
            pck = '' if base_module.__package__ is None else \
                    base_module.__package__.replace('.', os.sep)+os.sep
            return os.path.abspath(pytypes.stub_gen_dir)+os.sep+pck+bn+'.pyi2'
    else:
        # If there is no original file, no generated file(name) can be created:
        return None


def _check_py2_stubmodule(pyi_file, pyi2_module):
    if pyi2_module.__doc__ is None:
        # File was hand-crafted.
        return True
    lines = pyi2_module.__doc__.split('\n')
    if len(lines) < 5 or lines[4] != 'This file was generated by pytypes. Do not edit directly.':
        # File was hand-crafted.
        return True
    if (not pyi_file is None) and os.path.normpath(pyi_file) != os.path.normpath(lines[2]):
        # File wasn't generated from the source we thought it was.
        return False
    in_file = lines[2] if pyi_file is None else pyi_file
    if os.path.isfile(in_file):
        return lines[3].endswith(util._md5(in_file))
    else:
        return False


def get_stub_module(func):
    if not hasattr(func, '__module__') or func.__module__ is None:
        return None
    if not func.__module__ in sys.modules or sys.modules[func.__module__] is None:
        return None
    module = sys.modules[func.__module__]
    assert(ismodule(module))
    m_name = module.__name__

    if m_name.endswith('.pyi') or m_name.endswith('.pyi2'):
        return None
    m_key = m_name+str(id(module))
    if m_key in stub_modules:
        return stub_modules[m_key]
    if m_key in _stub_modules_loading:
        _re_match_module(m_name)
        return _stub_modules_loading[m_key]

    # Built-in modules have no __file__ attribute
    try:
        mdfile = module.__file__
    except AttributeError:
        return None

    # Jython-specific:
    # This is currently just a crutch; todo: resolve __pyclasspath__ properly!
    mdfile = mdfile.replace('__pyclasspath__', os.path.realpath(''))
    module_filepath = mdfile.rpartition(module_filename_delim)[0]+'.pyi'
    module_filepath2 = _plain_stub2_filename(mdfile)
    stub_files = _find_stub_files(m_name)
    if os.path.isfile(module_filepath):
        stub_files[0].append(module_filepath)
    if os.path.isfile(module_filepath2):
        stub_files[1].append(module_filepath2)
    module_filepath2_gen = _gen_stub2_filename(module_filepath, module)
    if not (sys.version_info.major >= 3 and sys.version_info.minor >= 5):
        # Python version < 3.5, so try to use a Python 2-style stub.
        # First look for a not-generated one:
        for module_filepath2_plain in stub_files[1]:
            stub_module = _get_stub_module(module_filepath2_plain, module)
            if not stub_module is None:
                _stub_modules_loading[m_key] = stub_module
                return stub_module
        # Now for a previously generated one:
        if (not module_filepath2_gen is None) and os.path.isfile(module_filepath2_gen):
            stub_module = _get_stub_module(module_filepath2_gen, module)
            if not stub_module is None:
                # A generated module might be outdated:
                # We only check this and attempt to re-create outdated stub-files
                # for files found under stub_gen_dir.
                for module_filepath in stub_files[0]:
                    if _check_py2_stubmodule(module_filepath, stub_module):
                        _stub_modules_loading[m_key] = stub_module
                        return stub_module
                # Otherwise we let the code below re-create the module.
                # Note that we cannot be in tmp-dir mode, since the pyi2-file
                # would not have been kept in that case.
    # Python >= 3.5 or no Python 2-style stub available, so try original stub:
    # Simply try to load one of the stubs in search-folders:
    for module_filepath in stub_files[0]:
        stub_module = _get_stub_module(module_filepath, module)
        if not stub_module is None:
            _stub_modules_loading[m_key] = stub_module
            return stub_module
    # Try Python2-style stubs in search-folders, even if running Python 3:
    for module_filepath in stub_files[1]:
        stub_module = _get_stub_module(module_filepath, module)
        if not stub_module is None:
            _stub_modules_loading[m_key] = stub_module
            return stub_module
    # Finally try to convert a Python3 stub to Python2-style:
    if not (sys.version_info.major >= 3 and sys.version_info.minor >= 5):
        # Most likely the module-stub could not be loaded due to Python 3.5-syntax
        if util._check_python3_5_version():
            for module_filepath in stub_files[0]:
                # We try to use a local Python 3 version to generate a Python 2-style stub:
                _create_Python_2_stub(module_filepath, module_filepath2_gen)
                if os.path.isfile(module_filepath2_gen):
                    stub_module = _get_stub_module(module_filepath2_gen, module)
                    if pytypes.stub_gen_dir is None:
                        atexit.register(os.remove, module_filepath2_gen)
                        atexit.register(os.remove, module_filepath2_gen+'c')
                        # Todo: Clean up other potential by-products
                    if not stub_module is None:
                        _stub_modules_loading[m_key] = stub_module
                        return stub_module
                #else:
                # Todo: Raise warning in verbose mode.
    # No stub-file available
    stub_modules[m_key] = None
    return None


def _match_stub_type(stub_type):
    if not (sys.version_info.major >= 3):
        return stub_type
    # Todo: Only apply if stub-module is involved
    # Todo: Somehow cache results
    if pytypes.is_Tuple(stub_type):
        prms = pytypes.get_Tuple_params(stub_type)
        res = Tuple[(tuple(_match_stub_type(t) for t in prms))]
    elif pytypes.is_Union(stub_type):
        try:
            # Python 3.6
            res = Union[tuple(_match_stub_type(t) for t in stub_type.__args__)]
        except AttributeError:
            res = Union[tuple(_match_stub_type(t) for t in stub_type.__union_params__)]
    elif pytypes.is_Generic(stub_type):
        if stub_type.__args__ is None:
            res = stub_type
        elif pytypes.is_Callable(stub_type):
            if hasattr(stub_type, '__result__'):
                res = Callable[tuple(_match_stub_type(t) for t in stub_type.__args__)]
                res.__result__ = _match_stub_type(stub_type.__result__)
            else:
                res = Callable[tuple([
                        [_match_stub_type(t) for t in stub_type.__args__[:-1]],
                        _match_stub_type(stub_type.__args__[-1]) ]) ]
        else:
            tpl = tuple(_match_stub_type(t) for t in stub_type.__args__)
            try:
                res = stub_type.__origin__[tpl]
            except TypeError:
                res = pytypes.abc2typing_dict[stub_type.__origin__][tpl]
    elif isclass(stub_type):
        res = stub_type._match_type if hasattr(stub_type, '_match_type') else stub_type
    else:
        res = stub_type
    return res


def as_stub_func_if_any(func0, decorated_func = None, func_class = None, nesting = None):
    # Check for stubfile
    # Todo: Compactify
    module = get_stub_module(func0)
    if not module is None:
        if hasattr(module, func0.__name__):
            res = getattr(module, func0.__name__)
            if inspect.isfunction(res) or inspect.ismethod(res) \
                    or inspect.ismethoddescriptor(res):
                return getattr(module, func0.__name__)
        if not decorated_func is None and ismethod(decorated_func):
            cls = util.get_class_that_defined_method(decorated_func)
            if hasattr(module, cls.__name__):
                cls2 = getattr(module, cls.__name__)
                if hasattr(cls2, func0.__name__):
                    return getattr(cls2, func0.__name__)
            else:
                if nesting is None:
                    nesting = util._get_class_nesting_list(cls, sys.modules[cls.__module__])
                else:
                    nesting = nesting[:-1]
                if not nesting is None:
                    mcls = module
                    try:
                        for cl in nesting:
                            mcls = getattr(mcls, cl.__name__)
                        mcls = getattr(mcls, cls.__name__)
                        return getattr(mcls, func0.__name__)
                    except AttributeError:
                        pass
        elif not func_class is None:
            if hasattr(module, func_class.__name__):
                cls2 = getattr(module, func_class.__name__)
                if hasattr(cls2, func0.__name__):
                    return getattr(cls2, func0.__name__)
            else:
                if nesting is None:
                    nesting = util._get_class_nesting_list(func_class, sys.modules[func_class.__module__])
                if not nesting is None:
                    mcls = module
                    try:
                        for cl in nesting:
                            mcls = getattr(mcls, cl.__name__)
                        mcls = getattr(mcls, func_class.__name__)
                        return getattr(mcls, func0.__name__)
                    except AttributeError:
                        pass

        if nesting is None:
            nesting = util._get_class_nesting_list_for_staticmethod(decorated_func,
                    sys.modules[func0.__module__], [], set())
        if not nesting is None:
                mcls = module
                try:
                    for cl in nesting:
                        mcls = getattr(mcls, cl.__name__)
                    return getattr(mcls, func0.__name__)
                except AttributeError:
                    pass
    return func0
