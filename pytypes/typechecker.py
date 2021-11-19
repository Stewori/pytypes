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

# Created on 20.08.2016

"""
Part of pytypes. Contains code specifically for typechecking.
"""

import atexit
import inspect
import re as _re
import sys
import types
import typing
import collections
from inspect import isclass, ismodule, isfunction, ismethod, ismethoddescriptor
from warnings import warn

import pytypes
from .exceptions import InputTypeError, ReturnTypeError, OverrideError
from .stubfile_manager import _match_stub_type, _re_match_module
from .util import getargspecs, _actualfunc
from .type_util import type_str, has_type_hints, _has_type_hints, is_builtin_type, \
        deep_type, _funcsigtypes, _issubclass, _isinstance, _find_typed_base_method, \
        _preprocess_typecheck, _raise_typecheck_error, _check_caller_type, TypeAgent, \
        _check_as_func, is_Tuple, get_orig_class
from . import util, type_util

if sys.version_info.major >= 3:
    import builtins
else:
    import __builtin__ as builtins

_not_type_checked = set()
_fully_typechecked_modules = {}
_auto_override_modules = {}

_pending_modules = {}
_delayed_checks = []

_import_hook_installed = False

# Monkeypatch import to
# process forward-declarations after module loading finished
# and eventually apply global typechecking:
_python___import__ = builtins.__import__
# Todo: We will turn this monkeypatch into an import hook.
def _pytypes___import__(name, globls=None, locls=None, fromlist=(), level=0):
    if not name in _pending_modules:
        _pending_modules[name] = []
        res = _python___import__(name, globls, locls, fromlist, level)
        pending_decorators = _pending_modules[name]
        del _pending_modules[name]
        for decorator in pending_decorators:
            decorator.__call__(res)
    else:
        res = _python___import__(name, globls, locls, fromlist, level)
    if sys.version_info.major >= 3:
        if fromlist is None:
            _re_match_module(name, True)
        else:
            for mod_name in fromlist:
                mod_name_full = name+'.'+mod_name
                if mod_name_full in sys.modules:
                    _re_match_module(mod_name_full, True)
    _run_delayed_checks(True, name)
    if pytypes.global_typechecked_decorator or pytypes.global_auto_override_decorator or \
            pytypes.global_annotations_decorator or pytypes.global_typelogged_decorator:
        if fromlist is None:
            if name in sys.modules:
                if pytypes.global_typechecked_decorator:
                    typechecked_module(name)
                if pytypes.global_typelogged_decorator:
                    pytypes.typelogged_module(name)
                if pytypes.global_auto_override_decorator:
                    auto_override_module(name)
                if pytypes.global_annotations_decorator:
                    type_util.annotations_module(name)
        else:
            for mod_name in fromlist:
                mod_name_full = name+'.'+mod_name
                if mod_name_full in sys.modules:
                    if pytypes.global_typechecked_decorator:
                        typechecked_module(mod_name_full, True)
                    if pytypes.global_auto_override_decorator:
                        auto_override_module(mod_name_full, True)
                    if pytypes.global_annotations_decorator:
                        type_util.annotations_module(mod_name_full)
    return res

def _install_import_hook():
    global _import_hook_installed
    if not _import_hook_installed:
        builtins.__import__ = _pytypes___import__
        _import_hook_installed = True

class _DelayedCheck():
    """Delayed checks are needed for definition time typechecks that involve
    forward declarations.
    """
    def __init__(self, func, method, class_name, base_method, base_class, exc_info):
        # lazily install import hook (Todo: Maybe move this to a better place)
        if pytypes.import_hook_enabled:
            _install_import_hook()
        self.func = func
        self.method = method
        self.class_name = class_name
        self.base_method = base_method
        self.base_class = base_class
        self.exc_info = exc_info
        self.raising_module_name = func.__module__

    def run_check(self, raise_NameError = False):
        if raise_NameError:
            meth_types = _funcsigtypes(self.func, True, self.base_class)
            _check_override_types(self.method, meth_types, self.class_name,
                    self.base_method, self.base_class)
        else:
            try:
                meth_types = _funcsigtypes(self.func, True, self.base_class)
                _check_override_types(self.method, meth_types, self.class_name,
                        self.base_method, self.base_class)
            except NameError:
                pass


def _run_delayed_checks(raise_NameError = False, module_name = None):
    global _delayed_checks
    if module_name is None:
        to_run = _delayed_checks
        _delayed_checks = []
    else:
        new_delayed_checks = []
        to_run = []
        for check in _delayed_checks:
            if check.raising_module_name.startswith(module_name):
                to_run.append(check)
            else:
                new_delayed_checks.append(check)
        _delayed_checks = new_delayed_checks
    for check in to_run:
        check.run_check(raise_NameError)

atexit.register(_run_delayed_checks, True)


