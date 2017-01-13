'''
Created on 25.08.2016

@author: Stefan Richthofer
'''

import unittest, sys, os, warnings
if __name__ == '__main__':
	sys.path.append(sys.path[0]+os.sep+'..'+os.sep+'..')
import pytypes
pytypes.check_override_at_class_definition_time = False
pytypes.check_override_at_runtime = True
from pytypes import typechecked, override, no_type_check, get_types, get_type_hints, \
		TypeCheckError, InputTypeError, ReturnTypeError, OverrideError
import typing; from typing import Tuple, List, Union, Any, Dict, Generator, TypeVar, \
		Generic, Iterable, Iterator, Sequence, Callable, Mapping
from numbers import Real
import abc; from abc import abstractmethod

class testClass(str):
	@typechecked
	def testmeth(self, a, b):
		# type: (int, Real) -> str
		return '-'.join((str(a), str(b), self))

	@typechecked
	def testmeth2(self,
				a, # type: int
				b  # type: Real
				):
		# type: (...) -> str
		return '-'.join((str(a), str(b), self))

	@typechecked
	@classmethod
	def testmeth_class(cls,
				a, # type: int
				b  # type: Real
				):
		# type: (...) -> str
		return '-'.join((str(a), str(b), str(cls)))

	@typechecked
	@classmethod
	def testmeth_class2(cls, a, b):
		# type: (int, Real) -> str
		return '-'.join((str(a), str(b), str(cls)))

	@typechecked
	@classmethod
	def testmeth_class2_err(cls, a, b):
		# type: (int, Real) -> int
		return '-'.join((str(a), str(b), str(cls)))

	@typechecked
	@staticmethod
	def testmeth_static(
				a, # type: int
				b  # type: Real
				):
		# type: (...) -> str
		return '-'.join((str(a), str(b), 'static'))

	@staticmethod
	def testmeth_static_raw(a, b):
		# type: (int, Real) -> str
		return '-'.join((str(a), str(b), 'static'))

	@classmethod
	def testmeth_class_raw(cls, a, b):
		# type: (int, Real) -> str
		return '-'.join((str(a), str(b), 'static'))

	@typechecked
	@staticmethod
	def testmeth_static2(a, b):
		# type: (int, Real) -> str
		return '-'.join((str(a), str(b), 'static'))

	@typechecked
	def testmeth_forward(self, a, b):
		# type: (int, testClass2) -> int
		assert b.__class__ is testClass2
		return len(str(a)+str(b)+str(self))


class testClass2Base(str):
	# actually methods here should be abstract

	def __repr__(self):
		return super(testClass2Base, self).__repr__()

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

	def testmeth3b(self, a, b):
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

	# testmeth6 intentionally not defined

	def testmeth7(self, a):
		# type:(int) -> testClass2
		pass


class testClass2(testClass2Base):
	@override
	def __repr__(self, a): # Should fail because of arg-count mismatch
		return super(testClass2, self).__repr__()

	def testmeth0(self,
				a, # type: int
				b  # type: Real
				):
		# type: (...) -> str
		return '-'.join((str(a), str(b), self))

	@typechecked
	@override
	def testmeth(self,
				a, # type: int
				b  # type: Real
				):
		# type: (...) -> str
		return '-'.join((str(a), str(b), self))

	@override
	def testmeth2(self, a, b):
		# type: (str, Real) -> Union[str, int]
		return '-'.join((str(a), str(b), self))

	@override
	def testmeth2b(self, a, b):
		# type: (int, Real) -> Union[str, Real]
		return '-'.join((str(a), str(b), self))

	def testmeth2c(self, a, b):
		# type: (int, Real) -> Union[str, Real]
		return '-'.join((str(a), str(b), self))

	@typechecked
	@override
	def testmeth3(self, a, b):
		# type: (int, Real) -> str
		return '-'.join((str(a), str(b), self))

	@typechecked
	@override
	def testmeth3_err(self, a, b):
		# type: (int, Real) -> int
		return '-'.join((str(a), str(b), self))

	@override
	def testmeth4(self, a, b):
		return '-'.join((str(a), str(b), self))

	@override
	def testmeth5(self, a, b):
		# type: (...) -> str
		return '-'.join((str(a), str(b), self))

	@override
	def testmeth6(self,
				a, # type: int
				b  # type: Real
				):
		# type: (...) -> str
		return '-'.join((str(a), str(b), self))

	@typechecked
	def testmeth_err(self, a, b):
		# type: (int, Real) -> int
		return '-'.join((str(a), str(b), self))


class testClass2_init_ov(testClass2Base):
	@override
	def __init__(self): # should fail because of invalid use of @override
		pass


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
		return '-'.join((str(a), str(b), str(type(self))))


@typechecked
class testClass4(str):
	def testmeth(self, a, b):
		# type: (int, Real) -> str
		return '-'.join((str(a), str(b), self))

	def testmeth_err(self, a, b):
		# type: (int, Real) -> int
		return '-'.join((str(a), str(b), self))

	@no_type_check
	def testmeth_raw(self, a, b):
		# type: (int, Real) -> str
		return '-'.join((str(a), str(b), self))

	def testmeth2(self,
				a, # type: int
				b  # type: Real
				):
		# type: (...) -> str
		return '-'.join((str(a), str(b), self))

	@classmethod
	def testmeth_class(cls,
				a, # type: int
				b  # type: Real
				):
		# type: (...) -> str
		return '-'.join((str(a), str(b), str(cls)))

	@classmethod
	def testmeth_class2(cls, a, b):
		# type: (int, Real) -> str
		return '-'.join((str(a), str(b), str(cls)))

	@classmethod
	def testmeth_class2_err(cls, a, b):
		# type: (int, Real) -> int
		return '-'.join((str(a), str(b), str(cls)))

	@staticmethod
	def testmeth_static(
				a, # type: int
				b  # type: Real
				):
		# type: (...) -> str
		return '-'.join((str(a), str(b), 'static'))

	@no_type_check
	@staticmethod
	def testmeth_static_raw(a, b):
		# type: (int, Real) -> str
		return '-'.join((str(a), str(b), 'static'))

	@no_type_check
	@classmethod
	def testmeth_class_raw(cls,
				a, # type: int
				b  # type: Real
				):
		# type: (...) -> str
		return '-'.join((str(a), str(b), str(cls)))

	@staticmethod
	def testmeth_static2(a, b):
		# type: (int, Real) -> str
		return '-'.join((str(a), str(b), 'static'))


