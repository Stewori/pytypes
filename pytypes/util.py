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

# Created on 12.12.2016

"""
Contains utility functions that are not strictly related to typing.
This scopes e.g. inspection, OOP, etc.

Todo: Some functions in this module can be simplified or replaced
      by more consequent use of inspect module.
"""

import pytypes
import subprocess
import hashlib
import sys
import os
import inspect
import traceback
from warnings import warn_explicit


_code_callable_dict = {}
_sys_excepthook = sys.__excepthook__


def _check_python3_5_version():
    try:
        ver = subprocess.check_output([pytypes.python3_5_executable, '--version'])
        ver = ver[:-1].split(' ')[-1].split('.')
        return (int(ver[0]) >= 3 and int(ver[1]) >= 5)
    except Exception:
        return False


def _md5(fname):
    m = hashlib.md5()
    with open(fname, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            m.update(chunk)
    return m.hexdigest()


def _python_version_string():
    try:
        impl = sys.subversion[0]
    except AttributeError:
        impl = sys.implementation.name
        if impl == 'cpython':
            impl = 'CPython'
    lst = [impl,
            '.'.join([str(x) for x in sys.version_info[:3]]),
            ' '.join([str(x) for x in sys.version_info[3:]])]
    return '%s %s %s' % tuple(lst)


def _full_module_file_name_nosuffix(module_name):
    module = sys.modules[module_name]
    bn = os.path.basename(module.__file__).partition('.')[0]
    if not (module.__package__ is None or module.__package__ == ''):
        return module.__package__.replace('.', os.sep)+os.sep+bn
    else:
        return bn


def _find_files(file_name, search_paths):
    res = []
    if os.path.isfile(file_name):
        res.append(file_name)
    if search_paths is None:
        return res
    for path in search_paths:
        if not path.endswith(os.sep):
            file_path = path+os.sep+file_name
        else:
            file_path = path+file_name
        if os.path.isfile(file_path):
            res.append(file_path)
    return res


def getargspecs(func):
    """Bridges inspect.getargspec and inspect.getfullargspec.
    Automatically selects the proper one depending of current Python version.
    Automatically bypasses wrappers from typechecked- and override-decorators.
    """
    if func is None:
        raise TypeError('None is not a Python function')
    if hasattr(func, 'ch_func'):
        return getargspecs(func.ch_func)
    elif hasattr(func, 'ov_func'):
        return getargspecs(func.ov_func)
    if hasattr(inspect, 'getfullargspec'):
        return inspect.getfullargspec(func) # Python 3
    else:
        return inspect.getargspec(func)


def get_required_kwonly_args(argspecs):
    """Determines whether given argspecs implies required keywords-only args
    and returns them as a list. Returns empty list if no such args exist.
    """
    try:
        kwonly = argspecs.kwonlyargs
        if argspecs.kwonlydefaults is None:
            return kwonly
        res = []
        for name in kwonly:
            if not name in argspecs.kwonlydefaults:
                res.append(name)
        return res
    except AttributeError:
        return []


def getargnames(argspecs, with_unbox=False):
    """Resembles list of arg-names as would be seen in a function signature, including
    var-args, var-keywords and keyword-only args.
    """
    # todo: We can maybe make use of inspect.formatargspec
    args = argspecs.args
    vargs = argspecs.varargs
    try:
        kw = argspecs.keywords
    except AttributeError:
        kw = argspecs.varkw
    try:
        kwonly = argspecs.kwonlyargs
    except AttributeError:
        kwonly = None
    res = []
    if not args is None:
        res.extend(args)
    if not vargs is None:
        res.append('*'+vargs if with_unbox else vargs)
    if not kwonly is None:
        res.extend(kwonly)
    if not kw is None:
        res.append('**'+kw if with_unbox else kw)
    return res


def getargskw(args, kw, argspecs):
    """Resembles list of args as would be passed to a function call, including
    var-args, var-keywords and keyword-only args.
    Arg values are taken from args, kw and - if needed - from argspecs defaults.
    These values are then ordered according to argspecs and returned as a list.
    """
    return _getargskw(args, kw, argspecs)[0]


def _getargskw(args, kw, argspecs):
    res = []
    err = False
    try:
        kwds = argspecs.keywords
    except AttributeError:
        kwds = argspecs.varkw
    if not kwds is None:
        used = set()
    if len(args) > len(argspecs.args):
        if not argspecs.varargs is None:
            # include the remaining args as varargs
            res.extend(args[:len(argspecs.args)])
            res.append(args[len(argspecs.args):])
        else:
            # note an err, but still add all args for tracking
            err = True
            res.extend(args)
    elif len(args) < len(argspecs.args):
        res.extend(args)
        # we'll try to get the remaining args from kw or defaults
        ipos = -len(argspecs.args)+len(res)
        for name in argspecs.args[len(args):]:
            if name in kw:
                res.append(kw[name])
                if not kwds is None:
                    used.add(name)
            elif not argspecs.defaults is None:
                # Todo: Guard failure here and set err accordingly
                res.append(argspecs.defaults[ipos])
            else:
                err = True
            ipos += 1
        if not argspecs.varargs is None:
            res.append(tuple())
    else:
        res.extend(args)
        if not argspecs.varargs is None:
            res.append(tuple())
    try:
        # eventually process kw-only args
        ipos = -len(argspecs.kwonlyargs)
        for name in argspecs.kwonlyargs:
            if name in kw:
                res.append(kw[name])
                if not kwds is None:
                    used.add(name)
            else:
                # Todo: Guard failure here and set err accordingly
#				This assumed kwonlydefaults to be a list:
#				if not argspecs.kwonlydefaults is None and \
#						len(argspecs.kwonlydefaults) > ipos:
#					res.append(argspecs.kwonlydefaults[ipos])
                if not argspecs.kwonlydefaults is None and \
                        name in argspecs.kwonlydefaults:
                    res.append(argspecs.kwonlydefaults[name])
                else:
                    err = True
            ipos += 1
    except AttributeError:
        pass
    except TypeError:
        err = True
    if not kwds is None:
        if len(used) > 0:
            kw2 = {}
            if len(used) < len(kw):
                for name in kw:
                    if not name in used:
                        kw2[name] = kw[name]
            res.append(kw2)
        else:
            res.append(kw)
    return tuple(res), err


def fromargskw(argskw, argspecs, slf_or_clsm = False):
    """Turns a linearized list of args into (args, keywords) form
    according to given argspecs (like inspect module provides).
    """
    res_args = argskw
    try:
        kwds = argspecs.keywords
    except AttributeError:
        kwds = argspecs.varkw
    if not kwds is None:
        res_kw = argskw[-1]
        res_args = argskw[:-1]
    else:
        res_kw = None
    if not argspecs.varargs is None:
        vargs_pos = (len(argspecs.args)-1) \
                if slf_or_clsm else len(argspecs.args)
        if vargs_pos > 0:
            res_lst = list(argskw[:vargs_pos])
            res_lst.extend(argskw[vargs_pos])
            res_args = tuple(res_lst)
        else:
            res_args = argskw[0]
    try:
        if len(argspecs.kwonlyargs) > 0:
            res_kw = {} if res_kw is None else dict(res_kw)
            ipos = -len(argspecs.kwonlyargs) - (0 if kwds is None else 1)
            for name in argspecs.kwonlyargs:
                res_kw[name] = argskw[ipos]
                ipos += 1
    except AttributeError:
        pass
    if res_kw is None:
        res_kw = {}
    return res_args, res_kw


def _unchecked_backend(func):
    if hasattr(func, 'ov_func'):
        return _unchecked_backend(func.ov_func)
    elif hasattr(func, 'ch_func'):
        return _unchecked_backend(func.ch_func)
    else:
        return func


def _actualfunc(func, prop_getter = False):
    if type(func) == classmethod or type(func) == staticmethod:
        return _actualfunc(func.__func__, prop_getter)
    if isinstance(func, property):
        if prop_getter: # force getter
            return _actualfunc(func.fget, prop_getter)
        else: # auto decide
            return _actualfunc(func.fget if func.fset is None else func.fset, prop_getter)
    # Todo: maybe rename ov_func and ch_func also to __func__
    elif hasattr(func, 'ov_func'):
        return _actualfunc((func.ov_func), prop_getter)
    elif hasattr(func, 'ch_func'):
        return _actualfunc((func.ch_func), prop_getter)
    return func


def _get_class_nesting_list_for_staticmethod(staticmeth, module_or_class, stack, rec_set):
    if hasattr(module_or_class, _actualfunc(staticmeth).__name__):
        val = getattr(module_or_class, _actualfunc(staticmeth).__name__)
        bck = _unchecked_backend(staticmeth)
        try:
            if _unchecked_backend(val) is bck.__func__:
                return stack
        except AttributeError:
            pass
        if _unchecked_backend(val) is bck:
            return stack
    classes = [cl[1] for cl in inspect.getmembers(module_or_class, inspect.isclass)]
    mod_name = module_or_class.__module__ if inspect.isclass(module_or_class) \
            else module_or_class.__name__
    for cl in classes:
        if cl.__module__ == mod_name and not cl in rec_set:
            stack.append(cl)
            rec_set.add(cl)
            result = _get_class_nesting_list_for_staticmethod(staticmeth, cl, stack, rec_set)
            if not result is None:
                return result
            stack.pop()
    return None


def _get_class_nesting_list_py2(cls, module_or_class, stack, rec_set):
    classes = [cl[1] for cl in inspect.getmembers(module_or_class, inspect.isclass)]
    mod_name = module_or_class.__module__ if inspect.isclass(module_or_class) \
            else module_or_class.__name__
    for cl in classes:
        if cl.__module__ == mod_name and not cl in rec_set:
            if cl is cls:
                return stack
            stack.append(cl)
            rec_set.add(cl)
            result = _get_class_nesting_list_py2(cls, cl, stack, rec_set)
            if not result is None:
                return result
            stack.pop()
    return None


def _get_class_nesting_list(cls, module_or_class):
    if hasattr(cls, '__qualname__'):
        names = cls.__qualname__.split('.')
        cl = module_or_class
        res = []
        for name in names[:-1]:
            cl = getattr(cl, name)
            res.append(cl)
        return res
    else:
        res = _get_class_nesting_list_py2(cls, module_or_class, [], set())
        return [] if res is None else res


def get_staticmethod_qualname(staticmeth):
    """Determines the fully qualified name of a static method.
    Yields a result similar to what __qualname__ would contain, but is applicable
    to static methods and also works in Python 2.7.
    """
    func = _actualfunc(staticmeth)
    module = sys.modules[func.__module__]
    nst = _get_class_nesting_list_for_staticmethod(staticmeth, module, [], set())
    nst = [cl.__name__ for cl in nst]
    return '.'.join(nst)+'.'+func.__name__


def get_class_qualname(cls):
    """Determines the fully qualified name of a class.
    Yields a result similar to what __qualname__ contains, but also works on
    Python 2.7.
    """
    if hasattr(cls, '__qualname__'):
        return cls.__qualname__
    module = sys.modules[cls.__module__]
    if not hasattr(cls, '__name__'):
        # Python 3.7
        res = cls._name if not cls._name is None else cls.__origin__.__name__
        return res
    if hasattr(module, cls.__name__) and getattr(module, cls.__name__) is cls:
        return cls.__name__
    else:
        nst = _get_class_nesting_list(cls, module)
        nst.append(cls)
        nst = [cl.__name__ for cl in nst]
        return '.'.join(nst)
    return cls.__name__


def search_class_module(cls, deep_search=True):
    """E.g. if cls is a TypeVar, cls.__module__ won't contain the actual module
    that declares cls. This returns the actual module declaring cls.
    Can be used with any class (not only TypeVar), though usually cls.__module__
    is the recommended way.
    If deep_search is True (default) this even finds the correct module if it
    declares cls as an inner class of another class.
    """
    for md_name in sys.modules:
        module = sys.modules[md_name]
        if hasattr(module, cls.__name__) and getattr(module, cls.__name__) is cls:
            return module
    if deep_search:
        for md_name in sys.modules:
            module = sys.modules[md_name]
            try:
                nst = _get_class_nesting_list(cls, module)
                if cls is nst[-1]:
                    return module
            except:
                pass
    return None


def get_class_that_defined_method(meth):
    """Determines the class owning the given method.
    """
    if is_classmethod(meth):
        return meth.__self__
    if hasattr(meth, 'im_class'):
        return meth.im_class
    elif hasattr(meth, '__qualname__'):
        # Python 3
        try:
            cls_names = meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0].split('.')
            cls = inspect.getmodule(meth)
            for cls_name in cls_names:
                cls = getattr(cls, cls_name)
            if isinstance(cls, type):
                return cls
        except AttributeError:
            # If this was called from a decorator and meth is not a method, this
            # can result in AttributeError, because at decorator-time meth has not
            # yet been added to module. If it's really a method, its class would be
            # already in, so no problem in that case.
            pass
    raise ValueError(str(meth)+' is not a method.')


