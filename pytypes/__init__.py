'''
Created on 12.12.2016

@author: Stefan Richthofer
'''

import typing, sys

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
		make_Tuple, make_Union, annotations, get_member_types, Empty, \
		_catch_up_global_annotations
from .util import getargspecs, get_staticmethod_qualname, get_class_qualname, mro, \
		get_class_that_defined_method, is_method, is_classmethod, _pytypes_excepthook
from .stubfile_manager import get_stub_module, as_stub_func_if_any
from .typechecker import typechecked, typechecked_module, no_type_check, \
		is_no_type_check, override, check_argument_types, _catch_up_global_checking, \
		_catch_up_global_auto_override, _catch_up_global_typelog, auto_override, \
		typelogged

set_clean_traceback()

# Some exemplary overrides for this modules's global settings:

# Set custom Python3-executable like this:
#pytypes.python3_5_executable = '/data/workspace/linux/Python-3.5.2/python'

# Set custom directory to store generated stubfiles like this:
# Unlike in tmp directory mode, these are kept over distinct runs.
#stub_gen_dir = '../py2_stubs'