def testClass2_defTimeCheck():
	class testClass2b(testClass2Base):
		def testmeth0(self,
					a, # type: int
					b  # type: Real
					):
			# type: (...) -> str
			return '-'.join((str(a), str(b), self))
	
		@typechecked
		@override
		def testmeth(self,
					a, # type: int
					b  # type: Real
					):
			# type: (...) -> str
			return '-'.join((str(a), str(b), self))
	
		def testmeth2c(self, a, b):
			# type: (int, Real) -> Union[str, Real]
			return '-'.join((str(a), str(b), self))
	
		@typechecked
		@override
		def testmeth3(self, a, b):
			# type: (int, Real) -> str
			return '-'.join((str(a), str(b), self))
	
		@typechecked
		@override
		def testmeth3b(self, a, b):
			return '-'.join((str(a), str(b), self))

		@typechecked
		@override
		def testmeth3_err(self, a, b):
			# type: (int, Real) -> int
			return '-'.join((str(a), str(b), self))
	
		@override
		def testmeth4(self, a, b):
			return '-'.join((str(a), str(b), self))
	
		@override
		def testmeth5(self, a, b):
			# type: (...) -> str
			return '-'.join((str(a), str(b), self))
	
		@typechecked
		def testmeth_err(self, a, b):
			# type: (int, Real) -> int
			return '-'.join((str(a), str(b), self))

	return testClass2b()

def testClass2_defTimeCheck2():
	class testClass2b(testClass2Base):
		@override
		def testmeth2(self, a, b):
			# type: (str, Real) -> Union[str, int]
			return '-'.join((str(a), str(b), self))


def testClass2_defTimeCheck3():
	class testClass2b(testClass2Base):
		@override
		def testmeth2b(self, a, b):
			# type: (int, Real) -> Union[str, Real]
			return '-'.join((str(a), str(b), self))

def testClass2_defTimeCheck4():
	class testClass2b(testClass2Base):
		@override
		def testmeth6(self,
					a, # type: int
					b  # type: Real
					):
			# type: (...) -> str
			return '-'.join((str(a), str(b), self))

def testClass3_defTimeCheck():
	class testClass3b(testClass3Base):
		@typechecked
		@override
		def testmeth(self, a, b):
			return '-'.join((str(a), str(b), str(type(self))))

def testClass2_defTimeCheck_init_ov():
	class testClass2_defTime_init_ov(testClass2Base):
		@override
		def __init__(self): # should fail because of invalid use of @override
			pass


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

@typechecked
def testfunc_None_ret(a, b):
	# type: (int, Real) -> None
	pass

@typechecked
def testfunc_None_ret_err(a, b):
	# type: (int, Real) -> None
	return 7

@typechecked
def testfunc_None_arg(a, b):
	# type: (int, None) -> int
	return a*a

@typechecked
def testfunc_Dict_arg(a, b):
	# type: (int, Dict[str, Union[int, str]]) -> None
	assert isinstance(b[str(a)], str) or isinstance(b[str(a)], int)

@typechecked
def testfunc_Mapping_arg(a, b):
	# type: (int, Mapping[str, Union[int, str]]) -> None
	assert isinstance(b[str(a)], str) or isinstance(b[str(a)], int)

@typechecked
def testfunc_Dict_ret(a):
	# type: (str) -> Dict[str, Union[int, str]]
	return {a: len(a), 2*a: a}

@typechecked
def testfunc_Dict_ret_err(a):
	# type: (int) -> Dict[str, Union[int, str]]
	return {a: str(a), 2*a: a}

@typechecked
def testfunc_Seq_arg(a):
	# type: (Sequence[Tuple[int, str]]) -> int
	return len(a)

@typechecked
def testfunc_Seq_ret_List(a, b):
	# type: (int, str) -> Sequence[Union[int, str]]
	return [a, b]

@typechecked
def testfunc_Seq_ret_Tuple(a, b):
	# type: (int, str) -> Sequence[Union[int, str]]
	return a, b

@typechecked
def testfunc_Seq_ret_err(a, b):
	# type: (int, str) -> Sequence[Union[int, str]]
	return {a: str(a), b: str(b)}

@typechecked
def testfunc_Iter_arg(a, b):
	# type: (Iterable[int], str) -> List[int]
	return [r for r in a]

@typechecked
def testfunc_Iter_str_arg(a):
	# type: (Iterable[str]) -> List[int]
	return [ord(r) for r in a]

@typechecked
def testfunc_Iter_ret():
	# type: () -> Iterable[int]
	return [1, 2, 3, 4, 5]

@typechecked
def testfunc_Iter_ret_err():
	# type: () -> Iterable[str]
	return [1, 2, 3, 4, 5]

@typechecked
def testfunc_Callable_arg(a, b):
	# type: (Callable[[str, int], str], str) -> str
	return a(b, len(b))

@typechecked
def testfunc_Callable_call_err(a, b):
	# type: (Callable[[str, int], str], str) -> str
	return a(b, b)

@typechecked
def testfunc_Callable_ret(a, b):
	# type: (int, str) -> Callable[[str, int], str]
	
	def m(x, y):
		# type: (str, int) -> str
		return x+str(y)+b*a

	return m

# Todo: Test regarding wrong-typed Callables
@typechecked
def testfunc_Callable_ret_err():
	# type: () -> Callable[[str, int], str]
	return 5

@typechecked
def testfunc_Generator():
	# type: () -> Generator[int, Union[str, None], Any]
	s = yield
	while not s is None:
		if s == 'fail':
			s = yield 'bad yield'
		s = yield len(s)

@typechecked
def testfunc_Generator_arg(gen):
	# type: (Generator[int, Union[str, None], Any]) -> List[int]
	# should raise error because of illegal use of typing.Generator
	lst = ('ab', 'nmrs', 'u')
	res = [gen.send(x) for x in lst]
	return res

@typechecked
def testfunc_Generator_ret():
	# type: () -> Generator[int, Union[str, None], Any]
	# should raise error because of illegal use of typing.Generator
	res = testfunc_Generator()
	return res

T_1 = TypeVar('T_1')
class Custom_Generic(Generic[T_1]):
	
	def __init__(self, val):
		# type: (T_1) -> None
		self.val = val

	def v(self):
		# type: () -> T_1
		return self.val

@typechecked
def testfunc_Generic_arg(x):
	# type: (Custom_Generic[str]) -> str
	return x.v()

@typechecked
def testfunc_Generic_ret(x):
	# type: (int) -> Custom_Generic[int]
	return Custom_Generic[int](x)

@typechecked
def testfunc_Generic_ret_err(x):
	# type: (int) -> Custom_Generic[int]
	return Custom_Generic[str](str(x))