def _preprocess_override(meth_types, base_types, meth_argspec, base_argspec):
    """This function linearizes type info of ordinary, vararg, kwonly and varkw
    arguments, such that override-feasibility can be conveniently checked. 
    """
    try:
        base_kw = base_argspec.keywords
        kw = meth_argspec.keywords
    except AttributeError:
        base_kw = base_argspec.varkw
        kw = meth_argspec.varkw
    try:
        kwonly = meth_argspec.kwonlyargs
        base_kwonly = base_argspec.kwonlyargs
    except AttributeError:
        kwonly = None
        base_kwonly = None
    if meth_argspec.varargs is None and base_argspec.varargs is None \
            and kw is None and base_kw is None \
            and kwonly is None and base_kwonly is None \
            and (meth_argspec.defaults is None or \
                len(meth_argspec.args) == len(base_argspec.args)):
        return meth_types, base_types
    arg_types = type_util.get_Tuple_params(meth_types[0])
    base_arg_types = type_util.get_Tuple_params(base_types[0])
    kw_off = len(meth_argspec.args)-1 # -1 for self
    if not meth_argspec.defaults is None and base_argspec.varargs is None:
        kw_off -= len(meth_argspec.defaults)
    base_kw_off = len(base_argspec.args)
    if base_argspec.varargs is None:
        base_kw_off -= 1 # one decrement anyway for self
    arg_types2 = list(arg_types[:kw_off])
    base_arg_types2 = list(base_arg_types[:base_kw_off])
    base_vargtype = None
    vargtype = None
    base_argnames = None
    argnames = None
    if not base_argspec.varargs is None or not base_kw is None:
        base_argnames = util.getargnames(base_argspec)[1:]
        if not base_argspec.varargs is None:
            base_vargtype = base_arg_types[base_argnames.index(base_argspec.varargs)]
            # Should have been already checked:
            assert not meth_argspec.varargs is None
    if not meth_argspec.varargs is None or not kw is None:
        argnames = util.getargnames(meth_argspec)[1:]
        if not meth_argspec.varargs is None:
            vargtype = arg_types[argnames.index(meth_argspec.varargs)]
    if not meth_argspec.defaults is None:
        pos = 0
        if not base_argspec.varargs is None:
            # fill up parent's types with varg type to account for child's defaults
            while len(arg_types2) > len(base_arg_types2):
                base_arg_types2.append(base_vargtype)
            base_arg_types2.append(base_vargtype) # restore one more for the actual vargtype
        else:
            # parent has no vargtype, so fill up child with default-types afap
            while len(arg_types2) < len(base_arg_types2) and \
                    pos < len(meth_argspec.defaults):
                arg_types2.append(arg_types[kw_off+pos])
                pos += 1
    while len(arg_types2) < len(base_arg_types2):
        arg_types2.append(vargtype)
    if not kw is None:
        kw_type = arg_types[argnames.index(kw)]
    if not base_kwonly is None:
        for name in base_kwonly:
            base_arg_types2.append(base_arg_types[base_argnames.index(name)])
            if name in argnames:
                arg_types2.append(arg_types[argnames.index(name)])
            else:
                arg_types2.append(kw_type)
    if not base_kw is None:
        base_arg_types2.append(base_arg_types[base_argnames.index(base_kw)])
        arg_types2.append(kw_type)
    return (typing.Tuple[tuple(arg_types2)], meth_types[1]), \
            (typing.Tuple[tuple(base_arg_types2)], base_types[1])


def _check_override_types(method, meth_types, class_name, base_method, base_class):
    # regarding kw:
    # For child to have wider args than parent:
    # if parent allows varkw, child must allow varkw too
    # every kw-only arg of parent must be present in child (as kw-only, ordinary or via var-kw)
    # if child allows varkw, kw-only args of parent are automatically fulfilled
    # type of child-varkw must be wider than of parent-varkw
    # if parent defines kwonly, child's kw-only or ordinary representation of
    # these args must be wider in type
    # if child serves parent's kw-only via varkw, child's varkw type must be
    # wider than any kw-only type of parent
    # (use Any if nothing else fits)
    base_types = _match_stub_type(_funcsigtypes(base_method, True, base_class))
    meth_types = _match_stub_type(meth_types)
    meth_types, base_types = _preprocess_override(meth_types, base_types,
            util.getargspecs(method), util.getargspecs(base_method))
    if has_type_hints(base_method):
        if not _issubclass(base_types[0], meth_types[0]):
            fq_name_child = util._fully_qualified_func_name(method, True, None, class_name)
            fq_name_parent = util._fully_qualified_func_name(base_method, True, base_class)
            #assert fq_name_child == ('%s.%s.%s' % (method.__module__, class_name, method.__name__))
            #assert fq_name_parent == ('%s.%s.%s' % (base_method.__module__, base_class.__name__, base_method.__name__))

            raise OverrideError('\n  %s\ncannot override\n  %s.\n'
                    % (fq_name_child, fq_name_parent)
                    + 'Incompatible arg type  %s\nis not supertype of    %s'
                    % (type_str(meth_types[0]), type_str(base_types[0])))
        if not _issubclass(meth_types[1], base_types[1]):
            fq_name_child = util._fully_qualified_func_name(method, True, None, class_name)
            fq_name_parent = util._fully_qualified_func_name(base_method, True, base_class)
            #assert fq_name_child == ('%s.%s.%s' % (method.__module__, class_name, method.__name__))
            #assert fq_name_parent == ('%s.%s.%s' % (base_method.__module__, base_class.__name__, base_method.__name__))

            raise OverrideError('%s cannot override %s.\n'
                    % (fq_name_child, fq_name_parent)
                    + 'Incompatible result types: %s is not a subtype of %s.'
                    % (type_str(meth_types[1]), type_str(base_types[1])))