def is_method(func):
    """Detects if the given callable is a method. In context of pytypes this
    function is more reliable than plain inspect.ismethod, e.g. it automatically
    bypasses wrappers from typechecked and override decorators.
    """
    func0 = _actualfunc(func)
    argNames = getargnames(getargspecs(func0))
    if len(argNames) > 0:
        if argNames[0] == 'self':
            if inspect.ismethod(func):
                return True
            elif sys.version_info.major >= 3:
                # In Python3 there are no unbound methods, so we count as method,
                # if first arg is called 'self' 
                return True
            else:
                _warn_argname('is_method encountered non-method declaring self',
                        func0, False, False, None)
        else:
            return inspect.ismethod(func)
    return False


def is_classmethod(meth):
    """Detects if the given callable is a classmethod.
    """
    if inspect.ismethoddescriptor(meth):
        return isinstance(meth, classmethod)
    if not inspect.ismethod(meth):
        return False
    if not inspect.isclass(meth.__self__):
        return False
    if not hasattr(meth.__self__, meth.__name__):
        return False
    return meth == getattr(meth.__self__, meth.__name__)


def _fully_qualified_func_name(func, slf_or_clsm, func_class, cls_name = None):
    func0 = _actualfunc(func)
    # Todo: separate classmethod/static method prefix from qualified_func_name
    if slf_or_clsm:
        # Todo: This can be simplified
        if (not func_class is None) and (not type(func) is classmethod) \
                and (not is_classmethod(func)):
            func = getattr(func_class, func.__name__)
        if ((not cls_name is None) or hasattr(func, 'im_class')) and not is_classmethod(func):
            return ('%s.%s.%s') % (func0.__module__,
                    cls_name if not cls_name is None else get_class_qualname(func.im_class),
                    func0.__name__)
        else:
            assert (not func_class is None or not cls_name is None)
            prefix = 'classmethod ' if is_classmethod(func) else ''
            return (prefix+'%s.%s.%s') % (func0.__module__,
                    cls_name if not cls_name is None else get_class_qualname(func_class),
                    func0.__name__)
    else:
        stat = type(func) == staticmethod
        if not stat and not func_class is None:
            stat = type(func_class.__dict__[func.__name__]) == staticmethod
        if stat:
            if not func_class is None:
                stat_qn = '%s.%s' % (
                        cls_name if not cls_name is None else get_class_qualname(func_class),
                        func0.__name__)
            else:
                stat_qn = get_staticmethod_qualname(func)
            return ('static method %s.%s') % (func0.__module__, stat_qn)
        elif not func_class is None:
            return ('%s.%s.%s') % (func0.__module__,
                    cls_name if not cls_name is None else get_class_qualname(func_class),
                    func0.__name__)
        else:
            return ('%s.%s') % (func0.__module__, func0.__name__)