class test_iter():
	def __init__(self, itrbl):
		self.itrbl = itrbl
		self.pos = 0

	def __iter__(self):
		return self

	def __next__(self):
		if self.pos == len(self.itrbl.tpl):
			raise StopIteration()
		else:
			res = self.itrbl.tpl[self.pos]
			self.pos += 1
			return res

	def next(self):
		if self.pos == len(self.itrbl.tpl):
			raise StopIteration()
		else:
			res = self.itrbl.tpl[self.pos]
			self.pos += 1
			return res


class test_iterable():
	def __init__(self, tpl):
		self.tpl = tpl

	def __iter__(self):
		return test_iter(self)


class test_iterable_annotated():
	def __init__(self, tpl):
		self.tpl = tpl

	def __iter__(self):
		# type: () -> Iterator[int]
		return test_iter(self)


class TestTypecheck(unittest.TestCase):
	def test_function(self):
		self.assertEqual(testfunc(3, 2.5, 'abcd'), (9, 7.5))
		self.assertEqual(testfunc(7, b=12.5, c='cdef'), (49, 87.5))
		self.assertRaises(InputTypeError, lambda: testfunc('string', 2.5, 'abcd'))
		tc = testClass('efgh')
		self.assertEqual(testfunc2(12, 3.5, tc), (144, 42.0))
		self.assertRaises(InputTypeError, lambda: testfunc2(12, 2.5, 'abcd'))
		self.assertRaises(ReturnTypeError, lambda: testfunc_err(12, 2.5, 'abcd'))
		self.assertEqual(testfunc4(12, 3.5, tc), (144, 42.0))
		self.assertIsNone(testfunc_None_ret(2, 3.0))
		self.assertEqual(testfunc_None_arg(4, None), 16)
		self.assertRaises(InputTypeError, lambda: testfunc_None_arg(4, 'vvv'))
		self.assertRaises(ReturnTypeError, lambda: testfunc_None_ret_err(2, 3.0))

	def test_classmethod(self):
		tc = testClass('efgh')
		self.assertEqual(tc.testmeth_class(23, 1.1), "23-1.1-<class '__main__.testClass'>")
		self.assertRaises(InputTypeError, lambda: tc.testmeth_class(23, '1.1'))
		self.assertEqual(tc.testmeth_class2(23, 1.1), "23-1.1-<class '__main__.testClass'>")
		self.assertRaises(InputTypeError, lambda: tc.testmeth_class2(23, '1.1'))
		self.assertRaises(ReturnTypeError, lambda: tc.testmeth_class2_err(23, 1.1))

	def test_method(self):
		tc2 = testClass2('ijkl')
		self.assertEqual(tc2.testmeth(1, 2.5), '1-2.5-ijkl')
		self.assertRaises(InputTypeError, lambda: tc2.testmeth(1, 2.5, 7))
		self.assertRaises(ReturnTypeError, lambda: tc2.testmeth_err(1, 2.5))

	def test_method_forward(self):
		tc = testClass('ijkl2')
		tc2 = testClass2('ijkl3')
		self.assertEqual(tc.testmeth_forward(5, tc2), 11)
		self.assertRaises(InputTypeError, lambda: tc.testmeth_forward(5, 7))
		self.assertRaises(InputTypeError, lambda: tc.testmeth_forward(5, tc))

	def test_staticmethod(self):
		tc = testClass('efgh')
		self.assertEqual(tc.testmeth_static(12, 0.7), '12-0.7-static')
		self.assertRaises(InputTypeError, lambda: tc.testmeth_static(12, [3]))
		self.assertEqual(tc.testmeth_static2(11, 1.9), '11-1.9-static')
		self.assertRaises(InputTypeError, lambda: tc.testmeth_static2(11, ('a', 'b'), 1.9))

	def test_abstract_override(self):
		tc3 = testClass3()
		self.assertEqual(tc3.testmeth(1, 2.5), "1-2.5-<class '__main__.testClass3'>")

	def test_get_types(self):
		tc = testClass('mnop')
		tc2 = testClass2('qrst')
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

	def test_sequence(self):
		self.assertEqual(testfunc_Seq_arg(((3, 'ab'), (8, 'qvw'))), 2)
		self.assertEqual(testfunc_Seq_arg([(3, 'ab'), (8, 'qvw'), (4, 'cd')]), 3)
		self.assertRaises(InputTypeError, lambda: testfunc_Seq_arg({(3, 'ab'), (8, 'qvw')}))
		self.assertRaises(InputTypeError, lambda: testfunc_Seq_arg(((3, 'ab'), (8, 'qvw', 2))))
		self.assertRaises(InputTypeError, lambda: testfunc_Seq_arg([(3, 1), (8, 'qvw'), (4, 'cd')]))
		self.assertEqual(testfunc_Seq_ret_List(7, 'mno'), [7, 'mno'])
		self.assertEqual(testfunc_Seq_ret_Tuple(3, 'mno'), (3, 'mno'))
		self.assertRaises(ReturnTypeError, lambda: testfunc_Seq_ret_err(29, 'def'))

	def test_iterable(self):
		self.assertEqual(testfunc_Iter_arg((9, 8, 7, 6), 'vwxy'), [9, 8, 7, 6])
		self.assertEqual(testfunc_Iter_str_arg('defg'), [100, 101, 102, 103])
		self.assertRaises(InputTypeError, lambda: testfunc_Iter_arg((9, '8', 7, 6), 'vwxy'))
		self.assertRaises(InputTypeError, lambda: testfunc_Iter_arg(7, 'vwxy'))
		self.assertRaises(InputTypeError, lambda: testfunc_Iter_arg([9, 8, 7, '6'], 'vwxy'))
		self.assertEqual(testfunc_Iter_arg([9, 8, 7, 6], 'vwxy'), [9, 8, 7, 6])
		res = testfunc_Iter_arg({9, 8, 7, 6}, 'vwxy'); res.sort()
		self.assertEqual(res, [6, 7, 8, 9])
		res = testfunc_Iter_arg({19: 'a', 18: 'b', 17: 'c', 16: 'd'}, 'vwxy'); res.sort()
		self.assertEqual(res, [16, 17, 18, 19])
		self.assertEqual(testfunc_Iter_ret(), [1, 2, 3, 4, 5])
		self.assertRaises(ReturnTypeError, lambda: testfunc_Iter_ret_err())
		ti = test_iterable((2, 4, 6))
		self.assertRaises(InputTypeError, lambda: testfunc_Iter_arg(ti, 'vwxy'))
		tia = test_iterable_annotated((3, 6, 9))
		self.assertEqual(testfunc_Iter_arg(tia, 'vwxy'), [3, 6, 9])

	def test_dict(self):
		self.assertIsNone(testfunc_Dict_arg(5, {'5': 4, 'c': '8'}))
		self.assertIsNone(testfunc_Dict_arg(5, {'5': 'A', 'c': '8'}))
		self.assertIsNone(testfunc_Mapping_arg(7, {'7': 4, 'c': '8'}))
		self.assertIsNone(testfunc_Mapping_arg(5, {'5': 'A', 'c': '8'}))
		self.assertRaises(InputTypeError, lambda: testfunc_Dict_arg(5, {4: 4, 3: '8'}))
		self.assertRaises(InputTypeError, lambda: testfunc_Dict_arg(5, {'5': (4,), 'c': '8'}))
		self.assertEqual(testfunc_Dict_ret('defg'), {'defgdefg': 'defg', 'defg': 4})
		self.assertRaises(ReturnTypeError, lambda: testfunc_Dict_ret_err(6))

	def test_callable(self):
		def clb(s, i):
			# type: (str, int) -> str
			return '_'+s+'*'*i
		
		def clb2(s, i):
			# type: (str, str) -> str
			return '_'+s+'*'*i
		
		def clb3(s, i):
			# type: (str, int) -> int
			return '_'+s+'*'*i

		self.assertTrue(pytypes.is_of_type(clb, typing.Callable[[str, int], str]))
		self.assertFalse(pytypes.is_of_type(clb, typing.Callable[[str, str], str]))
		self.assertFalse(pytypes.is_of_type(clb, typing.Callable[[str, int], float]))

		self.assertEqual(testfunc_Callable_arg(clb, 'pqrs'), '_pqrs****')
		self.assertRaises(InputTypeError, lambda: testfunc_Callable_arg(clb2, 'pqrs'))
		self.assertRaises(InputTypeError, lambda: testfunc_Callable_arg(clb3, 'pqrs'))
		self.assertRaises(InputTypeError, lambda: testfunc_Callable_call_err(clb, 'tuvw'))
		self.assertEqual(testfunc_Callable_arg(lambda s, i: '__'+s+'-'*i, 'pqrs'), '__pqrs----')
		self.assertRaises(InputTypeError,
				lambda: testfunc_Callable_call_err(lambda s, i: '__'+s+'-'*i, 'tuvw'))
		fnc = testfunc_Callable_ret(5, 'qvwx')
		self.assertEqual(fnc.__class__.__name__, 'function')
		self.assertEqual(fnc.__name__, 'm')
		self.assertRaises(ReturnTypeError, lambda: testfunc_Callable_ret_err())

	def test_generator(self):
		test_gen = testfunc_Generator()
		self.assertIsNone(test_gen.send(None))
		self.assertEqual(test_gen.send('abc'), 3)
		self.assertEqual(test_gen.send('ddffd'), 5)
		self.assertRaises(InputTypeError, lambda: test_gen.send(7))
		test_gen2 = testfunc_Generator()
		self.assertIsNone(test_gen2.next() if hasattr(test_gen2, 'next') else test_gen2.__next__())
		self.assertEqual(test_gen2.send('defg'), 4)
		self.assertRaises(ReturnTypeError, lambda: test_gen2.send('fail'))
		self.assertRaises(TypeCheckError, lambda: testfunc_Generator_arg(test_gen))
		self.assertRaises(TypeCheckError, lambda: testfunc_Generator_ret())

	def test_custom_generic(self):
		self.assertEqual(testfunc_Generic_arg(Custom_Generic[str]('abc')), 'abc')
		self.assertEqual(testfunc_Generic_ret(5).v(), 5)
		self.assertRaises(InputTypeError, lambda: testfunc_Generic_arg(Custom_Generic[int](9)))
		self.assertRaises(InputTypeError, lambda: testfunc_Generic_arg(Custom_Generic(7)))
		self.assertRaises(ReturnTypeError, lambda: testfunc_Generic_ret_err(8))

	def test_various(self):
		self.assertEqual(get_type_hints(testfunc),
				{'a': int, 'c': str, 'b': Real, 'return': Tuple[int, Real]})
		self.assertEqual(pytypes.deep_type(('abc', [3, 'a', 7], 4.5)),
				Tuple[str, List[Union[int, str]], float])
		tc2 = testClass2('bbb')
		self.assertEqual(pytypes.get_class_that_defined_method(tc2.testmeth2c), testClass2)
		self.assertEqual(pytypes.get_class_that_defined_method(testClass2.testmeth2c), testClass2)
		self.assertEqual(pytypes.get_class_that_defined_method(tc2.testmeth2b), testClass2)
		self.assertEqual(pytypes.get_class_that_defined_method(testClass2.testmeth2b), testClass2)
		self.assertEqual(pytypes.get_class_that_defined_method(tc2.testmeth3), testClass2)
		self.assertEqual(pytypes.get_class_that_defined_method(testClass2.testmeth3), testClass2)
		self.assertRaises(ValueError, lambda: pytypes.get_class_that_defined_method(testfunc))
		# old-style:
		tc3 = testClass3()
		self.assertEqual(pytypes.get_class_that_defined_method(tc3.testmeth), testClass3)
		self.assertEqual(pytypes.get_class_that_defined_method(testClass3.testmeth), testClass3)