def _check_override_argspecs(method, argSpecs, class_name, base_method, base_class):
    ovargs = util.getargspecs(base_method)
    vargs_ok = None
    varkw_ok = None
    if not ovargs.varargs is None:
        vargs_ok = not argSpecs.varargs is None
    elif not argSpecs.varargs is None:
        vargs_ok = True
    try:
        ov_kw = ovargs.keywords
        kw = argSpecs.keywords
    except AttributeError:
        ov_kw = ovargs.varkw
        kw = argSpecs.varkw
    # regarding kw - for child to have wider args than parent:
    # if parent allows varkw, child must allow varkw too
    # every kw-only arg of parent must be present in child (as kw-only, ordinary or via var-kw)
    # if child allows varkw, kw-only args of parent are automatically fulfilled
    try:
        kwonly = argSpecs.kwonlyargs
        ov_kwonly = ovargs.kwonlyargs
    except AttributeError:
        kwonly = None
        ov_kwonly = None
    if not kw is None:
        varkw_ok = True
    elif not ov_kw is None:
        varkw_ok = False
    elif ov_kwonly is None or len(ov_kwonly) == 0:
        varkw_ok = True
    elif not kwonly is None:
        varkw_ok = True
        for kwo in ov_kwonly:
            if not kwo in kwonly and not kwo in argSpecs.args:
                varkw_ok = False
                break
    else:
        varkw_ok = True
        for kwo in ov_kwonly:
            if not kwo in argSpecs.args:
                varkw_ok = False
                break

    if not vargs_ok is None and not vargs_ok:
        fq_name_child = util._fully_qualified_func_name(method, True, None, class_name)
        fq_name_parent = util._fully_qualified_func_name(base_method, True, base_class)
        raise OverrideError('%s\n  cannot override\n%s:\n'
                % (fq_name_child, fq_name_parent)
                + "Child-method does not account for parent's var-length args.")
    elif not varkw_ok:
        fq_name_child = util._fully_qualified_func_name(method, True, None, class_name)
        fq_name_parent = util._fully_qualified_func_name(base_method, True, base_class)
        raise OverrideError('\n%s\n  cannot override\n%s:\n'
                % (fq_name_child, fq_name_parent)
                + "Child-method does not account for parent's keyword(-only) args.")
    if varkw_ok:
        req_kw = util.get_required_kwonly_args(argSpecs)
        ov_req_kw = util.get_required_kwonly_args(ovargs)
        add_req = []
        for kwo in req_kw:
            if not kwo in ov_req_kw:
                add_req.append(kwo)
        if len(add_req) > 0:
            fq_name_child = util._fully_qualified_func_name(method, True, None, class_name)
            fq_name_parent = util._fully_qualified_func_name(base_method, True, base_class)
            raise OverrideError('\n%s\n  cannot override\n%s:\n'
                    % (fq_name_child, fq_name_parent)
                    + "Child-method requires keyword-only arg(s) not required by parent:\n"
                    + str(add_req))

    d1 = 0 if ovargs.defaults is None else len(ovargs.defaults)
    d2 = 0 if argSpecs.defaults is None else len(argSpecs.defaults)
    if (ovargs.varargs is None and len(ovargs.args)-d1 < len(argSpecs.args)-d2) or \
            (argSpecs.varargs is None and len(ovargs.args) > len(argSpecs.args)) or \
            (not vargs_ok is None and not vargs_ok) or not varkw_ok:
        #assert fq_name_child == ('%s.%s.%s' % (method.__module__, class_name, method.__name__))
        #assert fq_name_parent == ('%s.%s.%s' % (base_method.__module__, base_class.__name__, base_method.__name__))
        fq_name_child = util._fully_qualified_func_name(method, True, None, class_name)
        fq_name_parent = util._fully_qualified_func_name(base_method, True, base_class)
        raise OverrideError('%s\n  cannot override\n%s:\n'
                % (fq_name_child, fq_name_parent)
                + 'Mismatching argument count. Base-method: %i+%i   child: %i+%i'
                % (len(ovargs.args)-d1, d1, len(argSpecs.args)-d2, d2))


def _no_base_method_error(method):
    return OverrideError('%s in %s does not override any other method.\n'
            % (method.__name__, method.__module__))


def _function_instead_of_method_error(method):
    return OverrideError('@override was applied to a function, not a method: %s.%s.\n'
            % (method.__module__, method.__name__))


