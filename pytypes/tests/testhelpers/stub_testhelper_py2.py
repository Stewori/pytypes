'''
Created on 08.11.2016

@author: Stefan Richthofer
'''

from pytypes import typechecked
from typing import Generic, TypeVar

@typechecked
def testfunc1_py2(a, b):
	# actually (int, int) -> str from stubfile
	return "testfunc1_"+str(a)+" -- "+str(b)

@typechecked
class class1_py2():
	# actually a: float, b: str -> str
	def meth1_py2(self, a, b):
		return b + '----'+str(a)

	def meth2_py2(self, d, c):
	# actually d, c: str -> int
		return str(len(c))+str(d) # intentionally faulty

	@staticmethod
	def static_meth_py2(d, c):
	# actually d, c: str) -> int
		return len(c+str(d))

	@classmethod
	def class_meth_py2(cls, a, b):
	# actually cls, a: str, b: int -> float
		return len(cls.__name__)*len(a)*b/5.0

	class class1_inner_py2():
		# actually a: float, b: str -> int
		def inner_meth1_py2(self, a, b):
			return len(b) + len(str(a))

		@staticmethod
		def inner_static_meth_py2(d, c):
		# actually d: float, c: class1_py2 -> int
			return len(c+str(d))

		@classmethod
		def inner_class_meth_py2(cls, a, b):
		# actually cls, a: str, b: int -> float
			return str(len(cls.__name__)*len(a)*b/5.0)

@typechecked
class class2_py2(class1_py2):
	def meth1b_py2(self, a):
	# actually a: ... -> str
		return str(a)

	def meth2b_py2(self, b):
	# actually class1_py2 -> str
		return str(b)

	@classmethod
	def class_methb_py2(cls, a, b):
	# actually cls, a: str, b: class1_py2 -> float
		return a + (cls.__name__) + str(b)

@typechecked
def testfunc_class_in_list_py2(a):
	# actually a: List[class1_py2] -> int
	return len(a)

@typechecked
def testfunc_None_ret_py2(a, b):
	# actually (int, Real) -> None
	pass

@typechecked
def testfunc_None_ret_err_py2(a, b):
	# actually (int, Real) -> None
	return 7

@typechecked
def testfunc_None_arg_py2(a, b):
	# actually (int, None) -> int
	return a*a

@typechecked
def testfunc_Dict_arg_py2(a, b):
	# actually (int, Dict[str, Union[int, str]]) -> None
	assert isinstance(b[str(a)], str) or isinstance(b[str(a)], int)

@typechecked
def testfunc_Mapping_arg_py2(a, b):
	# actually (int, Mapping[str, Union[int, str]]) -> None
	assert isinstance(b[str(a)], str) or isinstance(b[str(a)], int)

@typechecked
def testfunc_Dict_ret_py2(a):
	# actually (str) -> Dict[str, Union[int, str]]
	return {a: len(a), 2*a: a}

@typechecked
def testfunc_Dict_ret_err_py2(a):
	# actually (int) -> Dict[str, Union[int, str]]
	return {a: str(a), 2*a: a}

@typechecked
def testfunc_Seq_arg_py2(a):
	# actually (Sequence[Tuple[int, str]]) -> int
	return len(a)

@typechecked
def testfunc_Seq_ret_List_py2(a, b):
	# actually (int, str) -> Sequence[Union[int, str]]
	return [a, b]

@typechecked
def testfunc_Seq_ret_Tuple_py2(a, b):
	# actually (int, str) -> Sequence[Union[int, str]]
	return a, b

@typechecked
def testfunc_Seq_ret_err_py2(a, b):
	# actually (int, str) -> Sequence[Union[int, str]]
	return {a: str(a), b: str(b)}

@typechecked
def testfunc_Iter_arg_py2(a, b):
	# actually (Iterable[int], str) -> List[int]
	return [r for r in a]

@typechecked
def testfunc_Iter_str_arg_py2(a):
	# actually (Iterable[str]) -> List[int]
	return [ord(r) for r in a]

@typechecked
def testfunc_Iter_ret_py2():
	# actually () -> Iterable[int]
	return [1, 2, 3, 4, 5]

@typechecked
def testfunc_Iter_ret_err_py2():
	# actually () -> Iterable[str]
	return [1, 2, 3, 4, 5]

@typechecked
def testfunc_Callable_arg_py2(a, b):
	# actually (Callable[[str, int], str], str) -> str
	return a(b, len(b))

@typechecked
def testfunc_Callable_call_err_py2(a, b):
	# actually (Callable[[str, int], str], str) -> str
	return a(b, b)

@typechecked
def testfunc_Callable_ret_py2(a, b):
	# actually (int, str) -> Callable[[str, int], str]
	
	def m(x, y):
		# type: (str, int) -> str
		return x+str(y)+b*a

	return m

# Todo: Test regarding wrong-typed Callables
@typechecked
def testfunc_Callable_ret_err_py2():
	# actually () -> Callable[[str, int], str]
	return 5

@typechecked
def testfunc_Generator_py2():
	# actually () -> Generator[int, Union[str, None], Any]
	s = yield
	while not s is None:
		if s == 'fail':
			s = yield 'bad yield'
		s = yield len(s)

@typechecked
def testfunc_Generator_arg_py2(gen):
	# actually (Generator[int, Union[str, None], Any]) -> List[int]
	# should raise error because of illegal use of typing.Generator
	lst = ('ab', 'nmrs', 'u')
	res = [gen.send(x) for x in lst]
	return res

@typechecked
def testfunc_Generator_ret_py2():
	# actually () -> Generator[int, Union[str, None], Any]
	# should raise error because of illegal use of typing.Generator
	res = testfunc_Generator_py2()
	return res


T_1_py2 = TypeVar('T_1_py2')
class Custom_Generic_py2(Generic[T_1_py2]):
	
	def __init__(self, val):
		# type: (T_1_py2) -> None
		self.val = val

	def v(self):
		# type: () -> T_1_py2
		return self.val


@typechecked
def testfunc_Generic_arg_py2(x):
	# actually (Custom_Generic_py2[str]) -> str
	return x.v()

@typechecked
def testfunc_Generic_ret_py2(x):
	# actually (int) -> Custom_Generic[int]
	return Custom_Generic_py2[int](x)

@typechecked
def testfunc_Generic_ret_err_py2(x):
	# actually (int) -> Custom_Generic[int]
	return Custom_Generic_py2[str](str(x))
