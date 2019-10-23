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

# Created on 12.12.2016

"""
pytypes main package.

This file provides some behavioral flags and options you can modify to
control various aspects of pytypes.


Attributes
----------

version : str
    Version of this pytypes distribution as a string.

checking_enabled : bool
    Flag to enable or disable runtime typechecking.
    Default: True, unless -o is set.
    Note that you cannot change this flag later on. You must specify
    this right after first import of pytypes, because typecheck decorators
    are applied on function definition time and install wrapper functions.

typelogging_enabled : bool
    Flag to enable or disable typelogging.
    Default: True
    Note that you cannot change this flag later on. You must specify
    this right after first import of pytypes, because typelogging decorators
    are applied on function definition time and install wrapper functions.

do_logging_in_typechecked : bool
    Let the typechecked-decorator also perform typelogging.
    Default: False
    In contrast to checking_enabled and typelogging_enabled, this can be
    switched on and off at any time.

global_typechecked_decorator : bool
    Flag indicating global typechecking mode via decorators.
    Default: False
    Every function or method with type annotation is typechecked now.
    Will affect all functions and methods imported after this flag
    was set. Use enable_global_typechecked_decorator for a retrospective option.
    Does not work if checking_enabled is false.
    Does not work reliably if checking_enabled has ever been set to
    false during current run.

global_auto_override_decorator : bool
    Flag indicating global auto_override mode via decorators.
    Default: False
    Every method with type annotation that also has a parent method
    with type annotation is now checked for type consistency with its
    parent.
    Will affect all functions and methods imported after this flag
    was set. Use enable_global_auto_override_decorator for a retrospective option.

global_annotations_decorator : bool
    Flag indicating global annotation mode via decorators.
    Default: False
    Methods with typestring will have type hints parsed from that
    string and get them attached as __annotations__ attribute.
    Methods with either a typestring or ordinary type annotations in
    a stubfile will get that information attached as __annotations__
    attribute. Behavior in case of collision with previously (manually)
    attached __annotations__ can be controlled using the flags
    annotations_override_typestring and annotations_from_typestring.
    Will affect all methods imported after this flag
    was set. Use enable_global_annotations_decorator for a retrospective option.

global_typelogged_decorator : bool
    Flag indicating global typelog mode via decorators.
    Default: False
    Every function and method call is recorded. The observed type
    information can be written into stubfiles by calling dump_cache.
    Will affect all methods imported after this flag
    was set. Use enable_global_typelogged_decorator for a retrospective option.

global_typechecked_profiler : bool
    Flag indicating global typechecking mode via profiler.
    Default: False
    Read-only flag. Use enable_global_typechecked_profiler to change it.

global_typelogged_profiler : bool
    Flag indicating global typelog mode via profiler.
    Default: False
    Read-only flag. Use enable_global_typelogged_profiler to change it.

warning_mode : bool
    Flag indicating that typecheck errors shall be raised as warnings.
    Default: False

warn_argnames : bool
    Flag indicating that warnings for non-idiomatic names of first
    argument of methods and classmethods shall be raised.
    Idiomatic names would be 'self' and 'cls' respectively.
    Default: True

check_override_at_runtime : bool
    Flag indicating override consistency is checked at runtime.
    Default: False

check_override_at_class_definition_time : bool
    Flag indicating override consistency is checked at class definition time.
    Default: True

always_check_parent_types : bool
    Lets typechecked decorator also apply check like done in auto_override.
    Default: True
    If true, typechecked decorator always checks type consistency with
    type-annotated parent methods if any exist.

check_callables : bool
    Turns callables into typechecked wrappers.
    Default: True
    If true, callables that pass a typecheck decorator are passed on wrapped
    into another typechecker that checks calls according to type info from a
    Callable type object. Will only be applied if such type information exists.

check_iterables : bool
    Turns iterables into typechecked wrappers.
    Default: True
    If true, iterables that pass a typecheck decorator are passed on wrapped
    into another typechecker that checks elements returned by iterators according
    to type info from an Iterable type object.
    Will only be applied if such type information exists.

check_generators : bool
    Turns generators into typechecked wrappers.
    Default: True
    If true, generators that pass a typecheck decorator are passed on wrapped
    into another typechecker that checks elements returned by yield, etc. according
    to type info from an Generator type object.
    Will only be applied if such type information exists.

check_unbound_types : bool
    If true, treat missing parameters as unknown.
    Default: True
    Tells pytypes to actually attempt typechecking of unbound types, e.g
    things like is_subtype(List[Any], list).
    If false such checks are prohibited.
    If true, missing parameters are treated as unknown, which in turn is
    treated according to strict_unknown_check flag.

strict_unknown_check : bool
    Controls the meaning of unknown parameters.
    Default: False
    If false, treat unknown parameters somewhat like Any.
    If true (i.e. strict mode), treat unknown parameters
    somewhat like 'nothing', because no assumptions can be made.

apply_numeric_tower : bool
    Lets pytypes treat int as subtype of float as subtype of complex
    Default: True
    If true, numeric tower like described in
    https://www.python.org/dev/peps/pep-0484/#the-numeric-tower
    is applied to runtime typechecking and typelogging.

covariant_Mapping : bool
    For runtime checking, treat Mapping-types as covariant.
    Default: True
    For runtime checking it is usually okay to treat Mapping-types as covariant,
    given that a Mapping here wouldn't accept every value of proper type anyway.
    (Unlike a mathematical mapping that accepts all values from a certain set.)
    Note that we cannot treat the key type as contravariant as one might expect,
    because in Python Mappings are Iterables over the key type.

infer_default_value_types : bool
    Lets pytypes take type information from default values into account.
    Default: True
    If true, lets pytypes apply deep_type on default values of functions and
    methods. Will only be applied to parameters without type annotation.
    The default values are obtained via inspect.getargspec (Python 2.7) or
    inspect.getfullargspec (Python 3.x).

annotations_override_typestring : bool
    A manually inserted __annotations__ will override a typestring.
    Default: False

annotations_from_typestring : bool
    Lets typechecked decorator work like annotations decorator.
    Default: False
    If true, typechecked decorator will automatically attach parsed
    typestrings as __annotations__ to the according function or method.
    Won't be applied if annotations_override_typestring is true.

strict_annotation_collision_check : bool
    Prohibits to have __annotations__ and typestring at the same time.
    Default: False
    According to
    https://www.python.org/dev/peps/pep-0484/#suggested-syntax-for-python-2-7-and-straddling-code
    __annotations__ and typestring must not be present for the same
    function or method at the same time. By default pytypes does not
    enforce this rule, but instead asserts equivalence of such concurring
    type hints.
    If this flag is true, pytypes will prohibit multiple type hints.

tp_comment_parser_import_typing : bool
    Lets type comment parser implicitly import typing on parsing.
    Default: True
    With this flag enabled it is not necessary for modules with type comments
    to import the typing module. For usual production mode with typechecking
    disabled, the typing module would be an unnecessary and undesired import.

default_typecheck_depth : int
    Specifies maximal recursion depth of deep_type.
    Default: 10
    Default maximal recursion depth for inferring a structured type of
    a given object.

deep_type_samplesize : int
    The number of elements pytypes considers when it determines the element
    type of a list, set or dict.
    Default: -1
    When it builds a List, Set or Dict type from a given list, set or dict,
    pytypes considers all elements within by default to determine the element
    type. For larger data amounts one might want to base this procedure on a
    smaller, somewhat randomly drawn set of elements.
    -1 lets pytypes always evaluate the whole list, set or dict, while other
    positive values let it only check a somewhat random sample of that size.

canonical_type_str : bool
    Forces type_util.type_str to sort parameters of Unions.
    Default: True
    While the order of type parameters of a Union is arbitrary, it might be
    desirable to obtain a canonical type string that properly reflects equality
    of the same Union with different parameter order. This is achieved by sorting
    the string representations of the parameters.
    Set this flag to False, if a representation of the internal type structure is
    desired.
    Note that this flag not only affects string representations of Unions, but of
    every type that contains a Union directly or indirectly as a parameter.

dump_typelog_at_exit : bool
    Lets typelogger dump typelog at exit.
    Default: True

dump_typelog_at_exit_python2 : bool
    Lets typelogger dump Python 2 style typelog at exit.
    If used in combination with dump_typelog_at_exit, two logs are dumped -
    one in Python 2 style, one in Python 3 style.
    Default: False

clean_traceback : bool
    If true, hides pytypes' internal part of exception traceback output.
    Default: True
    Use this variable only for reading. Use enable_clean_traceback function to
    modify it. Disable clean_traceback, if you want to trace a bug in pytypes.

import_hook_enabled : bool
    Required for some edgy situations with stubfiles and forward declarations.
    Default: True
    This lets pytypes hook into import.
    In case this is not desired, use this flag to disable it.
    Setting this flag only has effect right after first import of pytypes.
    Note that with this flag disabled, global decorator mode won't work.

python3_5_executable : str
    Python command used to parse Python 3.5 style stubfiles.
    Default: 'python3'
    Must be >= 3.5.0.
    pytypes comes with the stubfile converter stub_2_convert that creates
    Python 2.7 compliant stubfiles. The converter itself requires Python 3.5
    to run. On Python 2.7 pytype can use this command to convert Python 3.5
    stubfiles to Python 2.7, so they can be used in current execution then.

stub_path : List[str]
    Search-path for stubfiles.
    Default: []
    Additionally to this list of paths, pytypes will look for stubfiles on
    the pythonpath.

stub_gen_dir : Optional[str]
    Directory to collect generated stubs.
    Default: None
    When pytypes uses stub_2_convert, the output files will land in this folder.
    If None, tempfile.gettempdir() is used.

default_indent : str
    Indentation used by typelogger when generating stubfiles.
    Default: '\t'

default_typelogger_path : str
    Directory where typelogger places generated stubs.
    Default: 'typelogger_output'
"""

