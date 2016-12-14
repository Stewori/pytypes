'''
Created on 08.11.2016

@author: Stefan Richthofer
'''

from pytypes import typechecked #, get_type_hints

@typechecked
def testfunc1_py2(a, b):
	# will feature (int, int) -> str from stubfile
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
		# actually d: float, c: class1_py2) -> int
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