def get_current_function(caller_level = 0):
    """Determines the function from which this function was called.
    Use caller_level > 0 to get even earlier functions from current stack.
    """
    return _get_current_function_fq(1+caller_level)[0][0]


def _get_current_function_fq(caller_level = 0):
    stck = inspect.stack()
    code = stck[1+caller_level][0].f_code
    res = get_callable_fq_for_code(code)
    if res[0] is None and len(stck) > 2+caller_level:
        res = get_callable_fq_for_code(code, stck[2+caller_level][0].f_locals)
    return res, code


def get_current_args(caller_level = 0, func = None, argNames = None):
    """Determines the args of current function call.
    Use caller_level > 0 to get args of even earlier function calls in current stack.
    """
    if argNames is None:
        argNames = getargnames(getargspecs(func))
    if func is None:
        func = get_current_function(caller_level+1)
    if isinstance(func, property):
        func = func.fget if func.fset is None else func.fset
    stck = inspect.stack()
    lcs = stck[1+caller_level][0].f_locals
    return tuple([lcs[t] for t in argNames])


def get_current_module(caller_level = 0):
    stck = inspect.stack()
    return getmodule(stck[1+caller_level][0].f_code)


def getmodule(code):
    """More robust variant of inspect.getmodule.
    E.g. has less issues on Jython.
    """
    try:
        md = inspect.getmodule(code, code.co_filename)
    except AttributeError:
        return inspect.getmodule(code)
    if md is None:
        # Jython-specific:
        # This is currently just a crutch; todo: resolve __pyclasspath__ properly!
        cfname = code.co_filename.replace('__pyclasspath__',
                os.path.realpath('')+os.sep+'__pyclasspath__')
        cfname = cfname.replace('$py.class', '.py')
        md = inspect.getmodule(code, cfname)
    if md is None:
        md = inspect.getmodule(code)
    return md


