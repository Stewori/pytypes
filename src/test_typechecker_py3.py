'''
Created on 12.09.2016

@author: Stefan Richthofer
'''

from typechecker import typechecked, override
from typing import Tuple, List, Union, Any
import abc; from abc import abstractmethod
from numbers import Real, Complex

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

class testClass2Base(str):
	def testmeth(self, a: int, b: Real) -> Union[str, int]:
		pass

	def testmeth2(self, a: int, b: Real) -> Union[str, int]:
		pass

	def testmeth3(self, a: int, b: Real) -> Union[str, int]:
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

	@typechecked
	@override
	def testmeth3(self, a, b):
		return "-".join((str(a), str(b), self))

	@override
	def testmeth4(self, a: int, b: Real) -> str:
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
