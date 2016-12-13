'''
Created on 12.12.2016

@author: Stefan Richthofer
'''

from typing import Sequence, Union, Generic, GenericMeta, TupleMeta

checking_enabled = False
def set_checking_enabled(flag = True):
	global checking_enabled
	checking_enabled = flag
	return checking_enabled

# This way we glue typechecking to activeness of the assert-statement by default,
# no matter what conditions it depends on (or will depend on, e.g. currently -O flag).
assert(set_checking_enabled())

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

# Monkeypatch GenericMeta.__subclasscheck__ to work properly with Tuples:
_GenericMeta__subclasscheck__ = GenericMeta.__subclasscheck__
def __GenericMeta__subclasscheck__(self, cls):
	if isinstance(cls, TupleMeta):
		if _GenericMeta__subclasscheck__(self, Sequence[Union[cls.__tuple_params__]]):
			return True
	return _GenericMeta__subclasscheck__(self, cls)
GenericMeta.__subclasscheck__ = __GenericMeta__subclasscheck__


# Some exemplary overrides for this modules's global settings:

# Set custom Python3-executable like this:
#pytypes.python3_5_executable = '/data/workspace/linux/Python-3.5.2/python'

# Set custom directory to store generated stubfiles like this:
# Unlike in tmp-directory mode, these are kept over distinct runs.
#stub_gen_dir = '../py2_stubs'