class TestTypecheck_class(unittest.TestCase):
	def test_classmethod(self):
		tc = testClass4('efghi')
		self.assertEqual(tc.testmeth_class(23, 1.1), "23-1.1-<class '__main__.testClass4'>")
		self.assertRaises(InputTypeError, lambda: tc.testmeth_class(23, '1.1'))
		# Tests @no_type_check:
		self.assertEqual(tc.testmeth_class_raw('23', 1.1), "23-1.1-<class '__main__.testClass4'>")
		self.assertEqual(tc.testmeth_class2(23, 1.1), "23-1.1-<class '__main__.testClass4'>")
		self.assertRaises(InputTypeError, lambda: tc.testmeth_class2(23, '1.1'))
		self.assertRaises(ReturnTypeError, lambda: tc.testmeth_class2_err(23, 1.1))

	def test_method(self):
		tc = testClass4('ijklm')
		self.assertEqual(tc.testmeth(1, 2.5), '1-2.5-ijklm')
		self.assertRaises(InputTypeError, lambda: tc.testmeth(1, 2.5, 7))
		self.assertRaises(ReturnTypeError, lambda: tc.testmeth_err(1, 2.5))
		# Tests @no_type_check:
		self.assertEqual(tc.testmeth_raw('1', 2.5), '1-2.5-ijklm')

	def test_staticmethod(self):
		tc = testClass4('efghj')
		self.assertEqual(tc.testmeth_static(12, 0.7), '12-0.7-static')
		self.assertRaises(InputTypeError, lambda: tc.testmeth_static(12, [3]))
		# Tests @no_type_check:
		self.assertEqual(tc.testmeth_static_raw('12', 0.7), '12-0.7-static')
		self.assertEqual(tc.testmeth_static2(11, 1.9), '11-1.9-static')
		self.assertRaises(InputTypeError, lambda: tc.testmeth_static2(11, ('a', 'b'), 1.9))


