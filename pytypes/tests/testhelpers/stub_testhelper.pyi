'''
Created on 21.10.2016

@author: Stefan Richthofer
'''

from numbers import Real
from typing import List

def testfunc1(a: int, b: Real) -> str: ...

class class1():
	def meth1(self, a: float, b: str) -> str: ...
	def meth2(self, d, c: str) -> int: ...

	@staticmethod
	def static_meth(d, c: str) -> int: ...

	@classmethod
	def class_meth(cls, a: str, b: int) -> float: ...

	class class1_inner():
		def inner_meth1(self, a: float, b: str) -> int: ...

		@staticmethod
		def inner_static_meth(d: float, c: str) -> int: ...


class class2(class1):
	def meth1b(self, a) -> str: ...

	def meth2b(self, b: class1) -> str: ...


def testfunc_class_in_list(a: List[class1]) -> int: ...
