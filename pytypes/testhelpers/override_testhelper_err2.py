'''
Created on 01.12.2016

Designed to cause a NameError on import.
(unless typechecker.check_override_at_runtime == False)

@author: Stefan Richthofer
'''

from typechecker import override

class TestClass():
	def test_meth0(self, a):
		# type: (int) -> str
		pass

	def test_meth1(self, a):
		# type: (TestArg2) -> str
		pass

	def test_meth2(self, a):
		# type: (int) -> TestResult1
		pass

class TestClass2(TestClass):
	@override
	def test_meth0(self, a):
		# type: (int) -> str
		pass

	@override
	def test_meth1(self, a):
		# type: (TestArg1) -> str
		pass

	@override
	def test_meth2(self, a):
		# type: (int) -> TestResult2
		pass

class TestClass3(TestClass):
	@override
	def test_meth1(self, a):
		# type: (TestArg1) -> str
		pass

	@override
	def test_meth2(self, a):
		# type: (int) -> TestResult2
		pass

class TestArg1():
	pass

class TestResult1():
	pass

class TestClass3(TestClass):
	@override
	def test_meth1(self,
				a # type: TestArg1
				):
		# type: (...) -> strr
		pass

	@override
	def test_meth2(self,
				a # type: int
				):
		# type: (...) -> TestResult2
		pass

class TestArg2(TestArg1):
	pass

class TestResult2(TestResult1):
	pass