def override(func, auto = False):
    """Decorator applicable to methods only.
    For a version applicable also to classes or modules use auto_override.
    Asserts that for the decorated method a parent method exists in its mro.
    If both the decorated method and its parent method are type annotated,
    the decorator additionally asserts compatibility of the annotated types.
    Note that the return type is checked in contravariant manner.
    A successful check guarantees that the child method can always be used in
    places that support the parent method's signature.
    Use pytypes.check_override_at_runtime and pytypes.check_override_at_class_definition_time
    to control whether checks happen at class definition time or at "actual runtime".
    """
    if not pytypes.checking_enabled:
        return func
    # notes:
    # - don't use @override on __init__ (raise warning? Error for now!),
    #   because __init__ is not intended to be called after creation
    # - @override applies typechecking to every match in mro, because class might be used as
    #   replacement for each class in its mro. So each must be compatible.
    # - @override does not/cannot check signature of builtin ancestors (for now).
    # - @override starts checking only at its declaration level. If in a subclass an @override
    #   annotated method is not s.t. @override any more.
    #   This is difficult to achieve in case of a call to super. Runtime-override checking
    #   would use the subclass-self and thus unintentionally would also check the submethod's
    #   signature. We actively avoid this here.
    func.override_checked = True
    _actualfunc(func).override_checked = True
    if pytypes.check_override_at_class_definition_time:
        # We need some trickery here, because details of the class are not yet available
        # as it is just getting defined. Luckily we can get base-classes via inspect.stack():
        stack = inspect.stack()
        try:
            base_classes = _re.search(r'class.+\((.+)\)\s*\:', stack[2][4][0]).group(1)
        except IndexError:
            raise _function_instead_of_method_error(func)
        except AttributeError:
            base_classes = 'object'
        meth_cls_name = stack[1][3]
        if func.__name__ == '__init__':
            raise OverrideError(
                    'Invalid use of @override in %s:\n  @override must not be applied to __init__.'
                    % util._fully_qualified_func_name(func, True, None, meth_cls_name))
        # handle multiple inheritance
        base_classes = [s.strip() for s in base_classes.split(',')]
        if not base_classes:
            raise ValueError('@override: unable to determine base class') 

        # stack[0]=overrides, stack[1]=inside class def'n, stack[2]=outside class def'n
        derived_class_locals = stack[2][0].f_locals
        derived_class_globals = stack[2][0].f_globals

        # replace each class name in base_classes with the actual class type
        for i, base_class in enumerate(base_classes):
            if '.' not in base_class:
                if base_class in derived_class_locals:
                    base_classes[i] = derived_class_locals[base_class]
                elif base_class in derived_class_globals:
                    base_classes[i] = derived_class_globals[base_class]
                elif base_class in types.__builtins__:
                    base_classes[i] = types.__builtins__[base_class]
                else:
                    raise TypeError("Could not lookup type: "+base_class)
            else:
                components = base_class.split('.')
                # obj is either a module or a class
                if components[0] in derived_class_locals:
                    obj = derived_class_locals[components[0]]
                elif components[0] in derived_class_globals:
                    obj = derived_class_globals[components[0]]
                elif components[0] in types.__builtins__:
                    obj = types.__builtins__[components[0]]
                elif components[0] in sys.modules:
                    obj = sys.modules[components[0]]
                else:
                    raise TypeError("Could not lookup type or module: "+base_class)
                for c in components[1:]:
                    assert(ismodule(obj) or isclass(obj))
                    obj = getattr(obj, c)
                base_classes[i] = obj

        mro_set = set() # contains everything in would-be-mro, however in unspecified order
        mro_pool = [base_classes]
        while len(mro_pool) > 0:
            lst = mro_pool.pop()
            for base_cls in lst:
                if not is_builtin_type(base_cls):
                    mro_set.add(base_cls)
                    mro_pool.append(base_cls.__bases__)

        base_method_exists = False
        argSpecs = util.getargspecs(func)
        for cls in mro_set:
            if hasattr(cls, func.__name__):
                base_method_exists = True
                base_method = getattr(cls, func.__name__)
                _check_override_argspecs(func, argSpecs, meth_cls_name, base_method, cls)
                if has_type_hints(func):
                    try:
                        _check_override_types(func, _funcsigtypes(func, True, cls), meth_cls_name,
                                base_method, cls)
                    except NameError:
                        _delayed_checks.append(_DelayedCheck(func, func, meth_cls_name, base_method,
                                cls, sys.exc_info()))
        if not base_method_exists:
            if not auto:
                raise _no_base_method_error(func)

    if pytypes.check_override_at_runtime:
        specs = util.getargspecs(func)
        argNames = util.getargnames(specs)
        def checker_ov(*args, **kw):
            if hasattr(checker_ov, '__annotations__') and len(checker_ov.__annotations__) > 0:
                checker_ov.ov_func.__annotations__ = checker_ov.__annotations__
            args_kw = util.getargskw(args, kw, specs)
            if len(argNames) > 0 and argNames[0] == 'self':
                if hasattr(args_kw[0].__class__, func.__name__) and \
                        ismethod(getattr(args_kw[0], func.__name__)):
                    actual_class = args_kw[0].__class__
                    if _actualfunc(getattr(args_kw[0], func.__name__)) != func:
                        for acls in util.mro(args_kw[0].__class__):
                            if not is_builtin_type(acls):
                                if hasattr(acls, func.__name__) and func.__name__ in acls.__dict__ and \
                                        _actualfunc(acls.__dict__[func.__name__]) == func:
                                    actual_class = acls
                    if func.__name__ == '__init__':
                        raise OverrideError(
                                'Invalid use of @override in %s:\n    @override must not be applied to __init__.'
                                % util._fully_qualified_func_name(func, True, actual_class))
                    ovmro = []
                    base_method_exists = False
                    for mc in util.mro(actual_class)[1:]:
                        if hasattr(mc, func.__name__):
                            ovf = getattr(mc, func.__name__)
                            base_method_exists = True
                            if not is_builtin_type(mc):
                                ovmro.append(mc)
                    if not base_method_exists:
                        if not auto:
                            raise _no_base_method_error(func)
                        else:
                            return func(*args, **kw)
                    # Not yet support overloading
                    # Check arg-count compatibility
                    for ovcls in ovmro:
                        ovf = getattr(ovcls, func.__name__)
                        _check_override_argspecs(func, specs, actual_class.__name__, ovf, ovcls)
                    # Check arg/res-type compatibility
                    meth_types = _funcsigtypes(func, True, args_kw[0].__class__)
                    if has_type_hints(func):
                        for ovcls in ovmro:
                            ovf = getattr(ovcls, func.__name__)
                            _check_override_types(func, meth_types, actual_class.__name__, ovf, ovcls)
                else:
                    raise OverrideError('@override was applied to a non-method: %s.%s.\n'
                        % (func.__module__, func.__name__)
                        + "that declares 'self' although not a method.")
            else:
                raise _function_instead_of_method_error(func)
            return func(*args, **kw)
    
        checker_ov.ov_func = func
        if hasattr(func, '__func__'):
            checker_ov.__func__ = func.__func__
        checker_ov.__name__ = func.__name__
        checker_ov.__module__ = func.__module__
        checker_ov.__globals__.update(func.__globals__)
        if hasattr(func, '__annotations__'):
            checker_ov.__annotations__ = func.__annotations__
        if hasattr(func, '__qualname__'):
            checker_ov.__qualname__ = func.__qualname__
        checker_ov.__doc__ = func.__doc__
        # Todo: Check what other attributes might be needed (e.g. by debuggers).
        checker_ov._check_parent_types = True
        return checker_ov
    else:
        func._check_parent_types = True
        return func

def _make_type_error_message(tp, func, slf, func_class, expected_tp, \
            incomp_text, prop_getter = False, bound_typevars=None):
    _cmp_msg_format = 'Expected: %s\nReceived: %s'
    if type(func) is property:
        assert slf is True
        if func.fset is None or prop_getter:
            fq_func_name = util._fully_qualified_func_name(func.fget, True, func_class)+'/getter'
        else:
            fq_func_name = util._fully_qualified_func_name(func.fset, True, func_class)+'/setter'
    else:
        fq_func_name = util._fully_qualified_func_name(
                func, slf or util.is_classmethod(func), func_class)
    # Todo: Clarify if an @override-induced check caused this
    # Todo: Python3 misconcepts method as classmethod here, because it doesn't
    # detect it as bound method, because ov_checker or tp_checker obfuscate it
    return '\n  '+fq_func_name+'\n  '+incomp_text+':\n'+_cmp_msg_format % ( \
            type_str(expected_tp, bound_Generic=func_class, bound_typevars=bound_typevars),
            type_str(tp, bound_Generic=func_class, bound_typevars=bound_typevars))


