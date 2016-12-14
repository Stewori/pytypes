'''
Created on 08.11.2016

@author: Stefan Richthofer
'''

from typing import Any
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