_version = '>=1.0b5' # Only used as fallback for jython-standalone.jar
# Needs to be imported before touching the Python import machinery
try:
    import pkg_resources
except ImportError:
    pass

try:
    from backports import typing
except ImportError:
    import typing

typing_3_7 = False
try:
    from typing import ForwardRef
    typing_3_7 = True
except: pass

from .typechecker import _install_import_hook

checking_enabled = False # Will be enabled by default, unless -o is set
# Note that you cannot change this flag later on. You must specify
# this right after first import of pytypes.

typelogging_enabled = True
# Note that you cannot change this flag later on. You must specify
# this right after first import of pytypes.

do_logging_in_typechecked = False # Let the typechecked-decorator also perform logging
typelogger_include_typehint = True # Let typelogger also include info from existing typehint

global_typechecked_decorator = False
global_auto_override_decorator = False
global_annotations_decorator = False
global_typelogged_decorator = False

global_typechecked_profiler = False
global_typelogged_profiler = False

_global_type_agent = None

# Some behavior flags:

warning_mode = False
warn_argnames = True

check_override_at_runtime = False
check_override_at_class_definition_time = True
always_check_parent_types = True

check_callables = True
check_iterables = True
check_generators = True

check_unbound_types = True # if true, treat missing parameters as unknown
strict_unknown_check = False # if false, treat unknown parameters somewhat like Any
apply_numeric_tower = True # i.e. int is subtype of float is subtype of complex