def _checkinstance(obj, cls, bound_Generic, bound_typevars, bound_typevars_readonly,
            follow_fwd_refs, _recursion_check, is_args, func, force = False):
    if is_Tuple(cls):
        prms = pytypes.get_Tuple_params(cls)
        elps = pytypes.is_Tuple_ellipsis(cls)
        try:
            if not elps and len(obj) != len(prms):
                    return False, obj
        except TypeError:
            return False, obj
        lst = []
        if isinstance(obj, tuple):
            for i in range(len(obj)):
                res, obj2 = _checkinstance(obj[i], prms[0 if elps else i], bound_Generic, bound_typevars,
                        bound_typevars_readonly, follow_fwd_refs, _recursion_check,
                        is_args, func)
                if not res:
                    return False, obj
                else:
                    lst.append(obj2)
            return True, tuple(lst)
        else:
            return False, obj
    # This (optionally) turns some types into a checked version, e.g. generators or callables
    if type_util.is_Callable(cls):
        if not type_util._isinstance_Callable(obj, cls, bound_Generic, bound_typevars,
                    bound_typevars_readonly, follow_fwd_refs, _recursion_check, False):
            return False, obj
        if pytypes.check_callables:
            # Todo: Only this part shall reside in _checkInstance
            # Todo: Invent something to avoid stacking of type checkers
            # Note that these might check different type-aspects. With IntersectionTypes one day
            # we can merge them into one checker. Maybe checker should already support this?
            clb_args, clb_res = pytypes.get_Callable_args_res(cls)
            return True, typechecked_func(obj, force, typing.Tuple[clb_args], clb_res)
        return True, obj
    if type_util.is_Generic(cls):
        if cls.__origin__ in (type_util._orig_Iterable, type_util._orig_Iterator):
            if not type_util.is_iterable(obj):
                return False, obj
            itp = type_util.get_iterable_itemtype(obj)
            if itp is None:
                if pytypes.check_iterables:
                    if cls.__origin__ is type_util._orig_Iterator:
                        return True, type_util._typechecked_Iterator(obj, cls, bound_Generic,
                                bound_typevars, bound_typevars_readonly, follow_fwd_refs,
                                _recursion_check, force)
                    else:
                        assert cls.__origin__ is type_util._orig_Iterable
                        return True, type_util._typechecked_Iterable(obj, cls, bound_Generic,
                                bound_typevars, bound_typevars_readonly, follow_fwd_refs,
                                _recursion_check, force)
                else:
                    return _isinstance(obj, cls, bound_Generic, bound_typevars,
                            bound_typevars_readonly, follow_fwd_refs, _recursion_check), obj
# 	There was this idea of monkeypatching, but it doesn't work in Python 3 and is anyway too invasive.
# 					if not hasattr(obj, '__iter__'):
# 						raise TypeError(
# 								'Can only create iterable-checker for objects with __iter__ method.')
# 					else:
# 						__iter__orig = obj.__iter__
# 						def __iter__checked(self):
# 							res = __iter__orig()
# 							if sys.version_info.major == 3:
# 								# Instance-level monkeypatching doesn't seem to work in Python 3
# 								res.__next__ = types.MethodType(typechecked_func(res.__next__.__func__,
# 										force, typing.Tuple[tuple()], cls.__args__[0]), res)
# 							else:
# 								# We're running Python 2
# 								res.next = types.MethodType(typechecked_func(res.next.__func__,
# 										force, typing.Tuple[tuple()], cls.__args__[0]), res)
# 							return res
# 						obj.__iter__ = types.MethodType(__iter__checked, obj)
# 						return True, obj
            else:
                return _issubclass(itp, cls.__args__[0], bound_Generic, bound_typevars,
                        bound_typevars_readonly, follow_fwd_refs, _recursion_check), obj
        elif type_util.is_Generator(cls):
            if is_args or not inspect.isgeneratorfunction(func):
                # Todo: Insert fully qualified function name
                # Todo: Move or port this to _isInstance (?)
                raise pytypes.TypeCheckError(
                        'typing.Generator must only be used as result type of generator functions.')
            if isinstance(obj, types.GeneratorType):
                if pytypes.check_generators:
                    if obj.__name__.startswith('generator_checker_py'):
                        return True, obj
                    if sys.version_info.major == 2:
                        wrgen = type_util.generator_checker_py2(obj, cls,
                                bound_Generic, bound_typevars,
                                bound_typevars_readonly, follow_fwd_refs,
                                _recursion_check)
                    else:
                        wrgen = type_util.generator_checker_py3(obj, cls,
                                bound_Generic, bound_typevars,
                                bound_typevars_readonly, follow_fwd_refs,
                                _recursion_check)
                        try:
                            wrgen.__qualname__ = obj.__qualname__
                        except:
                            pass
                    type_util._checked_generator_types[wrgen] = cls
                    return True, wrgen
                else:
                    return True, obj
            else:
                return False, obj
    return _isinstance(obj, cls, bound_Generic, bound_typevars,
            bound_typevars_readonly, follow_fwd_refs, _recursion_check), obj


def _checkfunctype(argSig, check_val, func, slf, func_class, make_checked_val=False,
            prop_getter=False, argspecs=None, var_type=None, force_exception=False,
            bound_typevars={}, bound_typevars_readonly=False, follow_fwd_refs=True,
            _recursion_check=None):
    if argspecs is None:
        argspecs = getargspecs(_actualfunc(func, prop_getter))
    argSig = _preprocess_typecheck(argSig, argspecs, slf) \
            if var_type is None else var_type
    if make_checked_val:
        result, checked_val = _checkinstance(check_val, argSig,
                func_class, bound_typevars, bound_typevars_readonly, follow_fwd_refs,
                _recursion_check, True, func)
    else:
        result = _isinstance(check_val, argSig, func_class, bound_typevars,
                bound_typevars_readonly, follow_fwd_refs, _recursion_check)
        checked_val = None
    if not result:
        tpch = deep_type(check_val)
        msg = _make_type_error_message(tpch, func, slf, func_class, argSig,
                'called with incompatible types', prop_getter, bound_typevars)
        _raise_typecheck_error(msg, False, check_val, tpch, argSig, func)
        if force_exception:
            raise InputTypeError(msg)
    return checked_val


