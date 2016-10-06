'''
Created on 25.08.2016

@author: Stefan Richthofer
'''

import unittest
import sys
import typechecker
typechecker.check_override_at_class_definition_time = False
typechecker.check_override_at_runtime = True
from typechecker import typechecked, override, get_types, get_type_hints, deep_type, \
		InputTypeError, ReturnTypeError, OverrideError
import typing; from typing import Tuple, List, Union, Any
from numbers import Real, Complex
import abc; from abc import abstractmethod

class testClass(str):
	@typechecked
	def testmeth(self, a, b):
		# type: (int, Real) -> str
		return "-".join((str(a), str(b), self))

	@typechecked
	def testmeth2(self,
				a, # type: int
				b  # type: Real
				):
		# type: (...) -> str
		return "-".join((str(a), str(b), self))

	@typechecked
	@classmethod
	def testmeth_class(cls,
				a, # type: int
				b  # type: Real
				):
		# type: (...) -> str
		return "-".join((str(a), str(b), str(cls)))

	@typechecked
	@classmethod
	def testmeth_class2(cls, a, b):
		# type: (int, Real) -> str
		return "-".join((str(a), str(b), str(cls)))

	@typechecked
	@classmethod
	def testmeth_class2_err(cls, a, b):
		# type: (int, Real) -> int
		return "-".join((str(a), str(b), str(cls)))

	@typechecked
	@staticmethod
	def testmeth_static(
				a, # type: int
				b  # type: Real
				):
		# type: (...) -> str
		return "-".join((str(a), str(b), "static"))

	@staticmethod
	def testmeth_static_raw(a, b):
		# type: (int, Real) -> str
		return "-".join((str(a), str(b), "static"))

	@classmethod
	def testmeth_class_raw(cls, a, b):
		# type: (int, Real) -> str
		return "-".join((str(a), str(b), "static"))

	@typechecked
	@staticmethod
	def testmeth_static2(a, b):
		# type: (int, Real) -> str
		return "-".join((str(a), str(b), "static"))

class testClass2Base(str):
	def testmeth(self, a, b):
		# type: (int, Real) -> Union[str, int]
		pass

	def testmeth2(self, a, b):
		# type: (int, Real) -> Union[str, int]
		pass

	def testmeth2b(self, a, b):
		# type: (int, Real) -> Union[str, int]
		pass

	def testmeth3(self, a, b):
		# type: (int, Real) -> Union[str, int]
		pass

	def testmeth3_err(self, a, b):
		# type: (int, Real) -> Union[str, int]
		pass
	
	def testmeth4(self,
				a, # type: int
				b  # type: Real
				):
		# type: (...) -> str
		pass

	def testmeth5(self,
				a, # type: int
				b  # type: Real
				):
		# type: (...) -> str
		pass

class testClass2(testClass2Base):
	def testmeth0(self,
				a, # type: int
				b  # type: Real
				):
		# type: (...) -> str
		return "-".join((str(a), str(b), self))

	@typechecked
	@override
	def testmeth(self,
				a, # type: int
				b  # type: Real
				):
		# type: (...) -> str
		return "-".join((str(a), str(b), self))

	@override
	def testmeth2(self, a, b):
		# type: (str, Real) -> Union[str, int]
		return "-".join((str(a), str(b), self))

	@override
	def testmeth2b(self, a, b):
		# type: (int, Real) -> Union[str, Real]
		return "-".join((str(a), str(b), self))

	def testmeth2c(self, a, b):
		# type: (int, Real) -> Union[str, Real]
		return "-".join((str(a), str(b), self))

	@typechecked
	@override
	def testmeth3(self, a, b):
		# type: (int, Real) -> str
		return "-".join((str(a), str(b), self))

	@typechecked
	@override
	def testmeth3_err(self, a, b):
		# type: (int, Real) -> int
		return "-".join((str(a), str(b), self))

	@override
	def testmeth4(self, a, b):
		return "-".join((str(a), str(b), self))

	@override
	def testmeth5(self, a, b):
		# type: (...) -> str
		return "-".join((str(a), str(b), self))

	@override
	def testmeth6(self,
				a, # type: int
				b  # type: Real
				):
		# type: (...) -> str
		return "-".join((str(a), str(b), self))

	@typechecked
	def testmeth_err(self, a, b):
		# type: (int, Real) -> int
		return "-".join((str(a), str(b), self))