def getmodule_for_member(func, prop_getter=False):
    if isinstance(func, property):
        md = func.fget.__module__ if prop_getter else func.fset.__module__
        return sys.modules[md]
    else:
        func0 = func
        while hasattr(func0, '__func__'):
            func0 = func0.__func__
        return sys.modules[func0.__module__]


def get_callable_fq_for_code(code, locals_dict = None):
    """Determines the function belonging to a given code object in a fully qualified fashion.
    Returns a tuple consisting of
    - the callable
    - a list of classes and inner classes, locating the callable (like a fully qualified name)
    - a boolean indicating whether the callable is a method
    """
    if code in _code_callable_dict:
        res = _code_callable_dict[code]
        if not res[0] is None or locals_dict is None:
            return res
    md = getmodule(code)
    if not md is None:
        nesting = []
        res, slf = _get_callable_fq_for_code(code, md, md, False, nesting, set())
        if res is None and not locals_dict is None:
            nesting = []
            res, slf = _get_callable_from_locals(code, locals_dict, md, False, nesting)
        else:
            _code_callable_dict[code] = (res, nesting, slf)
        return res, nesting, slf
    else:
        return None, None, None


def _get_callable_from_locals(code, locals_dict, module, slf, nesting):
    keys = [key for key in locals_dict]
    for key in keys:
        slf2 = slf
        obj = locals_dict[key]
        if inspect.isfunction(obj):
            try:
                if obj.__module__ == module.__name__ and _code_matches_func(obj, code):
                    return obj, slf2
            except AttributeError:
                try:
                    if obj.__func__.__module__ == module.__name__ and \
                            _code_matches_func(obj, code):
                        return obj, slf2
                except AttributeError:
                    pass
        elif inspect.isclass(obj) and obj.__module__ == module.__name__:
            nesting.append(obj)
            res, slf2 = _get_callable_fq_for_code(code, obj, module, True, nesting, set())
            if not res is None:
                return res, slf2
            else:
                nesting.pop()
    return None, False