# For runtime checking it is usually okay to treat Mapping-types as covariant,
# given that a Mapping here wouldn't accept every value of proper type anyway.
# (Unlike a mathematical mapping that accepts all values from a certain set.)
# Note that we cannot treat the key type as contravariant as one might expect,
# because in Python Mappings are Iterables over the Key-type.
covariant_Mapping = True

infer_default_value_types = True
annotations_override_typestring = False
annotations_from_typestring = False
strict_annotation_collision_check = False

tp_comment_parser_import_typing = True

default_typecheck_depth = 10
# -1 lets pytypes always evaluate the whole list, set or dict
deep_type_samplesize = -1

canonical_type_str = True

dump_typelog_at_exit = True
dump_typelog_at_exit_python2 = False

clean_traceback = True

import_hook_enabled = True

python3_5_executable = 'python3' # Must be >= 3.5.0


def enable_checking(flag = True):
    """Convenience function to set the checking_enabled flag. Intended
    for use in an assert statement, so the call depends on -o flag.
    """
    global checking_enabled
    checking_enabled = flag
    return checking_enabled


def enable_global_typechecked_decorator(flag = True, retrospective = True):
    """Enables or disables global typechecking mode via decorators.
    See flag global_typechecked_decorator.
    In contrast to setting the flag directly, this function provides
    a retrospective option. If retrospective is true, this will also
    affect already imported modules, not only future imports.
    Does not work if checking_enabled is false.
    Does not work reliably if checking_enabled has ever been set to
    false during current run.
    """
    global global_typechecked_decorator
    global_typechecked_decorator = flag
    if import_hook_enabled:
        _install_import_hook()
    if global_typechecked_decorator and retrospective:
        _catch_up_global_typechecked_decorator()
    return global_typechecked_decorator


