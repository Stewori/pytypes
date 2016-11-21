'''
Created on 21.10.2016

@author: Stefan Richthofer
'''

from typechecker import typechecked #, get_type_hints 

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
		# actually d: float, c: class1_py2) -> int
			return len(c+str(d))

@typechecked
class class2(class1):
	def meth1b(self, a):
	# actually a -> str
		return str(a)

	def meth2b(self, b):
	# actually class1_py2 -> str
		return str(b)
