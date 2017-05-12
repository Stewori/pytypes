'''
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

global_checking : bool
	Flag indicating global typechecking mode.
	Default: False
	Every function or method with type annotation is typechecked now.
	Will affect all functions and methods imported after this flag
	was set. Use set_global_checking for a retrospective option.
	Does not work if checking_enabled is false.
	Does not work reliably if checking_enabled has ever been set to
	false during current run.

global_auto_override : bool
	Flag indicating global auto_override mode.
	Default: False
	Every method with type annotation that also has a parent method
	with type annotation is now checked for type consistency with its
	parent.
	Will affect all functions and methods imported after this flag
	was set. Use set_global_auto_override for a retrospective option.

global_annotations : bool
	Flag indicating global annotation mode.
	Default: False
	Methods with typestring will have type hints parsed from that
	string and get them attached as __annotations__ attribute.
	Methods with either a typestring or ordinary type annotations in
	a stubfile will get that information attached as __annotations__
	attribute. Behavior in case of collision with previously (manually)
	attached __annotations__ can be controlled using the flags
	annotations_override_typestring  and annotations_from_typestring.
	Will affect all methods imported after this flag
	was set. Use set_global_annotations for a retrospective option.

global_typelog : bool
	Flag indicating global typelog mode.
	Default: False
	Every function and method call is recorded. The observed type
	information can be written into stubfiles by calling dump_cache.
	Will affect all methods imported after this flag
	was set. Use set_global_typelog for a retrospective option.

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

clean_traceback : bool
	If true, hides pytypes' internal part of exception traceback output.
	Default: True
	Turn this off if you want to trace a bug in pytypes.

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


Created on 12.12.2016

@author: Stefan Richthofer
'''

import typing, sys

version = '1.0a1'

checking_enabled = False # Will be enabled by default, unless -o is set
# Note that you cannot change this flag later on. You must specify
# this right after first import of pytypes.

typelogging_enabled = True
# Note that you cannot change this flag later on. You must specify
# this right after first import of pytypes.

do_logging_in_typechecked = False # Let the typechecked-decorator also perform logging

global_checking = False
global_auto_override = False
global_annotations = False
global_typelog = False

# Some behavior flags:

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

default_typecheck_depth = 10
# -1 lets pytypes always evaluate the whole list, set or dict
deep_type_samplesize = -1

clean_traceback = True

python3_5_executable = 'python3' # Must be >= 3.5.0

def set_checking_enabled(flag = True):
	global checking_enabled
	checking_enabled = flag
	return checking_enabled

def set_global_checking(flag = True, retrospective = True):
	global global_checking
	global_checking = flag
	if global_checking and retrospective:
		_catch_up_global_checking()
	return global_checking

def set_global_auto_override(flag = True, retrospective = True):
	global global_auto_override
	global_auto_override = flag
	if global_auto_override and retrospective:
		_catch_up_global_auto_override()
	return global_auto_override

def set_global_annotations(flag = True, retrospective = True):
	global global_annotations
	global_annotations = flag
	if global_checking and retrospective:
		_catch_up_global_annotations()
	return global_annotations

def set_global_typelog(flag = True, retrospective = True):
	global global_typelog
	global_typelog = flag
	if global_typelog and retrospective:
		_catch_up_global_typelog()
	return global_typelog

def set_clean_traceback(flag = True):
	'''Activates traceback cleaning. This means that traceback of uncaught
	TypeErrors does not include pytypes' internal calls for typechecking etc,
	but instead focuses on the location of an ill-typed call itself.
	'''
	global clean_traceback
	clean_traceback = flag
	if clean_traceback:
		sys.excepthook = _pytypes_excepthook

# This way we glue typechecking to activeness of the assert statement by default,
# no matter what conditions it depends on (or will depend on, e.g. currently -O flag).
assert(set_checking_enabled())

def _detect_issue351():
	'''Detect if github.com/python/typing/issues/351 applies
	to the installed typing-version.
	'''
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
if not hasattr(typing, '_generic_new'):
	_Generic__new__ = typing.Generic.__new__
	def __Generic__new__(cls, *args, **kwds):
		res = _Generic__new__(cls, *args, **kwds)
		res.__orig_class__ = cls
		return res
	typing.Generic.__new__ = __Generic__new__

class TypeCheckError(TypeError): pass
class InputTypeError(TypeCheckError): pass
class ReturnTypeError(TypeCheckError): pass
class OverrideError(TypeError): pass
class TypeSyntaxError(TypeError): pass

# We import some public API for central access:
from .type_util import deep_type, is_builtin_type, has_type_hints, \
		type_str, get_types, get_type_hints, is_iterable, get_iterable_itemtype, \
		get_generator_type, get_generator_yield_type, \
		is_Union, get_Union_params, get_Tuple_params, \
		get_Callable_args_res, _issubclass as is_subtype, _isinstance as is_of_type, \
		annotations, get_member_types, Empty, _catch_up_global_annotations
from .util import getargspecs, get_staticmethod_qualname, get_class_qualname, mro, \
		get_class_that_defined_method, is_method, is_classmethod, _pytypes_excepthook
from .stubfile_manager import get_stub_module, as_stub_func_if_any
from .typechecker import typechecked, typechecked_module, no_type_check, \
		is_no_type_check, override, check_argument_types, _catch_up_global_checking, \
		_catch_up_global_auto_override, auto_override
from .typelogger import dump_cache, log_type, typelogged, _catch_up_global_typelog

set_clean_traceback()

# Some exemplary overrides for this modules's global settings:

# Set custom Python3-executable like this:
#pytypes.python3_5_executable = '/data/workspace/linux/Python-3.5.2/python'

# Set custom directory to store generated stubfiles like this:
# Unlike in tmp directory mode, these are kept over distinct runs.
#stub_gen_dir = '../py2_stubs'
