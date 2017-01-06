'''
Created on 12.12.2016

@author: Stefan Richthofer
'''

from typing import Generic

checking_enabled = False
def set_checking_enabled(flag = True):
	global checking_enabled
	checking_enabled = flag
	return checking_enabled

# This way we glue typechecking to activeness of the assert-statement by default,
# no matter what conditions it depends on (or will depend on, e.g. currently -O flag).
assert(set_checking_enabled())

check_override_at_runtime = False
check_override_at_class_definition_time = True

check_callables = True
check_iterables = True
check_generators = True

# For runtime-checking it is usually okay to treat Mapping-types as covariant,
# given that a Mapping here wouldn't accept every value of proper type anyway.
# (Unlike a mathematical mapping that accepts all values from a certain set.)
# Note that we cannot treat the key-type as contravariant as one might expect,
# because in Python Mappings are Iterables over the Key-type.
covariant_Mapping = True

default_typecheck_depth = 10

python3_5_executable = 'python3' # Must be >= 3.5.0

# Search-path for stubfiles.
stub_path = []

# Directory to collect generated stubs. If None, tempfile.gettempdir() is used.
stub_gen_dir = None

# Monkeypatch Generic to circumvent type-erasure:
_Generic__new__ = Generic.__new__
def __Generic__new__(cls, *args, **kwds):
	res = _Generic__new__(cls, args, kwds)
	res.__gentype__ = cls
	return res
Generic.__new__ = __Generic__new__

class TypeCheckError(Exception): pass
class InputTypeError(TypeCheckError): pass
class ReturnTypeError(TypeCheckError): pass
class OverrideError(TypeCheckError): pass

# We import some public API for central access:
from .type_util import deep_type, is_builtin_type, has_type_hints, \
		type_str, get_types, get_type_hints, is_iterable, get_iterable_itemtype, \
		get_generator_type, get_generator_yield_type, is_Union, get_Tuple_params, \
		get_Callable_args_res, _issubclass as is_subtype, _isinstance as is_of_type
from .util import getargspecs, get_staticmethod_qualname, get_class_qualname, \
		get_class_that_defined_method, is_method, is_class, is_classmethod
from .stubfile_manager import get_stub_module, as_stub_func_if_any
from .typechecker import typechecked, typechecked_module, no_type_check, \
		is_no_type_check, override, OverrideError, InputTypeError, ReturnTypeError

# Some exemplary overrides for this modules's global settings:

# Set custom Python3-executable like this:
#pytypes.python3_5_executable = '/data/workspace/linux/Python-3.5.2/python'

# Set custom directory to store generated stubfiles like this:
# Unlike in tmp-directory mode, these are kept over distinct runs.
#stub_gen_dir = '../py2_stubs'