class TestOverride(unittest.TestCase):
	def test_override(self):
		tc2 = testClass2('uvwx')
		self.assertRaises(OverrideError, lambda: tc2.testmeth2(1, 2.5))
		self.assertRaises(OverrideError, lambda: tc2.testmeth2b(3, 1.1))
		self.assertRaises(OverrideError, lambda: tc2.testmeth6(1, 2.5))
		self.assertRaises(OverrideError, lambda: tc2.__repr__()) # i.e. no builtins-issue
		self.assertRaises(OverrideError, lambda: testClass2_init_ov())

	def test_override_typecheck(self):
		tc2 = testClass2('uvwx')
		self.assertEqual(tc2.testmeth(1, 2.5), '1-2.5-uvwx')
		self.assertEqual(tc2.testmeth3(1, 2.5), '1-2.5-uvwx')
		self.assertRaises(ReturnTypeError, lambda: tc2.testmeth3_err(1, 2.5))
		self.assertEqual(tc2.testmeth4(1, 2.5), '1-2.5-uvwx')
		self.assertEqual(tc2.testmeth5(1, 2.5), '1-2.5-uvwx')
		self.assertRaises(InputTypeError, lambda: tc2.testmeth3('1', 2.5))

	def test_override_at_definition_time(self):
		tmp = pytypes.check_override_at_class_definition_time
		pytypes.check_override_at_class_definition_time = True
		tc2 = testClass2_defTimeCheck()
		self.assertRaises(InputTypeError, lambda: tc2.testmeth3b(1, '2.5'))
		self.assertRaises(OverrideError, lambda: testClass2_defTimeCheck2())
		self.assertRaises(OverrideError, lambda: testClass2_defTimeCheck3())
		self.assertRaises(OverrideError, lambda: testClass2_defTimeCheck4())
		testClass3_defTimeCheck()
		self.assertRaises(OverrideError, lambda: testClass2_defTimeCheck_init_ov())
		pytypes.check_override_at_class_definition_time = tmp
	
	def test_override_at_definition_time_with_forward_decl(self):
		# This can only be sufficiently tested at import-time, so
		# we import helper-modules during this test.
		tmp = pytypes.check_override_at_class_definition_time
		pytypes.check_override_at_class_definition_time = True
		from pytypes.tests.testhelpers import override_testhelper # shall not raise error
		def _test_err():
			from pytypes.tests.testhelpers import override_testhelper_err
		def _test_err2():
			from pytypes.tests.testhelpers import override_testhelper_err2

		self.assertRaises(OverrideError, _test_err)
		self.assertRaises(NameError, _test_err2)

		pytypes.check_override_at_class_definition_time = tmp