def enable_global_auto_override_decorator(flag = True, retrospective = True):
    """Enables or disables global auto_override mode via decorators.
    See flag global_auto_override_decorator.
    In contrast to setting the flag directly, this function provides
    a retrospective option. If retrospective is true, this will also
    affect already imported modules, not only future imports.
    """
    global global_auto_override_decorator
    global_auto_override_decorator = flag
    if import_hook_enabled:
        _install_import_hook()
    if global_auto_override_decorator and retrospective:
        _catch_up_global_auto_override_decorator()
    return global_auto_override_decorator


def enable_global_annotations_decorator(flag = True, retrospective = True):
    """Enables or disables global annotation mode via decorators.
    See flag global_annotations_decorator.
    In contrast to setting the flag directly, this function provides
    a retrospective option. If retrospective is true, this will also
    affect already imported modules, not only future imports.
    """
    global global_annotations_decorator
    global_annotations_decorator = flag
    if import_hook_enabled:
        _install_import_hook()
    if global_annotations_decorator and retrospective:
        _catch_up_global_annotations_decorator()
    return global_annotations_decorator


def enable_global_typelogged_decorator(flag = True, retrospective = True):
    """Enables or disables global typelog mode via decorators.
    See flag global_typelogged_decorator.
    In contrast to setting the flag directly, this function provides
    a retrospective option. If retrospective is true, this will also
    affect already imported modules, not only future imports.
    """
    global global_typelogged_decorator
    global_typelogged_decorator = flag
    if import_hook_enabled:
        _install_import_hook()
    if global_typelogged_decorator and retrospective:
        _catch_up_global_typelogged_decorator()
    return global_typelogged_decorator


def enable_global_typechecked_profiler(flag = True):
    """Enables or disables global typechecking mode via a profiler.
    See flag global_typechecked_profiler.
    Does not work if checking_enabled is false.
    """
    global global_typechecked_profiler, _global_type_agent, global_typelogged_profiler
    global_typechecked_profiler = flag
    if flag and checking_enabled:
        if _global_type_agent is None:
            _global_type_agent = TypeAgent()
            _global_type_agent.start()
        elif not _global_type_agent.active:
            _global_type_agent.start()
    elif not flag and not global_typelogged_profiler and \
            not _global_type_agent is None and _global_type_agent.active:
        _global_type_agent.stop()


def enable_global_typelogged_profiler(flag = True):
    """Enables or disables global typelogging mode via a profiler.
    See flag global_typelogged_profiler.
    Does not work if typelogging_enabled is false.
    """
    global global_typelogged_profiler, _global_type_agent, global_typechecked_profiler
    global_typelogged_profiler = flag
    if flag and typelogging_enabled:
        if _global_type_agent is None:
            _global_type_agent = TypeAgent()
            _global_type_agent.start()
        elif not _global_type_agent.active:
            _global_type_agent.start()
    elif not flag and not global_typechecked_profiler and \
            not _global_type_agent is None and _global_type_agent.active:
        _global_type_agent.stop()


def enable_clean_traceback(flag = True):
    """Activates traceback cleaning. This means that traceback of uncaught
    TypeErrors does not include pytypes' internal calls for typechecking etc,
    but instead focuses on the location of an ill-typed call itself.
    """
    global clean_traceback
    clean_traceback = flag
    if clean_traceback:
        _install_excepthook()

# This way we glue typechecking to activeness of the assert statement by default,
# no matter what conditions it depends on (or will depend on, e.g. currently -O flag).
assert(enable_checking())


def _detect_issue351():
    """Detect if github.com/python/typing/issues/351 applies
    to the installed typing-version.
    """
    class Tuple(typing.Generic[typing.T]):
        pass

    res = Tuple[str] == typing.Tuple[str]
    del Tuple
    return res