def _get_callable_fq_for_code(code, module_or_class, module, slf, nesting, cache):
    keys = [key for key in module_or_class.__dict__]
    cache.add(module_or_class)
    for key in keys:
        slf2 = slf
        obj = module_or_class.__dict__[key]
        if pytypes.type_util._check_as_func(obj):
            if isinstance(obj, classmethod) or isinstance(obj, staticmethod):
                obj = obj.__func__
                slf2 = False
            elif isinstance(obj, property):
                slf2 = True
                if not obj.fset is None:
                    try:
                        if obj.fset.__module__ == module.__name__ and \
                                _code_matches_func(obj.fset, code):
                            return getattr(module_or_class, key), slf2
                    except AttributeError:
                        try:
                            if obj.fset.__func__.__module__ == module.__name__ and \
                                    _code_matches_func(obj.fset, code):
                                return getattr(module_or_class, key), slf2
                        except AttributeError:
                            pass
                obj = obj.fget
            try:
                if obj.__module__ == module.__name__ and _code_matches_func(obj, code):
                    return getattr(module_or_class, key), slf2
            except AttributeError:
                try:
                    if obj.__func__.__module__ == module.__name__ and \
                            _code_matches_func(obj, code):
                        return getattr(module_or_class, key), slf2
                except AttributeError:
                    pass
        elif inspect.isclass(obj) and obj.__module__ == module.__name__ and not obj in cache:
            nesting.append(obj)
            res, slf2 = _get_callable_fq_for_code(code, obj, module, True, nesting, cache)
            if not res is None:
                return res, slf2
            else:
                nesting.pop()
    return None, False


def _code_matches_func(func, code):
    if func.__code__ == code:
        return True
    else:
        try:
            return _code_matches_func(func.ch_func, code)
        except AttributeError:
            try:
                return _code_matches_func(func.ov_func, code)
            except AttributeError:
                try:
                    return _code_matches_func(func.__func__, code)
                except AttributeError:
                    return False