class TestStubfile(unittest.TestCase):
	'''
	Planned Test-cases:
	- each should test func-access, class-access, method, static method, classmethod
	
	[ Ok ] plain 2.7-stub
	[ToDo] plain 2.7-stub in search-dir
	
	Skip if 3.5 or no suitable Python3 executable registered:
	- each with stub from search-dir and source-dir
	[ToDo] generate 2.7-stub in tmp-dir
	[ToDo] generate 2.7-stub in stub-dir
	[ToDo] reuse 2.7-stub from stub-dir
	[ToDo] recreate outdated 2.7-stub in stub-dir
	[ToDo] Python 2-override of a 3.5-stub
	
	Skip if 2.7:
	[ Ok ] plain 3.5-stub
	[ToDo] plain 3.5-stub in search-dir
	[ToDo] 3.5-stub with Python 2-override
	'''

	def test_plain_2_7_stub(self):
		from pytypes.tests.testhelpers import stub_testhelper_py2 as stub_py2

		# Test function:
		self.assertEqual(stub_py2.testfunc1_py2(1, 7), 'testfunc1_1 -- 7')
		self.assertRaises(InputTypeError, lambda: stub_py2.testfunc1_py2(1, '7'))
		hints = get_type_hints(stub_py2.testfunc1_py2)
		self.assertEqual(hints['a'], int)
		self.assertEqual(hints['b'], Real)
		self.assertEqual(hints['return'], str)

		# Test method:
		cl1 = stub_py2.class1_py2()
		self.assertEqual(cl1.meth1_py2(0.76, 'abc'), 'abc----0.76')
		self.assertRaises(InputTypeError, lambda: cl1.meth1_py2('0.76', 'abc'))
		hints = get_type_hints(cl1.meth1_py2)
		self.assertEqual(hints['a'], float)
		self.assertEqual(hints['b'], str)
		self.assertEqual(hints['return'], str)
		self.assertRaises(ReturnTypeError, lambda: cl1.meth2_py2(4.9, 'cde'))

		# Test method of nested class:
		cl1b = cl1.class1_inner_py2()
		cl1b.inner_meth1_py2(3.4, 'inn')
		self.assertRaises(InputTypeError, lambda: cl1b.inner_meth1_py2('3', 'in2'))

		# Test static method:
		self.assertEqual(5, stub_py2.class1_py2.static_meth_py2(66, 'efg'))
		self.assertRaises(InputTypeError, lambda: stub_py2.class1_py2.static_meth_py2(66, ('efg',)))
		hints = get_type_hints(stub_py2.class1_py2.static_meth_py2)
		self.assertEqual(hints['c'], str)
		self.assertEqual(hints['d'], Any)
		self.assertEqual(hints['return'], int)

		# Test static method on instance:
		self.assertEqual(5, cl1.static_meth_py2(66, 'efg'))
		self.assertRaises(InputTypeError, lambda: cl1.static_meth_py2(66, ('efg',)))
		hints = get_type_hints(cl1.static_meth_py2)
		self.assertEqual(hints['c'], str)
		self.assertEqual(hints['d'], Any)
		self.assertEqual(hints['return'], int)

		# Test staticmethod with nested classes/instances:
		self.assertEqual(7,
				stub_py2.class1_py2.class1_inner_py2.inner_static_meth_py2(66.1, 'efg'))
		self.assertRaises(InputTypeError,
				lambda: stub_py2.class1_py2.class1_inner_py2.inner_static_meth_py2(66, ('efg',)))
		hints = get_type_hints(stub_py2.class1_py2.class1_inner_py2.inner_static_meth_py2)
		self.assertEqual(hints['c'], str)
		self.assertEqual(hints['d'], float)
		self.assertEqual(hints['return'], int)
		self.assertEqual(7, cl1.class1_inner_py2.inner_static_meth_py2(66.1, 'efg'))
		self.assertRaises(InputTypeError,
				lambda: cl1.class1_inner_py2.inner_static_meth_py2(66, ('efg',)))
		self.assertEqual(hints, get_type_hints(cl1.class1_inner_py2.inner_static_meth_py2))
		cl1_inner = stub_py2.class1_py2.class1_inner_py2()
		self.assertEqual(7, cl1_inner.inner_static_meth_py2(66.1, 'efg'))
		self.assertRaises(InputTypeError, lambda: cl1_inner.inner_static_meth_py2(66, ('efg',)))
		self.assertEqual(hints, get_type_hints(cl1_inner.inner_static_meth_py2))

		# Test classmethod:
		self.assertEqual(462.0, stub_py2.class1_py2.class_meth_py2('ghi', 77))
		self.assertRaises(InputTypeError, lambda: stub_py2.class1_py2.class_meth_py2(99, 77))

		# Test subclass and class-typed parameter:
		cl2 = stub_py2.class2_py2()
		hints = get_type_hints(cl2.meth2b_py2)
		self.assertEqual(hints['b'], stub_py2.class1_py2)
		self.assertTrue(cl2.meth2b_py2(cl1).startswith(
				'<pytypes.tests.testhelpers.stub_testhelper_py2.class1_py2'))
		self.assertRaises(InputTypeError, lambda: cl2.meth2b_py2('cl1'))


	@unittest.skipUnless(sys.version_info.major >= 3 and sys.version_info.minor >= 5,
		'Only applicable in Python >= 3.5.')
	def test_plain_3_5_stub(self):
		from pytypes.tests.testhelpers import stub_testhelper as stub_py3

		# Test function:
		self.assertEqual(stub_py3.testfunc1(1, 7), 'testfunc1_1 -- 7')
		self.assertRaises(InputTypeError, lambda: stub_py3.testfunc1(1, '7'))
		hints = get_type_hints(stub_py3.testfunc1)
		self.assertEqual(hints['a'], int)
		self.assertEqual(hints['b'], Real)
		self.assertEqual(hints['return'], str)

		# Test method:
		cl1 = stub_py3.class1()
		self.assertEqual(cl1.meth1(0.76, 'abc'), 'abc----0.76')
		self.assertRaises(InputTypeError, lambda: cl1.meth1('0.76', 'abc'))
		hints = get_type_hints(cl1.meth1)
		self.assertEqual(hints['a'], float)
		self.assertEqual(hints['b'], str)
		self.assertEqual(hints['return'], str)
		self.assertRaises(ReturnTypeError, lambda: cl1.meth2(4.9, 'cde'))

		# Test method of nested class:
		cl1b = cl1.class1_inner()
		cl1b.inner_meth1(3.4, 'inn')
		self.assertRaises(InputTypeError, lambda: cl1b.inner_meth1('3', 'in2'))

		# Test static method:
		self.assertEqual(5, stub_py3.class1.static_meth(66, 'efg'))
		self.assertRaises(InputTypeError, lambda: stub_py3.class1.static_meth(66, ('efg',)))
		hints = get_type_hints(stub_py3.class1.static_meth)
		self.assertEqual(hints['c'], str)
		self.assertEqual(hints['d'], Any)
		self.assertEqual(hints['return'], int)

		# Test static method on instance:
		self.assertEqual(5, cl1.static_meth(66, 'efg'))
		self.assertRaises(InputTypeError, lambda: cl1.static_meth(66, ('efg',)))
		hints = get_type_hints(cl1.static_meth)
		self.assertEqual(hints['c'], str)
		self.assertEqual(hints['d'], Any)
		self.assertEqual(hints['return'], int)

		# Test staticmethod with nested classes/instances:
		self.assertEqual(7,
				stub_py3.class1.class1_inner.inner_static_meth(66.1, 'efg'))
		self.assertRaises(InputTypeError,
				lambda: stub_py3.class1.class1_inner.inner_static_meth(66, ('efg',)))
		hints = get_type_hints(stub_py3.class1.class1_inner.inner_static_meth)
		self.assertEqual(hints['c'], str)
		self.assertEqual(hints['d'], float)
		self.assertEqual(hints['return'], int)
		self.assertEqual(7, cl1.class1_inner.inner_static_meth(66.1, 'efg'))
		self.assertRaises(InputTypeError,
				lambda: cl1.class1_inner.inner_static_meth(66, ('efg',)))
		self.assertEqual(hints, get_type_hints(cl1.class1_inner.inner_static_meth))
		cl1_inner = stub_py3.class1.class1_inner()
		self.assertEqual(7, cl1_inner.inner_static_meth(66.1, 'efg'))
		self.assertRaises(InputTypeError, lambda: cl1_inner.inner_static_meth(66, ('efg',)))
		self.assertEqual(hints, get_type_hints(cl1_inner.inner_static_meth))

		# Test classmethod:
		self.assertEqual(277.2, stub_py3.class1.class_meth('ghi', 77))
		self.assertRaises(InputTypeError, lambda: stub_py3.class1.class_meth(99, 77))

		# Test subclass and class-typed parameter:
		cl2 = stub_py3.class2()
		hints = get_type_hints(cl2.meth2b)
		self.assertEqual(hints['b'], stub_py3.class1)
		self.assertTrue(cl2.meth2b(cl1).startswith(
				'<pytypes.tests.testhelpers.stub_testhelper.class1 object at '))
		self.assertRaises(InputTypeError, lambda: cl2.meth2b('cl1'))


@unittest.skipUnless(sys.version_info.major >= 3 and sys.version_info.minor >= 5,
		'Only applicable in Python >= 3.5.')