def _checkfuncresult(resSig, check_val, func, slf, func_class, \
            make_checked_val=False, prop_getter=False, force_exception=False, \
            bound_typevars={}, bound_typevars_readonly=False, follow_fwd_refs=True,
            _recursion_check=None):
    if make_checked_val:
        result, checked_val = _checkinstance(check_val, _match_stub_type(resSig),
                func_class, bound_typevars, bound_typevars_readonly, follow_fwd_refs,
                _recursion_check, False, func)
    else:
        result = _isinstance(check_val, _match_stub_type(resSig),
                func_class, bound_typevars, bound_typevars_readonly, follow_fwd_refs,
                _recursion_check)
        checked_val = None
    if not result:
        # todo: constrain deep_type-depth
        tpch = deep_type(check_val)
        msg = _make_type_error_message(tpch, func, slf, func_class, resSig,
                'returned incompatible type', prop_getter, bound_typevars)
        _raise_typecheck_error(msg, True, check_val, tpch, resSig, func)
        if force_exception:
            raise ReturnTypeError(msg)
    return checked_val


# Todo: Rename to something that better indicates this is also applicable to some descriptors,
#       e.g. to typechecked_member
def typechecked_func(func, force = False, argType = None, resType = None, prop_getter = False):
    """Works like typechecked, but is only applicable to functions, methods and properties.
    """
    if not pytypes.checking_enabled and not pytypes.do_logging_in_typechecked:
        return func
    assert(_check_as_func(func))
    if not force and is_no_type_check(func):
        return func
    if hasattr(func, 'do_typecheck'):
        func.do_typecheck = True
        return func
    elif hasattr(func, 'do_logging'):
        # actually shouldn't happen
        return _typeinspect_func(func, True, func.do_logging, argType, resType, prop_getter)
    else:
        return _typeinspect_func(func, True, False, argType, resType, prop_getter)

def _typeinspect_func(func, do_typecheck, do_logging, \
            argType = None, resType = None, prop_getter = False):
    clsm = isinstance(func, classmethod)
    stat = isinstance(func, staticmethod)
    prop = isinstance(func, property)
    auto_prop_getter = prop and func.fset is None
    func0 = _actualfunc(func, prop_getter)
    specs = getargspecs(func0)
    argNames = util.getargnames(specs)
    if do_logging and pytypes.typelogger_include_typehint and _has_type_hints(func):
        try:
            clss = util.get_class_that_defined_method(func)
            pytypes._register_logged_func(func, True, prop_getter, clss, specs)
        except ValueError:
            pytypes._register_logged_func(func, False, prop_getter, None, specs)
    def checker_tp(*args, **kw):
        if hasattr(checker_tp, '__annotations__') and len(checker_tp.__annotations__) > 0:
            checker_tp.ch_func.__annotations__ = checker_tp.__annotations__
        # check consistency regarding special case with 'self'-keyword
        slf = False
        args_kw = util.getargskw(args, kw, specs)
        # Todo: Use argskw_err for better error msg or to fail early
        # args_kw, argskw_err = util._getargskw(args, kw, specs)

        if len(argNames) > 0:
            if clsm:
                if argNames[0] != 'cls':
                    util._warn_argname('classmethod using non-idiomatic cls argname',
                            func0, slf, clsm)
                check_args = args_kw[1:] # omit self
            elif argNames[0] == 'self':
                if prop or prop_getter or (hasattr(args_kw[0].__class__, func0.__name__) and
                        ismethod(getattr(args_kw[0], func0.__name__))):
                    check_args = args_kw[1:] # omit self
                    slf = True
                else:
                    util._warn_argname('non-method declaring self', func0, slf, clsm)
                    check_args = args_kw
            else:
                if prop or prop_getter:
                    slf = True
                    util._warn_argname('property using non-idiomatic self argname',
                            func0, slf, clsm)
                    check_args = args_kw[1:] # omit self
                else:
                    check_args = args_kw
        else:
            # Todo: Fill in fully qualified names
            if clsm:
                raise TypeError("classmethod without cls-arg: "+str(func))
            elif prop or prop_getter:
                raise TypeError("property without self-arg: "+str(func))
            check_args = args_kw
        
        parent_class = None
        if slf:
            parent_class = get_orig_class(args_kw[0], True)
        elif clsm:
            parent_class = args_kw[0]

        if not do_typecheck:
            if do_logging: # or (do_typecheck and pytypes.do_logging_in_typechecked):
                if clsm or stat:
                    res = func.__func__(*args, **kw)
                elif prop:
                    if prop_getter or func.fset is None:
                        res = func.fget(*args, **kw)
                    else:
                        res = func.fset(*args, **kw)
                else:
                    res = func(*args, **kw)
                pytypes.log_type(check_args, res, func, slf, prop_getter, parent_class, specs)
                return res
            else:
                return func(*args, **kw)
        else:
            if pytypes.always_check_parent_types:
                checkParents = True
            elif hasattr(func, '_check_parent_types'):
                checkParents = func._check_parent_types
            else:
                checkParents = False
            if checkParents:
                if not slf:
                    if not pytypes.always_check_parent_types:
                        raise OverrideError('@override with non-instancemethod not supported: %s.%s.%s.\n'
                                % (func0.__module__, args_kw[0].__class__.__name__, func0.__name__))
                    else:
                        toCheck = func
                else:
                    tfunc, _ = _find_typed_base_method(func, args_kw[0].__class__)
                    toCheck = tfunc if not tfunc is None else func
            else:
                toCheck = func
            if argType is None or resType is None:
                argSig, resSig = _funcsigtypes(toCheck, slf or clsm,
                        parent_class, None, prop_getter or auto_prop_getter)
                if argType is None:
                    argSig = _match_stub_type(argSig)
                else:
                    argSig = argType
                if resType is None:
                    resSig = _match_stub_type(resSig)
                else:
                    resSig = resType
            else:
                argSig, resSig = argType, resType
            make_checked = pytypes.check_callables or \
                    pytypes.check_iterables or pytypes.check_generators
            bound_typevars = {}
            checked_val = _checkfunctype(argSig, check_args,
                    toCheck, slf or clsm, parent_class, make_checked,
                    prop_getter or auto_prop_getter, specs, bound_typevars=bound_typevars)
            if make_checked:
                checked_args, checked_kw = util.fromargskw(checked_val, specs, slf or clsm)
            else:
                checked_args = args
                checked_kw = kw
    
            # perform backend-call:
            if clsm or stat:
                if len(args_kw) != len(checked_val):
                    res = func.__func__(args[0], *checked_args, **checked_kw)
                else:
                    res = func.__func__(*checked_args, **checked_kw)
            elif prop:
                if prop_getter or func.fset is None:
                    res = func.fget(args[0], *checked_args, **checked_kw)
                else:
                    res = func.fset(args[0], *checked_args, **checked_kw)
            else:
                if len(args_kw) != len(checked_val):
                    res = func(args[0], *checked_args, **checked_kw)
                else:
                    res = func(*checked_args, **checked_kw)

            checked_res = _checkfuncresult(resSig, res, toCheck, \
                    slf or clsm, parent_class, True, prop_getter, bound_typevars=bound_typevars)
            if pytypes.do_logging_in_typechecked:
                pytypes.log_type(check_args, res, func, slf, prop_getter, parent_class, specs)
            return checked_res

    checker_tp.ch_func = func
    checker_tp.do_typecheck = do_typecheck
    checker_tp.do_logging = do_logging
    if hasattr(func, '__func__'):
        checker_tp.__func__ = func.__func__
    checker_tp.__name__ = func0.__name__
    checker_tp.__module__ = func0.__module__
    checker_tp.__globals__.update(func0.__globals__)
    if hasattr(func, '__annotations__'):
        checker_tp.__annotations__ = func.__annotations__
    if hasattr(func, '__qualname__'):
        checker_tp.__qualname__ = func.__qualname__
    checker_tp.__doc__ = func.__doc__
    # Todo: Check what other attributes might be needed (e.g. by debuggers).
    if clsm:
        return classmethod(checker_tp)
    elif stat:
        return staticmethod(checker_tp)
    elif prop and not prop_getter:
        if func.fset is None:
            return property(checker_tp, None, func.fdel, func.__doc__)
        else:
            if not hasattr(func.fget, 'ch_func'):
                #todo: What about @no_type_check applied to getter/setter?
                checker_tp_get = _typeinspect_func(func, do_typecheck, do_logging, \
                        argType, resType, True)
                return property(checker_tp_get, checker_tp, func.fdel, func.__doc__)
            return property(func.fget, checker_tp, func.fdel, func.__doc__)
    else:
        return checker_tp