class testClass3Base():
	__metaclass__  = abc.ABCMeta

	@abstractmethod
	def testmeth(self, a, b):
		# type: (int, Real) -> Union[str, int]
		pass

class testClass3(testClass3Base):

	@typechecked
	@override
	def testmeth(self, a, b):
		return "-".join((str(a), str(b), str(type(self))))


def testClass2_defTimeCheck():
	class testClass2b(testClass2Base):
		def testmeth0(self,
					a, # type: int
					b  # type: Real
					):
			# type: (...) -> str
			return "-".join((str(a), str(b), self))
	
		@typechecked
		@override
		def testmeth(self,
					a, # type: int
					b  # type: Real
					):
			# type: (...) -> str
			return "-".join((str(a), str(b), self))
	
		def testmeth2c(self, a, b):
			# type: (int, Real) -> Union[str, Real]
			return "-".join((str(a), str(b), self))
	
		@typechecked
		@override
		def testmeth3(self, a, b):
			# type: (int, Real) -> str
			return "-".join((str(a), str(b), self))
	
		@typechecked
		@override
		def testmeth3_err(self, a, b):
			# type: (int, Real) -> int
			return "-".join((str(a), str(b), self))
	
		@override
		def testmeth4(self, a, b):
			return "-".join((str(a), str(b), self))
	
		@override
		def testmeth5(self, a, b):
			# type: (...) -> str
			return "-".join((str(a), str(b), self))
	
		@typechecked
		def testmeth_err(self, a, b):
			# type: (int, Real) -> int
			return "-".join((str(a), str(b), self))


def testClass2_defTimeCheck2():
	class testClass2b(testClass2Base):
		@override
		def testmeth2(self, a, b):
			# type: (str, Real) -> Union[str, int]
			return "-".join((str(a), str(b), self))


def testClass2_defTimeCheck3():
	class testClass2b(testClass2Base):
		@override
		def testmeth2b(self, a, b):
			# type: (int, Real) -> Union[str, Real]
			return "-".join((str(a), str(b), self))

def testClass2_defTimeCheck4():
	class testClass2b(testClass2Base):
		@override
		def testmeth6(self,
					a, # type: int
					b  # type: Real
					):
			# type: (...) -> str
			return "-".join((str(a), str(b), self))


def testClass3_defTimeCheck():
	class testClass3b(testClass3Base):
		@typechecked
		@override
		def testmeth(self, a, b):
			return "-".join((str(a), str(b), str(type(self))))


@typechecked
def testfunc(a, # type: int
			b,  # type: Real
			c   # type: str
			):
	# type: (...) -> Tuple[int, Real]
	return a*a, a*b

@typechecked
def testfunc_err(
			a, # type: int
			b, # type: Real
			c  # type: str
			):
	# type: (...) -> Tuple[str, Real]
	return a*a, a*b

@typechecked
def testfunc2(a, b, c):
	# type: (int, Real, testClass) -> Tuple[int, float]
	return a*a, a*b

@typechecked
def testfunc4(a, b, c):
	return a*a, a*b

