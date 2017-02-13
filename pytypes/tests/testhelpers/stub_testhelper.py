'''
Created on 21.10.2016

@author: Stefan Richthofer
'''

from pytypes import typechecked, check_argument_types
from typing import Generic, TypeVar

@typechecked
def testfunc1(a, b):
	# will feature (int, int) -> str from stubfile
	return "testfunc1_"+str(a)+" -- "+str(b)

@typechecked
class class1():
	# actually a: float, b: str -> str
	def meth1(self, a, b):
		return b + '----'+str(a)

	def meth2(self, d, c):
	# actually d, c: str -> int
		return str(len(c))+str(d) # intentionally faulty

	@staticmethod
	def static_meth(d, c):
	# actually d, c: str) -> int
		return len(c+str(d))

	@classmethod
	def class_meth(cls, a, b):
	# actually cls, a: str, b: int -> float
		return len(cls.__name__)*len(a)*b/5.0

	class class1_inner():
		def inner_meth1(self, a, b):
			# actually a: float, b: str -> int
			return len(b) + len(str(a))

		@staticmethod
		def inner_static_meth(d, c):
		# actually d: float, c: class1) -> int
			return len(c+str(d))

@typechecked
class class2(class1):
	def meth1b(self, a):
	# actually a -> str
		return str(a)

	def meth2b(self, b):
	# actually class1 -> str
		return str(b)

@typechecked
def testfunc_class_in_list(a):
	# actually a: List[class1] -> int
	return len(a)


@typechecked
def testfunc_None_ret(a, b):
	# actually (int, Real) -> None
	pass

@typechecked
def testfunc_None_ret_err(a, b):
	# actually (int, Real) -> None
	return 7

@typechecked
def testfunc_None_arg(a, b):
	# actually (int, None) -> int
	return a*a

@typechecked
def testfunc_Dict_arg(a, b):
	# actually (int, Dict[str, Union[int, str]]) -> None
	assert isinstance(b[str(a)], str) or isinstance(b[str(a)], int)

@typechecked
def testfunc_Mapping_arg(a, b):
	# actually (int, Mapping[str, Union[int, str]]) -> None
	assert isinstance(b[str(a)], str) or isinstance(b[str(a)], int)

@typechecked
def testfunc_Dict_ret(a):
	# actually (str) -> Dict[str, Union[int, str]]
	return {a: len(a), 2*a: a}

@typechecked
def testfunc_Dict_ret_err(a):
	# actually (int) -> Dict[str, Union[int, str]]
	return {a: str(a), 2*a: a}

@typechecked
def testfunc_Seq_arg(a):
	# actually (Sequence[Tuple[int, str]]) -> int
	return len(a)

@typechecked
def testfunc_Seq_ret_List(a, b):
	# actually (int, str) -> Sequence[Union[int, str]]
	return [a, b]

@typechecked
def testfunc_Seq_ret_Tuple(a, b):
	# actually (int, str) -> Sequence[Union[int, str]]
	return a, b

@typechecked
def testfunc_Seq_ret_err(a, b):
	# actually (int, str) -> Sequence[Union[int, str]]
	return {a: str(a), b: str(b)}

@typechecked
def testfunc_Iter_arg(a, b):
	# actually (Iterable[int], str) -> List[int]
	return [r for r in a]

@typechecked
def testfunc_Iter_str_arg(a):
	# actually (Iterable[str]) -> List[int]
	return [ord(r) for r in a]

@typechecked
def testfunc_Iter_ret():
	# actually () -> Iterable[int]
	return [1, 2, 3, 4, 5]

@typechecked
def testfunc_Iter_ret_err():
	# actually () -> Iterable[str]
	return [1, 2, 3, 4, 5]

@typechecked
def testfunc_Callable_arg(a, b):
	# actually (Callable[[str, int], str], str) -> str
	return a(b, len(b))

@typechecked
def testfunc_Callable_call_err(a, b):
	# actually (Callable[[str, int], str], str) -> str
	return a(b, b)

@typechecked
def testfunc_Callable_ret(a, b):
	# actually (int, str) -> Callable[[str, int], str]
	
	def m(x, y):
		# type: (str, int) -> str
		return x+str(y)+b*a

	return m

# Todo: Test regarding wrong-typed Callables
@typechecked
def testfunc_Callable_ret_err():
	# actually () -> Callable[[str, int], str]
	return 5

@typechecked
def testfunc_Generator():
	# actually () -> Generator[int, Union[str, None], Any]
	s = yield
	while not s is None:
		if s == 'fail':
			s = yield 'bad yield'
		s = yield len(s)

@typechecked
def testfunc_Generator_arg(gen):
	# actually (Generator[int, Union[str, None], Any]) -> List[int]
	# should raise error because of illegal use of typing.Generator
	lst = ('ab', 'nmrs', 'u')
	res = [gen.send(x) for x in lst]
	return res

@typechecked
def testfunc_Generator_ret():
	# actually () -> Generator[int, Union[str, None], Any]
	# should raise error because of illegal use of typing.Generator
	res = testfunc_Generator()
	return res


T_1 = TypeVar('T_1')
class Custom_Generic(Generic[T_1]):
	
	def __init__(self, val: T_1) -> None:
		self.val = val

	def v(self) -> T_1:
		return self.val


@typechecked
def testfunc_Generic_arg(x):
	# actually (Custom_Generic[str]) -> str
	return x.v()

@typechecked
def testfunc_Generic_ret(x):
	# actually (int) -> Custom_Generic[int]
	return Custom_Generic[int](x)

@typechecked
def testfunc_Generic_ret_err(x):
	# actually (int) -> Custom_Generic[int]
	return Custom_Generic[str](str(x))


class testClass_property(object):

	@typechecked
	@property
	def testprop(self):
		# actually () -> int
		return self._testprop

	@typechecked
	@testprop.setter
	def testprop(self, value):
		# actually (int) -> None
		self._testprop = value

	@typechecked
	@property
	def testprop2(self):
		# actually () -> str
		return self._testprop2

	@testprop2.setter
	def testprop2(self, value):
		# actually (str) -> None
		self._testprop2 = value

	@typechecked
	@property
	def testprop3(self):
		# actually () -> Tuple[int, str]
		return self._testprop3

	@testprop3.setter
	def testprop3(self, value):
		# actually (Tuple[int, str]) -> None
		check_argument_types()
		self._testprop3 = value


@typechecked
class testClass_property_class_check(object):
	@property
	def testprop(self):
		# actually () -> int
		return self._testprop

	@testprop.setter
	def testprop(self, value):
		# actually (int) -> None
		self._testprop = value

	@property
	def testprop2(self):
		# actually () -> float
		return 'abc'

	@testprop2.setter
	def testprop2(self, value):
		# actually (float) -> None
		pass