def typechecked_class(cls, force = False, force_recursive = False):
    """Works like typechecked, but is only applicable to classes.
    """
    return _typechecked_class(cls, set(), force, force_recursive)


def _typechecked_class(cls, cache, force = False, force_recursive = False, nesting = None):
    if not pytypes.checking_enabled:
        return cls
    assert(isclass(cls))
    if not force and is_no_type_check(cls):
        return cls
    cache.add(cls)
    # To play it safe we avoid to modify the dict while iterating over it,
    # so we previously cache keys.
    # For this we don't use keys() because of Python 3.
    # Todo: Better use inspect.getmembers here
    nst = [cls] if nesting is None else nesting
    keys = [key for key in cls.__dict__]
    for key in keys:
        memb = cls.__dict__[key]
        if force_recursive or not is_no_type_check(memb):
            if type_util._check_as_func(memb):
                if _has_type_hints(getattr(cls, key), cls, nst) or \
                        hasattr(_actualfunc(memb), 'override_checked'):
                    setattr(cls, key, typechecked_func(memb, force_recursive))
# 				else:
# 					print ("wouldn't check", key, cls, memb, getattr(cls, key))
            elif isclass(memb) and not memb in cache:
                if not nesting is None:
                    nst2 = []
                    nst2.extend(nesting)
                else:
                    nst2 = [cls]
                nst2.append(memb)
                _typechecked_class(memb, cache, force_recursive, force_recursive, nst2)
    return cls

# Todo: Extend tests for this
def typechecked_module(md, force_recursive = False):
    """Works like typechecked, but is only applicable to modules (by explicit call).
    md must be a module or a module name contained in sys.modules.
    """
    if not pytypes.checking_enabled:
        return md
    # Save input to return original string if input was a string.
    md_arg = md
    if isinstance(md, str):
        if md in sys.modules:
            md = sys.modules[md]
            if md is None:
                return md_arg
        elif md in _pending_modules:
            # if import is pending, we just store this call for later
            _pending_modules[md].append(lambda t: typechecked_module(t, True))
            return md_arg
        else:
            raise KeyError('Found no module {!r} to typecheck'.format(md))
    assert(ismodule(md))
    if md.__name__ in _pending_modules:
            # if import is pending, we just store this call for later
            _pending_modules[md.__name__].append(lambda t: typechecked_module(t, True))
            # we already process the module now as far as possible for its internal use
            # todo: Issue warning here that not the whole module might be covered yet
    if md.__name__ in _fully_typechecked_modules and \
            _fully_typechecked_modules[md.__name__] == len(md.__dict__):
        return md_arg
    # To play it safe we avoid to modify the dict while iterating over it,
    # so we previously cache keys.
    # For this we don't use keys() because of Python 3.
    # Todo: Better use inspect.getmembers here
    keys = [key for key in md.__dict__]
    for key in keys:
        memb = md.__dict__[key]
        if force_recursive or not is_no_type_check(memb) and hasattr(memb, '__module__'):
            if _check_as_func(memb) and memb.__module__ == md.__name__ and \
                    has_type_hints(memb):
                setattr(md, key, typechecked_func(memb, force_recursive))
            elif isclass(memb) and memb.__module__ == md.__name__:
                typechecked_class(memb, force_recursive, force_recursive)
    if not md.__name__ in _pending_modules:
        _fully_typechecked_modules[md.__name__] = len(md.__dict__)
    return md_arg


def typechecked(memb):
    """Decorator applicable to functions, methods, properties,
    classes or modules (by explicit call).
    If applied on a module, memb must be a module or a module name contained in sys.modules.
    See pytypes.set_global_typechecked_decorator to apply this on all modules.
    Asserts compatibility of runtime argument and return values of all targeted functions
    and methods w.r.t. PEP 484-style type annotations of these functions and methods.
    """
    if not pytypes.checking_enabled:
        return memb
    if is_no_type_check(memb):
        return memb
    if type_util._check_as_func(memb):
        return typechecked_func(memb)
    if isclass(memb):
        return typechecked_class(memb)
    if ismodule(memb):
        return typechecked_module(memb, True)
    if memb in sys.modules or memb in _pending_modules:
        return typechecked_module(memb, True)
    return memb