class TestTypecheck(unittest.TestCase):
	def test_function(self):
		self.assertEqual(testfunc(3, 2.5, "abcd"), (9, 7.5))
		self.assertRaises(InputTypeError, lambda: testfunc("string", 2.5, "abcd"))
		tc = testClass("efgh")
		self.assertEqual(testfunc2(12, 3.5, tc), (144, 42.0))
		self.assertRaises(InputTypeError, lambda: testfunc2(12, 2.5, "abcd"))
		self.assertRaises(ReturnTypeError, lambda: testfunc_err(12, 2.5, "abcd"))
		self.assertEqual(testfunc4(12, 3.5, tc), (144, 42.0))

	def test_classmethod(self):
		tc = testClass("efgh")
		self.assertEqual(tc.testmeth_class(23, 1.1), "23-1.1-<class '__main__.testClass'>")
		self.assertRaises(InputTypeError, lambda: tc.testmeth_class(23, '1.1'))
		self.assertEqual(tc.testmeth_class2(23, 1.1), "23-1.1-<class '__main__.testClass'>")
		self.assertRaises(InputTypeError, lambda: tc.testmeth_class2(23, '1.1'))
		self.assertRaises(ReturnTypeError, lambda: tc.testmeth_class2_err(23, 1.1))

	def test_method(self):
		tc2 = testClass2("ijkl")
		self.assertEqual(tc2.testmeth(1, 2.5), "1-2.5-ijkl")
		self.assertRaises(InputTypeError, lambda: tc2.testmeth(1, 2.5, 7))
		self.assertRaises(ReturnTypeError, lambda: tc2.testmeth_err(1, 2.5))

	def test_staticmethod(self):
		tc = testClass("efgh")
		self.assertEqual(tc.testmeth_static(12, 0.7), "12-0.7-static")
		self.assertRaises(InputTypeError, lambda: tc.testmeth_static(12, [3]))
		self.assertEqual(tc.testmeth_static2(11, 1.9), "11-1.9-static")
		self.assertRaises(InputTypeError, lambda: tc.testmeth_static2(11, ("a", "b"), 1.9))

	def test_abstract_override(self):
		tc3 = testClass3()
		self.assertEqual(tc3.testmeth(1, 2.5), "1-2.5-<class '__main__.testClass3'>")

	def test_get_types(self):
		tc = testClass("mnop")
		tc2 = testClass2("qrst")
		tc3 = testClass3()
		self.assertEqual(get_types(testfunc), (Tuple[int, Real, str], Tuple[int, Real]))
		self.assertEqual(get_types(testfunc2), (Tuple[int, Real, testClass], Tuple[int, float]))
		self.assertEqual(get_types(testfunc4), (Any, Any))
		self.assertEqual(get_types(tc2.testmeth), (Tuple[int, Real], str))
		self.assertEqual(get_types(testClass2.testmeth), (Tuple[int, Real], str))
		self.assertEqual(get_types(tc3.testmeth), (Any, Any))
		self.assertEqual(get_types(testClass3Base.testmeth), (Tuple[int, Real], Union[str, int]))
		self.assertEqual(get_types(tc.testmeth2), (Tuple[int, Real], str))
		self.assertEqual(get_types(tc.testmeth_class), (Tuple[int, Real], str))
		self.assertEqual(get_types(tc.testmeth_class2), (Tuple[int, Real], str))
		self.assertEqual(get_types(tc.testmeth_static), (Tuple[int, Real], str))
		self.assertEqual(get_types(tc.testmeth_static2), (Tuple[int, Real], str))
		self.assertEqual(get_types(testfunc), (Tuple[int, Real, str], Tuple[int, Real]))

	def test_various(self):
		self.assertEqual(get_type_hints(testfunc), {'a': int, 'c': str, 'b': Real, 'return': Tuple[int, Real]})
		self.assertEqual(deep_type(('abc', [3, 'a', 7], 4.5)), Tuple[str, List[Union[int, str]], float])
		tc2 = testClass2("bbb")
		self.assertEqual(typechecker.get_class_that_defined_method(tc2.testmeth2c), testClass2)
		self.assertEqual(typechecker.get_class_that_defined_method(testClass2.testmeth2c), testClass2)
		self.assertEqual(typechecker.get_class_that_defined_method(tc2.testmeth2b), testClass2)
		self.assertEqual(typechecker.get_class_that_defined_method(testClass2.testmeth2b), testClass2)
		self.assertEqual(typechecker.get_class_that_defined_method(tc2.testmeth3), testClass2)
		self.assertEqual(typechecker.get_class_that_defined_method(testClass2.testmeth3), testClass2)
		self.assertRaises(ValueError, lambda: typechecker.get_class_that_defined_method(testfunc))
		# old-style:
		tc3 = testClass3()
		self.assertEqual(typechecker.get_class_that_defined_method(tc3.testmeth), testClass3)
		self.assertEqual(typechecker.get_class_that_defined_method(testClass3.testmeth), testClass3)

