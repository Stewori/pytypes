'''
Created on 08.11.2016

@author: Stefan Richthofer
'''

from typing import Any, TypeVar, Generic, Generator, Iterable, Sequence, \
		Tuple, List, Callable, Dict, Mapping, Union
from numbers import Real

def testfunc1_py2(a, b):
	# type: (int, Real) -> str
	pass


class class1_py2():
	def meth1_py2(self, a, b):
		# type: (float, str) -> str
		pass

	def meth2_py2(self, d, c):
		# type: (Any, str) -> int
		pass

	@staticmethod
	def static_meth_py2(d, c):
		# type: (Any, str) -> int
		pass

	@classmethod
	def class_meth_py2(cls, a, b):
		# type: (str, int) -> float
		pass

	class class1_inner_py2():
		def inner_meth1_py2(self, a, b):
			# type: (float, str) -> int
			pass

		@staticmethod
		def inner_static_meth_py2(d, c):
			# type: (float, str) -> int
			pass

		@classmethod
		def inner_class_meth_py2(cls, a, b):
			# type: (str, int) -> float
			pass


class class2_py2(class1_py2):
	def meth1b_py2(self, a):
		# type: (...) -> str
		pass

	def meth2b_py2(self, b):
		# type: (class1_py2) -> str
		pass

	@classmethod
	def class_methb_py2(cls, a, b):
		# type: (str, class1_py2) -> float
		pass


def testfunc_class_in_list_py2(a):
	# type: (List[class1_py2]) -> int
	pass

def testfunc_None_ret_py2(a, b):
	# type: (int, Real) -> None
	pass

def testfunc_None_ret_err_py2(a, b):
	# type: (int, Real) -> None
	pass

def testfunc_None_arg_py2(a, b):
	# type: (int, None) -> int
	pass

def testfunc_Dict_arg_py2(a, b):
	# type: (int, Dict[str, Union[int, str]]) -> None
	pass

def testfunc_Mapping_arg_py2(a, b):
	# type: (int, Mapping[str, Union[int, str]]) -> None
	pass

def testfunc_Dict_ret_py2(a):
	# type: (str) -> Dict[str, Union[int, str]]
	pass

def testfunc_Dict_ret_err_py2(a):
	# type: (int) -> Dict[str, Union[int, str]]
	pass

def testfunc_Seq_arg_py2(a):
	# type: (Sequence[Tuple[int, str]]) -> int
	pass

def testfunc_Seq_ret_List_py2(a, b):
	# type: (int, str) -> Sequence[Union[int, str]]
	pass

def testfunc_Seq_ret_Tuple_py2(a, b):
	# type: (int, str) -> Sequence[Union[int, str]]
	pass

def testfunc_Seq_ret_err_py2(a, b):
	# type: (int, str) -> Sequence[Union[int, str]]
	pass

def testfunc_Iter_arg_py2(a, b):
	# type: (Iterable[int], str) -> List[int]
	pass

def testfunc_Iter_str_arg_py2(a):
	# type: (Iterable[str]) -> List[int]
	pass

def testfunc_Iter_ret_py2():
	# type: () -> Iterable[int]
	pass

def testfunc_Iter_ret_err_py2():
	# type: () -> Iterable[str]
	pass

def testfunc_Callable_arg_py2(a, b):
	# type: (Callable[[str, int], str], str) -> str
	pass

def testfunc_Callable_call_err_py2(a, b):
	# type: (Callable[[str, int], str], str) -> str
	pass

def testfunc_Callable_ret_py2(a, b):
	# type: (int, str) -> Callable[[str, int], str]
	pass

def testfunc_Callable_ret_err_py2():
	# type: () -> Callable[[str, int], str]
	pass

def testfunc_Generator_py2():
	# type: () -> Generator[int, Union[str, None], Any]
	pass

def testfunc_Generator_arg_py2(gen):
	# type: (Generator[int, Union[str, None], Any]) -> List[int]
	pass

def testfunc_Generator_ret_py2():
	# type: () -> Generator[int, Union[str, None], Any]
	pass

def testfunc_Generic_arg_py2(x):
	# type: (Custom_Generic_py2[str]) -> str
	pass

def testfunc_Generic_ret_py2(x):
	# type: (int) -> Custom_Generic_py2[int]
	pass

def testfunc_Generic_ret_err_py2(x):
	# type: (int) -> Custom_Generic_py2[int]
	pass