def auto_override_class(cls, force = False, force_recursive = False):
    """Works like auto_override, but is only applicable to classes.
    """
    if not pytypes.checking_enabled:
        return cls
    assert(isclass(cls))
    if not force and is_no_type_check(cls):
        return cls
    # To play it safe we avoid to modify the dict while iterating over it,
    # so we previously cache keys.
    # For this we don't use keys() because of Python 3.
    # Todo: Better use inspect.getmembers here
    keys = [key for key in cls.__dict__]
    for key in keys:
        memb = cls.__dict__[key]
        if force_recursive or not is_no_type_check(memb):
            if isfunction(memb) or ismethod(memb) or ismethoddescriptor(memb):
                if util._has_base_method(memb, cls):
                    setattr(cls, key, override(memb))
            elif isclass(memb):
                auto_override_class(memb, force_recursive, force_recursive)
    return cls


def auto_override_module(md, force_recursive = False):
    """Works like auto_override, but is only applicable to modules (by explicit call).
    md must be a module or a module name contained in sys.modules.
    """
    if not pytypes.checking_enabled:
        return md
    if isinstance(md, str):
        if md in sys.modules:
            md = sys.modules[md]
            if md is None:
                return md
        elif md in _pending_modules:
            # if import is pending, we just store this call for later
            _pending_modules[md].append(lambda t: auto_override_module(t, True))
            return md
    assert(ismodule(md))
    if md.__name__ in _pending_modules:
            # if import is pending, we just store this call for later
            _pending_modules[md.__name__].append(lambda t: auto_override_module(t, True))
            # we already process the module now as far as possible for its internal use
            # todo: Issue warning here that not the whole module might be covered yet
    if md.__name__ in _auto_override_modules and \
            _auto_override_modules[md.__name__] == len(md.__dict__):
        return md
    # To play it safe we avoid to modify the dict while iterating over it,
    # so we previously cache keys.
    # For this we don't use keys() because of Python 3.
    # Todo: Better use inspect.getmembers here
    keys = [key for key in md.__dict__]
    for key in keys:
        memb = md.__dict__[key]
        if force_recursive or not is_no_type_check(memb):
            if isclass(memb) and memb.__module__ == md.__name__:
                auto_override_class(memb, force_recursive, force_recursive)
    if not md.__name__ in _pending_modules:
        _auto_override_modules[md.__name__] = len(md.__dict__)
    return md


def auto_override(memb):
    """Decorator applicable to methods, classes or modules (by explicit call).
    If applied on a module, memb must be a module or a module name contained in sys.modules.
    See pytypes.set_global_auto_override_decorator to apply this on all modules.
    Works like override decorator on type annotated methods that actually have a type
    annotated parent method. Has no effect on methods that do not override anything.
    In contrast to plain override decorator, auto_override can be applied easily on
    every method in a class or module.
    In contrast to explicit override decorator, auto_override is not suitable to detect
    typos in spelling of a child method's name. It is only useful to assert compatibility
    of type information (note that return type is contravariant).
    Use pytypes.check_override_at_runtime and pytypes.check_override_at_class_definition_time
    to control whether checks happen at class definition time or at "actual runtime".
    """
    if type_util._check_as_func(memb):
        return override(memb, True)
    if isclass(memb):
        return auto_override_class(memb)
    if ismodule(memb):
        return auto_override_module(memb, True)
    if memb in sys.modules or memb in _pending_modules:
        return auto_override_module(memb, True)
    return memb


def _catch_up_global_typechecked_decorator():
    mod_names = None
    while mod_names is None:
        try:
            mod_names = [mn for mn in sys.modules]
        except RuntimeError: # dictionary changed size during iteration
            pass
        
    for mod_name in mod_names:
        if not mod_name in _fully_typechecked_modules:
            try:
                md = sys.modules[mod_name]
            except KeyError:
                md = None
            if not md is None and ismodule(md):
                typechecked_module(mod_name)


def _catch_up_global_auto_override_decorator():
    for mod_name in sys.modules:
        if not mod_name in _auto_override_modules:
            try:
                md = sys.modules[mod_name]
            except KeyError:
                md = None
            if not md is None and ismodule(md):
                auto_override_module(mod_name)


def no_type_check(memb):
    """Works like typing.no_type_check, but also supports cases where
    typing.no_type_check fails due to AttributeError. This can happen,
    because typing.no_type_check wants to access __no_type_check__, which
    might fail if e.g. a class is using slots or an object doesn't support
    custom attributes.
    """
    try:
        return typing.no_type_check(memb)
    except(AttributeError):
        _not_type_checked.add(memb)
        return memb


def is_no_type_check(memb):
    """Checks if an object was annotated with @no_type_check
    (from typing or pytypes.typechecker).
    """
    try:
        return hasattr(memb, '__no_type_check__') and memb.__no_type_check__ or \
                memb in _not_type_checked
    except TypeError:
        return False


def check_argument_types(cllable = None, call_args = None, clss = None, caller_level = 0):
    """Can be called from within a function or method to apply typechecking to
    the arguments that were passed in by the caller. Checking is applied w.r.t.
    type hints of the function or method hosting the call to check_argument_types.
    """
    return _check_caller_type(False, cllable, call_args, clss, caller_level+1)


def check_return_type(value, cllable = None, clss = None, caller_level = 0):
    """Can be called from within a function or method to apply typechecking to
    the value that is going to be returned. Checking is applied w.r.t.
    type hints of the function or method hosting the call to check_return_type.
    """
    return _check_caller_type(True, cllable, value, clss, caller_level+1)


class TypeChecker(TypeAgent):

    def __init__(self, all_threads = True):
        TypeAgent.__init__(self, all_threads)
        self._checking_enabled = True