class TestOverride(unittest.TestCase):
	def test_override(self):
		tc2 = testClass2("uvwx")
		self.assertRaises(OverrideError, lambda: tc2.testmeth2(1, 2.5))
		self.assertRaises(OverrideError, lambda: tc2.testmeth2b(3, 1.1))
		self.assertRaises(OverrideError, lambda: tc2.testmeth6(1, 2.5))

	def test_override_typecheck(self):
		tc2 = testClass2("uvwx")
		self.assertEqual(tc2.testmeth(1, 2.5), "1-2.5-uvwx")
		self.assertEqual(tc2.testmeth3(1, 2.5), "1-2.5-uvwx")
		self.assertRaises(ReturnTypeError, lambda: tc2.testmeth3_err(1, 2.5))
		self.assertEqual(tc2.testmeth4(1, 2.5), "1-2.5-uvwx")
		self.assertEqual(tc2.testmeth5(1, 2.5), "1-2.5-uvwx")
		self.assertRaises(InputTypeError, lambda: tc2.testmeth3('1', 2.5))

	def test_override_at_definition_time(self):
		tmp = typechecker.check_override_at_class_definition_time
		typechecker.check_override_at_class_definition_time = True
		testClass2_defTimeCheck()
		self.assertRaises(OverrideError, lambda: testClass2_defTimeCheck2())
		self.assertRaises(OverrideError, lambda: testClass2_defTimeCheck3())
		self.assertRaises(OverrideError, lambda: testClass2_defTimeCheck4())
		testClass3_defTimeCheck()
		typechecker.check_override_at_class_definition_time = tmp

@unittest.skipUnless(sys.version_info.major >= 3 and sys.version_info.minor >= 5,
		'Only applicable in Python >= 3.5.')