if _detect_issue351():
    # monkeypatch the issue away...
    _GenericMeta__new__ = typing.GenericMeta.__new__
    def _GenericMeta__new__351(cls, *args, **kwds):
        origin = None
        if len(args) >= 6:
            # origin is at index 5 in original signature:
            # name, bases, namespace, tvars=None, args=None, origin=None, extra=None, orig_bases=None
            origin = args[5]
        elif 'origin' in kwds:
            origin = kwds['origin']
        res = _GenericMeta__new__(cls, *args, **kwds)
        # we correct the hash according to the fix in https://github.com/python/typing/pull/371
        res.__tree_hash__ = (hash(res._subs_tree()) if origin else
                super(typing.GenericMeta, res).__hash__())
        return res
    typing.GenericMeta.__new__ = staticmethod(_GenericMeta__new__351)

# Search-path for stubfiles.
stub_path = []

# Directory to collect generated stubs. If None, tempfile.gettempdir() is used.
stub_gen_dir = None

# Used if get_indentation doesn't yield a result.
default_indent = '\t'
default_typelogger_path = 'typelogger_output'

# typelogger uses this to indent typestrings in output files.
# Uses get_indentation if None.
# typelogger_indent = None # currently uses default_indent always

# Monkeypatch Generic to circumvent type erasure:
# (Only applies to legacy versions of typing.
#  Existence of '_generic_new' is suitable to detect whether this
#  monkeypatch is required, i.e. in typing-3.5.2.2.)
if not hasattr(typing, '_generic_new') and not typing_3_7:

# This former approach has issues if self.__orig_class__ is needed in __init__:
# 	_Generic__new__ = typing.Generic.__new__
# 	def __Generic__new__(cls, *args, **kwds):
# 		res = _Generic__new__(cls, *args, **kwds)
# 		res.__orig_class__ = cls
# 		return res

    def __Generic__new__(cls, *args, **kwds):
        # this is based on Generic.__new__ from typing-3.5.2.2
        if cls.__origin__ is None:
            obj = cls.__next_in_mro__.__new__(cls)
            obj.__orig_class__ = cls
        else:
            origin = typing._gorg(cls)
            obj = cls.__next_in_mro__.__new__(origin)
            obj.__orig_class__ = cls
            obj.__init__(*args, **kwds)
        return obj
    typing.Generic.__new__ = __Generic__new__


# We import some public API for central access:
from .exceptions import TypeCheckError, InputTypeError, ReturnTypeError, TypeWarning, \
    InputTypeWarning, ReturnTypeWarning, OverrideError, TypeSyntaxError, ForwardRefError
from .type_util import deep_type, is_builtin_type, has_type_hints, resolve_fw_decl, \
    type_str, get_types, get_type_hints, is_iterable, get_iterable_itemtype, get_generator_type, \
    get_generator_yield_type, is_Union, get_Union_params, get_Tuple_params, is_Tuple_ellipsis, \
    get_Callable_args_res, get_Generic_itemtype, get_Mapping_key_value, get_Generic_parameters,\
    get_arg_for_TypeVar, _issubclass as is_subtype, _isinstance as is_of_type, annotations, \
    get_member_types, Empty, _catch_up_global_annotations_decorator, TypeAgent, restore_profiler, \
    is_Tuple, is_Generic, is_Callable, _extra_dict as abc2typing_dict, _bases as type_bases, \
    get_Generic_type, get_orig_class
from .util import getargspecs, get_staticmethod_qualname, get_class_qualname, mro, \
    get_class_that_defined_method, is_method, is_classmethod, _pytypes_excepthook, \
    _install_excepthook
from .stubfile_manager import get_stub_module, as_stub_func_if_any
from .typechecker import typechecked, typechecked_module, no_type_check, \
    is_no_type_check, override, check_argument_types, auto_override, \
    _catch_up_global_auto_override_decorator, _catch_up_global_typechecked_decorator, \
    TypeChecker, _checkfunctype, _checkfuncresult
from .typelogger import dump_cache, log_type, typelogged, typelogged_module, \
    _catch_up_global_typelogged_decorator, _register_logged_func, TypeLogger

enable_clean_traceback()

# Some exemplary overrides for this modules's global settings:

# Set custom Python3-executable like this:
#pytypes.python3_5_executable = '/data/workspace/linux/Python-3.5.2/python'

# Set custom directory to store generated stubfiles like this:
# Unlike in tmp directory mode, these are kept over distinct runs.
#stub_gen_dir = '../py2_stubs'