class TestTypecheck_Python3_5(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		global py3
		from pytypes.tests.testhelpers import typechecker_testhelper_py3 as py3

	def test_function_py3(self):
		self.assertEqual(py3.testfunc(3, 2.5, 'abcd'), (9, 7.5))
		self.assertEqual(py3.testfunc(7, 12.5, c='cdef'), (49, 87.5))
		self.assertRaises(InputTypeError, lambda: py3.testfunc('string', 2.5, 'abcd'))
		tc = py3.testClass('efgh')
		self.assertEqual(py3.testfunc2(12, 3.5, tc), (144, 42.0))
		self.assertRaises(InputTypeError, lambda: py3.testfunc2(12, 2.5, 'abcd'))
		self.assertRaises(ReturnTypeError, lambda: py3.testfunc_err(12, 2.5, 'abcd'))
		self.assertIsNone(py3.testfunc_None_ret(2, 3.0))
		self.assertEqual(py3.testfunc_None_arg(4, None), 16)
		self.assertRaises(InputTypeError, lambda: py3.testfunc_None_arg(4, 'vvv'))
		self.assertRaises(ReturnTypeError, lambda: py3.testfunc_None_ret_err(2, 3.0))

	def test_classmethod_py3(self):
		tc = py3.testClass('efgh')
		self.assertEqual(tc.testmeth_class(23, 1.1),
				"23-1.1-<class 'pytypes.tests.testhelpers.typechecker_testhelper_py3.testClass'>")
		self.assertRaises(InputTypeError, lambda: tc.testmeth_class(23, '1.1'))
		self.assertEqual(tc.testmeth_class2(23, 1.1),
				"23-1.1-<class 'pytypes.tests.testhelpers.typechecker_testhelper_py3.testClass'>")
		self.assertRaises(InputTypeError, lambda: tc.testmeth_class2(23, '1.1'))
		self.assertRaises(ReturnTypeError, lambda: tc.testmeth_class2_err(23, 1.1))

	def test_method_py3(self):
		tc2 = py3.testClass2('ijkl')
		self.assertEqual(tc2.testmeth(1, 2.5), '1-2.5-ijkl')
		self.assertRaises(InputTypeError, lambda: tc2.testmeth(1, 2.5, 7))
		self.assertRaises(ReturnTypeError, lambda: tc2.testmeth_err(1, 2.5))

	def test_method_forward_py3(self):
		tc = py3.testClass('ijkl2')
		tc2 = py3.testClass2('ijkl3')
		self.assertEqual(tc.testmeth_forward(5, tc2), 11)
		self.assertEqual(typing.get_type_hints(tc.testmeth_forward), get_type_hints(tc.testmeth_forward))
		self.assertRaises(InputTypeError, lambda: tc.testmeth_forward(5, 7))
		self.assertRaises(InputTypeError, lambda: tc.testmeth_forward(5, tc))

	def test_staticmethod_py3(self):
		tc = py3.testClass('efgh')
		self.assertEqual(tc.testmeth_static(12, 0.7), '12-0.7-static')
		self.assertRaises(InputTypeError, lambda: tc.testmeth_static(12, [3]))
		self.assertEqual(tc.testmeth_static2(11, 1.9), '11-1.9-static')
		self.assertRaises(InputTypeError, lambda: tc.testmeth_static2(11, ('a', 'b'), 1.9))

	def test_abstract_override_py3(self):
		tc3 = py3.testClass3()
		self.assertEqual(tc3.testmeth(1, 2.5),
				"1-2.5-<class 'pytypes.tests.testhelpers.typechecker_testhelper_py3.testClass3'>")

	def test_get_types_py3(self):
		tc = py3.testClass('mnop')
		tc2 = py3.testClass2('qrst')
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

	def test_sequence_py3(self):
		self.assertEqual(py3.testfunc_Seq_arg(((3, 'ab'), (8, 'qvw'))), 2)
		self.assertEqual(py3.testfunc_Seq_arg([(3, 'ab'), (8, 'qvw'), (4, 'cd')]), 3)
		self.assertRaises(InputTypeError, lambda: py3.testfunc_Seq_arg({(3, 'ab'), (8, 'qvw')}))
		self.assertRaises(InputTypeError, lambda: py3.testfunc_Seq_arg(((3, 'ab'), (8, 'qvw', 2))))
		self.assertRaises(InputTypeError, lambda: py3.testfunc_Seq_arg([(3, 1), (8, 'qvw'), (4, 'cd')]))
		self.assertEqual(py3.testfunc_Seq_ret_List(7, 'mno'), [7, 'mno'])
		self.assertEqual(py3.testfunc_Seq_ret_Tuple(3, 'mno'), (3, 'mno'))
		self.assertRaises(ReturnTypeError, lambda: py3.testfunc_Seq_ret_err(29, 'def'))

	def test_iterable_py3(self):
		self.assertEqual(py3.testfunc_Iter_arg((9, 8, 7, 6), 'vwxy'), [9, 8, 7, 6])
		self.assertEqual(py3.testfunc_Iter_str_arg('defg'), [100, 101, 102, 103])
		self.assertRaises(InputTypeError, lambda: py3.testfunc_Iter_arg((9, '8', 7, 6), 'vwxy'))
		self.assertRaises(InputTypeError, lambda: py3.testfunc_Iter_arg(7, 'vwxy'))
		self.assertRaises(InputTypeError, lambda: py3.testfunc_Iter_arg([9, 8, 7, '6'], 'vwxy'))
		self.assertEqual(py3.testfunc_Iter_arg([9, 8, 7, 6], 'vwxy'), [9, 8, 7, 6])
		res = py3.testfunc_Iter_arg({9, 8, 7, 6}, 'vwxy'); res.sort()
		self.assertEqual(res, [6, 7, 8, 9])
		res = py3.testfunc_Iter_arg({19: 'a', 18: 'b', 17: 'c', 16: 'd'}, 'vwxy'); res.sort()
		self.assertEqual(res, [16, 17, 18, 19])
		self.assertEqual(py3.testfunc_Iter_ret(), [1, 2, 3, 4, 5])
		self.assertRaises(ReturnTypeError, lambda: py3.testfunc_Iter_ret_err())
		ti = py3.test_iterable((2, 4, 6))
		self.assertRaises(InputTypeError, lambda: py3.testfunc_Iter_arg(ti, 'vwxy'))
		tia = py3.test_iterable_annotated((3, 6, 9))
		self.assertEqual(py3.testfunc_Iter_arg(tia, 'vwxy'), [3, 6, 9])

	def test_dict_py3(self):
		self.assertIsNone(py3.testfunc_Dict_arg(5, {'5': 4, 'c': '8'}))
		self.assertIsNone(py3.testfunc_Dict_arg(5, {'5': 'A', 'c': '8'}))
		self.assertIsNone(py3.testfunc_Mapping_arg(7, {'7': 4, 'c': '8'}))
		self.assertIsNone(py3.testfunc_Mapping_arg(5, {'5': 'A', 'c': '8'}))
		self.assertRaises(InputTypeError, lambda: py3.testfunc_Dict_arg(5, {4: 4, 3: '8'}))
		self.assertRaises(InputTypeError, lambda: py3.testfunc_Dict_arg(5, {'5': (4,), 'c': '8'}))
		self.assertEqual(py3.testfunc_Dict_ret('defg'), {'defgdefg': 'defg', 'defg': 4})
		self.assertRaises(ReturnTypeError, lambda: py3.testfunc_Dict_ret_err(6))

	def test_callable_py3(self):
		self.assertTrue(pytypes.is_of_type(py3.pclb, typing.Callable[[str, int], str]))
		self.assertFalse(pytypes.is_of_type(py3.pclb, typing.Callable[[str, str], str]))
		self.assertFalse(pytypes.is_of_type(py3.pclb, typing.Callable[[str, int], float]))

		self.assertEqual(py3.testfunc_Callable_arg(py3.pclb, 'pqrs'), '_pqrs****')
		self.assertRaises(InputTypeError, lambda: py3.testfunc_Callable_arg(py3.pclb2, 'pqrs'))
		self.assertRaises(InputTypeError, lambda: py3.testfunc_Callable_arg(py3.pclb3, 'pqrs'))
		self.assertRaises(InputTypeError, lambda: py3.testfunc_Callable_call_err(py3.pclb, 'tuvw'))
		self.assertEqual(py3.testfunc_Callable_arg(lambda s, i: '__'+s+'-'*i, 'pqrs'), '__pqrs----')
		self.assertRaises(InputTypeError,
				lambda: py3.testfunc_Callable_call_err(lambda s, i: '__'+s+'-'*i, 'tuvw'))
		fnc = py3.testfunc_Callable_ret(5, 'qvwx')
		self.assertEqual(fnc.__class__.__name__, 'function')
		self.assertEqual(fnc.__name__, 'm')
		self.assertRaises(ReturnTypeError, lambda: py3.testfunc_Callable_ret_err())

	def test_generator_py3(self):
		test_gen = py3.testfunc_Generator()
		self.assertIsNone(test_gen.send(None))
		self.assertEqual(test_gen.send('abc'), 3)
		self.assertEqual(test_gen.send('ddffd'), 5)
		self.assertRaises(InputTypeError, lambda: test_gen.send(7))
		test_gen2 = py3.testfunc_Generator()
		self.assertIsNone(test_gen2.__next__())
		self.assertEqual(test_gen2.send('defg'), 4)
		self.assertRaises(ReturnTypeError, lambda: test_gen2.send('fail'))
		self.assertRaises(TypeCheckError, lambda: testfunc_Generator_arg(test_gen))
		self.assertRaises(TypeCheckError, lambda: testfunc_Generator_ret())
		test_gen3 = py3.testfunc_Generator()
		self.assertIsNone(test_gen3.send(None))
		self.assertEqual(test_gen3.send('abcxyz'), 6)
		with warnings.catch_warnings():
			warnings.simplefilter('ignore')
			# Causes deprecation warning:
			self.assertRaises(StopIteration, lambda: test_gen3.send('ret'))
		test_gen4 = py3.testfunc_Generator()
		self.assertIsNone(test_gen4.send(None))
		self.assertEqual(test_gen4.send('abcdefgh'), 8)
		self.assertRaises(ReturnTypeError, lambda: test_gen4.send('ret_fail'))

	def test_custom_generic_py3(self):
		self.assertEqual(py3.testfunc_Generic_arg(py3.Custom_Generic[str]('abc')), 'abc')
		self.assertEqual(py3.testfunc_Generic_ret(5).v(), 5)
		self.assertRaises(InputTypeError, lambda: py3.testfunc_Generic_arg(py3.Custom_Generic[int](9)))
		self.assertRaises(InputTypeError, lambda: py3.testfunc_Generic_arg(py3.Custom_Generic(7)))
		self.assertRaises(ReturnTypeError, lambda: py3.testfunc_Generic_ret_err(8))

	def test_various_py3(self):
		self.assertEqual(get_type_hints(testfunc),
				{'a': int, 'c': str, 'b': Real, 'return': Tuple[int, Real]})
		self.assertEqual(pytypes.deep_type(('abc', [3, 'a', 7], 4.5)),
				Tuple[str, List[Union[int, str]], float])


@unittest.skipUnless(sys.version_info.major >= 3 and sys.version_info.minor >= 5,
		'Only applicable in Python >= 3.5.')
class TestOverride_Python3_5(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		global py3
		from pytypes.tests.testhelpers import typechecker_testhelper_py3 as py3

	def test_override_py3(self):
		tc2 = py3.testClass2('uvwx')
		self.assertRaises(OverrideError, lambda: tc2.testmeth2(1, 2.5))
		self.assertRaises(OverrideError, lambda: tc2.testmeth2b(3, 1.1))
		self.assertRaises(OverrideError, lambda: tc2.testmeth6(1, 2.5))

	def test_override_typecheck(self):
		tc2 = py3.testClass2('uvwx')
		self.assertEqual(tc2.testmeth(1, 2.5), '1-2.5-uvwx')
		self.assertEqual(tc2.testmeth3(1, 2.5), '1-2.5-uvwx')
		self.assertRaises(ReturnTypeError, lambda: tc2.testmeth3_err(1, 2.5))
		self.assertEqual(tc2.testmeth4(1, 2.5), '1-2.5-uvwx')
		self.assertEqual(tc2.testmeth5(1, 2.5), '1-2.5-uvwx')
		self.assertRaises(InputTypeError, lambda: tc2.testmeth3('1', 2.5))

	def test_override_at_definition_time(self):
		tmp = pytypes.check_override_at_class_definition_time
		pytypes.check_override_at_class_definition_time = True
		py3.testClass2_defTimeCheck()
		self.assertRaises(OverrideError, lambda: py3.testClass2_defTimeCheck2())
		self.assertRaises(OverrideError, lambda: py3.testClass2_defTimeCheck3())
		self.assertRaises(OverrideError, lambda: py3.testClass2_defTimeCheck4())
		py3.testClass3_defTimeCheck()
		pytypes.check_override_at_class_definition_time = tmp

	def test_override_at_definition_time_with_forward_decl(self):
		tmp = pytypes.check_override_at_class_definition_time
		pytypes.check_override_at_class_definition_time = True
		from pytypes.tests.testhelpers import override_testhelper_py3 # shall not raise error
		def _test_err_py3():
			from pytypes.tests.testhelpers import override_testhelper_err_py3
		def _test_err2_py3():
			from pytypes.tests.testhelpers import override_testhelper_err2_py3

		self.assertRaises(OverrideError, _test_err_py3)
		self.assertRaises(NameError, _test_err2_py3)

		pytypes.check_override_at_class_definition_time = tmp

if __name__ == '__main__':
	unittest.main()

#print (pytypes.type_util._issubclass(Tuple[str, float], tuple))
# should be false, because former type is more specialized
# todo: same for list etc