class TestTypecheck_Python3_5(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		global py3
		import test_typechecker_py3 as py3

	def test_function_py3(self):
		self.assertEqual(py3.testfunc(3, 2.5, "abcd"), (9, 7.5))
		self.assertRaises(InputTypeError, lambda: py3.testfunc("string", 2.5, "abcd"))
		tc = py3.testClass("efgh")
		self.assertEqual(py3.testfunc2(12, 3.5, tc), (144, 42.0))
		self.assertRaises(InputTypeError, lambda: py3.testfunc2(12, 2.5, "abcd"))
		self.assertRaises(ReturnTypeError, lambda: py3.testfunc_err(12, 2.5, "abcd"))

	def test_classmethod_py3(self):
		tc = py3.testClass("efgh")
		self.assertEqual(tc.testmeth_class(23, 1.1), "23-1.1-<class 'test_typechecker_py3.testClass'>")
		self.assertRaises(InputTypeError, lambda: tc.testmeth_class(23, '1.1'))
		self.assertEqual(tc.testmeth_class2(23, 1.1), "23-1.1-<class 'test_typechecker_py3.testClass'>")
		self.assertRaises(InputTypeError, lambda: tc.testmeth_class2(23, '1.1'))
		self.assertRaises(ReturnTypeError, lambda: tc.testmeth_class2_err(23, 1.1))

	def test_method_py3(self):
		tc2 = py3.testClass2("ijkl")
		self.assertEqual(tc2.testmeth(1, 2.5), "1-2.5-ijkl")
		self.assertRaises(InputTypeError, lambda: tc2.testmeth(1, 2.5, 7))
		self.assertRaises(ReturnTypeError, lambda: tc2.testmeth_err(1, 2.5))

	def test_staticmethod_py3(self):
		tc = py3.testClass("efgh")
		self.assertEqual(tc.testmeth_static(12, 0.7), "12-0.7-static")
		self.assertRaises(InputTypeError, lambda: tc.testmeth_static(12, [3]))
		self.assertEqual(tc.testmeth_static2(11, 1.9), "11-1.9-static")
		self.assertRaises(InputTypeError, lambda: tc.testmeth_static2(11, ("a", "b"), 1.9))

	def test_abstract_override_py3(self):
		tc3 = py3.testClass3()
		self.assertEqual(tc3.testmeth(1, 2.5), "1-2.5-<class 'test_typechecker_py3.testClass3'>")

	def test_get_types_py3(self):
		tc = py3.testClass("mnop")
		tc2 = py3.testClass2("qrst")
		tc3 = py3.testClass3()
		self.assertEqual(get_types(py3.testfunc), (Tuple[int, Real, str], Tuple[int, Real]))
		self.assertEqual(get_types(py3.testfunc2), (Tuple[int, Real, py3.testClass], Tuple[int, float]))
		self.assertEqual(get_types(tc2.testmeth), (Tuple[int, Real], str))
		self.assertEqual(get_types(py3.testClass2.testmeth), (Tuple[int, Real], str))
		self.assertEqual(get_types(tc3.testmeth), (Any, Any))
		self.assertEqual(get_types(py3.testClass3Base.testmeth), (Tuple[int, Real], Union[str, int]))
		self.assertEqual(get_types(tc.testmeth2), (Tuple[int, Real], str))
		self.assertEqual(get_types(tc.testmeth_class), (Tuple[int, Real], str))
		self.assertEqual(get_types(tc.testmeth_class2), (Tuple[int, Real], str))
		self.assertEqual(get_types(tc.testmeth_static), (Tuple[int, Real], str))
		self.assertEqual(get_types(tc.testmeth_static2), (Tuple[int, Real], str))
		self.assertEqual(get_types(py3.testfunc), (Tuple[int, Real, str], Tuple[int, Real]))

	def test_various_py3(self):
		self.assertEqual(get_type_hints(testfunc), {'a': int, 'c': str, 'b': Real, 'return': Tuple[int, Real]})
		self.assertEqual(deep_type(('abc', [3, 'a', 7], 4.5)), Tuple[str, List[Union[int, str]], float])


@unittest.skipUnless(sys.version_info.major >= 3 and sys.version_info.minor >= 5,
		'Only applicable in Python >= 3.5.')
class TestOverride_Python3_5(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		global py3
		import test_typechecker_py3 as py3

	def test_override_py3(self):
		# Todo: Test Python 3.5-style type-hints
		#print("Checking py3")
		tc2 = py3.testClass2("uvwx")
		self.assertRaises(OverrideError, lambda: tc2.testmeth2(1, 2.5))
		self.assertRaises(OverrideError, lambda: tc2.testmeth2b(3, 1.1))
		self.assertRaises(OverrideError, lambda: tc2.testmeth6(1, 2.5))

	def test_override_typecheck(self):
		tc2 = py3.testClass2("uvwx")
		self.assertEqual(tc2.testmeth(1, 2.5), "1-2.5-uvwx")
		self.assertEqual(tc2.testmeth3(1, 2.5), "1-2.5-uvwx")
		self.assertRaises(ReturnTypeError, lambda: tc2.testmeth3_err(1, 2.5))
		self.assertEqual(tc2.testmeth4(1, 2.5), "1-2.5-uvwx")
		self.assertEqual(tc2.testmeth5(1, 2.5), "1-2.5-uvwx")
		self.assertRaises(InputTypeError, lambda: tc2.testmeth3('1', 2.5))

	def test_override_at_definition_time(self):
		tmp = typechecker.check_override_at_class_definition_time
		typechecker.check_override_at_class_definition_time = True
		py3.testClass2_defTimeCheck()
		self.assertRaises(OverrideError, lambda: py3.testClass2_defTimeCheck2())
		self.assertRaises(OverrideError, lambda: py3.testClass2_defTimeCheck3())
		self.assertRaises(OverrideError, lambda: py3.testClass2_defTimeCheck4())
		py3.testClass3_defTimeCheck()
		typechecker.check_override_at_class_definition_time = tmp


def testCl4():
	class testClass4Base(str):
		def testmeth(self, a, b):
			# type: (int, int) -> Union[str, Real]
			pass
	
	# 	def testmeth(self, a: int, b: Real) -> Union[str, int]:
	# 		pass
	
	class testClass4(testClass4Base):
# 		@override
# 		def testmeth(self, a, b):
# 			# type: (int, int) -> Union[str, int]
# 			return "testMeth"

		@override
		def testmeth(self,
					a, # type: int
					b  # type: Real
					):
			# type: (...) -> Union[str, Real]
			return "testMeth"
	
	# 	@typechecker.overrides
	# 	def testmeth(self, a: int, b: Real) -> Union[str, Real]:
	# 		return "testMeth"

# @typechecker.overrides
# def tf4():
# 	print("tf4")

if __name__ == '__main__':
	#typechecker.check_override_at_class_definition_time = True
	testCl4()
# 	tc4 = testClass4()
# 	print(tc4.testmeth(3, 2.3))
	unittest.main()
	#tc2 = testClass2("uvwx")
	#tc2.testmeth2(1, 2.5)
	#tc2.testmeth2b(3, 1.1)
	print("done")