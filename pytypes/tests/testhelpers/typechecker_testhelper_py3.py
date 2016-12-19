'''
Created on 12.09.2016

@author: Stefan Richthofer
'''

from pytypes import typechecked, override
from typing import Tuple, Union, Dict, Generator, TypeVar, \
		Generic, Iterable, Sequence, Callable, List, Any
import abc; from abc import abstractmethod
from numbers import Real

class testClass(str):
	@typechecked
	def testmeth(self, a: int, b: Real) -> str:
		return "-".join((str(a), str(b), self))

	@typechecked
	def testmeth2(self, a: int, b: Real) -> str:
		# type: (int, Real) -> str
		return "-".join((str(a), str(b), self))

	@typechecked
	@classmethod
	def testmeth_class(cls, a: int, b: Real) -> str:
		# type: (int, Real) -> str
		return "-".join((str(a), str(b), str(cls)))

	@typechecked
	@classmethod
	def testmeth_class2(cls, a: int, b: Real) -> str:
		return "-".join((str(a), str(b), str(cls)))

	@typechecked
	@classmethod
	def testmeth_class2_err(cls, a: int, b: Real) -> int:
		return "-".join((str(a), str(b), str(cls)))

	@typechecked
	@staticmethod
	def testmeth_static(a: int, b: Real) -> str:
		# type: (int, Real) -> str
		return "-".join((str(a), str(b), "static"))

	@staticmethod
	def testmeth_static_raw(a: int, b: Real) -> str:
		return "-".join((str(a), str(b), "static"))

	@classmethod
	def testmeth_class_raw(cls, a: int, b: Real) -> str:
		return "-".join((str(a), str(b), "static"))

	@typechecked
	@staticmethod
	def testmeth_static2(a: int, b: Real) -> str:
		return "-".join((str(a), str(b), "static"))

	@typechecked
	def testmeth_forward(self, a: int, b: 'testClass2') -> int:
		assert b.__class__ is testClass2
		return len(str(a)+str(b)+str(self))


class testClass2Base(str):
	def testmeth(self, a: int, b: Real) -> Union[str, int]:
		pass

	def testmeth2(self, a: int, b: Real) -> Union[str, int]:
		pass

	def testmeth2b(self, a: int, b: Real) -> Union[str, int]:
		pass

	def testmeth3(self, a: int, b: Real) -> Union[str, int]:
		pass

	def testmeth3_err(self, a: int, b: Real) -> Union[str, int]:
		pass

	def testmeth4(self, a: int, b: Real) -> str:
		pass

	def testmeth5(self, a: int, b: Real) -> str:
		pass


class testClass2(testClass2Base):
	def testmeth0(self, a: int, b: Real) -> str:
		# type: (int, Real) -> str
		return "-".join((str(a), str(b), self))

	@typechecked
	@override
	def testmeth(self, a: int, b: Real) -> str:
		# type: (int, Real) -> str
		return "-".join((str(a), str(b), self))

	@override
	def testmeth2(self, a: str, b: Real) -> Union[str, int]:
		return "-".join((str(a), str(b), self))

	@override
	def testmeth2b(self, a: int, b: Real) -> Union[str, Real]:
		return "-".join((str(a), str(b), self))

	@typechecked
	@override
	def testmeth3(self, a, b):
		return "-".join((str(a), str(b), self))

	@typechecked
	@override
	def testmeth3_err(self, a: int, b: Real) -> int:
		return "-".join((str(a), str(b), self))

	@override
	def testmeth4(self, a, b):
		return "-".join((str(a), str(b), self))

	@override
	def testmeth5(self, a, b) -> str:
		return "-".join((str(a), str(b), self))

	@override
	def testmeth6(self, a: int, b: Real) -> str:
		# type: (int, Real) -> str
		return "-".join((str(a), str(b), self))

	@typechecked
	def testmeth_err(self, a: int, b: Real) -> int:
		return "-".join((str(a), str(b), self))


class testClass3Base():
	__metaclass__  = abc.ABCMeta

	@abstractmethod
	def testmeth(self, a: int, b: Real) -> Union[str, int]:
		pass

class testClass3(testClass3Base):

	@typechecked
	@override
	def testmeth(self, a, b):
		return "-".join((str(a), str(b), str(type(self))))