def get_function_perspective_globals(module_name, level=0, max_level=None):
    globs = {}
    if not module_name is None:
        if module_name.endswith('.pyi') or module_name.endswith('.pyi2'):
            globs.update(sys.modules[module_name].__dict__)
            try:
                # In case of something like stubfile_2_converter a stub without module
                # might be present, which would cause KeyError here.
                globs.update(sys.modules[module_name.rsplit('.', 1)[0]].__dict__)
            except KeyError:
                pass
        else:
            globs.update(sys.modules[module_name].__dict__)
    if level != max_level:
        stck = inspect.stack()
        for ln in stck[level:max_level]:
            globs.update(ln[0].f_locals)
    return globs


def _mro(clss, dest = []):
    if not clss in dest:
        dest.append(clss)
        for clss2 in clss.__bases__:
            _mro(clss2, dest)
    return dest


def mro(clss):
    # We can replace this by inspect.getmro, but we should
    # wait until http://bugs.jython.org/issue2581 is fixed.
    try:
        return clss.__mro__
    except AttributeError:
        return _mro(clss)


def _orig_mro(clss, dest = []):
    if not clss in dest:
        dest.append(clss)
        for clss2 in pytypes.type_util._bases(clss):
                _orig_mro(clss2, dest)
    return dest


def orig_mro(clss):
    return _orig_mro(clss)


def _has_base_method(meth, cls):
    meth0 = _actualfunc(meth)
    for cls1 in mro(cls)[1:]:
        if hasattr(cls1, meth0.__name__):
            fmeth = getattr(cls1, meth0.__name__)
            if inspect.isfunction(fmeth) or inspect.ismethod(fmeth) \
                    or inspect.ismethoddescriptor(fmeth):
                return True
    return False


def _calc_traceback_limit(tb):
    """Calculates limit-parameter to strip away pytypes' internals when used
    with API from traceback module.
    """
    limit = 1
    tb2 = tb
    while not tb2.tb_next is None:
        try:
            maybe_pytypes = tb2.tb_next.tb_frame.f_code.co_filename.split(os.sep)[-2]
        except IndexError:
            maybe_pytypes = None
        if maybe_pytypes == 'pytypes' and not \
                tb2.tb_next.tb_frame.f_code == pytypes.typechecker._pytypes___import__.__code__:
            break
        else:
            limit += 1
            tb2 = tb2.tb_next
    return limit


def _calc_traceback_list_offset(tb_list):
    for off in range(len(tb_list)):
        # if tb_list[off].filename looks like '.../pytypes/x/y':
        try:
            path = tb_list[off].filename.split(os.sep)
        except AttributeError:
            return 0
        if len(path) >= 2 and path[-2] == 'pytypes':
            return off-2 if off >= 2 else 0
    return -1


def _warn_argname(msg, func, slf, clsm, cls=None, warn_tp=pytypes.exceptions.TypeWarning):
    if not pytypes.warn_argnames:
        return
    if cls is None:
        if slf or clsm:
            try:
                cls_name = get_class_that_defined_method(func).__name__
            except:
                cls_name = '<unknown class>'
        else:
            cls_name = None
    else:
        cls_name = cls.__name__
    tb = traceback.extract_stack()
    off = _calc_traceback_list_offset(tb)
    if cls_name is None:
        _msg = '%s: %s.%s'%(msg, func.__module__, func.__name__)
    else:
        _msg = '%s: %s.%s.%s'%(msg, func.__module__, cls_name, func.__name__)
    warn_explicit(_msg, warn_tp, tb[off][0], tb[off][1])


def _install_excepthook():
    global _sys_excepthook #, _excepthook_installed
# 	if _excepthook_installed:
# 		return
# 	_excepthook_installed = True
    if sys.excepthook != _pytypes_excepthook:
        _sys_excepthook = sys.excepthook
        sys.excepthook = _pytypes_excepthook


def _pytypes_excepthook(exctype, value, tb):
    """"An excepthook suitable for use as sys.excepthook, that strips away
    the part of the traceback belonging to pytypes' internals.
    Can be switched on and off via pytypes.clean_traceback
    or pytypes.set_clean_traceback.
    The latter automatically installs this hook in sys.excepthook.
    """
    if pytypes.clean_traceback and issubclass(exctype, TypeError):
        traceback.print_exception(exctype, value, tb, _calc_traceback_limit(tb))
    else:
        if _sys_excepthook is None:
            sys.__excepthook__(exctype, value, tb)
        else:
            _sys_excepthook(exctype, value, tb)


def _is_in(obj, lst):
    """Checks if obj is in lst using referential equality.
    """
    return any(el is obj for el in lst)