def testClass2_defTimeCheck():
	class testClass2b(testClass2Base):
		def testmeth0(self, a: int, b: Real) -> str:
			return "-".join((str(a), str(b), self))
	
		@typechecked
		@override
		def testmeth(self, a: int, b: Real) -> str:
			return "-".join((str(a), str(b), self))
	
		def testmeth2c(self, a: int, b: Real) -> Union[str, Real]:
			# type: (int, Real) -> Union[str, Real]
			return "-".join((str(a), str(b), self))
	
		@typechecked
		@override
		def testmeth3(self, a: int, b: Real) -> str:
			# type: (int, Real) -> str
			return "-".join((str(a), str(b), self))
	
		@typechecked
		@override
		def testmeth3_err(self, a: int, b: Real) -> int:
			# type: (int, Real) -> int
			return "-".join((str(a), str(b), self))
	
		@override
		def testmeth4(self, a, b):
			return "-".join((str(a), str(b), self))
	
		@override
		def testmeth5(self, a, b) -> str:
			return "-".join((str(a), str(b), self))
	
		@typechecked
		def testmeth_err(self, a: int, b: Real) -> int:
			return "-".join((str(a), str(b), self))

def testClass2_defTimeCheck2():
	class testClass2b(testClass2Base):
		@override
		def testmeth2(self, a: str, b: Real) -> Union[str, int]:
			return "-".join((str(a), str(b), self))

def testClass2_defTimeCheck3():
	class testClass2b(testClass2Base):
		@override
		def testmeth2b(self, a: int, b: Real) -> Union[str, Real]:
			return "-".join((str(a), str(b), self))

def testClass2_defTimeCheck4():
	class testClass2b(testClass2Base):
		@override
		def testmeth6(self, a: int, b: Real) -> str:
			return "-".join((str(a), str(b), self))


def testClass3_defTimeCheck():
	class testClass3b(testClass3Base):
		@typechecked
		@override
		def testmeth(self, a, b):
			return "-".join((str(a), str(b), str(type(self))))


@typechecked
def testfunc(a: int, b: Real, c: str) -> Tuple[int, Real]:
	# type: (int, Real, str) -> Tuple[int, Real]
	return a*a, a*b

@typechecked
def testfunc_err(a: int, b: Real, c: str) -> Tuple[str, Real]:
	# type: (int, Real, str) -> Tuple[str, Real]
	return a*a, a*b

@typechecked
def testfunc2(a: int, b: Real, c: testClass) -> Tuple[int, float]:
	return a*a, a*b

@typechecked
def testfunc_None_ret(a: int, b: Real) -> None:
	pass

@typechecked
def testfunc_None_ret_err(a: int, b: Real) -> None:
	# type: (int, Real) -> None
	# (asserting compatibility between different annotation formats)
	return 7

@typechecked
def testfunc_None_arg(a: int, b: None) -> int:
	return a*a

def testfunc_Dict_arg(a: int, b: Dict[str, Union[int, str]]) -> None:
	assert isinstance(b[str(a)], str) or isinstance(b[str(a)], int)

def testfunc_Dict_ret(a: str) -> Dict[str, Union[int, str]]:
	return {a: len(a), 2*a: a}

def testfunc_Dict_ret_err(a: int) -> Dict[str, Union[int, str]]:
	return {a: str(a), 2*a: a}

def testfunc_Seq_arg(a: Sequence[Tuple[int, str]]) -> int:
	return len(a)

def testfunc_Seq_ret_List(a: int, b: str) -> Sequence[Union[int, str]]:
	return [a, b]

def testfunc_Seq_ret_Tuple(a: int, b: str) -> Sequence[Union[int, str]]:
	return a, b

def testfunc_Seq_ret_err(a: int, b: str) -> Sequence[Union[int, str]]:
	return {a: str(a), b: str(b)}

def testfunc_Iter_arg(a: Iterable[int], b: str) -> List[int]:
	return [r for r in a]

def testfunc_Iter_ret() -> Iterable[int]:
	return range(22)

def testfunc_Iter_ret_err() -> Iterable[str]:
	return range(22)

def testfunc_Callable_arg(a: Callable[[str, int], str], b: str) -> str:
	return a(b, len(b))

def testfunc_Callable_ret(a: int, b: str) -> Callable[[str, int], str]:
	
	def m(x: str, y: int) -> str:
		return x+str(y)+b*a

	return m

def testfunc_Callable_ret_err() -> Callable[[str, int], str]:
	return 5

@typechecked
def testfunc_Generator() -> Generator[int, Union[str, None], float]:
	s = yield
	while not s is None:
		if s == 'fail':
			s = yield 'bad yield'
		elif s == 'ret':
			return 7.5
		elif s == 'ret_fail':
			return 'bad return'
		s = yield len(s)

@typechecked
def testfunc_Generator_arg(gen: Generator[int, Union[str, None], Any]) -> List[int]:
	# should raise error because of illegal use of typing.Generator
	lst = ('ab', 'nmrs', 'u')
	res = [gen.send(x) for x in lst]
	return res

@typechecked
def testfunc_Generator_ret() -> Generator[int, Union[str, None], Any]:
	# should raise error because of illegal use of typing.Generator
	res = testfunc_Generator()
	return res
