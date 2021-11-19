# Copyright 2017, 2018, 2021 Stefan Richthofer
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Created on 25.08.2016

import abc
import sys
import unittest
import warnings
import collections
from abc import abstractmethod
from numbers import Real
import pytypes
from pytypes import typechecked, override, auto_override, no_type_check, get_types, \
    get_type_hints, TypeCheckError, InputTypeError, ReturnTypeError, OverrideError, \
    TypeSyntaxError, check_argument_types, annotations, get_member_types, resolve_fw_decl, \
    TypeChecker, restore_profiler, is_subtype, is_of_type, type_bases
    
pytypes.clean_traceback = False
import typing
from typing import Tuple, List, Union, Any, Dict, Generator, TypeVar, Generic, Iterable, \
    Iterator, Sequence, Callable, Mapping, Set, Optional, \
    T_co, V_co, VT_co, T_contra, KT, T, VT

pytypes.check_override_at_class_definition_time = False
pytypes.check_override_at_runtime = True
pytypes.always_check_parent_types = False


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

class testClass3_no_override(testClass3Base):
    @typechecked
    def testmeth(self, a, b):
        return '-'.join((str(a), str(b), str(type(self))))

class testClass3_no_override_err(testClass3Base):
    @typechecked
    def testmeth(self, a, b):
        return 7.5

class testClass3_no_override_check_argtypes(testClass3Base):
    def testmeth(self, a, b):
        check_argument_types()
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
    def testmeth_static2(a, q):
        # type: (int, Real) -> str
        return '-'.join((str(a), str(q), 'static'))


class testClass5_base(object):
    def testmeth_cls5(self, a, b):
        # type: (int, Real) -> str
        return 'Dummy implementation 5'


@typechecked
class testClass5(testClass5_base):
    @override
    def testmeth_cls5(self, a, b):
        return '-'.join((str(a), str(b)))

    def testmeth2_cls5(self, a, b):
        return '-'.join((str(a), str(b)))


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

@typechecked
def testfunc_numeric_tower_float(x):
    # type: (float) -> str
    return str(x)

@typechecked
def testfunc_numeric_tower_complex(x):
    # type: (complex) -> str
    return str(x)

@typechecked
def testfunc_numeric_tower_tuple(x):
    # type: (Tuple[float, str]) -> str
    return str(x)

@typechecked
def testfunc_numeric_tower_return(x):
    # type: (str) -> float
    return len(x)

@typechecked
def testfunc_numeric_tower_return_err(x):
    # type: (str) -> int
    return len(x)*1.5

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


class testClass_check_argument_types(object):

    def testMeth_check_argument_types(self, a):
        # type: (int) -> None
        check_argument_types()

    @classmethod
    def testClassmeth_check_argument_types(cls, a):
        # type: (int) -> None
        check_argument_types()

    @staticmethod
    def testStaticmeth_check_argument_types(a):
        # type: (int) -> None
        check_argument_types()

def testfunc_check_argument_types(a, b, c):
    # type: (int, float, str) -> None
    check_argument_types()

def testfunc_check_argument_types2(a):
    # type: (Sequence[float]) -> None
    check_argument_types()

def testfunc_check_argument_types_empty():
    # type: () -> None
    check_argument_types()


class testClass_property(object):

    @typechecked
    @property
    def testprop(self):
        # type: () -> int
        return self._testprop

    @typechecked
    @testprop.setter
    def testprop(self, value):
        # type: (int) -> None
        self._testprop = value

    @typechecked
    @property
    def testprop2(self):
        # type: () -> str
        return self._testprop2

    @testprop2.setter
    def testprop2(self, value):
        # type: (str) -> None
        self._testprop2 = value

    @typechecked
    @property
    def testprop3(self):
        # type: () -> Tuple[int, str]
        return self._testprop3

    @testprop3.setter
    def testprop3(self, value):
        # type: (Tuple[int, str]) -> None
        check_argument_types()
        self._testprop3 = value


@typechecked
class testClass_property_class_check(object):
    @property
    def testprop(self):
        # type: () -> int
        return self._testprop

    @testprop.setter
    def testprop(self, value):
        # type: (int) -> None
        self._testprop = value

    @property
    def testprop2(self):
        # type: () -> float
        return 'abc'

    @testprop2.setter
    def testprop2(self, value):
        # type: (float) -> None
        pass


def testfunc_custom_annotations_plain(a, b):
    # type: (str, float) -> float
    check_argument_types()
    return len(a)/float(b)

def testfunc_custom_annotations(a, b):
    check_argument_types()
    return len(a)/float(b)
testfunc_custom_annotations.__annotations__ = {'a': str, 'b': float, 'return': float}

@typechecked
def testfunc_custom_annotations_typechecked(a, b):
    return len(a)/float(b)
testfunc_custom_annotations_typechecked.__annotations__ = \
        {'a': str, 'b': int, 'return': float}

@typechecked
def testfunc_custom_annotations_typechecked_err(a, b):
    return a+str(b)
testfunc_custom_annotations_typechecked_err.__annotations__ = \
        {'a': str, 'b': float, 'return': int}

@annotations
def testfunc_annotations_from_tpstring_by_decorator(a, b):
    # type: (str, int) -> int
    return len(a)/b

def testfunc_annotations_from_tpstring(a, b):
    # type: (str, int) -> int
    return len(a)/b


@typechecked
def testfunc_varargs1(*argss):
    # type: (*float) -> Tuple[int, float]
    res = 1.0
    for arg in argss:
        res *= arg
    return len(argss), res

@typechecked
def testfunc_varargs2(a, b, c, *varg):
    # type: (str, int, None, *int) -> Tuple[int, str]
    res = 1
    for arg in varg:
        res *= arg
    return res, a*b

@typechecked
def testfunc_varargs3(*args, **kwds):
    # type: (*int, **float) -> Tuple[str, float]
    longest = ''
    for key in kwds:
        if len(key) > len(longest):
            longest = key
    return longest*(args[0]//len(args)), \
            0 if longest == '' else kwds[longest]

@typechecked
def testfunc_varargs4(**kwds):
    # type: (**float) -> float
    longest = ''
    for key in kwds:
        if len(key) > len(longest):
            longest = key
    return 0 if longest == '' else kwds[longest]

@typechecked
def testfunc_varargs5(a1, a2, *vargss, **vkwds):
    # type: (int, str, *float, **int) -> List[int]
    return [len(vargss), len(str(vargss[a1])), vkwds[a2]]

@typechecked
def testfunc_varargs_err(a1, a2, *vargss, **vkwds):
    # type: (int, str, *float, **int) -> List[int]
    return [len(vargss), str(vargss[a1]), vkwds[a2]]

@typechecked
class testclass_vararg(object):
    def testmeth_varargs1(self, *vargs):
        # type: (*Tuple[str, int]) -> int
        res = 1
        for arg in vargs:
            res += len(arg[0])*arg[1]
        return res-len(self.__class__.__name__)

    def testmeth_varargs2(self, q1, q2, *varargs, **varkw):
        # type: (int, str, *float, **int) -> List[int]
        return [len(varargs), len(str(varargs[q1])), varkw[q2],
                len(self.__class__.__name__)]
    
    @staticmethod
    def testmeth_varargs_static1(*vargs_st):
        # type: (*float) -> Tuple[int, float]
        res = 1.0
        for arg in vargs_st:
            res *= arg
        return len(vargs_st), res

    @staticmethod
    def testmeth_varargs_static2(q1_st, q2_st, *varargs_st, **varkw_st):
        # type: (int, str, *float, **int) -> List[int]
        return [len(varargs_st), len(str(varargs_st[q1_st])), varkw_st[q2_st]]

    @classmethod
    def testmeth_varargs_class1(cls, *vargs_cls):
        # type: (*Tuple[str, int]) -> int
        res = 1
        for arg in vargs_cls:
            res += len(arg[0])*arg[1]
        return res-len(cls.__name__)

    @classmethod
    def testmeth_varargs_class2(cls, q1_cls, q2_cls, *varargs_cls, **varkw_cls):
        # type: (int, str, *float, **int) -> List[int]
        return [len(varargs_cls), len(str(varargs_cls[q1_cls])),
                varkw_cls[q2_cls], len(cls.__name__)]

    @property
    def prop1(self):
        # type: () -> str
        return self._prop1

    @prop1.setter
    def prop1(self, *vargs_prop):
        # type: (*str) -> None
        self._prop1 = vargs_prop[0]

def testfunc_varargs_ca1(*argss):
    # type: (*float) -> Tuple[int, float]
    check_argument_types()
    res = 1.0
    for arg in argss:
        res *= arg
    return len(argss), res

def testfunc_varargs_ca2(a, b, c, *varg):
    # type: (str, int, None, *int) -> Tuple[int, str]
    check_argument_types()
    res = 1
    for arg in varg:
        res *= arg
    return res, a*b

def testfunc_varargs_ca3(*args, **kwds):
    # type: (*int, **float) -> Tuple[str, float]
    check_argument_types()
    longest = ''
    for key in kwds:
        if len(key) > len(longest):
            longest = key
    return longest*(args[0]//len(args)), kwds[longest]

def testfunc_varargs_ca4(**kwds):
    # type: (**float) -> float
    check_argument_types()
    longest = ''
    for key in kwds:
        if len(key) > len(longest):
            longest = key
    return 0 if longest == '' else kwds[longest]

def testfunc_varargs_ca5(a1, a2, *vargss, **vkwds):
    # type: (int, str, *float, **int) -> List[int]
    check_argument_types()
    return [len(vargss), len(str(vargss[a1])), vkwds[a2]]

class testclass_vararg_ca(object):
    def testmeth_varargs_ca1(self, *vargs):
        # type: (*Tuple[str, int]) -> int
        check_argument_types()
        res = 1
        for arg in vargs:
            res += len(arg[0])*arg[1]
        return res-len(self.__class__.__name__)

    def testmeth_varargs_ca2(self, q1, q2, *varargs, **varkw):
        # type: (int, str, *float, **int) -> List[int]
        check_argument_types()
        return [len(varargs), len(str(varargs[q1])), varkw[q2],
                len(self.__class__.__name__)]
    
    @staticmethod
    def testmeth_varargs_static_ca1(*vargs_st):
        # type: (*float) -> Tuple[int, float]
        check_argument_types()
        res = 1.0
        for arg in vargs_st:
            res *= arg
        return len(vargs_st), res

    @staticmethod
    def testmeth_varargs_static_ca2(q1_st, q2_st, *varargs_st, **varkw_st):
        # type: (int, str, *float, **int) -> List[int]
        check_argument_types()
        return [len(varargs_st), len(str(varargs_st[q1_st])), varkw_st[q2_st]]

    @classmethod
    def testmeth_varargs_class_ca1(cls, *vargs_cls):
        # type: (*Tuple[str, int]) -> int
        check_argument_types()
        res = 1
        for arg in vargs_cls:
            res += len(arg[0])*arg[1]
        return res-len(cls.__name__)

    @classmethod
    def testmeth_varargs_class_ca2(cls, q1_cls, q2_cls, *varargs_cls, **varkw_cls):
        # type: (int, str, *float, **int) -> List[int]
        check_argument_types()
        return [len(varargs_cls), len(str(varargs_cls[q1_cls])),
                varkw_cls[q2_cls], len(cls.__name__)]

    @property
    def prop_ca1(self):
        # type: () -> str
        check_argument_types()
        return self._prop_ca1

    @prop_ca1.setter
    def prop_ca1(self, *vargs_prop):
        # type: (*str) -> None
        check_argument_types()
        self._prop_ca1 = vargs_prop[0]


@typechecked
def func_defaults_typecheck(a, b, c=4, d=2.5):
    # type: (str) -> str
    try:
        return a+b*c
    except TypeError:
        return 'invalid'

@typechecked
def func_defaults_typecheck2(a, b, c=1, d=False):
    # type: (str, float, Optional[int], bool) -> str
    try:
        return a+str(b*c)+str(d)
    except TypeError:
        return 'invalid'

def func_defaults_checkargs(a, b, c=4, d=2.5):
    # type: (str) -> str
    check_argument_types()
    try:
        return a+b*c
    except TypeError:
        return 'invalid'

@annotations
def func_defaults_annotations(a, b, c=4):
    # type: (str) -> str
    b = 'abc'
    return a+b*c


class override_varargs_class_base(object):
# var-arg tests:
    def method_vararg1(self, a, b, *args):
        # type: (int, int, *int) -> int
        return a+b

    def method_vararg2(self, a, b):
        # type: (int, int) -> int
        return a+b

    def method_vararg3(self, a, b, c):
        # type: (int, int, float) -> int
        return a+b

    def method_vararg1_err(self, a, b, *args):
        # type: (int, int, *float) -> int
        return a+b

    def method_vararg2_err(self, a, b):
        # type: (float, int) -> int
        return a+b

    def method_vararg3_err(self, a, b, c):
        # type: (int, int, float) -> int
        return a+b

# var-kw tests:
    def method_varkw1(self, a, b, **kw):
        # type: (int, int, **int) -> int
        return a+b

    def method_varkw2(self, a, b, *arg, **kw):
        # type: (int, int, *str, **int) -> int
        return a+b

    def method_varkw1_err(self, a, b, **kw):
        # type: (int, int, **float) -> int
        return a+b

    def method_varkw2_err(self, a, b, *arg, **kw):
        # type: (int, int, *str, **float) -> int
        return a+b

    def method_varkw3_err(self, a, b, *arg, **kw):
        # type: (int, int, *str, **str) -> int
        return a+b

# default tests:
    def method_defaults1(self, a, b):
        # type: (int, int) -> int
        return a+b

    def method_defaults2(self, a, b, *vargs):
        # type: (int, int, *int) -> int
        return a+b

    def method_defaults1_err(self, a, b):
        # type: (int, float) -> int
        return a+b

    def method_defaults2_err(self, a, b, *vargs):
        # type: (int, int, *float) -> int
        return a+b

class override_varargs_class(override_varargs_class_base):
    @override
    def method_vararg1(self, a, b, *args):
        # type: (int, float, *int) -> int
        return len(args)

    @override
    def method_vararg2(self, a, b, *vargs):
        # type: (int, float, *str) -> int
        return a+len(str(b))+len(vargs)

    @override
    def method_vararg3(self, a, *vgs):
        # type: (int, *float) -> int
        return a+len(vgs)

    @override
    def method_vararg1_err(self, a, b, *args):
        # type: (int, float, *int) -> int
        return len(args)

    @override
    def method_vararg2_err(self, a, b, *vargs):
        # type: (int, float, *str) -> int
        return a+len(str(b))+len(vargs)

    @override
    def method_vararg3_err(self, a, *vgs):
        # type: (int, *int) -> int
        return a+len(vgs)

# var-kw tests:
    @override
    def method_varkw1(self, a, b, **kw):
        # type: (int, int, **float) -> int
        return a+b

    @override
    def method_varkw2(self, a, b, *arg, **kw):
        # type: (int, int, *str, **float) -> int
        return a+b

    @override
    def method_varkw1_err(self, a, b, **kw):
        # type: (int, int, **int) -> int
        return a+b

    @override
    def method_varkw2_err(self, a, b, *arg, **kw):
        # type: (int, int, *str, **int) -> int
        return a+b

    @override
    def method_varkw3_err(self, a, b, *arg):
        # type: (int, int, *str) -> int
        return a+b

# default tests:
    @override
    def method_defaults1(self, a, b, c=4.6):
        # type: (int, int) -> int
        return a+b

    @override
    def method_defaults2(self, a, b, c=4, *args):
        # type: (int, int, float, *int) -> int
        return a+b

    @override
    def method_defaults1_err(self, a, b, c=2):
        # type: (int, int) -> int
        return a+b

    @override
    def method_defaults2_err(self, a, b, c=3, *vargs):
        # type: (int, int, int, *float) -> int
        return a+b


class varagrs_call_class_base(object):
    def testmeth1(self, a, b):
        # type: (int, float) -> float
        return a+b

    def testmeth2(self, a, b):
        # type: (int, float) -> float
        return a+b

    def testmeth3(self, a, b):
        # type: (int, float) -> float
        return a+b

    def testmeth4(self, a, b):
        # type: (int, float) -> float
        return a+b

@typechecked
class varagrs_call_class(varagrs_call_class_base):
    
    @override
    def testmeth1(self, a, b, *vargs):
        return a+b

    @override
    def testmeth2(self, a, b, **kw):
        return a+b

    @override
    def testmeth3(self, a, b, *args, **kwords):
        return a+b

    @override
    def testmeth4(self, a, b, c, *varargs):
        return a+b


def func_bad_typestring1(a, b, c):
    # type: (int, *int, float) -> None
    pass

def func_bad_typestring2(a, b, c):
    # type: (int, int, **float) -> None
    pass

def func_bad_typestring3(a, b, *c):
    # type: (int, *int, *float) -> None
    pass

def func_bad_typestring4(a, b, *c):
    # type: (int, **int, **float) -> None
    pass

def func_bad_typestring5(a, *b, **c):
    # type: (int, *int, float) -> None
    pass

def func_bad_typestring6(a, b, *c):
    # type: (int, int, float) -> None
    pass

def func_bad_typestring7(a, b, **c):
    # type: (int, int, float) -> None
    pass

def func_bad_typestring8(a, *b, **c):
    # type: (int, int, float) -> None
    pass

def func_bad_typestring9(a, b, *c):
    # type: (int, *int, float) -> None
    pass

def func_bad_typestring10(a, *b, **c):
    # type: (int, **int, *float) -> None
    pass


class A_check_parent_types(object):
    def meth1(self, a):
        # type: (int) -> int
        return len(str(a))

class B_override_check_arg(A_check_parent_types):
    @override
    def meth1(self, a):
        check_argument_types()
        return len(str(a))

class B_no_override_check_arg(A_check_parent_types):
    def meth1(self, a):
        check_argument_types()
        return len(str(a))

class B_override_typechecked(A_check_parent_types):
    @typechecked
    @override
    def meth1(self, a):
        check_argument_types()
        return len(str(a))

class B_no_override_typechecked(A_check_parent_types):
    @typechecked
    def meth1(self, a):
        check_argument_types()
        return len(str(a))

class B_override_with_type_check_arg(A_check_parent_types):
    @override
    def meth1(self, a):
        # type: (float) -> int
        check_argument_types()
        return len(str(a))

class B_override_with_type_typechecked(A_check_parent_types):
    @typechecked
    @override
    def meth1(self, a):
        # type: (float) -> int
        check_argument_types()
        return len(str(a))


class A_diamond_override(object):
    def meth1(self, a):
        # type: (Tuple[int, int]) -> int
        return len(str(a))

class B_diamond_override(A_diamond_override):
    @override
    def meth1(self, a):
        # type: (Tuple[int, float]) -> int
        return len(str(a))

class C_diamond_override(A_diamond_override):
    @override
    def meth1(self, a):
        # type: (Tuple[float, int]) -> int
        return len(str(a))

class D_diamond_override(B_diamond_override, C_diamond_override):
    @override
    def meth1(self, a):
        # type: (Tuple[float, float]) -> int
        check_argument_types()
        return len(str(a))

class D_diamond_override_err1(B_diamond_override, C_diamond_override):
    @override
    def meth1(self, a):
        # type: (Tuple[float, int]) -> int
        return len(str(a))

class D_diamond_override_err2(B_diamond_override, C_diamond_override):
    @override
    def meth1(self, a):
        # type: (Tuple[int, float]) -> int
        return len(str(a))

class D_diamond_override_err3(B_diamond_override, C_diamond_override):
    @override
    def meth1(self, a):
        # type: (Tuple[int, int]) -> int
        return len(str(a))


class A_auto_override(object):
    def meth_1(self, a, b):
        # type: (str, Tuple[int, float]) -> int
        pass

@auto_override
class B_auto_override(A_auto_override):
    def meth_1(self, a, b):
        # type: (str, Tuple[float, float]) -> int
        return len(str(len(a)+b[0]-b[1]))

    def meth_2(self, c):
        # type: (str) -> int
        return 3*len(c)

@auto_override
class B_auto_override_err(A_auto_override):
    def meth_1(self, a, b):
        # type: (str, Tuple[int, int]) -> int
        return len(str(len(a)+b[0]-b[1]))

    def meth_2(self, c):
        # type: (str) -> int
        return 3*len(c)


@typechecked
class GetAttrDictWrapper(object):
    """Test a plausible use of __getattr__ -
    A class that wraps a dict, enabling the values to be accessed as if they were attributes
    (`d.abc` instead of `d['abc']`)
    For example, the `pyrsistent` library does this on its dict replacement.

    >>> o = GetAttrDictWrapper({'a': 5, 'b': 10})
    >>> o.a
    5
    >>> o.b
    10
    >>> o.nonexistent
    Traceback (most recent call last):
      ...
    AttributeError('nonexistent')
    
    """

    def __init__(self, dct):
        # type: (dict) -> None
        self.__dct = dct

    def __getattr__(self, attr):
        # type: (str) -> typing.Any
        dct = self.__dct # can safely access the attribute because it exists so it won't trigger __getattr__
        try:
            return dct[attr]
        except KeyError:
            raise AttributeError(attr)


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
        self.assertEqual(tc.testmeth_class(23, 1.1),
                "23-1.1-<class '%s.testClass'>"%self.__module__)
        self.assertRaises(InputTypeError, lambda:
                tc.testmeth_class(23, '1.1'))
        self.assertEqual(tc.testmeth_class2(23, 1.1),
                "23-1.1-<class '%s.testClass'>"%self.__module__)
        self.assertRaises(InputTypeError, lambda:
                tc.testmeth_class2(23, '1.1'))
        self.assertRaises(ReturnTypeError, lambda:
                tc.testmeth_class2_err(23, 1.1))

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
        self.assertRaises(InputTypeError, lambda:
                tc.testmeth_static(12, [3]))
        self.assertEqual(tc.testmeth_static2(11, 1.9), '11-1.9-static')
        self.assertRaises(InputTypeError, lambda:
                tc.testmeth_static2(11, ('a', 'b'), 1.9))

    def test_parent_typecheck_no_override(self):
        tmp = pytypes.always_check_parent_types
        pytypes.always_check_parent_types = False
        
        cl3 = testClass3_no_override()
        self.assertTrue(cl3.testmeth(3, 5).startswith('3-5-'))
        self.assertTrue(cl3.testmeth(3, '5').startswith('3-5-'))
        cl3 = testClass3_no_override_err()
        self.assertEqual(cl3.testmeth(3, 5), 7.5)
        self.assertEqual(cl3.testmeth(3, '5'), 7.5)
        cl3 = testClass3_no_override_check_argtypes()
        self.assertTrue(cl3.testmeth(3, 5).startswith('3-5-'))
        self.assertTrue(cl3.testmeth(3, '5').startswith('3-5-'))

        pytypes.always_check_parent_types = True

        cl3 = testClass3_no_override()
        self.assertTrue(cl3.testmeth(3, 5).startswith('3-5-'))
        self.assertRaises(InputTypeError, lambda: cl3.testmeth(3, '5'))
        cl3 = testClass3_no_override_err()
        self.assertRaises(ReturnTypeError, lambda: cl3.testmeth(3, 5))
        self.assertRaises(InputTypeError, lambda: cl3.testmeth(3, '5'))
        cl3 = testClass3_no_override_check_argtypes()
        self.assertTrue(cl3.testmeth(3, 5).startswith('3-5-'))
        self.assertRaises(InputTypeError, lambda: cl3.testmeth(3, '5'))

        pytypes.always_check_parent_types = tmp

    def test_parent_typecheck_other_signature(self):
        vcc = varagrs_call_class()
        self.assertRaises(InputTypeError, lambda: vcc.testmeth1(1, '2', 'a'))
        self.assertEqual(vcc.testmeth1(1, 2, 'a'), 3)
        self.assertRaises(InputTypeError, lambda: vcc.testmeth2('3', 4, q = 'b'))
        self.assertEqual(vcc.testmeth2(3, 4, q = 'b'), 7)
        self.assertRaises(InputTypeError, lambda: vcc.testmeth3(5.7, 6, 'c', k = 'd'))
        self.assertEqual(vcc.testmeth3(5, 6, 'c', k = 'd'), 11)
        self.assertRaises(InputTypeError, lambda: vcc.testmeth4(7, 8, 9, 'e', 'f'))

    def test_abstract_override(self):
        tc3 = testClass3()
        self.assertEqual(tc3.testmeth(1, 2.5),
                "1-2.5-<class '%s.testClass3'>"%self.__module__)

    def test_get_types(self):
        tc = testClass('mnop')
        tc2 = testClass2('qrst')
        tc3 = testClass3()
        self.assertEqual(get_types(testfunc),
                (Tuple[int, Real, str], Tuple[int, Real]))
        self.assertEqual(get_types(testfunc2),
                (Tuple[int, Real, testClass], Tuple[int, float]))
        self.assertEqual(get_types(testfunc4), (Any, Any))
        self.assertEqual(get_types(tc2.testmeth), (Tuple[int, Real], str))
        self.assertEqual(get_types(testClass2.testmeth), (Tuple[int, Real], str))
        self.assertEqual(get_types(tc3.testmeth), (Any, Any))
        self.assertEqual(get_types(testClass3Base.testmeth),
                (Tuple[int, Real], Union[str, int]))
        self.assertEqual(get_types(tc.testmeth2), (Tuple[int, Real], str))
        self.assertEqual(get_types(tc.testmeth_class), (Tuple[int, Real], str))
        self.assertEqual(get_types(tc.testmeth_class2), (Tuple[int, Real], str))
        self.assertEqual(get_types(tc.testmeth_static), (Tuple[int, Real], str))
        self.assertEqual(get_types(tc.testmeth_static2), (Tuple[int, Real], str))
        self.assertEqual(get_types(testfunc),
                (Tuple[int, Real, str], Tuple[int, Real]))

    def test_sequence(self):
        self.assertEqual(testfunc_Seq_arg(((3, 'ab'), (8, 'qvw'))), 2)
        self.assertEqual(testfunc_Seq_arg([(3, 'ab'), (8, 'qvw'), (4, 'cd')]), 3)
        self.assertRaises(InputTypeError, lambda:
                testfunc_Seq_arg({(3, 'ab'), (8, 'qvw')}))
        self.assertRaises(InputTypeError, lambda:
                testfunc_Seq_arg(((3, 'ab'), (8, 'qvw', 2))))
        self.assertRaises(InputTypeError, lambda:
                testfunc_Seq_arg([(3, 1), (8, 'qvw'), (4, 'cd')]))
        self.assertEqual(testfunc_Seq_ret_List(7, 'mno'), [7, 'mno'])
        self.assertEqual(testfunc_Seq_ret_Tuple(3, 'mno'), (3, 'mno'))
        self.assertRaises(ReturnTypeError, lambda:
                testfunc_Seq_ret_err(29, 'def'))

    def test_iterable(self):
        self.assertEqual(testfunc_Iter_arg((9, 8, 7, 6), 'vwxy'), [9, 8, 7, 6])
        self.assertEqual(testfunc_Iter_str_arg('defg'), [100, 101, 102, 103])
        self.assertRaises(InputTypeError, lambda:
                testfunc_Iter_arg((9, '8', 7, 6), 'vwxy'))
        self.assertRaises(InputTypeError, lambda:
                testfunc_Iter_arg(7, 'vwxy'))
        self.assertRaises(InputTypeError, lambda:
                testfunc_Iter_arg([9, 8, 7, '6'], 'vwxy'))
        self.assertEqual(testfunc_Iter_arg([9, 8, 7, 6], 'vwxy'), [9, 8, 7, 6])
        res = testfunc_Iter_arg({9, 8, 7, 6}, 'vwxy'); res.sort()
        self.assertEqual(res, [6, 7, 8, 9])
        res = testfunc_Iter_arg({19: 'a', 18: 'b', 17: 'c', 16: 'd'}, 'vwxy')
        res.sort()
        self.assertEqual(res, [16, 17, 18, 19])
        self.assertEqual(testfunc_Iter_ret(), [1, 2, 3, 4, 5])
        self.assertRaises(ReturnTypeError, lambda: testfunc_Iter_ret_err())
        ti = test_iterable((2, 4, 6, 'a'))
        self.assertRaises(ReturnTypeError, lambda: testfunc_Iter_arg(ti, 'vwxy'))
        tia = test_iterable_annotated((3, 6, 9))
        self.assertEqual(testfunc_Iter_arg(tia, 'vwxy'), [3, 6, 9])

    def test_iterable_subclass(self):
        # See https://github.com/Stewori/pytypes/issues/57
        T_it = TypeVar('T_it')
        class TypList(Generic[T_it], list):
            @typechecked
            def extend(self, itb):
                # type: (Iterator[T_it]) -> None
                super(TypList, self).extend(itb)
        class IntList(TypList[int]): pass

        il = IntList() 
        il.extend(iter([1, 2, 3]))
        self.assertRaises(ReturnTypeError, lambda: il.extend(iter(['a', 'b', 'c'])))
        self.assertRaises(InputTypeError, lambda: il.extend(['d', 'e', 'f']))
        il.extend([4, 5, 6])
        self.assertEqual(il, [1, 2, 3, 4, 5, 6])

    def test_dict(self):
        self.assertIsNone(testfunc_Dict_arg(5, {'5': 4, 'c': '8'}))
        self.assertIsNone(testfunc_Dict_arg(5, {'5': 'A', 'c': '8'}))
        self.assertIsNone(testfunc_Mapping_arg(7, {'7': 4, 'c': '8'}))
        self.assertIsNone(testfunc_Mapping_arg(5, {'5': 'A', 'c': '8'}))
        self.assertRaises(InputTypeError, lambda:
                testfunc_Dict_arg(5, {4: 4, 3: '8'}))
        self.assertRaises(InputTypeError, lambda:
                testfunc_Dict_arg(5, {'5': (4,), 'c': '8'}))
        self.assertEqual(
                testfunc_Dict_ret('defg'), {'defgdefg': 'defg', 'defg': 4})
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

        self.assertTrue(
                is_of_type(clb, typing.Callable[[str, int], str]))
        self.assertFalse(
                is_of_type(clb, typing.Callable[[str, str], str]))
        self.assertFalse(
                is_of_type(clb, typing.Callable[[str, int], float]))

        self.assertEqual(testfunc_Callable_arg(clb, 'pqrs'), '_pqrs****')
        self.assertRaises(InputTypeError, lambda:
                testfunc_Callable_arg(clb2, 'pqrs'))
        self.assertRaises(InputTypeError, lambda:
                testfunc_Callable_arg(clb3, 'pqrs'))
        self.assertRaises(InputTypeError, lambda:
                testfunc_Callable_call_err(clb, 'tuvw'))
        self.assertEqual(testfunc_Callable_arg(
                lambda s, i: '__'+s+'-'*i, 'pqrs'), '__pqrs----')
        self.assertRaises(InputTypeError, lambda:
                testfunc_Callable_call_err(lambda s, i: '__'+s+'-'*i, 'tuvw'))
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
        self.assertIsNone(test_gen2.next()
                if hasattr(test_gen2, 'next') else test_gen2.__next__())
        self.assertEqual(test_gen2.send('defg'), 4)
        self.assertRaises(ReturnTypeError, lambda: test_gen2.send('fail'))
        self.assertRaises(TypeCheckError, lambda:
                testfunc_Generator_arg(test_gen))
        self.assertRaises(TypeCheckError, lambda: testfunc_Generator_ret())
        self.assertEqual(pytypes.deep_type(test_gen), Generator[int, Union[str, None], Any])

    def test_custom_generic(self):
        self.assertEqual(testfunc_Generic_arg(Custom_Generic[str]('abc')), 'abc')
        self.assertEqual(testfunc_Generic_ret(5).v(), 5)
        self.assertRaises(InputTypeError, lambda:
                testfunc_Generic_arg(Custom_Generic[int](9)))
        self.assertRaises(InputTypeError, lambda:
                testfunc_Generic_arg(Custom_Generic(7)))
        self.assertRaises(ReturnTypeError, lambda:
                testfunc_Generic_ret_err(8))

    def test_various(self):
        self.assertEqual(get_type_hints(testfunc),
                {'a': int, 'c': str, 'b': Real, 'return': Tuple[int, Real]})
        self.assertEqual(pytypes.deep_type(('abc', [3, 'a', 7], 4.5)),
                Tuple[str, List[Union[int, str]], float])
        tc2 = testClass2('bbb')
        self.assertEqual(pytypes.get_class_that_defined_method(
                tc2.testmeth2c), testClass2)
        self.assertEqual(pytypes.get_class_that_defined_method(
                testClass2.testmeth2c), testClass2)
        self.assertEqual(pytypes.get_class_that_defined_method(
                tc2.testmeth2b), testClass2)
        self.assertEqual(pytypes.get_class_that_defined_method(
                testClass2.testmeth2b), testClass2)
        self.assertEqual(pytypes.get_class_that_defined_method(
                tc2.testmeth3), testClass2)
        self.assertEqual(pytypes.get_class_that_defined_method(
                testClass2.testmeth3), testClass2)
        self.assertRaises(ValueError, lambda:
                pytypes.get_class_that_defined_method(testfunc))
        # old-style:
        tc3 = testClass3()
        self.assertEqual(pytypes.get_class_that_defined_method(
                tc3.testmeth), testClass3)
        self.assertEqual(pytypes.get_class_that_defined_method(
                testClass3.testmeth), testClass3)

    @unittest.skipIf(sys.version_info.major >= 3 and sys.version_info.minor >= 7,
            'Currently fails in Python >= 3.7')
    def test_unparameterized(self):
        # invariant type-vars
        self.assertFalse(is_subtype(List, List[str]))
        self.assertFalse(is_subtype(List, List[Any]))
        self.assertFalse(is_subtype(List[str], List))
        self.assertFalse(is_subtype(list, List[str]))
        self.assertFalse(is_subtype(list, List[Any]))
        self.assertFalse(is_subtype(List[str], list))
        self.assertTrue(is_subtype(List, list))
        self.assertTrue(is_subtype(list, List))
        self.assertFalse(is_subtype(List[str], List[Any]))
        self.assertFalse(is_subtype(List[Any], List[str]))

        # covariant
        self.assertTrue(is_subtype(Sequence[str], Sequence[Any]))
        self.assertFalse(is_subtype(Sequence[Any], Sequence[str]))
        self.assertTrue(is_subtype(Sequence[str], Sequence))
        self.assertFalse(is_subtype(Sequence, Sequence[str]))

        # special case Tuple
        self.assertFalse(is_subtype(Tuple, Tuple[str]))
        self.assertTrue(is_subtype(Tuple[str], Tuple))
        self.assertFalse(is_subtype(tuple, Tuple[str]))
        self.assertTrue(is_subtype(Tuple[str], tuple))
        self.assertTrue(is_subtype(Tuple, tuple))
        self.assertTrue(is_subtype(tuple, Tuple))
        self.assertTrue(is_subtype(Tuple, Sequence))
        self.assertTrue(is_subtype(Tuple, Sequence[Any]))
        self.assertTrue(is_subtype(tuple, Sequence))
        self.assertTrue(is_subtype(tuple, Sequence[Any]))

    def test_empty(self):
        asg = {Dict, List, Set, pytypes.Empty}

        empty_dict = pytypes.Empty[Dict]
        self.assertEqual(pytypes.deep_type({}), empty_dict)
        self.assertEqual(pytypes.type_str(empty_dict, asg), 'Empty[Dict]')
        self.assertTrue(is_subtype(empty_dict, pytypes.Empty))
        #self.assertFalse(is_subtype(Dict[str, int], empty_dict))
        self.assertTrue(is_subtype(empty_dict, Dict[str, int]))
        self.assertTrue(is_subtype(empty_dict, Dict))

        empty_lst = pytypes.Empty[List]
        self.assertEqual(pytypes.deep_type([]), empty_lst)
        self.assertEqual(pytypes.type_str(empty_lst, asg), 'Empty[List]')
        self.assertTrue(is_subtype(empty_lst, pytypes.Empty))
        #self.assertFalse(is_subtype(List[str], empty_lst))
        self.assertTrue(is_subtype(empty_lst, List[int]))
        self.assertTrue(is_subtype(empty_lst, List))
        self.assertFalse(is_subtype(empty_lst, empty_dict))
        self.assertFalse(is_subtype(empty_dict, empty_lst))

        empty_seq = pytypes.Empty[Sequence]
        empty_con = pytypes.Empty[typing.Container]
        self.assertTrue(is_subtype(Dict[str, int],
                typing.Container[str]))
        self.assertFalse(is_subtype(empty_dict, empty_seq))
        self.assertTrue(is_subtype(empty_dict, empty_con))
        self.assertTrue(is_subtype(empty_lst, empty_seq))
        self.assertFalse(is_subtype(empty_seq, empty_lst))

        empty_set = pytypes.Empty[Set]
        self.assertEqual(pytypes.deep_type(set()), empty_set)
        self.assertEqual(pytypes.type_str(empty_set, asg), 'Empty[Set]')
        self.assertTrue(is_subtype(empty_set, pytypes.Empty))
        #self.assertFalse(is_subtype(Set[int], empty_set))
        self.assertTrue(is_subtype(empty_set, Set[int]))
        self.assertTrue(is_subtype(empty_set, Set))

    def test_numeric_tower(self):
        num_tow_tmp = pytypes.apply_numeric_tower
        pytypes.apply_numeric_tower = True

        self.assertTrue(is_subtype(int, float))
        self.assertTrue(is_subtype(int, complex))
        self.assertTrue(is_subtype(float, complex))

        self.assertFalse(is_subtype(float, int))
        self.assertFalse(is_subtype(complex, int))
        self.assertFalse(is_subtype(complex, float))

        self.assertTrue(is_subtype(Union[int, float], float))
        self.assertTrue(is_subtype(Sequence[int], Sequence[float]))
        self.assertTrue(is_subtype(List[int], Sequence[float]))
        self.assertTrue(is_subtype(Tuple[int, float], Tuple[float, complex]))
        self.assertTrue(is_subtype(Tuple[int, float], Sequence[float]))
        self.assertTrue(is_subtype(Tuple[List[int]], Tuple[Sequence[float]]))

        self.assertEqual(testfunc_numeric_tower_float(3), '3')
        self.assertEqual(testfunc_numeric_tower_float(1.7), '1.7')
        self.assertRaises(InputTypeError, lambda:
                testfunc_numeric_tower_float(1+3j))
        self.assertRaises(InputTypeError, lambda:
                testfunc_numeric_tower_float('abc'))
        self.assertRaises(InputTypeError, lambda:
                testfunc_numeric_tower_float(True))

        self.assertEqual(testfunc_numeric_tower_complex(5), '5')
        self.assertEqual(testfunc_numeric_tower_complex(8.7), '8.7')
        self.assertEqual(testfunc_numeric_tower_complex(1+3j), '(1+3j)')
        self.assertRaises(InputTypeError, lambda:
                testfunc_numeric_tower_complex('abc'))
        self.assertRaises(InputTypeError, lambda:
                testfunc_numeric_tower_complex(True))

        self.assertEqual(
                testfunc_numeric_tower_tuple((3, 'abc')), "(3, 'abc')")
        self.assertEqual(
                testfunc_numeric_tower_tuple((1.7, 'abc')), "(1.7, 'abc')")
        self.assertRaises(InputTypeError, lambda:
                testfunc_numeric_tower_tuple((1+3j, 'abc')))
        self.assertRaises(InputTypeError, lambda:
                testfunc_numeric_tower_tuple(('abc', 'def')))
        self.assertRaises(InputTypeError, lambda:
                testfunc_numeric_tower_tuple((True, 'abc')))
        self.assertRaises(InputTypeError, lambda:
                testfunc_numeric_tower_tuple(True))

        self.assertEqual(testfunc_numeric_tower_return('defg'), 4)
        self.assertRaises(ReturnTypeError, lambda:
                testfunc_numeric_tower_return_err('defg'))

        self.assertIsNone(testfunc_check_argument_types(2, 3, 'qvwx'))
        self.assertIsNone(testfunc_check_argument_types2([3, 2., 1]))
        self.assertIsNone(testfunc_check_argument_types_empty())


        pytypes.apply_numeric_tower = False

        self.assertFalse(is_subtype(int, float))
        self.assertFalse(is_subtype(int, complex))
        self.assertFalse(is_subtype(float, complex))

        self.assertFalse(is_subtype(float, int))
        self.assertFalse(is_subtype(complex, int))
        self.assertFalse(is_subtype(complex, float))

        self.assertFalse(is_subtype(Union[int, float], float))
        self.assertFalse(is_subtype(Sequence[int], Sequence[float]))
        self.assertFalse(is_subtype(List[int], Sequence[float]))
        self.assertFalse(is_subtype(Tuple[int, float], Tuple[float, complex]))
        self.assertFalse(is_subtype(Tuple[int, float], Sequence[float]))
        self.assertFalse(is_subtype(Tuple[List[int]], Tuple[Sequence[float]]))

        self.assertRaises(InputTypeError, lambda:
                testfunc_numeric_tower_float(3))
        self.assertEqual(testfunc_numeric_tower_float(1.7), '1.7')
        self.assertRaises(InputTypeError, lambda:
                testfunc_numeric_tower_float(1+3j))
        self.assertRaises(InputTypeError, lambda:
                testfunc_numeric_tower_float('abc'))
        self.assertRaises(InputTypeError, lambda:
                testfunc_numeric_tower_float(True))

        self.assertRaises(InputTypeError, lambda:
                testfunc_numeric_tower_complex(5))
        self.assertRaises(InputTypeError, lambda:
                testfunc_numeric_tower_complex(8.7))
        self.assertEqual(testfunc_numeric_tower_complex(1+3j), '(1+3j)')
        self.assertRaises(InputTypeError, lambda:
                testfunc_numeric_tower_complex('abc'))
        self.assertRaises(InputTypeError, lambda:
                testfunc_numeric_tower_complex(True))

        self.assertRaises(InputTypeError, lambda:
                testfunc_numeric_tower_tuple((3, 'abc')))
        self.assertEqual(
                testfunc_numeric_tower_tuple((1.7, 'abc')), "(1.7, 'abc')")
        self.assertRaises(InputTypeError, lambda:
                testfunc_numeric_tower_tuple((1+3j, 'abc')))
        self.assertRaises(InputTypeError, lambda:
                testfunc_numeric_tower_tuple(('abc', 'def')))
        self.assertRaises(InputTypeError, lambda:
                testfunc_numeric_tower_tuple((True, 'abc')))
        self.assertRaises(InputTypeError, lambda:
                testfunc_numeric_tower_tuple(True))

        self.assertRaises(ReturnTypeError, lambda:
                testfunc_numeric_tower_return('defg'))
        self.assertRaises(ReturnTypeError, lambda:
                testfunc_numeric_tower_return_err('defg'))

        self.assertRaises(InputTypeError, lambda:
                testfunc_check_argument_types(2, 3, 'qvwx'))
        self.assertRaises(InputTypeError, lambda:
                testfunc_check_argument_types2([3, 2., 1]))

        pytypes.apply_numeric_tower = num_tow_tmp

    def test_subtype_class_extends_generic(self):
        class Lint(List[int]):
            pass

        class Lint2(Lint):
            pass

        class Lfloat(List[float]):
            pass

        self.assertTrue(is_subtype(List[int], Sequence[int]))
        self.assertFalse(is_subtype(Iterable[int], Sequence[int]))

        self.assertTrue(is_subtype(Lint, Sequence[float]))
        self.assertFalse(is_subtype(Lint, List[float])) # False because mutable list is invariant
        self.assertTrue(is_subtype(Lint, List[int]))

        self.assertTrue(is_subtype(Lint2, Sequence[float]))
        self.assertFalse(is_subtype(Lint2, List[float])) # False because mutable list is invariant
        self.assertTrue(is_subtype(Lint2, List[int]))
        self.assertTrue(is_subtype(Lint2, Lint))

        self.assertTrue(is_subtype(Lfloat, Sequence[float]))
        self.assertTrue(is_subtype(Lfloat, List[float]))
        self.assertFalse(is_subtype(Lfloat, Sequence[int]))
        self.assertFalse(is_subtype(Lfloat, List[int]))
        self.assertFalse(is_subtype(Lfloat, Lint))
        self.assertFalse(is_subtype(Lint, Lfloat))


    def test_typevar_func(self):
        T_ct = TypeVar('T_ct', contravariant=True)
        T_cv = TypeVar('T_cv', covariant=True)
        T_ = TypeVar('T_')

        @typechecked
        def tpvar_test1(a, b):
            # type: (T_, T_) -> str
            return 'hello'

        @typechecked
        def tpvar_test2(a, b):
            # type: (T_cv, T_cv) -> str
            return 'hello'

        @typechecked
        def tpvar_test3(a, b):
            # type: (T_ct, T_ct) -> str
            return 'hello'

        @typechecked
        def tpvar_test4(lst, idx):
            # type: (List[T_], int) -> T_
            return lst[idx]

        @typechecked
        def tpvar_test5(lst, idx):
            # type: (List[T_], int) -> T_
            return str(lst[idx])

        self.assertEqual(tpvar_test1(2, 3), 'hello')
        self.assertRaises(InputTypeError, lambda: tpvar_test1(2, '3'))
        self.assertRaises(InputTypeError, lambda: tpvar_test1(2, 3.5))
        self.assertRaises(InputTypeError, lambda: tpvar_test1(2.5, 3))

        self.assertEqual(tpvar_test2(2, 3), 'hello')
        self.assertRaises(InputTypeError, lambda: tpvar_test2(2, '3'))
        self.assertRaises(InputTypeError, lambda: tpvar_test2(2, 3.5))
        self.assertEqual(tpvar_test2(2.5, 3), 'hello')

        self.assertEqual(tpvar_test3(2, 3), 'hello')
        self.assertRaises(InputTypeError, lambda: tpvar_test3(2, '3'))
        self.assertEqual(tpvar_test3(2, 3.5), 'hello')
        self.assertRaises(InputTypeError, lambda: tpvar_test3(2.5, 3))

        self.assertEqual(tpvar_test4([1.2, 2.6, 3.2], 1), 2.6)
        self.assertRaises(ReturnTypeError, lambda: tpvar_test5([1.2, 2.6, 3.2], 2))
        self.assertEqual(tpvar_test5(['a', 'b', 'c'], 1), 'b')


    def test_typevar_class(self):
        T2 = TypeVar('T2', covariant=True)

        @typechecked
        class A(Generic[T2]):
            def __init__(self, obj):
                # type: (T2) -> None
                super(A, self).__init__()
                self.obj = obj		

        class IntA(A[int]): pass
        class IntB(IntA): pass
        
        self.assertIsNotNone(IntA(5))
        self.assertRaises(InputTypeError, lambda: IntA(4.5))
        self.assertRaises(InputTypeError, lambda: IntA('acb'))
        self.assertIsNotNone(A[int](5))
        self.assertRaises(InputTypeError, lambda: A[int](4.5))
        self.assertRaises(InputTypeError, lambda: A[int]('acb'))
        self.assertIsNotNone(A[float](5))
        self.assertIsNotNone(A[float](4.5))
        self.assertRaises(InputTypeError, lambda: A[float]('acb'))
        self.assertRaises(InputTypeError, lambda: A[str](5))
        self.assertRaises(InputTypeError, lambda: A[str](4.5))
        self.assertIsNotNone(A[str]('acb'))
        
        @typechecked
        def test_typevar_A(x):
            # type: (A[int]) -> None
            pass
        
        self.assertIsNone(test_typevar_A(IntA(5)))
        self.assertRaises(InputTypeError, lambda: test_typevar_A(IntA(5.7)))
        self.assertIsNone(test_typevar_A(IntB(5)))
        self.assertRaises(InputTypeError, lambda: test_typevar_A(IntB(5.7)))

    @unittest.skipIf(sys.version_info.major >= 3 and sys.version_info.minor >= 7,
            'Tests with MRO that is invalid in Python >= 3.7')
    def test_get_generic_parameters_pre3_7(self):
        class sub_List(List[str]): pass
        class sub_List5(Generic[T_1], sub_List): pass
        class sub_Dict(Dict[str, int]): pass
        class sub_Dict5(Generic[T_1], sub_Dict): pass

        self.assertEqual(pytypes.get_Generic_itemtype(sub_List5), str)
        self.assertEqual(pytypes.get_Generic_itemtype(sub_List5[complex]), str)
        self.assertEqual(pytypes.get_Generic_itemtype(sub_Dict5), str)
        self.assertEqual(pytypes.get_Generic_itemtype(sub_Dict5[complex]), str)
        self.assertEqual(pytypes.get_Mapping_key_value(sub_Dict5), (str, int))
        self.assertEqual(pytypes.get_Mapping_key_value(sub_Dict5[complex]), (str, int))

        self.assertEqual(pytypes.get_arg_for_TypeVar(T_1, sub_List5[complex]), complex)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.T, sub_List5[complex]), str)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.T_co, sub_List5[complex]), str)

        self.assertEqual(pytypes.get_arg_for_TypeVar(T_1, sub_Dict5[float]), float)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.KT, sub_Dict5[float]), str)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.VT, sub_Dict5[float]), int)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.VT_co, sub_Dict5[float]), int)

    def test_get_generic_parameters(self):
        class sub_List(List[str]): pass
        class sub_List2(List[float], Generic[T_1]): pass
        class sub_List3(Generic[T_1], List[int]): pass
        class sub_List4(sub_List, Generic[T_1]): pass
        class sub_List6(List[T_1]): pass
        class sub_List7(Generic[T_1], List[T_1]): pass

        class sub_Dict(Dict[str, int]): pass
        class sub_Dict2(Dict[float, str], Generic[T_1]): pass
        class sub_Dict3(Generic[T_1], Dict[int, complex]): pass
        class sub_Dict4(sub_Dict, Generic[T_1]): pass
        class sub_Dict6(Dict[T_1, int]): pass
        class sub_Dict7(Dict[int, T_1]): pass
        class sub_Dict8(Generic[T_1], Dict[float, T_1]): pass

        self.assertEqual(pytypes.get_Generic_itemtype(Tuple[int, float, str]),
                Union[str, float])
        self.assertEqual(pytypes.get_Generic_itemtype(Dict[float, str]), float)
        self.assertEqual(pytypes.get_Generic_itemtype(Set[str]), str)
        self.assertEqual(pytypes.get_Generic_itemtype(List[complex]), complex)
        self.assertRaises(TypeError, lambda:
                pytypes.get_Generic_itemtype(Callable[[str, int], str]))
        self.assertEqual(pytypes.get_Generic_itemtype(sub_List), str)
        self.assertEqual(pytypes.get_Generic_itemtype(sub_List2), float)
        self.assertEqual(pytypes.get_Generic_itemtype(sub_List3), int)
        self.assertEqual(pytypes.get_Generic_itemtype(sub_List4), str)
        self.assertRaises(TypeError, lambda:
                pytypes.get_Generic_itemtype(sub_List6))
        self.assertRaises(TypeError, lambda:
                pytypes.get_Generic_itemtype(sub_List7))
        self.assertEqual(pytypes.get_Generic_itemtype(sub_List2[str]), float)
        self.assertEqual(pytypes.get_Generic_itemtype(sub_List3[complex]), int)
        self.assertEqual(pytypes.get_Generic_itemtype(sub_List4[float]), str)
        self.assertEqual(pytypes.get_Generic_itemtype(sub_List6[Union[int, str]]),
                Union[int, str])
        self.assertEqual(pytypes.get_Generic_itemtype(sub_List7[Union[complex, str]]),
                Union[complex, str])
        self.assertEqual(pytypes.get_Generic_itemtype(sub_Dict), str)
        self.assertEqual(pytypes.get_Generic_itemtype(sub_Dict2), float)
        self.assertEqual(pytypes.get_Generic_itemtype(sub_Dict3), int)
        self.assertEqual(pytypes.get_Generic_itemtype(sub_Dict4), str)
        self.assertRaises(TypeError, lambda: pytypes.get_Generic_itemtype(sub_Dict6))
        self.assertEqual(pytypes.get_Generic_itemtype(sub_Dict7), int)
        self.assertEqual(pytypes.get_Generic_itemtype(sub_Dict8), float)
        self.assertEqual(pytypes.get_Generic_itemtype(sub_Dict2[str]), float)
        self.assertEqual(pytypes.get_Generic_itemtype(sub_Dict3[complex]), int)
        self.assertEqual(pytypes.get_Generic_itemtype(sub_Dict4[float]), str)
        self.assertEqual(pytypes.get_Generic_itemtype(sub_Dict6[Union[int, str]]),
                Union[int, str])
        self.assertEqual(pytypes.get_Generic_itemtype(sub_Dict7[Union[complex, str]]),
                int)
        self.assertEqual(pytypes.get_Generic_itemtype(sub_Dict8[Union[float, str]]),
                float)
        self.assertEqual(pytypes.get_Mapping_key_value(Dict[complex, int]),
                (complex, int))
        self.assertEqual(pytypes.get_Mapping_key_value(typing.MutableMapping[str, int]),
                (str, int))
        self.assertEqual(pytypes.get_Mapping_key_value(typing.Mapping[float, str]),
                (float, str))
        self.assertEqual(pytypes.get_Mapping_key_value(sub_Dict), (str, int))
        self.assertEqual(pytypes.get_Mapping_key_value(sub_Dict2), (float, str))
        self.assertEqual(pytypes.get_Mapping_key_value(sub_Dict3), (int, complex))
        self.assertEqual(pytypes.get_Mapping_key_value(sub_Dict4), (str, int))
        self.assertRaises(TypeError, lambda: pytypes.get_Mapping_key_value(sub_Dict6))
        self.assertRaises(TypeError, lambda: pytypes.get_Mapping_key_value(sub_Dict7))
        self.assertRaises(TypeError, lambda: pytypes.get_Mapping_key_value(sub_Dict8))
        self.assertEqual(pytypes.get_Mapping_key_value(sub_Dict2[str]), (float, str))
        self.assertEqual(pytypes.get_Mapping_key_value(sub_Dict3[int]), (int, complex))
        self.assertEqual(pytypes.get_Mapping_key_value(sub_Dict4[float]), (str, int))
        self.assertEqual(pytypes.get_Mapping_key_value(sub_Dict6[str]), (str, int))
        self.assertEqual(pytypes.get_Mapping_key_value(sub_Dict7[str]), (int, str))
        self.assertEqual(pytypes.get_Mapping_key_value(sub_Dict8[Union[complex, str]]),
                (float, Union[complex, str]))

        self.assertEqual(pytypes.get_Generic_parameters(sub_List, List)[0], str)
        self.assertEqual(pytypes.get_Generic_parameters(sub_List2[str], List)[0], float)

        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.T, List[float]), float)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.T_co, List[float]), float)
        self.assertIsNone(pytypes.get_arg_for_TypeVar(typing.T, typing.Container[float]))
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.T_co, typing.Container[float]), float)

        self.assertIsNone(pytypes.get_arg_for_TypeVar(typing.T, Dict[float, str]))
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.KT, Dict[float, str]), float)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.VT, Dict[float, str]), str)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.VT_co, Dict[float, str]), str)

        self.assertIsNone(pytypes.get_arg_for_TypeVar(typing.T,
                typing.MutableMapping[float, str]))
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.KT,
                typing.MutableMapping[float, str]), float)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.VT,
                typing.MutableMapping[float, str]), str)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.VT_co,
                typing.MutableMapping[float, str]), str)

        self.assertIsNone(pytypes.get_arg_for_TypeVar(typing.T, typing.Mapping[float, str]))
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.KT,
                typing.Mapping[float, str]), float)
        self.assertIsNone(pytypes.get_arg_for_TypeVar(typing.VT, typing.Mapping[float, str]))
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.VT_co,
                typing.Mapping[float, str]), str)

        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.T, sub_List), str)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.T, sub_List2), float)
        self.assertEqual(pytypes.get_arg_for_TypeVar(T_1, sub_List3[complex]), complex)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.T, sub_List3[str]), int)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.T_co, sub_List3[str]), int)
        self.assertEqual(pytypes.get_arg_for_TypeVar(T_1, sub_List4[complex]), complex)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.T, sub_List4[complex]), str)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.T_co, sub_List4[complex]), str)
        self.assertEqual(pytypes.get_arg_for_TypeVar(T_1, sub_List6[complex]), complex)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.T, sub_List6[complex]), complex)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.T_co, sub_List6[complex]), complex)
        self.assertEqual(pytypes.get_arg_for_TypeVar(T_1, sub_List7[complex]), complex)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.T, sub_List7[complex]), complex)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.T_co, sub_List7[complex]), complex)

        self.assertIsNone(pytypes.get_arg_for_TypeVar(T_1, sub_Dict))
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.KT, sub_Dict), str)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.VT, sub_Dict), int)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.VT_co, sub_Dict), int)

        self.assertEqual(pytypes.get_arg_for_TypeVar(T_1, sub_Dict2[complex]), complex)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.KT, sub_Dict2[complex]), float)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.VT, sub_Dict2[complex]), str)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.VT_co, sub_Dict2[complex]), str)

        self.assertEqual(pytypes.get_arg_for_TypeVar(T_1, sub_Dict3[float]), float)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.KT, sub_Dict3[float]), int)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.VT, sub_Dict3[float]), complex)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.VT_co, sub_Dict3[float]), complex)

        self.assertEqual(pytypes.get_arg_for_TypeVar(T_1, sub_Dict4[float]), float)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.KT, sub_Dict4[float]), str)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.VT, sub_Dict4[float]), int)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.VT_co, sub_Dict4[float]), int)

        self.assertEqual(pytypes.get_arg_for_TypeVar(T_1, sub_Dict6[float]), float)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.KT, sub_Dict6[float]), float)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.VT, sub_Dict6[float]), int)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.VT_co, sub_Dict6[float]), int)

        self.assertEqual(pytypes.get_arg_for_TypeVar(T_1, sub_Dict7[float]), float)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.KT, sub_Dict7[float]), int)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.VT, sub_Dict7[float]), float)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.VT_co, sub_Dict7[float]), float)

        self.assertEqual(pytypes.get_arg_for_TypeVar(T_1, sub_Dict8[complex]), complex)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.KT, sub_Dict8[complex]), float)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.VT, sub_Dict8[complex]), complex)
        self.assertEqual(pytypes.get_arg_for_TypeVar(typing.VT_co, sub_Dict8[complex]), complex)

    def test_typevar_collision(self):
        # See: https://github.com/Stewori/pytypes/issues/62
        T1 = typing.TypeVar("T1")
        T2 = typing.TypeVar("T2")
        
        class D0(Dict[T1, T2]):
            def show_types(self):
                gt = pytypes.get_Generic_type(self)
                return gt, pytypes.get_Generic_parameters(gt, D0)
        
        class D1(D0[int, T1]): pass
        class D2(D1[str]): pass
        
        self.assertEqual(D0[int, str]().show_types(), (D0[int, str], (int, str)))
        self.assertEqual(D1[str]().show_types(), (D1[str], (int, str)))
        self.assertEqual(D2().show_types(), (D2, (int, str))) # was (str, str) before the fix

    def test_property(self):
        tcp = testClass_property()
        tcp.testprop = 7
        self.assertEqual(tcp.testprop, 7)
        def tcp_prop1(): tcp.testprop = 7.2
        self.assertRaises(InputTypeError, tcp_prop1)
        tcp._testprop = 'abc'
        self.assertRaises(ReturnTypeError, lambda: tcp.testprop)

        tcp.testprop2 = 'def'
        self.assertEqual(tcp.testprop2, 'def')
        tcp.testprop2 = 7.2
        self.assertRaises(ReturnTypeError, lambda: tcp.testprop2)

        tcp.testprop3 = (22, 'ghi')
        self.assertEqual(tcp.testprop3, (22, 'ghi'))
        def tcp_prop3(): tcp.testprop3 = 9
        self.assertRaises(InputTypeError, tcp_prop3)
        tcp._testprop3 = 9
        self.assertRaises(ReturnTypeError, lambda: tcp.testprop3)

        tcp_ch = testClass_property_class_check()
        tcp_ch.testprop = 17
        self.assertEqual(tcp_ch.testprop, 17)
        def tcp_ch_prop(): tcp_ch.testprop = 71.2
        self.assertRaises(InputTypeError, tcp_ch_prop)
        tcp_ch._testprop = 'abc'
        self.assertRaises(ReturnTypeError, lambda: tcp_ch.testprop)

        tcp_ch.testprop2 = 7.2
        self.assertRaises(ReturnTypeError, lambda: tcp_ch.testprop2)

        self.assertEqual(get_member_types(tcp, 'testprop'), (Tuple[int], type(None)))
        self.assertEqual(get_member_types(tcp, 'testprop', True), (Tuple[()], int))

    def test_custom_annotations(self):
        annotations_override_typestring_tmp = pytypes.annotations_override_typestring

        hnts = testfunc_custom_annotations.__annotations__
        self.assertEqual(hnts['a'], str)
        self.assertEqual(hnts['b'], float)
        self.assertEqual(hnts['return'], float)

        if sys.version_info.major >= 3:
            hnts = typing.get_type_hints(testfunc_custom_annotations)
            self.assertEqual(hnts['a'], str)
            self.assertEqual(hnts['b'], float)
            self.assertEqual(hnts['return'], float)
        else:
            self.assertIsNone(typing.get_type_hints(testfunc_custom_annotations))

        hnts = pytypes.get_type_hints(testfunc_custom_annotations)
        self.assertEqual(hnts['a'], str)
        self.assertEqual(hnts['b'], float)
        self.assertEqual(hnts['return'], float)
        self.assertEqual(pytypes.get_types(testfunc_custom_annotations),
                (typing.Tuple[str, float], float))
        self.assertEqual(testfunc_custom_annotations('abc', 2.5), 1.2)
        self.assertRaises(InputTypeError, lambda:
                testfunc_custom_annotations('abc', 'd'))

        self.assertEqual(testfunc_custom_annotations_typechecked('qvw', 2), 1.5)
        self.assertRaises(InputTypeError,
                lambda: testfunc_custom_annotations_typechecked('qvw', 2.2))
        self.assertRaises(InputTypeError,
                lambda: testfunc_custom_annotations_typechecked_err(7, 1.5))
        self.assertRaises(ReturnTypeError,
                lambda: testfunc_custom_annotations_typechecked_err('hij', 1.5))

        if sys.version_info.major >= 3:
            self.assertTrue(
                    hasattr(testfunc_custom_annotations_plain, '__annotations__'))
            self.assertEqual(
                    len(testfunc_custom_annotations_plain.__annotations__), 0)
            self.assertEqual(
                    len(typing.get_type_hints(testfunc_custom_annotations_plain)), 0)
        else:
            self.assertFalse(
                    hasattr(testfunc_custom_annotations_plain, '__annotations__'))
            self.assertIsNone(
                    typing.get_type_hints(testfunc_custom_annotations_plain))

        hnts = pytypes.get_type_hints(testfunc_custom_annotations_plain)
        self.assertEqual(hnts['a'], str)
        self.assertEqual(hnts['b'], float)
        self.assertEqual(hnts['return'], float)
        self.assertEqual(get_types(testfunc_custom_annotations_plain),
                (Tuple[str, float], float))
        pytypes.annotations_override_typestring = False
        self.assertEqual(get_types(testfunc_custom_annotations_plain),
                (Tuple[str, float], float))
        self.assertEqual(testfunc_custom_annotations_plain('abc', 1.5), 2.0)
        testfunc_custom_annotations_plain.__annotations__ = \
                {'a': str, 'b': int, 'return': 'float'}
        self.assertRaises(TypeError, lambda:
                testfunc_custom_annotations_plain('abc', 1.5))
        pytypes.annotations_override_typestring = True
        self.assertEqual(testfunc_custom_annotations_plain('abc', 1), 3.0)
        self.assertRaises(InputTypeError,
                lambda: testfunc_custom_annotations_plain('abc', 1.5))
        hnts = pytypes.get_type_hints(testfunc_custom_annotations_plain)
        self.assertEqual(hnts['a'], str)
        self.assertEqual(hnts['b'], int)
        self.assertEqual(hnts['return'], float)
        hnts = testfunc_custom_annotations_plain.__annotations__
        self.assertEqual(hnts['a'], str)
        self.assertEqual(hnts['b'], int)
        self.assertEqual(hnts['return'], 'float')
        pytypes.annotations_override_typestring = False
        self.assertRaises(TypeError,
                lambda: pytypes.get_type_hints(testfunc_custom_annotations_plain))

        pytypes.annotations_override_typestring = annotations_override_typestring_tmp 

    def test_annotations_from_typestring(self):
        # via decorator
        annt = testfunc_annotations_from_tpstring_by_decorator.__annotations__
        self.assertEqual(annt['a'], str)
        self.assertEqual(annt['b'], int)
        self.assertEqual(annt['return'], int)

        # via pytypes-flag
        annotations_from_typestring_tmp = pytypes.annotations_from_typestring

        self.assertTrue(not hasattr(
                testfunc_annotations_from_tpstring, '__annotations__') or
                len(testfunc_annotations_from_tpstring.__annotations__) == 0)
        pytypes.annotations_from_typestring = False
        self.assertEqual(pytypes.get_types(testfunc_annotations_from_tpstring),
                (Tuple[str, int],int))
        self.assertTrue(not hasattr(
                testfunc_annotations_from_tpstring, '__annotations__') or
                len(testfunc_annotations_from_tpstring.__annotations__) == 0)
        pytypes.annotations_from_typestring = True
        self.assertEqual(pytypes.get_types(testfunc_annotations_from_tpstring),
                (Tuple[str, int],int))
        annt = testfunc_annotations_from_tpstring.__annotations__
        self.assertEqual(annt['a'], str)
        self.assertEqual(annt['b'], int)
        self.assertEqual(annt['return'], int)

        pytypes.annotations_from_typestring = annotations_from_typestring_tmp

    def test_varargs(self):
        self.assertEqual(testfunc_varargs1(16.4, 2, 3.2), (3, 104.96))
        self.assertEqual(testfunc_varargs1(), (0, 1.0))
        self.assertRaises(InputTypeError, lambda:
                testfunc_varargs1((16.4, 2, 3.2)))
        self.assertRaises(InputTypeError, lambda:
                testfunc_varargs1(16.4, '2', 3.2))
        self.assertEqual(testfunc_varargs2('cdef', 3, None, 5, 4, 7, 17, -2),
                (-4760, 'cdefcdefcdef'))
        self.assertRaises(InputTypeError, lambda:
                testfunc_varargs2('cdef', 3, 'a', 5, 4, 7, 17, -2))
        self.assertRaises(InputTypeError, lambda:
                testfunc_varargs2('cdef', 3, None, (5, 4, 7, 17, -2)))
        self.assertRaises(InputTypeError, lambda:
                testfunc_varargs2('cdef', 3, None, 5, 4, 7.1, 17, -2))
        self.assertEqual(testfunc_varargs3(14, 3, -4, a=8, ab=7.7, q=-3.2),
                ('abababab', 7.7))
        self.assertRaises(InputTypeError, lambda:
                testfunc_varargs3(14, 3.2, -4, a=8, b=7.7, q=-3.2))
        self.assertRaises(InputTypeError, lambda:
                testfunc_varargs3((14, 3, -4), a=8, b=7.7, q=-3.2))
        self.assertRaises(InputTypeError, lambda:
                testfunc_varargs3(14, 3, -4, a=8, b='7.7', q=-3.2))
        self.assertEqual(testfunc_varargs4(cx = 7, d = 9), 7)
        self.assertEqual(testfunc_varargs4(cx = 7.5, d = 9), 7.5)
        self.assertEqual(testfunc_varargs4(), 0)
        self.assertRaises(InputTypeError, lambda: testfunc_varargs4(2, 3))
        self.assertRaises(InputTypeError, lambda:
                testfunc_varargs4(cx = 7.1, d = '9'))
        self.assertEqual(testfunc_varargs5(
                3, 'qvw', 3.3, 3.1, 2.778, 9, v=6, x=-8, qvw=99), [4, 1, 99])
        self.assertRaises(InputTypeError, lambda: testfunc_varargs5(
                3, 'qvw', 3.3, 3.1, 2.778, 9, v=6.2, x=-8, qvw=99))
        self.assertRaises(InputTypeError, lambda: testfunc_varargs5(
                3, 3, 3.3, 3.1, 2.778, 9, v=6, x=-8, qvw=99))
        self.assertRaises(InputTypeError, lambda: testfunc_varargs5(
                3, 'qvw', (3.3, 3.1, 2.778, 9), v=6, x=-8, qvw=99))
        self.assertRaises(InputTypeError, lambda: testfunc_varargs5())
        self.assertRaises(InputTypeError, lambda: testfunc_varargs_err(
                3.0, 'qvw', 3.3, 9, v=6, x=-8, qvw=9.9))
        self.assertRaises(ReturnTypeError, lambda: testfunc_varargs_err(
                3, 'qvw', 3.3, 3.1, 2.778, 9, v=6, x=-8, qvw=99))
        tcv = testclass_vararg()
        self.assertEqual(tcv.testmeth_varargs1(
                ('k', 7), ('bxx', 19), ('bxy', 27)), 130)
        self.assertEqual(tcv.testmeth_varargs1(), -15)
        self.assertRaises(InputTypeError, lambda:
                tcv.testmeth_varargs1(('k', 7), 19, ('bxy', 27)))
        self.assertEqual(tcv.testmeth_varargs2(
                2, 'xt', 1.2, 1.4, -9.2, cx=8, xt=7), [3, 4, 7, 16])
        self.assertRaises(InputTypeError, lambda:
                tcv.testmeth_varargs2(2, 'xt', 1.2, 1.4, -9.2, cx=8.2, xt=7))
        self.assertEqual(testclass_vararg.testmeth_varargs_static1(
                10, 4, 1.0, -4.2), (4, -168.0))
        self.assertEqual(testclass_vararg.testmeth_varargs_static1(), (0, 1.0))
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg.testmeth_varargs_static1((10, 4, 1.0, -4.2)))
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg.testmeth_varargs_static1('10, 4', 1.0, -4.2))
        self.assertEqual(testclass_vararg.testmeth_varargs_static2(
                0, 'cx', 1.2, -9.2, cx=2, xt=7), [2, 3, 2])
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg.testmeth_varargs_static2(
                0, 'cx', 1.2, -9.2, cx=2.1, xt=7))
        self.assertEqual(testclass_vararg.testmeth_varargs_class1(), -15)
        self.assertEqual(testclass_vararg.testmeth_varargs_class1(
                ('abc', -12), ('txxt', 2)), -43)
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg.testmeth_varargs_class1(
                ('abc', -12.1), ('txxt', 2)))
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg.testmeth_varargs_class1(
                ('abc', -12), 'txxt'))
        self.assertEqual(testclass_vararg.testmeth_varargs_class2(
                1, 'xt', .2, -92, cx=2, xt=7), [2, 3, 7, 16])
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg.testmeth_varargs_class2())
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg.testmeth_varargs_class2(
                0, 'cx', 1.2, -9.2, cx=2, xt=.7))
        tcv.prop1 = 'test_prop1'
        self.assertEqual(tcv.prop1, 'test_prop1')
        def _set_prop1(): tcv.prop1 = 8
        self.assertRaises(InputTypeError, _set_prop1)
        tcv._prop1 = 8
        self.assertRaises(ReturnTypeError, lambda: tcv.prop1)

    def test_varargs_check_argument_types(self):
        self.assertEqual(testfunc_varargs_ca1(16.4, 2, 3.2), (3, 104.96))
        self.assertEqual(testfunc_varargs_ca1(), (0, 1.0))
        self.assertRaises(InputTypeError, lambda:
                testfunc_varargs_ca1((16.4, 2, 3.2)))
        self.assertRaises(InputTypeError, lambda:
                testfunc_varargs_ca1(16.4, '2', 3.2))
        self.assertEqual(testfunc_varargs_ca2('cdef', 3, None, 5, 4, 7, 17, -2),
                (-4760, 'cdefcdefcdef'))
        self.assertRaises(InputTypeError, lambda:
                testfunc_varargs_ca2('cdef', 3, 'a', 5, 4, 7, 17, -2))
        self.assertRaises(InputTypeError, lambda:
                testfunc_varargs_ca2('cdef', 3, None, (5, 4, 7, 17, -2)))
        self.assertRaises(InputTypeError, lambda:
                testfunc_varargs_ca2('cdef', 3, None, 5, 4, 7.1, 17, -2))
        self.assertEqual(testfunc_varargs_ca3(14, 3, -4, a=8, ab=7.7, q=-3.2),
                ('abababab', 7.7))
        self.assertRaises(InputTypeError, lambda:
                testfunc_varargs_ca3(14, 3.2, -4, a=8, b=7.7, q=-3.2))
        self.assertRaises(InputTypeError, lambda:
                testfunc_varargs_ca3((14, 3, -4), a=8, b=7.7, q=-3.2))
        self.assertRaises(InputTypeError, lambda:
                testfunc_varargs_ca3(14, 3, -4, a=8, b='7.7', q=-3.2))
        self.assertEqual(testfunc_varargs_ca4(cx = 7, d = 9), 7)
        self.assertEqual(testfunc_varargs_ca4(cx = 7.5, d = 9), 7.5)
        self.assertEqual(testfunc_varargs_ca4(), 0)
        # In this case it's an ordinary type-error, because Python catches it before
        # pytypes gets hands on it to make a more sophisticated InputTypeError:
        self.assertRaises(TypeError, lambda: testfunc_varargs_ca4(2, 3))
        self.assertRaises(InputTypeError, lambda:
                testfunc_varargs_ca4(cx = 7.1, d = '9'))
        self.assertEqual(testfunc_varargs_ca5(
                3, 'qvw', 3.3, 3.1, 2.778, 9, v=6, x=-8, qvw=99), [4, 1, 99])
        self.assertRaises(InputTypeError, lambda: testfunc_varargs_ca5(
                3, 'qvw', 3.3, 3.1, 2.778, 9, v=6.2, x=-8, qvw=99))
        self.assertRaises(InputTypeError, lambda: testfunc_varargs_ca5(
                3, 3, 3.3, 3.1, 2.778, 9, v=6, x=-8, qvw=99))
        self.assertRaises(InputTypeError, lambda: testfunc_varargs_ca5(
                3, 'qvw', (3.3, 3.1, 2.778, 9), v=6, x=-8, qvw=99))
        # In this case it's an ordinary type-error, because Python catches it before
        # pytypes gets hands on it to make a more sophisticated InputTypeError:
        self.assertRaises(TypeError, lambda: testfunc_varargs_ca5())
        tcv = testclass_vararg_ca()
        self.assertEqual(tcv.testmeth_varargs_ca1(
                ('k', 7), ('bxx', 19), ('bxy', 27)), 127)
        self.assertEqual(tcv.testmeth_varargs_ca1(), -18)
        self.assertRaises(InputTypeError, lambda:
                tcv.testmeth_varargs_ca1(('k', 7), 19, ('bxy', 27)))
        self.assertEqual(tcv.testmeth_varargs_ca2(2, 'xt', 1.2, 1.4, -9.2, cx=8, xt=7),
                [3, 4, 7, 19])
        self.assertRaises(InputTypeError, lambda:
                tcv.testmeth_varargs_ca2(2, 'xt', 1.2, 1.4, -9.2, cx=8.2, xt=7))
        self.assertEqual(testclass_vararg_ca.testmeth_varargs_static_ca1(
                10, 4, 1.0, -4.2), (4, -168.0))
        self.assertEqual(testclass_vararg_ca.testmeth_varargs_static_ca1(), (0, 1.0))
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg_ca.testmeth_varargs_static_ca1((10, 4, 1.0, -4.2)))
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg_ca.testmeth_varargs_static_ca1('10, 4', 1.0, -4.2))
        self.assertEqual(testclass_vararg_ca.testmeth_varargs_static_ca2(
                0, 'cx', 1.2, -9.2, cx=2, xt=7), [2, 3, 2])
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg_ca.testmeth_varargs_static_ca2(
                0, 'cx', 1.2, -9.2, cx=2.1, xt=7))
        self.assertEqual(testclass_vararg_ca.testmeth_varargs_class_ca1(), -18)
        self.assertEqual(testclass_vararg_ca.testmeth_varargs_class_ca1(
                ('abc', -12), ('txxt', 2)), -46)
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg_ca.testmeth_varargs_class_ca1(
                ('abc', -12.1), ('txxt', 2)))
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg_ca.testmeth_varargs_class_ca1(('abc', -12), 'txxt'))
        self.assertEqual(testclass_vararg_ca.testmeth_varargs_class_ca2(
                1, 'xt', .2, -92, cx=2, xt=7), [2, 3, 7, 19])
        # In this case it's an ordinary type-error, because Python catches it before
        # pytypes gets hands on it to make a more sophisticated InputTypeError:
        self.assertRaises(TypeError, lambda:
                testclass_vararg_ca.testmeth_varargs_class_ca2())
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg_ca.testmeth_varargs_class_ca2(
                0, 'cx', 1.2, -9.2, cx=2, xt=.7))
        tcv.prop_ca1 = 'test_prop1'
        self.assertEqual(tcv.prop_ca1, 'test_prop1')
        def _set_prop1(): tcv.prop_ca1 = 8
        self.assertRaises(InputTypeError, _set_prop1)
        # No point in checking for ReturnTypeError here;
        # check_argument_types wouldn't catch it.

    def test_defaults_inferred_types(self):
        tmp = pytypes.infer_default_value_types
        pytypes.infer_default_value_types = True

        self.assertEqual(get_types(func_defaults_typecheck),
                (Tuple[str, Any, int, float], str))
        self.assertEqual(pytypes.get_type_hints(func_defaults_typecheck),
                {'a': str, 'c': int, 'return': str, 'd': float})
        self.assertEqual(func_defaults_typecheck('qvw', 'abc', 2, 1.5), 'qvwabcabc')
        self.assertRaises(InputTypeError, lambda:
                func_defaults_typecheck('qvw', 'abc', 3.5))
        self.assertEqual(func_defaults_typecheck2('test', 12.2, 123), 'test1500.6False')
        self.assertRaises(InputTypeError, lambda:
                func_defaults_typecheck2('test', 12.2, 123, 3.5))

        self.assertRaises(InputTypeError, lambda:
                func_defaults_typecheck('qvw', 'abc', 3.5, 4.1))
        self.assertRaises(InputTypeError, lambda: func_defaults_typecheck(7, 'qvw'))

        self.assertEqual(func_defaults_checkargs('qvw', 'abc', 3, 1.5), 'qvwabcabcabc')
        self.assertRaises(InputTypeError, lambda:
                func_defaults_checkargs('qvw', 'abc', 3.5))
        self.assertRaises(InputTypeError, lambda:
                func_defaults_checkargs('qvw', 'abc', 3.5, 4.1))
        self.assertRaises(InputTypeError, lambda: func_defaults_checkargs(7, 'qvw'))

        self.assertEqual(get_types(func_defaults_annotations),
                (Tuple[str, Any, int], str))
        self.assertEqual(pytypes.get_type_hints(func_defaults_annotations),
                {'a': str, 'c': int, 'return': str})
        self.assertEqual(func_defaults_annotations.__annotations__,
                {'a': str, 'return': str})

        pytypes.infer_default_value_types = False

        self.assertEqual(get_types(func_defaults_typecheck),
                (Tuple[str, Any, Any, Any], str))
        self.assertEqual(pytypes.get_type_hints(func_defaults_typecheck),
                {'a': str, 'return': str})
        self.assertEqual(func_defaults_typecheck('qvw', 'abc', 3.5), 'invalid')
        self.assertEqual(func_defaults_typecheck('qvw', 'abc', 3.5, 4.1), 'invalid')
        self.assertRaises(InputTypeError, lambda: func_defaults_typecheck(7, 'qvw'))

        self.assertEqual(func_defaults_checkargs('qvw', 'abc', 3, 1.5), 'qvwabcabcabc')
        self.assertEqual(func_defaults_checkargs('qvw', 'abc', 3.5), 'invalid')
        self.assertEqual(func_defaults_checkargs('qvw', 'abc', 3.5, 4.1), 'invalid')
        self.assertRaises(InputTypeError, lambda: func_defaults_checkargs(7, 'qvw'))

        self.assertEqual(get_types(func_defaults_annotations),
                (Tuple[str, Any, Any], str))
        self.assertEqual(pytypes.get_type_hints(func_defaults_annotations),
                {'a': str, 'return': str})
        self.assertEqual(func_defaults_annotations.__annotations__,
                {'a': str, 'return': str})

        pytypes.infer_default_value_types = tmp

    def test_typestring_varargs_syntax(self):
        self.assertRaises(TypeSyntaxError, lambda:
                pytypes.get_types(func_bad_typestring1))
        self.assertRaises(TypeSyntaxError, lambda:
                pytypes.get_types(func_bad_typestring2))
        self.assertRaises(TypeSyntaxError, lambda:
                pytypes.get_types(func_bad_typestring3))
        self.assertRaises(TypeSyntaxError, lambda:
                pytypes.get_types(func_bad_typestring4))
        self.assertRaises(TypeSyntaxError, lambda:
                pytypes.get_types(func_bad_typestring5))
        self.assertRaises(TypeSyntaxError, lambda:
                pytypes.get_types(func_bad_typestring6))
        self.assertRaises(TypeSyntaxError, lambda:
                pytypes.get_types(func_bad_typestring7))
        self.assertRaises(TypeSyntaxError, lambda:
                pytypes.get_types(func_bad_typestring8))
        self.assertRaises(TypeSyntaxError, lambda:
                pytypes.get_types(func_bad_typestring9))
        self.assertRaises(TypeSyntaxError, lambda:
                pytypes.get_types(func_bad_typestring10))

    def test_typecheck_parent_type(self):
        always_check_parent_types_tmp = pytypes.always_check_parent_types
        pytypes.always_check_parent_types = False

        self.assertRaises(InputTypeError, lambda:
                B_override_check_arg().meth1(17.7))
        self.assertEqual(B_no_override_check_arg().meth1(17.7), 4)
        self.assertRaises(InputTypeError, lambda:
                B_override_typechecked().meth1(17.7))
        self.assertEqual(B_no_override_typechecked().meth1(17.7), 4)
        self.assertEqual(B_override_with_type_check_arg().meth1(17.7), 4)
        self.assertEqual(B_override_with_type_typechecked().meth1(17.7), 4)

        pytypes.always_check_parent_types = True

        self.assertRaises(InputTypeError, lambda:
                B_override_check_arg().meth1(17.7))
        self.assertRaises(InputTypeError, lambda:
                B_no_override_check_arg().meth1(17.7))
        self.assertRaises(InputTypeError, lambda:
                B_override_typechecked().meth1(17.7))
        self.assertRaises(InputTypeError, lambda:
                B_no_override_typechecked().meth1(17.7))
        self.assertEqual(B_override_with_type_check_arg().meth1(17.7), 4)
        self.assertEqual(B_override_with_type_typechecked().meth1(17.7), 4)

        pytypes.always_check_parent_types = always_check_parent_types_tmp


class TestTypecheck_class(unittest.TestCase):
    def test_classmethod(self):
        tc = testClass4('efghi')
        self.assertEqual(tc.testmeth_class(23, 1.1),
                "23-1.1-<class '%s.testClass4'>"%self.__module__)
        self.assertRaises(InputTypeError, lambda: tc.testmeth_class(23, '1.1'))
        # Tests @no_type_check:
        self.assertEqual(tc.testmeth_class_raw('23', 1.1),
                "23-1.1-<class '%s.testClass4'>"%self.__module__)
        self.assertEqual(tc.testmeth_class2(23, 1.1),
                "23-1.1-<class '%s.testClass4'>"%self.__module__)
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
        self.assertRaises(InputTypeError, lambda:
                tc.testmeth_static2(11, ('a', 'b'), 1.9))


class TestTypecheck_class_with_getattr(unittest.TestCase):
    """
    See pull request:
    https://github.com/Stewori/pytypes/pull/53
    commit #:
    e2523b347e52707f87d7078daad1a93940c12e2e
    """
    def test_valid_access(self):
        obj = GetAttrDictWrapper({'a': 5, 'b': 10})
        self.assertEqual(obj.a, 5)
        self.assertEqual(obj.b, 10)

    def test_invalid_access(self):
        obj = GetAttrDictWrapper({'a': 5, 'b': 10})
        self.assertRaises(AttributeError, lambda: obj.nonexistent)


class TestTypecheck_module(unittest.TestCase):
    def test_function_py2(self):
        from testhelpers import modulewide_typecheck_testhelper_py2 as mth
        self.assertEqual(mth.testfunc(3, 2.5, 'abcd'), (9, 7.5))
        with self.assertRaises(KeyError):
            pytypes.typechecked_module('nonexistent123')
        self.assertEqual(mth.testfunc(3, 2.5, 7), (9, 7.5)) # would normally fail
        module_name = 'testhelpers.modulewide_typecheck_testhelper_py2'
        returned_mth = pytypes.typechecked_module(module_name)
        self.assertEqual(returned_mth, module_name)
        returned_mth = pytypes.typechecked_module(mth)
        self.assertEqual(returned_mth, mth)
        self.assertEqual(mth.testfunc(3, 2.5, 'abcd'), (9, 7.5))
        self.assertRaises(InputTypeError, lambda: mth.testfunc(3, 2.5, 7))

    @unittest.skipUnless(sys.version_info.major >= 3 and sys.version_info.minor >= 5,
        'Only applicable in Python >= 3.5.')
    def test_function_py3(self):
        from testhelpers import modulewide_typecheck_testhelper as mth
        self.assertEqual(mth.testfunc(3, 2.5, 'abcd'), (9, 7.5))
        self.assertEqual(mth.testfunc(3, 2.5, 7), (9, 7.5)) # would normally fail
        returned_mth = pytypes.typechecked_module(mth)
        self.assertEqual(returned_mth, mth)
        self.assertEqual(mth.testfunc(3, 2.5, 'abcd'), (9, 7.5))
        self.assertRaises(InputTypeError, lambda: mth.testfunc(3, 2.5, 7))


class Test_check_argument_types(unittest.TestCase):
    def test_function(self):
        self.assertIsNone(testfunc_check_argument_types(2, 3.0, 'qvwx'))
        self.assertRaises(InputTypeError, lambda:
                testfunc_check_argument_types(2.7, 3.0, 'qvwx'))

    def test_methods(self):
        cl = testClass_check_argument_types()
        self.assertIsNone(cl.testMeth_check_argument_types(7))
        self.assertIsNone(cl.testClassmeth_check_argument_types(8))
        self.assertIsNone(cl.testStaticmeth_check_argument_types(9))

        self.assertRaises(InputTypeError, lambda:
                cl.testMeth_check_argument_types('7'))
        self.assertRaises(InputTypeError, lambda:
                cl.testClassmeth_check_argument_types(8.5))
        self.assertRaises(InputTypeError, lambda:
                cl.testStaticmeth_check_argument_types((9,)))

    def test_inner_method(self):
        def testf1():
            def testf2(x):
                # type: (Tuple[int, float]) -> str
                pytypes.check_argument_types()
                return str(x)
            return testf2((3, 6))
        self.assertEqual(testf1(), '(3, 6)')
        
        def testf1_err():
            def testf2(x):
                # type: (Tuple[int, float]) -> str
                pytypes.check_argument_types()
                return str(x)
            return testf2((3, '6'))
        self.assertRaises(InputTypeError, lambda: testf1_err())
    
    def test_inner_class(self):
        def testf1():
            class test_class_in_func(object):
                def testm1(self, x):
                    # type: (int) -> str
                    pytypes.check_argument_types()
                    return str(x)
            return test_class_in_func().testm1(99)
        self.assertEqual(testf1(), '99')

        def testf1_err():
            class test_class_in_func(object):
                def testm1(self, x):
                    # type: (int) -> str
                    pytypes.check_argument_types()
                    return str(x)
            return test_class_in_func().testm1(99.5)
        self.assertRaises(InputTypeError, lambda: testf1_err())


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

    def test_override_typecheck_class(self):
        tc5 = testClass5()
        self.assertEqual(tc5.testmeth_cls5(3, 7), '3-7')
        self.assertRaises(InputTypeError, lambda: tc5.testmeth_cls5(3, '8'))
        self.assertTrue(hasattr(tc5.testmeth_cls5, 'ch_func'))
        self.assertFalse(hasattr(tc5.testmeth2_cls5, 'ch_func'))

    def test_override_vararg(self):
        cl = override_varargs_class()
        self.assertEqual(cl.method_vararg1(1, 2.3, 4, 5), 2)
        self.assertEqual(cl.method_vararg2(6, 7.8, 'a', 'b', 'c'), 12)
        self.assertEqual(cl.method_vararg3(9, 10.1, 11.2, 12.3), 12)
        self.assertRaises(OverrideError, lambda: cl.method_vararg1_err(3, 4.5, 6, 7))
        self.assertRaises(OverrideError, lambda:
                cl.method_vararg2_err(8, 9.01, 'd', 'e', 'f'))
        self.assertRaises(OverrideError, lambda: cl.method_vararg3_err(4, 5, 6))
        self.assertEqual(cl.method_varkw1(7, 8, m=1.1, n=2.2, x=3.3), 15)
        self.assertEqual(cl.method_varkw2(9, 10, 'g', 'h', x=2.3, y=3.4, z=7.7), 19)
        self.assertRaises(OverrideError, lambda:
                cl.method_varkw1_err(11, 12, q=22, v=33, w=44))
        self.assertRaises(OverrideError, lambda:
                cl.method_varkw2_err(4, 5, 'i', 'j', g=3, h=7))
        self.assertRaises(OverrideError, lambda:
                cl.method_varkw3_err(14, 15, 'k', 'l'))
        self.assertEqual(cl.method_defaults1(21, 22), 43)
        self.assertEqual(cl.method_defaults2(23, 24, 31, 32, 33, 34), 47)
        self.assertRaises(OverrideError, lambda: cl.method_defaults1_err(101, 102))
        self.assertRaises(OverrideError, lambda:
                cl.method_defaults2_err(201, 202, 55.1, 55.2, 55.3))

    def test_override_diamond(self):
        self.assertEqual(D_diamond_override().meth1((12.4, 17.7)), 12)
        self.assertRaises(OverrideError, lambda:
                D_diamond_override_err1().meth1((12, 17)))
        self.assertRaises(OverrideError, lambda:
                D_diamond_override_err2().meth1((12, 17)))
        self.assertRaises(OverrideError, lambda:
                D_diamond_override_err3().meth1((12, 17)))

    def test_auto_override(self):
        self.assertEqual(B_auto_override().meth_1('abc', (4, 2)), 1)
        obj = B_auto_override_err()
        self.assertRaises(OverrideError, lambda: obj.meth_1('abc', (4, 2)))
        self.assertEqual(obj.meth_2('defg'), 12)

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
        from testhelpers import override_testhelper # shall not raise error
        def _test_err():
            from testhelpers import override_testhelper_err
        def _test_err2():
            from testhelpers import override_testhelper_err2

        self.assertRaises(OverrideError, _test_err)
        self.assertRaises(NameError, _test_err2)

        pytypes.check_override_at_class_definition_time = tmp


class TestStubfile(unittest.TestCase):
    """
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
    """

    def test_plain_2_7_stub(self):
        from testhelpers import stub_testhelper_py2 as stub_py2

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
        self.assertRaises(InputTypeError, lambda:
                stub_py2.class1_py2.static_meth_py2(66, ('efg',)))
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
        self.assertRaises(InputTypeError, lambda:
                stub_py2.class1_py2.class1_inner_py2.inner_static_meth_py2(66, ('efg',)))
        hints = get_type_hints(
                stub_py2.class1_py2.class1_inner_py2.inner_static_meth_py2)
        self.assertEqual(hints['c'], str)
        self.assertEqual(hints['d'], float)
        self.assertEqual(hints['return'], int)
        self.assertEqual(7, cl1.class1_inner_py2.inner_static_meth_py2(66.1, 'efg'))
        self.assertRaises(InputTypeError, lambda:
                cl1.class1_inner_py2.inner_static_meth_py2(66, ('efg',)))
        self.assertEqual(
                hints, get_type_hints(cl1.class1_inner_py2.inner_static_meth_py2))
        cl1_inner = stub_py2.class1_py2.class1_inner_py2()
        self.assertEqual(7, cl1_inner.inner_static_meth_py2(66.1, 'efg'))
        self.assertRaises(InputTypeError, lambda:
                cl1_inner.inner_static_meth_py2(66, ('efg',)))
        self.assertEqual(hints, get_type_hints(cl1_inner.inner_static_meth_py2))

        # Test classmethod:
        self.assertEqual(462.0, stub_py2.class1_py2.class_meth_py2('ghi', 77))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.class1_py2.class_meth_py2(99, 77))

        # Test subclass and class-typed parameter:
        cl2 = stub_py2.class2_py2()
        hints = get_type_hints(cl2.meth2b_py2)
        self.assertEqual(hints['b'], stub_py2.class1_py2)
        self.assertTrue(cl2.meth2b_py2(cl1).startswith(
                '<testhelpers.stub_testhelper_py2.class1_py2'))
        self.assertRaises(InputTypeError, lambda: cl2.meth2b_py2('cl1'))

        self.assertIsNone(stub_py2.testfunc_None_ret_py2(2, 3.0))
        self.assertEqual(stub_py2.testfunc_None_arg_py2(4, None), 16)
        self.assertEqual(stub_py2.testfunc_class_in_list_py2([cl1]), 1)
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_class_in_list_py2((cl1,)))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_class_in_list_py2(cl1))


# Todo: Add some of these tests for stubfile
# 	def test_get_types_plain_2_7_stub(self):
# 		from testhelpers import stub_testhelper_py2 as stub_py2
# 		tc = testClass('mnop')
# 		tc2 = testClass2('qrst')
# 		tc3 = testClass3()
# 		self.assertEqual(get_types(testfunc), (Tuple[int, Real, str], Tuple[int, Real]))
# 		self.assertEqual(get_types(testfunc2), (Tuple[int, Real, testClass], Tuple[int, float]))
# 		self.assertEqual(get_types(testfunc4), (Any, Any))
# 		self.assertEqual(get_types(tc2.testmeth), (Tuple[int, Real], str))
# 		self.assertEqual(get_types(testClass2.testmeth), (Tuple[int, Real], str))
# 		self.assertEqual(get_types(tc3.testmeth), (Any, Any))
# 		self.assertEqual(get_types(testClass3Base.testmeth), (Tuple[int, Real], Union[str, int]))
# 		self.assertEqual(get_types(tc.testmeth2), (Tuple[int, Real], str))
# 		self.assertEqual(get_types(tc.testmeth_class), (Tuple[int, Real], str))
# 		self.assertEqual(get_types(tc.testmeth_class2), (Tuple[int, Real], str))
# 		self.assertEqual(get_types(tc.testmeth_static), (Tuple[int, Real], str))
# 		self.assertEqual(get_types(tc.testmeth_static2), (Tuple[int, Real], str))
# 		self.assertEqual(get_types(testfunc), (Tuple[int, Real, str], Tuple[int, Real]))

    def test_sequence_plain_2_7_stub(self):
        from testhelpers import stub_testhelper_py2 as stub_py2
        self.assertEqual(stub_py2.testfunc_Seq_arg_py2(((3, 'ab'), (8, 'qvw'))), 2)
        self.assertEqual(
                stub_py2.testfunc_Seq_arg_py2([(3, 'ab'), (8, 'qvw'), (4, 'cd')]), 3)
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_Seq_arg_py2({(3, 'ab'), (8, 'qvw')}))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_Seq_arg_py2(((3, 'ab'), (8, 'qvw', 2))))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_Seq_arg_py2([(3, 1), (8, 'qvw'), (4, 'cd')]))
        self.assertEqual(stub_py2.testfunc_Seq_ret_List_py2(7, 'mno'), [7, 'mno'])
        self.assertEqual(stub_py2.testfunc_Seq_ret_Tuple_py2(3, 'mno'), (3, 'mno'))
        self.assertRaises(ReturnTypeError, lambda:
                stub_py2.testfunc_Seq_ret_err_py2(29, 'def'))

    def test_iterable_plain_2_7_stub(self):
        from testhelpers import stub_testhelper_py2 as stub_py2
        self.assertEqual(stub_py2.testfunc_Iter_arg_py2((9, 8, 7, 6), 'vwxy'),
                [9, 8, 7, 6])
        self.assertEqual(stub_py2.testfunc_Iter_str_arg_py2('defg'),
                [100, 101, 102, 103])
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_Iter_arg_py2((9, '8', 7, 6), 'vwxy'))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_Iter_arg_py2(7, 'vwxy'))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_Iter_arg_py2([9, 8, 7, '6'], 'vwxy'))
        self.assertEqual(stub_py2.testfunc_Iter_arg_py2([9, 8, 7, 6], 'vwxy'),
                [9, 8, 7, 6])
        res = stub_py2.testfunc_Iter_arg_py2({9, 8, 7, 6}, 'vwxy'); res.sort()
        self.assertEqual(res, [6, 7, 8, 9])
        res = stub_py2.testfunc_Iter_arg_py2(
                {19: 'a', 18: 'b', 17: 'c', 16: 'd'}, 'vwxy')
        res.sort()
        self.assertEqual(res, [16, 17, 18, 19])
        self.assertEqual(stub_py2.testfunc_Iter_ret_py2(), [1, 2, 3, 4, 5])
        self.assertRaises(ReturnTypeError, lambda:
                stub_py2.testfunc_Iter_ret_err_py2())
        ti = test_iterable((2, 4, 6, 'a'))
        self.assertRaises(ReturnTypeError, lambda:
                stub_py2.testfunc_Iter_arg_py2(ti, 'vwxy'))
        # tia = stub_py2.test_iterable_annotated_py2((3, 6, 9))
        # self.assertEqual(stub_py2.testfunc_Iter_arg_py2(tia, 'vwxy'), [3, 6, 9])

    def test_dict_plain_2_7_stub(self):
        from testhelpers import stub_testhelper_py2 as stub_py2
        self.assertIsNone(stub_py2.testfunc_Dict_arg_py2(5, {'5': 4, 'c': '8'}))
        self.assertIsNone(stub_py2.testfunc_Dict_arg_py2(5, {'5': 'A', 'c': '8'}))
        self.assertIsNone(stub_py2.testfunc_Mapping_arg_py2(7, {'7': 4, 'c': '8'}))
        self.assertIsNone(stub_py2.testfunc_Mapping_arg_py2(5, {'5': 'A', 'c': '8'}))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_Dict_arg_py2(5, {4: 4, 3: '8'}))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_Dict_arg_py2(5, {'5': (4,), 'c': '8'}))
        self.assertEqual(stub_py2.testfunc_Dict_ret_py2('defg'),
                {'defgdefg': 'defg', 'defg': 4})
        self.assertRaises(ReturnTypeError, lambda:
                stub_py2.testfunc_Dict_ret_err_py2(6))

    def test_callable_plain_2_7_stub(self):
        from testhelpers import stub_testhelper_py2 as stub_py2
        def clb(s, i):
            # type: (str, int) -> str
            return '_'+s+'*'*i
        
        def clb2(s, i):
            # type: (str, str) -> str
            return '_'+s+'*'*i
        
        def clb3(s, i):
            # type: (str, int) -> int
            return '_'+s+'*'*i

        self.assertTrue(is_of_type(clb, typing.Callable[[str, int], str]))
        self.assertFalse(is_of_type(clb, typing.Callable[[str, str], str]))
        self.assertFalse(is_of_type(clb, typing.Callable[[str, int], float]))

        self.assertEqual(
                stub_py2.testfunc_Callable_arg_py2(clb, 'pqrs'), '_pqrs****')
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_Callable_arg_py2(clb2, 'pqrs'))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_Callable_arg_py2(clb3, 'pqrs'))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_Callable_call_err_py2(clb, 'tuvw'))
        self.assertEqual(stub_py2.testfunc_Callable_arg_py2(
                lambda s, i: '__'+s+'-'*i, 'pqrs'), '__pqrs----')
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_Callable_call_err_py2(
                lambda s, i: '__'+s+'-'*i, 'tuvw'))
        fnc = stub_py2.testfunc_Callable_ret_py2(5, 'qvwx')
        self.assertEqual(fnc.__class__.__name__, 'function')
        self.assertEqual(fnc.__name__, 'm')
        self.assertRaises(ReturnTypeError, lambda:
                stub_py2.testfunc_Callable_ret_err_py2())

    def test_generator_plain_2_7_stub(self):
        from testhelpers import stub_testhelper_py2 as stub_py2
        test_gen = stub_py2.testfunc_Generator_py2()
        self.assertIsNone(test_gen.send(None))
        self.assertEqual(test_gen.send('abc'), 3)
        self.assertEqual(test_gen.send('ddffd'), 5)
        self.assertRaises(InputTypeError, lambda: test_gen.send(7))
        test_gen2 = stub_py2.testfunc_Generator_py2()
        self.assertIsNone(test_gen2.next()
                if hasattr(test_gen2, 'next') else test_gen2.__next__())
        self.assertEqual(test_gen2.send('defg'), 4)
        self.assertRaises(ReturnTypeError, lambda: test_gen2.send('fail'))
        self.assertRaises(TypeCheckError, lambda:
                stub_py2.testfunc_Generator_arg_py2(test_gen))
        self.assertRaises(TypeCheckError, lambda:
                stub_py2.testfunc_Generator_ret_py2())

    def test_custom_generic_plain_2_7_stub(self):
        from testhelpers import stub_testhelper_py2 as stub_py2
        self.assertEqual(stub_py2.testfunc_Generic_arg_py2(
                stub_py2.Custom_Generic_py2[str]('abc')), 'abc')
        self.assertEqual(stub_py2.testfunc_Generic_ret_py2(5).v(), 5)
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_Generic_arg_py2(Custom_Generic[int](9)))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_Generic_arg_py2(Custom_Generic(7)))
        self.assertRaises(ReturnTypeError, lambda:
                stub_py2.testfunc_Generic_ret_err_py2(8))

    def test_property_plain_2_7_stub(self):
        from testhelpers import stub_testhelper_py2 as stub_py2
        tcp = stub_py2.testClass_property_py2()
        tcp.testprop_py2 = 7
        self.assertEqual(tcp.testprop_py2, 7)
        def tcp_prop1_py2(): tcp.testprop_py2 = 7.2
        self.assertRaises(InputTypeError, tcp_prop1_py2)
        tcp._testprop_py2 = 'abc'
        self.assertRaises(ReturnTypeError, lambda: tcp.testprop_py2)

        tcp.testprop2_py2 = 'def'
        self.assertEqual(tcp.testprop2_py2, 'def')
        tcp.testprop2_py2 = 7.2
        self.assertRaises(ReturnTypeError, lambda: tcp.testprop2_py2)

        tcp.testprop3_py2 = (22, 'ghi')
        self.assertEqual(tcp.testprop3_py2, (22, 'ghi'))
        def tcp_prop3_py2(): tcp.testprop3_py2 = 9
        self.assertRaises(InputTypeError, tcp_prop3_py2)
        tcp._testprop3_py2 = 9
        self.assertRaises(ReturnTypeError, lambda: tcp.testprop3_py2)

        tcp_ch = stub_py2.testClass_property_class_check_py2()
        tcp_ch.testprop_py2 = 17
        self.assertEqual(tcp_ch.testprop_py2, 17)
        def tcp_ch_prop_py2(): tcp_ch.testprop_py2 = 71.2
        self.assertRaises(InputTypeError, tcp_ch_prop_py2)
        tcp_ch._testprop_py2 = 'abc'
        self.assertRaises(ReturnTypeError, lambda: tcp_ch.testprop_py2)

        tcp_ch.testprop2_py2 = 7.2
        self.assertRaises(ReturnTypeError, lambda: tcp_ch.testprop2_py2)

        self.assertEqual(get_member_types(tcp, 'testprop_py2'), (Tuple[int], type(None)))
        self.assertEqual(get_member_types(tcp, 'testprop_py2', True), (Tuple[()], int))

    def test_varargs_plain_2_7_stub(self):
        from testhelpers import stub_testhelper_py2 as stub_py2
        self.assertEqual(stub_py2.testfunc_varargs1_py2(16.4, 2, 3.2), (3, 104.96))
        self.assertEqual(stub_py2.testfunc_varargs1_py2(), (0, 1.0))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_varargs1_py2((16.4, 2, 3.2)))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_varargs1_py2(16.4, '2', 3.2))
        self.assertEqual(stub_py2.testfunc_varargs2_py2('cdef', 3, None, 5, 4, 7, 17, -2),
                (-4760, 'cdefcdefcdef'))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_varargs2_py2('cdef', 3, 'a', 5, 4, 7, 17, -2))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_varargs2_py2('cdef', 3, None, (5, 4, 7, 17, -2)))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_varargs2_py2('cdef', 3, None, 5, 4, 7.1, 17, -2))
        self.assertEqual(stub_py2.testfunc_varargs3_py2(
                14, 3, -4, a=8, ab=7.7, q=-3.2), ('abababab', 7.7))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_varargs3_py2(14, 3.2, -4, a=8, b=7.7, q=-3.2))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_varargs3_py2((14, 3, -4), a=8, b=7.7, q=-3.2))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_varargs3_py2(14, 3, -4, a=8, b='7.7', q=-3.2))
        self.assertEqual(stub_py2.testfunc_varargs4_py2(cx = 7, d = 9), 7)
        self.assertEqual(stub_py2.testfunc_varargs4_py2(cx = 7.5, d = 9), 7.5)
        self.assertEqual(stub_py2.testfunc_varargs4_py2(), 0)
        self.assertRaises(InputTypeError, lambda: stub_py2.testfunc_varargs4_py2(2, 3))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_varargs4_py2(cx = 7.1, d = '9'))
        self.assertEqual(stub_py2.testfunc_varargs5_py2(
                3, 'qvw', 3.3, 3.1, 2.778, 9, v=6, x=-8, qvw=99), [4, 1, 99])
        self.assertRaises(InputTypeError, lambda: stub_py2.testfunc_varargs5_py2(
                3, 'qvw', 3.3, 3.1, 2.778, 9, v=6.2, x=-8, qvw=99))
        self.assertRaises(InputTypeError, lambda: stub_py2.testfunc_varargs5_py2(
                3, 3, 3.3, 3.1, 2.778, 9, v=6, x=-8, qvw=99))
        self.assertRaises(InputTypeError, lambda: stub_py2.testfunc_varargs5_py2(
                3, 'qvw', (3.3, 3.1, 2.778, 9), v=6, x=-8, qvw=99))
        self.assertRaises(InputTypeError, lambda: stub_py2.testfunc_varargs5_py2())
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_varargs_err_py2(
                3.0, 'qvw', 3.3, 9, v=6, x=-8, qvw=9.9))
        self.assertRaises(ReturnTypeError, lambda: stub_py2.testfunc_varargs_err_py2(
                3, 'qvw', 3.3, 3.1, 2.778, 9, v=6, x=-8, qvw=99))
        tcv = stub_py2.testclass_vararg_py2()
        self.assertEqual(tcv.testmeth_varargs1_py2(
                ('k', 7), ('bxx', 19), ('bxy', 27)), 126)
        self.assertEqual(tcv.testmeth_varargs1_py2(), -19)
        self.assertRaises(InputTypeError, lambda:
                tcv.testmeth_varargs1_py2(('k', 7), 19, ('bxy', 27)))
        self.assertEqual(tcv.testmeth_varargs2_py2(
                2, 'xt', 1.2, 1.4, -9.2, cx=8, xt=7), [3, 4, 7, 20])
        self.assertRaises(InputTypeError, lambda:
                tcv.testmeth_varargs2_py2(2, 'xt', 1.2, 1.4, -9.2, cx=8.2, xt=7))
        self.assertEqual(stub_py2.testclass_vararg_py2.testmeth_varargs_static1_py2(
                10, 4, 1.0, -4.2), (4, -168.0))
        self.assertEqual(stub_py2.testclass_vararg_py2.testmeth_varargs_static1_py2(),
                (0, 1.0))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testclass_vararg_py2.testmeth_varargs_static1_py2(
                (10, 4, 1.0, -4.2)))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testclass_vararg_py2.testmeth_varargs_static1_py2(
                '10, 4', 1.0, -4.2))
        self.assertEqual(stub_py2.testclass_vararg_py2.testmeth_varargs_static2_py2(
                0, 'cx', 1.2, -9.2, cx=2, xt=7), [2, 3, 2])
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testclass_vararg_py2.testmeth_varargs_static2_py2(
                0, 'cx', 1.2, -9.2, cx=2.1, xt=7))
        self.assertEqual(
                stub_py2.testclass_vararg_py2.testmeth_varargs_class1_py2(), -19)
        self.assertEqual(stub_py2.testclass_vararg_py2.testmeth_varargs_class1_py2(
                ('abc', -12), ('txxt', 2)), -47)
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testclass_vararg_py2.testmeth_varargs_class1_py2(
                ('abc', -12.1), ('txxt', 2)))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testclass_vararg_py2.testmeth_varargs_class1_py2(
                ('abc', -12), 'txxt'))
        self.assertEqual(stub_py2.testclass_vararg_py2.testmeth_varargs_class2_py2(
                1, 'xt', .2, -92, cx=2, xt=7), [2, 3, 7, 20])
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testclass_vararg_py2.testmeth_varargs_class2_py2())
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testclass_vararg_py2.testmeth_varargs_class2_py2(
                0, 'cx', 1.2, -9.2, cx=2, xt=.7))
        tcv.prop1_py2 = 'test_prop1'
        self.assertEqual(tcv.prop1_py2, 'test_prop1')
        def _set_prop1_py2(): tcv.prop1_py2 = 8
        self.assertRaises(InputTypeError, _set_prop1_py2)
        tcv._prop1_py2 = 8
        self.assertRaises(ReturnTypeError, lambda: tcv.prop1_py2)

    def test_varargs_check_argument_types_plain_2_7_stub(self):
        from testhelpers import stub_testhelper_py2 as stub_py2
        self.assertEqual(stub_py2.testfunc_varargs_ca1_py2(16.4, 2, 3.2), (3, 104.96))
        self.assertEqual(stub_py2.testfunc_varargs_ca1_py2(), (0, 1.0))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_varargs_ca1_py2((16.4, 2, 3.2)))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_varargs_ca1_py2(16.4, '2', 3.2))
        self.assertEqual(stub_py2.testfunc_varargs_ca2_py2(
                'cdef', 3, None, 5, 4, 7, 17, -2), (-4760, 'cdefcdefcdef'))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_varargs_ca2_py2('cdef', 3, 'a', 5, 4, 7, 17, -2))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_varargs_ca2_py2('cdef', 3, None, (5, 4, 7, 17, -2)))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_varargs_ca2_py2('cdef', 3, None, 5, 4, 7.1, 17, -2))
        self.assertEqual(stub_py2.testfunc_varargs_ca3_py2(
                14, 3, -4, a=8, ab=7.7, q=-3.2), ('abababab', 7.7))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_varargs_ca3_py2(14, 3.2, -4, a=8, b=7.7, q=-3.2))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_varargs_ca3_py2((14, 3, -4), a=8, b=7.7, q=-3.2))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_varargs_ca3_py2(14, 3, -4, a=8, b='7.7', q=-3.2))
        self.assertEqual(stub_py2.testfunc_varargs_ca4_py2(cx = 7, d = 9), 7)
        self.assertEqual(stub_py2.testfunc_varargs_ca4_py2(cx = 7.5, d = 9), 7.5)
        self.assertEqual(stub_py2.testfunc_varargs_ca4_py2(), 0)
        # In this case it's an ordinary type-error, because Python catches it before
        # pytypes gets hands on it to make a more sophisticated InputTypeError:
        self.assertRaises(TypeError, lambda: stub_py2.testfunc_varargs_ca4_py2(2, 3))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testfunc_varargs_ca4_py2(cx = 7.1, d = '9'))
        self.assertEqual(stub_py2.testfunc_varargs_ca5_py2(
                3, 'qvw', 3.3, 3.1, 2.778, 9, v=6, x=-8, qvw=99), [4, 1, 99])
        self.assertRaises(InputTypeError, lambda: stub_py2.testfunc_varargs_ca5_py2(
                3, 'qvw', 3.3, 3.1, 2.778, 9, v=6.2, x=-8, qvw=99))
        self.assertRaises(InputTypeError, lambda: stub_py2.testfunc_varargs_ca5_py2(
                3, 3, 3.3, 3.1, 2.778, 9, v=6, x=-8, qvw=99))
        self.assertRaises(InputTypeError, lambda: stub_py2.testfunc_varargs_ca5_py2(
                3, 'qvw', (3.3, 3.1, 2.778, 9), v=6, x=-8, qvw=99))
        # In this case it's an ordinary type-error, because Python catches it before
        # pytypes gets hands on it to make a more sophisticated InputTypeError:
        self.assertRaises(TypeError, lambda: stub_py2.testfunc_varargs_ca5_py2())
        tcv = stub_py2.testclass_vararg_ca_py2()
        self.assertEqual(tcv.testmeth_varargs_ca1_py2(
                ('k', 7), ('bxx', 19), ('bxy', 27)), 123)
        self.assertEqual(tcv.testmeth_varargs_ca1_py2(), -22)
        self.assertRaises(InputTypeError, lambda:
                tcv.testmeth_varargs_ca1_py2(('k', 7), 19, ('bxy', 27)))
        self.assertEqual(tcv.testmeth_varargs_ca2_py2(2, 'xt', 1.2, 1.4, -9.2, cx=8, xt=7),
                [3, 4, 7, 23])
        self.assertRaises(InputTypeError, lambda:
                tcv.testmeth_varargs_ca2_py2(2, 'xt', 1.2, 1.4, -9.2, cx=8.2, xt=7))
        self.assertEqual(stub_py2.testclass_vararg_ca_py2.testmeth_varargs_static_ca1_py2(
                10, 4, 1.0, -4.2), (4, -168.0))
        self.assertEqual(stub_py2.testclass_vararg_ca_py2.testmeth_varargs_static_ca1_py2(),
                (0, 1.0))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testclass_vararg_ca_py2.testmeth_varargs_static_ca1_py2(
                (10, 4, 1.0, -4.2)))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testclass_vararg_ca_py2.testmeth_varargs_static_ca1_py2(
                '10, 4', 1.0, -4.2))
        self.assertEqual(stub_py2.testclass_vararg_ca_py2.testmeth_varargs_static_ca2_py2(
                0, 'cx', 1.2, -9.2, cx=2, xt=7), [2, 3, 2])
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testclass_vararg_ca_py2.testmeth_varargs_static_ca2_py2(
                0, 'cx', 1.2, -9.2, cx=2.1, xt=7))
        self.assertEqual(
                stub_py2.testclass_vararg_ca_py2.testmeth_varargs_class_ca1_py2(), -22)
        self.assertEqual(stub_py2.testclass_vararg_ca_py2.testmeth_varargs_class_ca1_py2(
                ('abc', -12), ('txxt', 2)), -50)
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testclass_vararg_ca_py2.testmeth_varargs_class_ca1_py2(
                ('abc', -12.1), ('txxt', 2)))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testclass_vararg_ca_py2.testmeth_varargs_class_ca1_py2(
                ('abc', -12), 'txxt'))
        self.assertEqual(stub_py2.testclass_vararg_ca_py2.testmeth_varargs_class_ca2_py2(
                1, 'xt', .2, -92, cx=2, xt=7), [2, 3, 7, 23])
        # In this case it's an ordinary type-error, because Python catches it before
        # pytypes gets hands on it to make a more sophisticated InputTypeError:
        self.assertRaises(TypeError, lambda:
                stub_py2.testclass_vararg_ca_py2.testmeth_varargs_class_ca2_py2())
        self.assertRaises(InputTypeError, lambda:
                stub_py2.testclass_vararg_ca_py2.testmeth_varargs_class_ca2_py2(
                0, 'cx', 1.2, -9.2, cx=2, xt=.7))
        tcv.prop_ca1_py2 = 'test_prop1'
        self.assertEqual(tcv.prop_ca1_py2, 'test_prop1')
        def _set_prop1_py2(): tcv.prop_ca1_py2 = 8
        self.assertRaises(InputTypeError, _set_prop1_py2)
        # No point in checking for ReturnTypeError here;
        # check_argument_types wouldn't catch it.

    def test_defaults_inferred_types_plain_2_7_stub(self):
        tmp = pytypes.infer_default_value_types
        pytypes.infer_default_value_types = True

        from testhelpers import stub_testhelper_py2 as stub_py2
        self.assertEqual(get_types(stub_py2.func_defaults_typecheck_py2),
                (Tuple[str, Any, int, float], str))
        self.assertEqual(pytypes.get_type_hints(stub_py2.func_defaults_typecheck_py2),
                        {'a': str, 'c': int, 'return': str, 'd': float})
        self.assertEqual(stub_py2.func_defaults_typecheck_py2('qvw', 'abc', 2, 1.5),
                'qvwabcabc')
        self.assertRaises(InputTypeError, lambda:
                stub_py2.func_defaults_typecheck_py2('qvw', 'abc', 3.5))

        self.assertRaises(InputTypeError, lambda:
                stub_py2.func_defaults_typecheck_py2('qvw', 'abc', 3.5, 4.1))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.func_defaults_typecheck_py2(7, 'qvw'))

        self.assertEqual(stub_py2.func_defaults_checkargs_py2('qvw', 'abc', 3, 1.5),
                'qvwabcabcabc')
        self.assertRaises(InputTypeError, lambda:
                stub_py2.func_defaults_checkargs_py2('qvw', 'abc', 3.5))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.func_defaults_checkargs_py2('qvw', 'abc', 3.5, 4.1))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.func_defaults_checkargs_py2(7, 'qvw'))

        self.assertEqual(get_types(stub_py2.func_defaults_annotations_py2),
                (Tuple[str, Any, int], str))
        self.assertEqual(pytypes.get_type_hints(stub_py2.func_defaults_annotations_py2),
                {'a': str, 'c': int, 'return': str})
        self.assertEqual(stub_py2.func_defaults_annotations_py2.__annotations__,
                {'a': str, 'return': str})

        pytypes.infer_default_value_types = False

        self.assertEqual(get_types(stub_py2.func_defaults_typecheck_py2),
                (Tuple[str, Any, Any, Any], str))
        self.assertEqual(pytypes.get_type_hints(stub_py2.func_defaults_typecheck_py2),
                {'a': str, 'return': str})
        self.assertEqual(stub_py2.func_defaults_typecheck_py2('qvw', 'abc', 3.5),
                'invalid')
        self.assertEqual(stub_py2.func_defaults_typecheck_py2('qvw', 'abc', 3.5, 4.1),
                'invalid')
        self.assertRaises(InputTypeError, lambda:
                stub_py2.func_defaults_typecheck_py2(7, 'qvw'))

        self.assertEqual(stub_py2.func_defaults_checkargs_py2('qvw', 'abc', 3, 1.5),
                'qvwabcabcabc')
        self.assertEqual(stub_py2.func_defaults_checkargs_py2('qvw', 'abc', 3.5),
                'invalid')
        self.assertEqual(stub_py2.func_defaults_checkargs_py2('qvw', 'abc', 3.5, 4.1),
                'invalid')
        self.assertRaises(InputTypeError, lambda:
                stub_py2.func_defaults_checkargs_py2(7, 'qvw'))

        self.assertEqual(get_types(stub_py2.func_defaults_annotations_py2),
                (Tuple[str, Any, Any], str))
        self.assertEqual(pytypes.get_type_hints(
                stub_py2.func_defaults_annotations_py2), {'a': str, 'return': str})
        self.assertEqual(stub_py2.func_defaults_annotations_py2.__annotations__,
                {'a': str, 'return': str})

        pytypes.infer_default_value_types = tmp

    def test_annotations_from_stubfile_plain_2_7_stub(self):
        from testhelpers import stub_testhelper_py2 as stub_py2
        self.assertEqual(stub_py2.func_defaults_annotations_py2.__annotations__,
                {'a': str, 'return': str})
        self.assertEqual(stub_py2.testfunc_annotations_from_stubfile_by_decorator_py2.
                __annotations__, {'a': str, 'b': int, 'return': int})

    def test_typecheck_parent_type_plain_2_7_stub(self):
        from testhelpers import stub_testhelper_py2 as stub_py2
        always_check_parent_types_tmp = pytypes.always_check_parent_types
        pytypes.always_check_parent_types = False

        self.assertRaises(InputTypeError, lambda:
                stub_py2.B_override_check_arg_py2().meth1_py2(17.7))
        self.assertEqual(stub_py2.B_no_override_check_arg_py2().meth1_py2(17.7), 4)
        self.assertRaises(InputTypeError, lambda:
                stub_py2.B_override_typechecked_py2().meth1_py2(17.7))
        self.assertEqual(stub_py2.B_no_override_typechecked_py2().meth1_py2(17.7), 4)
        self.assertEqual(stub_py2.B_override_with_type_check_arg_py2().meth1_py2(17.7), 4)
        self.assertEqual(stub_py2.B_override_with_type_typechecked_py2().meth1_py2(17.7), 4)

        pytypes.always_check_parent_types = True

        self.assertRaises(InputTypeError, lambda:
                stub_py2.B_override_check_arg_py2().meth1_py2(17.7))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.B_no_override_check_arg_py2().meth1_py2(17.7))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.B_override_typechecked_py2().meth1_py2(17.7))
        self.assertRaises(InputTypeError, lambda:
                stub_py2.B_no_override_typechecked_py2().meth1_py2(17.7))
        self.assertEqual(stub_py2.B_override_with_type_check_arg_py2().meth1_py2(17.7), 4)
        self.assertEqual(stub_py2.B_override_with_type_typechecked_py2().meth1_py2(17.7), 4)

        pytypes.always_check_parent_types = always_check_parent_types_tmp

    def test_override_diamond_plain_2_7_stub(self):
        from testhelpers import stub_testhelper_py2 as stub_py2
        self.assertEqual(stub_py2.D_diamond_override_py2().meth1_py2((12.4, 17.7)), 12)
        self.assertRaises(OverrideError, lambda:
                stub_py2.D_diamond_override_err1_py2().meth1_py2((12, 17)))
        self.assertRaises(OverrideError, lambda:
                stub_py2.D_diamond_override_err2_py2().meth1_py2((12, 17)))
        self.assertRaises(OverrideError, lambda:
                stub_py2.D_diamond_override_err3_py2().meth1_py2((12, 17)))


    @unittest.skipUnless(sys.version_info.major >= 3 and sys.version_info.minor >= 5,
            'Only applicable in Python >= 3.5.')
    def test_plain_3_5_stub(self):
        from testhelpers import stub_testhelper as stub_py3

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
        self.assertRaises(InputTypeError, lambda:
                stub_py3.class1.static_meth(66, ('efg',)))
        hints = get_type_hints(stub_py3.class1.static_meth)
        self.assertEqual(hints['c'], str)
        self.assertEqual(hints['return'], int)

        # Test static method on instance:
        self.assertEqual(5, cl1.static_meth(66, 'efg'))
        self.assertRaises(InputTypeError, lambda: cl1.static_meth(66, ('efg',)))
        hints = get_type_hints(cl1.static_meth)
        self.assertEqual(hints['c'], str)
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
                '<testhelpers.stub_testhelper.class1 object at '))
        self.assertRaises(InputTypeError, lambda: cl2.meth2b('cl1'))
        
        self.assertEqual(stub_py3.testfunc_class_in_list([cl1]), 1)
        self.assertRaises(InputTypeError, lambda: stub_py3.testfunc_class_in_list((cl1,)))
        self.assertRaises(InputTypeError, lambda: stub_py3.testfunc_class_in_list(cl1))

    @unittest.skipUnless(sys.version_info.major >= 3 and sys.version_info.minor >= 5,
            'Only applicable in Python >= 3.5.')
    def test_property_plain_3_5_stub(self):
        from testhelpers import stub_testhelper as stub_py3
        tcp = stub_py3.testClass_property()
        tcp.testprop = 7
        self.assertEqual(tcp.testprop, 7)
        def tcp_prop1_py3(): tcp.testprop = 7.2
        self.assertRaises(InputTypeError, tcp_prop1_py3)
        tcp._testprop = 'abc'
        self.assertRaises(ReturnTypeError, lambda: tcp.testprop)

        tcp.testprop2 = 'def'
        self.assertEqual(tcp.testprop2, 'def')
        tcp.testprop2 = 7.2
        self.assertRaises(ReturnTypeError, lambda: tcp.testprop2)

        tcp.testprop3 = (22, 'ghi')
        self.assertEqual(tcp.testprop3, (22, 'ghi'))
        def tcp_prop3_py3(): tcp.testprop3 = 9
        self.assertRaises(InputTypeError, tcp_prop3_py3)
        tcp._testprop3 = 9
        self.assertRaises(ReturnTypeError, lambda: tcp.testprop3)

        tcp_ch = stub_py3.testClass_property_class_check()
        tcp_ch.testprop = 17
        self.assertEqual(tcp_ch.testprop, 17)
        def tcp_ch_prop_py3(): tcp_ch.testprop = 71.2
        self.assertRaises(InputTypeError, tcp_ch_prop_py3)
        tcp_ch._testprop = 'abc'
        self.assertRaises(ReturnTypeError, lambda: tcp_ch.testprop)

        tcp_ch.testprop2 = 7.2
        self.assertRaises(ReturnTypeError, lambda: tcp_ch.testprop2)

        self.assertEqual(get_member_types(tcp, 'testprop'), (Tuple[int], type(None)))
        self.assertEqual(get_member_types(tcp, 'testprop', True), (Tuple[()], int))

    @unittest.skipUnless(sys.version_info.major >= 3 and sys.version_info.minor >= 5,
            'Only applicable in Python >= 3.5.')
    def test_varargs_plain_3_5_stub(self):
        from testhelpers import stub_testhelper as stub_py3
        self.assertEqual(stub_py3.testfunc_varargs1(16.4, 2, 3.2), (3, 104.96))
        self.assertEqual(stub_py3.testfunc_varargs1(), (0, 1.0))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs1((16.4, 2, 3.2)))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs1(16.4, '2', 3.2))
        self.assertEqual(stub_py3.testfunc_varargs2('cdef', 3, None, 5, 4, 7, 17, -2),
                (-4760, 'cdefcdefcdef'))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs2('cdef', 3, 'a', 5, 4, 7, 17, -2))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs2('cdef', 3, None, (5, 4, 7, 17, -2)))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs2('cdef', 3, None, 5, 4, 7.1, 17, -2))
        self.assertEqual(stub_py3.testfunc_varargs3(14, 3, -4, a=8, ab=7.7, q=-3.2),
                ('abababab', 7.7))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs3(14, 3.2, -4, a=8, b=7.7, q=-3.2))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs3((14, 3, -4), a=8, b=7.7, q=-3.2))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs3(14, 3, -4, a=8, b='7.7', q=-3.2))
        self.assertEqual(stub_py3.testfunc_varargs4(cx = 7, d = 9), 7)
        self.assertEqual(stub_py3.testfunc_varargs4(cx = 7.5, d = 9), 7.5)
        self.assertEqual(stub_py3.testfunc_varargs4(), 0)
        self.assertRaises(InputTypeError, lambda: stub_py3.testfunc_varargs4(2, 3))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs4(cx = 7.1, d = '9'))
        self.assertEqual(stub_py3.testfunc_varargs5(
                3, 'qvw', 3.3, 3.1, 2.778, 9, v=6, x=-8, qvw=99), [4, 1, 99])
        self.assertRaises(InputTypeError, lambda: stub_py3.testfunc_varargs5(
                3, 'qvw', 3.3, 3.1, 2.778, 9, v=6.2, x=-8, qvw=99))
        self.assertRaises(InputTypeError, lambda: stub_py3.testfunc_varargs5(
                3, 3, 3.3, 3.1, 2.778, 9, v=6, x=-8, qvw=99))
        self.assertRaises(InputTypeError, lambda: stub_py3.testfunc_varargs5(
                3, 'qvw', (3.3, 3.1, 2.778, 9), v=6, x=-8, qvw=99))
        self.assertRaises(InputTypeError, lambda: stub_py3.testfunc_varargs5())
        self.assertRaises(InputTypeError, lambda: stub_py3.testfunc_varargs_err(
                3.0, 'qvw', 3.3, 9, v=6, x=-8, qvw=9.9))
        self.assertRaises(ReturnTypeError, lambda: stub_py3.testfunc_varargs_err(
                3, 'qvw', 3.3, 3.1, 2.778, 9, v=6, x=-8, qvw=99))

        # Python 3 specific: kw-only args:
        self.assertEqual(stub_py3.testfunc_varargs6(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b1=27, b2='abc', ac=19), [4, 3, 19, 27, 3])
        self.assertEqual(stub_py3.testfunc_varargs6(2, 'ac', 1.2, 3, 4, 6.7,
                a=2, b=3, b1=27, b2='abc', ac=19), [4, 1, 19, 27, 3])
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs6(2.1, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b1=27, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda: stub_py3.testfunc_varargs6())
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs6(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs6(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b1=1.5, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs6(2, 'ac', 1.2, (3.4, 4.5, 6.7),
                a=2, b=3, b1=1.5, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs6(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3.5, b1=1.5, b2='abc', ac=19))

        self.assertEqual(stub_py3.testfunc_varargs6b(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b1=27, b2='abc', ac=19), [4, 3, 19, 27, 3])
        self.assertEqual(stub_py3.testfunc_varargs6b(2, 'ac', 1.2, 3, 4, 6.7,
                a=2, b=3, b1=27, b2='abc', ac=19), [4, 1, 19, 27, 3])
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs6b(2.1, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b1=27, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda: stub_py3.testfunc_varargs6b())
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs6b(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs6b(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b1=1.5, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs6b(2, 'ac', 1.2, (3.4, 4.5, 6.7),
                a=2, b=3, b1=1.5, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs6b(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3.5, b1=1.5, b2='abc', ac=19))
        
        tcv = stub_py3.testclass_vararg()
        self.assertEqual(tcv.testmeth_varargs1(('k', 7), ('bxx', 19), ('bxy', 27)), 130)
        self.assertEqual(tcv.testmeth_varargs1(), -15)
        self.assertRaises(InputTypeError, lambda:
                tcv.testmeth_varargs1(('k', 7), 19, ('bxy', 27)))
        self.assertEqual(tcv.testmeth_varargs2(2, 'xt', 1.2, 1.4, -9.2, cx=8, xt=7),
                [3, 4, 7, 16])
        self.assertRaises(InputTypeError, lambda:
                tcv.testmeth_varargs2(2, 'xt', 1.2, 1.4, -9.2, cx=8.2, xt=7))
        self.assertEqual(stub_py3.testclass_vararg.testmeth_varargs_static1(
                10, 4, 1.0, -4.2), (4, -168.0))
        self.assertEqual(stub_py3.testclass_vararg.testmeth_varargs_static1(), (0, 1.0))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testclass_vararg.testmeth_varargs_static1((10, 4, 1.0, -4.2)))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testclass_vararg.testmeth_varargs_static1('10, 4', 1.0, -4.2))
        self.assertEqual(stub_py3.testclass_vararg.testmeth_varargs_static2(
                0, 'cx', 1.2, -9.2, cx=2, xt=7), [2, 3, 2])
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testclass_vararg.testmeth_varargs_static2(
                0, 'cx', 1.2, -9.2, cx=2.1, xt=7))
        self.assertEqual(stub_py3.testclass_vararg.testmeth_varargs_class1(), -15)
        self.assertEqual(stub_py3.testclass_vararg.testmeth_varargs_class1(
                ('abc', -12), ('txxt', 2)), -43)
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testclass_vararg.testmeth_varargs_class1(
                ('abc', -12.1), ('txxt', 2)))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testclass_vararg.testmeth_varargs_class1(('abc', -12), 'txxt'))
        self.assertEqual(stub_py3.testclass_vararg.testmeth_varargs_class2(
                1, 'xt', .2, -92, cx=2, xt=7), [2, 3, 7, 16])
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testclass_vararg.testmeth_varargs_class2())
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testclass_vararg.testmeth_varargs_class2(
                0, 'cx', 1.2, -9.2, cx=2, xt=.7))
        tcv.prop1 = 'test_prop1'
        self.assertEqual(tcv.prop1, 'test_prop1')
        def _set_prop1(): tcv.prop1 = 8
        self.assertRaises(InputTypeError, _set_prop1)
        tcv._prop1 = 8
        self.assertRaises(ReturnTypeError, lambda: tcv.prop1)

    @unittest.skipUnless(sys.version_info.major >= 3 and sys.version_info.minor >= 5,
            'Only applicable in Python >= 3.5.')
    def test_varargs_check_argument_types_plain_3_5_stub(self):
        from testhelpers import stub_testhelper as stub_py3
        self.assertEqual(stub_py3.testfunc_varargs_ca1(16.4, 2, 3.2), (3, 104.96))
        self.assertEqual(stub_py3.testfunc_varargs_ca1(), (0, 1.0))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs_ca1((16.4, 2, 3.2)))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs_ca1(16.4, '2', 3.2))
        self.assertEqual(stub_py3.testfunc_varargs_ca2('cdef', 3, None, 5, 4, 7, 17, -2),
                (-4760, 'cdefcdefcdef'))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs_ca2('cdef', 3, 'a', 5, 4, 7, 17, -2))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs_ca2('cdef', 3, None, (5, 4, 7, 17, -2)))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs_ca2('cdef', 3, None, 5, 4, 7.1, 17, -2))
        self.assertEqual(stub_py3.testfunc_varargs_ca3(14, 3, -4, a=8, ab=7.7, q=-3.2),
                ('abababab', 7.7))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs_ca3(14, 3.2, -4, a=8, b=7.7, q=-3.2))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs_ca3((14, 3, -4), a=8, b=7.7, q=-3.2))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs_ca3(14, 3, -4, a=8, b='7.7', q=-3.2))
        self.assertEqual(stub_py3.testfunc_varargs_ca4(cx = 7, d = 9), 7)
        self.assertEqual(stub_py3.testfunc_varargs_ca4(cx = 7.5, d = 9), 7.5)
        self.assertEqual(stub_py3.testfunc_varargs_ca4(), 0)
        # In this case it's an ordinary type-error, because Python catches it before
        # pytypes gets hands on it to make a more sophisticated InputTypeError:
        self.assertRaises(TypeError, lambda: stub_py3.testfunc_varargs_ca4(2, 3))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs_ca4(cx = 7.1, d = '9'))
        self.assertEqual(stub_py3.testfunc_varargs_ca5(
                3, 'qvw', 3.3, 3.1, 2.778, 9, v=6, x=-8, qvw=99), [4, 1, 99])
        self.assertRaises(InputTypeError, lambda: stub_py3.testfunc_varargs_ca5(
                3, 'qvw', 3.3, 3.1, 2.778, 9, v=6.2, x=-8, qvw=99))
        self.assertRaises(InputTypeError, lambda: stub_py3.testfunc_varargs_ca5(
                3, 3, 3.3, 3.1, 2.778, 9, v=6, x=-8, qvw=99))
        self.assertRaises(InputTypeError, lambda: stub_py3.testfunc_varargs_ca5(
                3, 'qvw', (3.3, 3.1, 2.778, 9), v=6, x=-8, qvw=99))
        # In this case it's an ordinary type-error, because Python catches it before
        # pytypes gets hands on it to make a more sophisticated InputTypeError:
        self.assertRaises(TypeError, lambda: stub_py3.testfunc_varargs_ca5())

        # Python 3 specific: kw-only args:
        self.assertEqual(stub_py3.testfunc_varargs_ca6(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b1=27, b2='abc', ac=19), [4, 3, 19, 27, 3])
        self.assertEqual(stub_py3.testfunc_varargs_ca6(2, 'ac', 1.2, 3, 4, 6.7,
                a=2, b=3, b1=27, b2='abc', ac=19), [4, 1, 19, 27, 3])
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs_ca6(2.1, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b1=27, b2='abc', ac=19))
        # In this case it's an ordinary type-error, because Python catches it before
        # pytypes gets hands on it to make a more sophisticated InputTypeError:
        self.assertRaises(TypeError, lambda: stub_py3.testfunc_varargs_ca6())
        self.assertRaises(TypeError, lambda:
                stub_py3.testfunc_varargs_ca6(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs_ca6(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b1=1.5, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs_ca6(2, 'ac', 1.2, (3.4, 4.5, 6.7),
                a=2, b=3, b1=1.5, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs_ca6(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3.5, b1=1.5, b2='abc', ac=19))

        self.assertEqual(stub_py3.testfunc_varargs_ca6b(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b1=27, b2='abc', ac=19), [4, 3, 19, 27, 3])
        self.assertEqual(stub_py3.testfunc_varargs_ca6b(2, 'ac', 1.2, 3, 4, 6.7,
                a=2, b=3, b1=27, b2='abc', ac=19), [4, 1, 19, 27, 3])
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs_ca6b(2.1, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b1=27, b2='abc', ac=19))
        # In this case it's an ordinary type-error, because Python catches it before
        # pytypes gets hands on it to make a more sophisticated InputTypeError:
        self.assertRaises(TypeError, lambda: stub_py3.testfunc_varargs_ca6b())
        self.assertRaises(TypeError, lambda:
                stub_py3.testfunc_varargs_ca6b(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs_ca6b(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b1=1.5, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs_ca6b(2, 'ac', 1.2, (3.4, 4.5, 6.7),
                a=2, b=3, b1=1.5, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testfunc_varargs_ca6b(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3.5, b1=1.5, b2='abc', ac=19))

        tcv = stub_py3.testclass_vararg_ca()
        self.assertEqual(
                tcv.testmeth_varargs_ca1(('k', 7), ('bxx', 19), ('bxy', 27)), 127)
        self.assertEqual(tcv.testmeth_varargs_ca1(), -18)
        self.assertRaises(InputTypeError, lambda:
                tcv.testmeth_varargs_ca1(('k', 7), 19, ('bxy', 27)))
        self.assertEqual(tcv.testmeth_varargs_ca2(2, 'xt', 1.2, 1.4, -9.2, cx=8, xt=7),
                [3, 4, 7, 19])
        self.assertRaises(InputTypeError, lambda:
                tcv.testmeth_varargs_ca2(2, 'xt', 1.2, 1.4, -9.2, cx=8.2, xt=7))
        self.assertEqual(stub_py3.testclass_vararg_ca.testmeth_varargs_static_ca1(
                10, 4, 1.0, -4.2), (4, -168.0))
        self.assertEqual(
                stub_py3.testclass_vararg_ca.testmeth_varargs_static_ca1(), (0, 1.0))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testclass_vararg_ca.testmeth_varargs_static_ca1(
                (10, 4, 1.0, -4.2)))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testclass_vararg_ca.testmeth_varargs_static_ca1(
                '10, 4', 1.0, -4.2))
        self.assertEqual(stub_py3.testclass_vararg_ca.testmeth_varargs_static_ca2(
                0, 'cx', 1.2, -9.2, cx=2, xt=7), [2, 3, 2])
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testclass_vararg_ca.testmeth_varargs_static_ca2(
                0, 'cx', 1.2, -9.2, cx=2.1, xt=7))
        self.assertEqual(stub_py3.testclass_vararg_ca.testmeth_varargs_class_ca1(), -18)
        self.assertEqual(stub_py3.testclass_vararg_ca.testmeth_varargs_class_ca1(
                ('abc', -12), ('txxt', 2)), -46)
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testclass_vararg_ca.testmeth_varargs_class_ca1(
                ('abc', -12.1), ('txxt', 2)))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testclass_vararg_ca.testmeth_varargs_class_ca1(
                ('abc', -12), 'txxt'))
        self.assertEqual(stub_py3.testclass_vararg_ca.testmeth_varargs_class_ca2(
                1, 'xt', .2, -92, cx=2, xt=7), [2, 3, 7, 19])
        # In this case it's an ordinary type-error, because Python catches it before
        # pytypes gets hands on it to make a more sophisticated InputTypeError:
        self.assertRaises(TypeError, lambda:
                stub_py3.testclass_vararg_ca.testmeth_varargs_class_ca2())
        self.assertRaises(InputTypeError, lambda:
                stub_py3.testclass_vararg_ca.testmeth_varargs_class_ca2(
                0, 'cx', 1.2, -9.2, cx=2, xt=.7))
        tcv.prop_ca1 = 'test_prop1'
        self.assertEqual(tcv.prop_ca1, 'test_prop1')
        def _set_prop1(): tcv.prop_ca1 = 8
        self.assertRaises(InputTypeError, _set_prop1)
        # No point in checking for ReturnTypeError here; check_argument_types wouldn't catch it.

    @unittest.skipUnless(sys.version_info.major >= 3 and sys.version_info.minor >= 5,
            'Only applicable in Python >= 3.5.')
    def test_defaults_inferred_types_plain_3_5_stub(self):
        tmp = pytypes.infer_default_value_types
        pytypes.infer_default_value_types = True

        from testhelpers import stub_testhelper as stub_py3
        self.assertEqual(get_types(stub_py3.func_defaults_typecheck),
                (Tuple[str, Any, int, float], str))
        self.assertEqual(pytypes.get_type_hints(stub_py3.func_defaults_typecheck),
                        {'a': str, 'c': int, 'return': str, 'd': float})
        self.assertEqual(stub_py3.func_defaults_typecheck('qvw', 'abc', 2, 1.5),
                'qvwabcabc')
        self.assertRaises(InputTypeError, lambda:
                stub_py3.func_defaults_typecheck('qvw', 'abc', 3.5))

        self.assertRaises(InputTypeError, lambda:
                stub_py3.func_defaults_typecheck('qvw', 'abc', 3.5, 4.1))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.func_defaults_typecheck(7, 'qvw'))

        self.assertEqual(stub_py3.func_defaults_checkargs('qvw', 'abc', 3, 1.5),
                'qvwabcabcabc')
        self.assertRaises(InputTypeError, lambda:
                stub_py3.func_defaults_checkargs('qvw', 'abc', 3.5))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.func_defaults_checkargs('qvw', 'abc', 3.5, 4.1))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.func_defaults_checkargs(7, 'qvw'))

        self.assertEqual(get_types(stub_py3.func_defaults_annotations),
                (Tuple[str, Any, int], str))
        self.assertEqual(pytypes.get_type_hints(stub_py3.func_defaults_annotations),
                {'a': str, 'c': int, 'return': str})
        self.assertEqual(stub_py3.func_defaults_annotations.__annotations__,
                {'a': str, 'return': str})

        pytypes.infer_default_value_types = False

        self.assertEqual(get_types(stub_py3.func_defaults_typecheck),
                (Tuple[str, Any, Any, Any], str))
        self.assertEqual(pytypes.get_type_hints(stub_py3.func_defaults_typecheck),
                {'a': str, 'return': str})
        self.assertEqual(stub_py3.func_defaults_typecheck('qvw', 'abc', 3.5),
                'invalid')
        self.assertEqual(stub_py3.func_defaults_typecheck('qvw', 'abc', 3.5, 4.1),
                'invalid')
        self.assertRaises(InputTypeError, lambda:
                stub_py3.func_defaults_typecheck(7, 'qvw'))

        self.assertEqual(stub_py3.func_defaults_checkargs('qvw', 'abc', 3, 1.5),
                'qvwabcabcabc')
        self.assertEqual(stub_py3.func_defaults_checkargs('qvw', 'abc', 3.5),
                'invalid')
        self.assertEqual(stub_py3.func_defaults_checkargs('qvw', 'abc', 3.5, 4.1),
                'invalid')
        self.assertRaises(InputTypeError, lambda:
                stub_py3.func_defaults_checkargs(7, 'qvw'))

        self.assertEqual(get_types(stub_py3.func_defaults_annotations),
                (Tuple[str, Any, Any], str))
        self.assertEqual(pytypes.get_type_hints(
                stub_py3.func_defaults_annotations), {'a': str, 'return': str})
        self.assertEqual(stub_py3.func_defaults_annotations.__annotations__,
                {'a': str, 'return': str})

        pytypes.infer_default_value_types = tmp

    @unittest.skipUnless(sys.version_info.major >= 3 and sys.version_info.minor >= 5,
            'Only applicable in Python >= 3.5.')
    def test_annotations_from_stubfile_plain_3_5_stub(self):
        from testhelpers import stub_testhelper as stub_py3
        self.assertEqual(stub_py3.func_defaults_annotations.__annotations__,
                {'a': str, 'return': str})
        self.assertEqual(stub_py3.testfunc_annotations_from_stubfile_by_decorator.
                __annotations__, {'a': str, 'b': int, 'return': int})

    @unittest.skipUnless(sys.version_info.major >= 3 and sys.version_info.minor >= 5,
            'Only applicable in Python >= 3.5.')
    def test_typecheck_parent_type_plain_3_5_stub(self):
        from testhelpers import stub_testhelper as stub_py3
        always_check_parent_types_tmp = pytypes.always_check_parent_types
        pytypes.always_check_parent_types = False

        self.assertRaises(InputTypeError, lambda:
                stub_py3.B_override_check_arg().meth1(17.7))
        self.assertEqual(stub_py3.B_no_override_check_arg().meth1(17.7), 4)
        self.assertRaises(InputTypeError, lambda:
                stub_py3.B_override_typechecked().meth1(17.7))
        self.assertEqual(stub_py3.B_no_override_typechecked().meth1(17.7), 4)
        self.assertEqual(stub_py3.B_override_with_type_check_arg().meth1(17.7), 4)
        self.assertEqual(stub_py3.B_override_with_type_typechecked().meth1(17.7), 4)

        pytypes.always_check_parent_types = True

        self.assertRaises(InputTypeError, lambda:
                stub_py3.B_override_check_arg().meth1(17.7))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.B_no_override_check_arg().meth1(17.7))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.B_override_typechecked().meth1(17.7))
        self.assertRaises(InputTypeError, lambda:
                stub_py3.B_no_override_typechecked().meth1(17.7))
        self.assertEqual(stub_py3.B_override_with_type_check_arg().meth1(17.7), 4)
        self.assertEqual(stub_py3.B_override_with_type_typechecked().meth1(17.7), 4)

        pytypes.always_check_parent_types = always_check_parent_types_tmp

    @unittest.skipUnless(sys.version_info.major >= 3 and sys.version_info.minor >= 5,
            'Only applicable in Python >= 3.5.')
    def test_override_diamond_plain_3_5_stub(self):
        from testhelpers import stub_testhelper as stub_py3
        self.assertEqual(stub_py3.D_diamond_override().meth1((12.4, 17.7)), 12)
        self.assertRaises(OverrideError, lambda:
                stub_py3.D_diamond_override_err1().meth1((12, 17)))
        self.assertRaises(OverrideError, lambda:
                stub_py3.D_diamond_override_err2().meth1((12, 17)))
        self.assertRaises(OverrideError, lambda:
                stub_py3.D_diamond_override_err3().meth1((12, 17)))


@unittest.skipUnless(sys.version_info.major >= 3 and sys.version_info.minor >= 5,
        'Only applicable in Python >= 3.5.')
class TestTypecheck_Python3_5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global py3
        from testhelpers import typechecker_testhelper_py3 as py3

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
                "23-1.1-<class 'testhelpers.typechecker_testhelper_py3.testClass'>")
        self.assertRaises(InputTypeError, lambda: tc.testmeth_class(23, '1.1'))
        self.assertEqual(tc.testmeth_class2(23, 1.1),
                "23-1.1-<class 'testhelpers.typechecker_testhelper_py3.testClass'>")
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
        self.assertEqual(typing.get_type_hints(tc.testmeth_forward),
                get_type_hints(tc.testmeth_forward))
        self.assertRaises(InputTypeError, lambda: tc.testmeth_forward(5, 7))
        self.assertRaises(InputTypeError, lambda: tc.testmeth_forward(5, tc))

    def test_staticmethod_py3(self):
        tc = py3.testClass('efgh')
        self.assertEqual(tc.testmeth_static(12, 0.7), '12-0.7-static')
        self.assertRaises(InputTypeError, lambda: tc.testmeth_static(12, [3]))
        self.assertEqual(tc.testmeth_static2(11, 1.9), '11-1.9-static')
        self.assertRaises(InputTypeError, lambda: tc.testmeth_static2(11, ('a', 'b'), 1.9))

    def test_parent_typecheck_no_override_py3(self):
        tmp = pytypes.always_check_parent_types
        pytypes.always_check_parent_types = False
        
        cl3 = py3.testClass3_no_override()
        self.assertTrue(cl3.testmeth(3, 5).startswith('3-5-'))
        self.assertTrue(cl3.testmeth(3, '5').startswith('3-5-'))
        cl3 = py3.testClass3_no_override_err()
        self.assertEqual(cl3.testmeth(3, 5), 7.5)
        self.assertEqual(cl3.testmeth(3, '5'), 7.5)
        cl3 = py3.testClass3_no_override_check_argtypes()
        self.assertTrue(cl3.testmeth(3, 5).startswith('3-5-'))
        self.assertTrue(cl3.testmeth(3, '5').startswith('3-5-'))

        pytypes.always_check_parent_types = True

        cl3 = py3.testClass3_no_override()
        self.assertTrue(cl3.testmeth(3, 5).startswith('3-5-'))
        self.assertRaises(InputTypeError, lambda: cl3.testmeth(3, '5'))
        cl3 = py3.testClass3_no_override_err()
        self.assertRaises(ReturnTypeError, lambda: cl3.testmeth(3, 5))
        self.assertRaises(InputTypeError, lambda: cl3.testmeth(3, '5'))
        cl3 = py3.testClass3_no_override_check_argtypes()
        self.assertTrue(cl3.testmeth(3, 5).startswith('3-5-'))
        self.assertRaises(InputTypeError, lambda: cl3.testmeth(3, '5'))

        pytypes.always_check_parent_types = tmp

    def test_parent_typecheck_other_signature_py3(self):
        vcc = py3.varagrs_call_class()
        self.assertRaises(InputTypeError, lambda: vcc.testmeth1(1, '2', 'a'))
        self.assertEqual(vcc.testmeth1(1, 2, 'a'), 3)
        self.assertRaises(InputTypeError, lambda: vcc.testmeth2('3', 4, q = 'b'))
        self.assertEqual(vcc.testmeth2(3, 4, q = 'b'), 7)
        self.assertRaises(InputTypeError, lambda: vcc.testmeth3(5.7, 6, 'c', k = 'd'))
        self.assertEqual(vcc.testmeth3(5, 6, 'c', k = 'd'), 11)
        self.assertRaises(InputTypeError, lambda: vcc.testmeth4(7, 8, 9, 'e', 'f'))

    def test_abstract_override_py3(self):
        tc3 = py3.testClass3()
        self.assertEqual(tc3.testmeth(1, 2.5),
                "1-2.5-<class 'testhelpers.typechecker_testhelper_py3.testClass3'>")

    def test_get_types_py3(self):
        tc = py3.testClass('mnop')
        tc2 = py3.testClass2('qrst')
        tc3 = py3.testClass3()
        self.assertEqual(get_types(py3.testfunc),
                (Tuple[int, Real, str], Tuple[int, Real]))
        self.assertEqual(get_types(py3.testfunc2),
                (Tuple[int, Real, py3.testClass], Tuple[int, float]))
        self.assertEqual(get_types(tc2.testmeth), (Tuple[int, Real], str))
        self.assertEqual(get_types(py3.testClass2.testmeth), (Tuple[int, Real], str))
        self.assertEqual(get_types(tc3.testmeth), (Any, Any))
        self.assertEqual(get_types(py3.testClass3Base.testmeth),
                (Tuple[int, Real], Union[str, int]))
        self.assertEqual(get_types(tc.testmeth2), (Tuple[int, Real], str))
        self.assertEqual(get_types(tc.testmeth_class), (Tuple[int, Real], str))
        self.assertEqual(get_types(tc.testmeth_class2), (Tuple[int, Real], str))
        self.assertEqual(get_types(tc.testmeth_static), (Tuple[int, Real], str))
        self.assertEqual(get_types(tc.testmeth_static2), (Tuple[int, Real], str))
        self.assertEqual(get_types(py3.testfunc),
                (Tuple[int, Real, str], Tuple[int, Real]))

    def test_sequence_py3(self):
        self.assertEqual(py3.testfunc_Seq_arg(((3, 'ab'), (8, 'qvw'))), 2)
        self.assertEqual(py3.testfunc_Seq_arg([(3, 'ab'), (8, 'qvw'), (4, 'cd')]), 3)
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_Seq_arg({(3, 'ab'), (8, 'qvw')}))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_Seq_arg(((3, 'ab'), (8, 'qvw', 2))))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_Seq_arg([(3, 1), (8, 'qvw'), (4, 'cd')]))
        self.assertEqual(py3.testfunc_Seq_ret_List(7, 'mno'), [7, 'mno'])
        self.assertEqual(py3.testfunc_Seq_ret_Tuple(3, 'mno'), (3, 'mno'))
        self.assertRaises(ReturnTypeError, lambda: py3.testfunc_Seq_ret_err(29, 'def'))

    def test_iterable_py3(self):
        self.assertEqual(py3.testfunc_Iter_arg((9, 8, 7, 6), 'vwxy'), [9, 8, 7, 6])
        self.assertEqual(py3.testfunc_Iter_str_arg('defg'), [100, 101, 102, 103])
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_Iter_arg((9, '8', 7, 6), 'vwxy'))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_Iter_arg(7, 'vwxy'))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_Iter_arg([9, 8, 7, '6'], 'vwxy'))
        self.assertEqual(py3.testfunc_Iter_arg([9, 8, 7, 6], 'vwxy'), [9, 8, 7, 6])
        res = py3.testfunc_Iter_arg({9, 8, 7, 6}, 'vwxy'); res.sort()
        self.assertEqual(res, [6, 7, 8, 9])
        res = py3.testfunc_Iter_arg({19: 'a', 18: 'b', 17: 'c', 16: 'd'}, 'vwxy')
        res.sort()
        self.assertEqual(res, [16, 17, 18, 19])
        self.assertEqual(py3.testfunc_Iter_ret(), [1, 2, 3, 4, 5])
        self.assertRaises(ReturnTypeError, lambda: py3.testfunc_Iter_ret_err())
        ti = py3.test_iterable((2, 4, 6, 'a'))
        self.assertRaises(ReturnTypeError, lambda: py3.testfunc_Iter_arg(ti, 'vwxy'))
        tia = py3.test_iterable_annotated((3, 6, 9))
        self.assertEqual(py3.testfunc_Iter_arg(tia, 'vwxy'), [3, 6, 9])

    def test_iterable_subclass_py3(self):
        # See https://github.com/Stewori/pytypes/issues/57
        class IntList(py3.test_iterable_subclass_TypList[int]): pass

        il = IntList() 
        il.extend(iter([1, 2, 3]))
        self.assertRaises(ReturnTypeError, lambda: il.extend(iter(['a', 'b', 'c'])))
        self.assertRaises(InputTypeError, lambda: il.extend(['d', 'e', 'f']))
        il.extend([4, 5, 6])
        self.assertEqual(il, [1, 2, 3, 4, 5, 6])

    def test_dict_py3(self):
        self.assertIsNone(py3.testfunc_Dict_arg(5, {'5': 4, 'c': '8'}))
        self.assertIsNone(py3.testfunc_Dict_arg(5, {'5': 'A', 'c': '8'}))
        self.assertIsNone(py3.testfunc_Mapping_arg(7, {'7': 4, 'c': '8'}))
        self.assertIsNone(py3.testfunc_Mapping_arg(5, {'5': 'A', 'c': '8'}))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_Dict_arg(5, {4: 4, 3: '8'}))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_Dict_arg(5, {'5': (4,), 'c': '8'}))
        self.assertEqual(py3.testfunc_Dict_ret('defg'), {'defgdefg': 'defg', 'defg': 4})
        self.assertRaises(ReturnTypeError, lambda: py3.testfunc_Dict_ret_err(6))

    def test_callable_py3(self):
        self.assertTrue(is_of_type(py3.pclb, typing.Callable[[str, int], str]))
        self.assertFalse(is_of_type(py3.pclb, typing.Callable[[str, str], str]))
        self.assertFalse(is_of_type(py3.pclb, typing.Callable[[str, int], float]))

        self.assertEqual(py3.testfunc_Callable_arg(py3.pclb, 'pqrs'), '_pqrs****')
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_Callable_arg(py3.pclb2, 'pqrs'))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_Callable_arg(py3.pclb3, 'pqrs'))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_Callable_call_err(py3.pclb, 'tuvw'))
        self.assertEqual(py3.testfunc_Callable_arg(
                lambda s, i: '__'+s+'-'*i, 'pqrs'), '__pqrs----')
        self.assertRaises(InputTypeError,
                lambda: py3.testfunc_Callable_call_err(lambda s, i: '__'+s+'-'*i, 'tuvw'))
        fnc = py3.testfunc_Callable_ret(5, 'qvwx')
        self.assertEqual(fnc.__class__.__name__, 'function')
        self.assertEqual(fnc.__name__, 'm')
        self.assertRaises(ReturnTypeError, lambda: py3.testfunc_Callable_ret_err())

    def test_generator_py3(self):
        test_gen = py3.testfunc_Generator()
        self.assertEqual(pytypes.deep_type(test_gen), Generator[int, Union[str, None], float])
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
        self.assertRaises(StopIteration, lambda: test_gen3.send('ret'))
        test_gen4 = py3.testfunc_Generator()
        self.assertIsNone(test_gen4.send(None))
        self.assertEqual(test_gen4.send('abcdefgh'), 8)
        self.assertRaises(ReturnTypeError, lambda: test_gen4.send('ret_fail'))

    def test_custom_generic_py3(self):
        self.assertEqual(py3.testfunc_Generic_arg(py3.Custom_Generic[str]('abc')), 'abc')
        self.assertEqual(py3.testfunc_Generic_ret(5).v(), 5)
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_Generic_arg(py3.Custom_Generic[int](9)))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_Generic_arg(py3.Custom_Generic(7)))
        self.assertRaises(ReturnTypeError, lambda: py3.testfunc_Generic_ret_err(8))

    def test_various_py3(self):
        self.assertEqual(get_type_hints(testfunc),
                {'a': int, 'c': str, 'b': Real, 'return': Tuple[int, Real]})
        self.assertEqual(pytypes.deep_type(('abc', [3, 'a', 7], 4.5)),
                Tuple[str, List[Union[int, str]], float])

    def test_property(self):
        tcp = py3.testClass_property()
        tcp.testprop = 7
        self.assertEqual(tcp.testprop, 7)
        def tcp_prop1(): tcp.testprop = 7.2
        self.assertRaises(InputTypeError, tcp_prop1)
        tcp._testprop = 'abc'
        self.assertRaises(ReturnTypeError, lambda: tcp.testprop)

        tcp.testprop2 = 'def'
        self.assertEqual(tcp.testprop2, 'def')
        tcp.testprop2 = 7.2
        self.assertRaises(ReturnTypeError, lambda: tcp.testprop2)

        tcp.testprop3 = (22, 'ghi')
        self.assertEqual(tcp.testprop3, (22, 'ghi'))
        def tcp_prop3(): tcp.testprop3 = 9
        self.assertRaises(InputTypeError, tcp_prop3)
        tcp._testprop3 = 9
        self.assertRaises(ReturnTypeError, lambda: tcp.testprop3)

        tcp_ch = py3.testClass_property_class_check()
        tcp_ch.testprop = 17
        self.assertEqual(tcp_ch.testprop, 17)
        def tcp_ch_prop(): tcp_ch.testprop = 71.2
        self.assertRaises(InputTypeError, tcp_ch_prop)
        tcp_ch._testprop = 'abc'
        self.assertRaises(ReturnTypeError, lambda: tcp_ch.testprop)

        tcp_ch.testprop2 = 7.2
        self.assertRaises(ReturnTypeError, lambda: tcp_ch.testprop2)

        self.assertEqual(get_member_types(tcp, 'testprop'), (Tuple[int], type(None)))
        self.assertEqual(get_member_types(tcp, 'testprop', True), (Tuple[()], int))

    def test_varargs(self):
        self.assertEqual(py3.testfunc_varargs1(16.4, 2, 3.2), (3, 104.96))
        self.assertEqual(py3.testfunc_varargs1(), (0, 1.0))
        self.assertRaises(InputTypeError, lambda: py3.testfunc_varargs1((16.4, 2, 3.2)))
        self.assertRaises(InputTypeError, lambda: py3.testfunc_varargs1(16.4, '2', 3.2))
        self.assertEqual(py3.testfunc_varargs2('cdef', 3, None, 5, 4, 7, 17, -2),
                (-4760, 'cdefcdefcdef'))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs2('cdef', 3, 'a', 5, 4, 7, 17, -2))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs2('cdef', 3, None, (5, 4, 7, 17, -2)))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs2('cdef', 3, None, 5, 4, 7.1, 17, -2))
        self.assertEqual(py3.testfunc_varargs3(14, 3, -4, a=8, ab=7.7, q=-3.2),
                ('abababab', 7.7))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs3(14, 3.2, -4, a=8, b=7.7, q=-3.2))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs3((14, 3, -4), a=8, b=7.7, q=-3.2))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs3(14, 3, -4, a=8, b='7.7', q=-3.2))
        self.assertEqual(py3.testfunc_varargs4(cx = 7, d = 9), 7)
        self.assertEqual(py3.testfunc_varargs4(cx = 7.5, d = 9), 7.5)
        self.assertEqual(py3.testfunc_varargs4(), 0)
        self.assertRaises(InputTypeError, lambda: py3.testfunc_varargs4(2, 3))
        self.assertRaises(InputTypeError, lambda: py3.testfunc_varargs4(cx = 7.1, d = '9'))
        self.assertEqual(py3.testfunc_varargs5(
                3, 'qvw', 3.3, 3.1, 2.778, 9, v=6, x=-8, qvw=99), [4, 1, 99])
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs5(3, 'qvw', 3.3, 3.1, 2.778, 9, v=6.2, x=-8, qvw=99))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs5(3, 3, 3.3, 3.1, 2.778, 9, v=6, x=-8, qvw=99))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs5(3, 'qvw', (3.3, 3.1, 2.778, 9), v=6, x=-8, qvw=99))
        self.assertRaises(InputTypeError, lambda: py3.testfunc_varargs5())
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs_err(3.0, 'qvw', 3.3, 9, v=6, x=-8, qvw=9.9))
        self.assertRaises(ReturnTypeError, lambda:
                py3.testfunc_varargs_err(3, 'qvw', 3.3, 3.1, 2.778, 9, v=6, x=-8, qvw=99))

        # Python 3 specific: kw-only args:
        self.assertEqual(py3.testfunc_varargs6(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b1=27, b2='abc', ac=19), [4, 3, 19, 27, 3])
        self.assertEqual(py3.testfunc_varargs6(2, 'ac', 1.2, 3, 4, 6.7,
                a=2, b=3, b1=27, b2='abc', ac=19), [4, 1, 19, 27, 3])
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs6(2.1, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b1=27, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:py3.testfunc_varargs6())
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs6(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs6(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b1=1.5, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs6(2, 'ac', 1.2, (3.4, 4.5, 6.7),
                a=2, b=3, b1=1.5, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs6(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3.5, b1=1.5, b2='abc', ac=19))

        self.assertEqual(py3.testfunc_varargs6b(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b1=27, b2='abc', ac=19), [4, 3, 19, 27, 3])
        self.assertEqual(py3.testfunc_varargs6b(2, 'ac', 1.2, 3, 4, 6.7,
                a=2, b=3, b1=27, b2='abc', ac=19), [4, 1, 19, 27, 3])
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs6b(2.1, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b1=27, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda: py3.testfunc_varargs6b())
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs6b(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs6b(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b1=1.5, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs6b(2, 'ac', 1.2, (3.4, 4.5, 6.7),
                a=2, b=3, b1=1.5, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs6b(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3.5, b1=1.5, b2='abc', ac=19))
        
        tcv = py3.testclass_vararg()
        self.assertEqual(tcv.testmeth_varargs1(('k', 7), ('bxx', 19), ('bxy', 27)), 130)
        self.assertEqual(tcv.testmeth_varargs1(), -15)
        self.assertRaises(InputTypeError, lambda:
                tcv.testmeth_varargs1(('k', 7), 19, ('bxy', 27)))
        self.assertEqual(tcv.testmeth_varargs2(2, 'xt', 1.2, 1.4, -9.2, cx=8, xt=7),
                [3, 4, 7, 16])
        self.assertRaises(InputTypeError, lambda:
                tcv.testmeth_varargs2(2, 'xt', 1.2, 1.4, -9.2, cx=8.2, xt=7))
        self.assertEqual(testclass_vararg.testmeth_varargs_static1(10, 4, 1.0, -4.2),
                (4, -168.0))
        self.assertEqual(testclass_vararg.testmeth_varargs_static1(), (0, 1.0))
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg.testmeth_varargs_static1((10, 4, 1.0, -4.2)))
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg.testmeth_varargs_static1('10, 4', 1.0, -4.2))
        self.assertEqual(testclass_vararg.testmeth_varargs_static2(
                0, 'cx', 1.2, -9.2, cx=2, xt=7), [2, 3, 2])
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg.testmeth_varargs_static2(
                0, 'cx', 1.2, -9.2, cx=2.1, xt=7))
        self.assertEqual(testclass_vararg.testmeth_varargs_class1(), -15)
        self.assertEqual(testclass_vararg.testmeth_varargs_class1(
                ('abc', -12), ('txxt', 2)), -43)
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg.testmeth_varargs_class1(('abc', -12.1), ('txxt', 2)))
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg.testmeth_varargs_class1(('abc', -12), 'txxt'))
        self.assertEqual(testclass_vararg.testmeth_varargs_class2(
                1, 'xt', .2, -92, cx=2, xt=7), [2, 3, 7, 16])
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg.testmeth_varargs_class2())
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg.testmeth_varargs_class2(
                0, 'cx', 1.2, -9.2, cx=2, xt=.7))
        tcv.prop1 = 'test_prop1'
        self.assertEqual(tcv.prop1, 'test_prop1')
        def _set_prop1(): tcv.prop1 = 8
        self.assertRaises(InputTypeError, _set_prop1)
        tcv._prop1 = 8
        self.assertRaises(ReturnTypeError, lambda: tcv.prop1)

    def test_varargs_check_argument_types(self):
        self.assertEqual(py3.testfunc_varargs_ca1(16.4, 2, 3.2), (3, 104.96))
        self.assertEqual(py3.testfunc_varargs_ca1(), (0, 1.0))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs_ca1((16.4, 2, 3.2)))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs_ca1(16.4, '2', 3.2))
        self.assertEqual(py3.testfunc_varargs_ca2('cdef', 3, None, 5, 4, 7, 17, -2),
                (-4760, 'cdefcdefcdef'))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs_ca2('cdef', 3, 'a', 5, 4, 7, 17, -2))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs_ca2('cdef', 3, None, (5, 4, 7, 17, -2)))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs_ca2('cdef', 3, None, 5, 4, 7.1, 17, -2))
        self.assertEqual(py3.testfunc_varargs_ca3(14, 3, -4, a=8, ab=7.7, q=-3.2),
                ('abababab', 7.7))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs_ca3(14, 3.2, -4, a=8, b=7.7, q=-3.2))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs_ca3((14, 3, -4), a=8, b=7.7, q=-3.2))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs_ca3(14, 3, -4, a=8, b='7.7', q=-3.2))
        self.assertEqual(py3.testfunc_varargs_ca4(cx = 7, d = 9), 7)
        self.assertEqual(py3.testfunc_varargs_ca4(cx = 7.5, d = 9), 7.5)
        self.assertEqual(py3.testfunc_varargs_ca4(), 0)
        # In this case it's an ordinary type-error, because Python catches it before
        # pytypes gets hands on it to make a more sophisticated InputTypeError:
        self.assertRaises(TypeError, lambda: py3.testfunc_varargs_ca4(2, 3))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs_ca4(cx = 7.1, d = '9'))
        self.assertEqual(py3.testfunc_varargs_ca5(
                3, 'qvw', 3.3, 3.1, 2.778, 9, v=6, x=-8, qvw=99), [4, 1, 99])
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs_ca5(
                3, 'qvw', 3.3, 3.1, 2.778, 9, v=6.2, x=-8, qvw=99))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs_ca5(3, 3, 3.3, 3.1, 2.778, 9, v=6, x=-8, qvw=99))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs_ca5(3, 'qvw', (
                3.3, 3.1, 2.778, 9), v=6, x=-8, qvw=99))
        # In this case it's an ordinary type-error, because Python catches it before
        # pytypes gets hands on it to make a more sophisticated InputTypeError:
        self.assertRaises(TypeError, lambda: py3.testfunc_varargs_ca5())

        # Python 3 specific: kw-only args:
        self.assertEqual(py3.testfunc_varargs_ca6(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b1=27, b2='abc', ac=19), [4, 3, 19, 27, 3])
        self.assertEqual(py3.testfunc_varargs_ca6(2, 'ac', 1.2, 3, 4, 6.7,
                a=2, b=3, b1=27, b2='abc', ac=19), [4, 1, 19, 27, 3])
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs_ca6(2.1, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b1=27, b2='abc', ac=19))
        # In this case it's an ordinary type-error, because Python catches it before
        # pytypes gets hands on it to make a more sophisticated InputTypeError:
        self.assertRaises(TypeError, lambda: py3.testfunc_varargs_ca6())
        self.assertRaises(TypeError, lambda:
                py3.testfunc_varargs_ca6(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs_ca6(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b1=1.5, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs_ca6(2, 'ac', 1.2, (3.4, 4.5, 6.7),
                a=2, b=3, b1=1.5, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs_ca6(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3.5, b1=1.5, b2='abc', ac=19))

        self.assertEqual(py3.testfunc_varargs_ca6b(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b1=27, b2='abc', ac=19), [4, 3, 19, 27, 3])
        self.assertEqual(py3.testfunc_varargs_ca6b(2, 'ac', 1.2, 3, 4, 6.7,
                a=2, b=3, b1=27, b2='abc', ac=19), [4, 1, 19, 27, 3])
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs_ca6b(2.1, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b1=27, b2='abc', ac=19))
        # In this case it's an ordinary type-error, because Python catches it before
        # pytypes gets hands on it to make a more sophisticated InputTypeError:
        self.assertRaises(TypeError, lambda: py3.testfunc_varargs_ca6b())
        self.assertRaises(TypeError, lambda:
                py3.testfunc_varargs_ca6b(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs_ca6b(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3, b1=1.5, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs_ca6b(2, 'ac', 1.2, (3.4, 4.5, 6.7),
                a=2, b=3, b1=1.5, b2='abc', ac=19))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_varargs_ca6b(2, 'ac', 1.2, 3.4, 4.5, 6.7,
                a=2, b=3.5, b1=1.5, b2='abc', ac=19))

        tcv = py3.testclass_vararg_ca()
        self.assertEqual(tcv.testmeth_varargs_ca1(
                ('k', 7), ('bxx', 19), ('bxy', 27)), 127)
        self.assertEqual(tcv.testmeth_varargs_ca1(), -18)
        self.assertRaises(InputTypeError, lambda:
                tcv.testmeth_varargs_ca1(('k', 7), 19, ('bxy', 27)))
        self.assertEqual(tcv.testmeth_varargs_ca2(2, 'xt', 1.2, 1.4, -9.2, cx=8, xt=7),
                [3, 4, 7, 19])
        self.assertRaises(InputTypeError, lambda:
                tcv.testmeth_varargs_ca2(2, 'xt', 1.2, 1.4, -9.2, cx=8.2, xt=7))
        self.assertEqual(testclass_vararg_ca.testmeth_varargs_static_ca1(
                10, 4, 1.0, -4.2), (4, -168.0))
        self.assertEqual(testclass_vararg_ca.testmeth_varargs_static_ca1(), (0, 1.0))
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg_ca.testmeth_varargs_static_ca1((10, 4, 1.0, -4.2)))
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg_ca.testmeth_varargs_static_ca1('10, 4', 1.0, -4.2))
        self.assertEqual(testclass_vararg_ca.testmeth_varargs_static_ca2(
                0, 'cx', 1.2, -9.2, cx=2, xt=7), [2, 3, 2])
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg_ca.testmeth_varargs_static_ca2(
                0, 'cx', 1.2, -9.2, cx=2.1, xt=7))
        self.assertEqual(testclass_vararg_ca.testmeth_varargs_class_ca1(), -18)
        self.assertEqual(testclass_vararg_ca.testmeth_varargs_class_ca1(
                ('abc', -12), ('txxt', 2)), -46)
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg_ca.testmeth_varargs_class_ca1(
                ('abc', -12.1), ('txxt', 2)))
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg_ca.testmeth_varargs_class_ca1(('abc', -12), 'txxt'))
        self.assertEqual(testclass_vararg_ca.testmeth_varargs_class_ca2(
                1, 'xt', .2, -92, cx=2, xt=7), [2, 3, 7, 19])
        # In this case it's an ordinary type-error, because Python catches it before
        # pytypes gets hands on it to make a more sophisticated InputTypeError:
        self.assertRaises(TypeError, lambda:
                testclass_vararg_ca.testmeth_varargs_class_ca2())
        self.assertRaises(InputTypeError, lambda:
                testclass_vararg_ca.testmeth_varargs_class_ca2(
                0, 'cx', 1.2, -9.2, cx=2, xt=.7))
        tcv.prop_ca1 = 'test_prop1'
        self.assertEqual(tcv.prop_ca1, 'test_prop1')
        def _set_prop1(): tcv.prop_ca1 = 8
        self.assertRaises(InputTypeError, _set_prop1)
        # No point in checking for ReturnTypeError here;
        # check_argument_types wouldn't catch it.

    def test_defaults_inferred_types(self):
        tmp = pytypes.infer_default_value_types
        pytypes.infer_default_value_types = True

        self.assertEqual(get_types(py3.func_defaults_typecheck),
                (Tuple[str, Any, int, float], str))
        self.assertEqual(pytypes.get_type_hints(py3.func_defaults_typecheck),
                        {'a': str, 'c': int, 'return': str, 'd': float})
        self.assertEqual(py3.func_defaults_typecheck('qvw', 'abc', 2, 1.5), 'qvwabcabc')
        self.assertRaises(InputTypeError, lambda:
                py3.func_defaults_typecheck('qvw', 'abc', 3.5))
        self.assertEqual(py3.func_defaults_typecheck2('test', 12.2, 323), 'test3940.6False')
        self.assertRaises(InputTypeError, lambda:
                py3.func_defaults_typecheck2('test', 12.2, 323, 3.5))

        self.assertRaises(InputTypeError, lambda:
                py3.func_defaults_typecheck('qvw', 'abc', 3.5, 4.1))
        self.assertRaises(InputTypeError, lambda: py3.func_defaults_typecheck(7, 'qvw'))

        self.assertEqual(py3.func_defaults_checkargs('qvw', 'abc', 3, 1.5), 'qvwabcabcabc')
        self.assertRaises(InputTypeError, lambda:
                py3.func_defaults_checkargs('qvw', 'abc', 3.5))
        self.assertRaises(InputTypeError, lambda:
                py3.func_defaults_checkargs('qvw', 'abc', 3.5, 4.1))
        self.assertRaises(InputTypeError, lambda: py3.func_defaults_checkargs(7, 'qvw'))

        self.assertEqual(get_types(py3.func_defaults_annotations),
                (Tuple[str, Any, int], str))
        self.assertEqual(pytypes.get_type_hints(py3.func_defaults_annotations),
                {'a': str, 'c': int, 'return': str})
        self.assertEqual(py3.func_defaults_annotations.__annotations__,
                {'a': str, 'return': str})

        pytypes.infer_default_value_types = False

        self.assertEqual(get_types(py3.func_defaults_typecheck),
                (Tuple[str, Any, Any, Any], str))
        self.assertEqual(pytypes.get_type_hints(py3.func_defaults_typecheck),
                {'a': str, 'return': str})
        self.assertEqual(py3.func_defaults_typecheck('qvw', 'abc', 3.5), 'invalid')
        self.assertEqual(py3.func_defaults_typecheck('qvw', 'abc', 3.5, 4.1), 'invalid')
        self.assertRaises(InputTypeError, lambda: py3.func_defaults_typecheck(7, 'qvw'))

        self.assertEqual(py3.func_defaults_checkargs('qvw', 'abc', 3, 1.5), 'qvwabcabcabc')
        self.assertEqual(py3.func_defaults_checkargs('qvw', 'abc', 3.5), 'invalid')
        self.assertEqual(py3.func_defaults_checkargs('qvw', 'abc', 3.5, 4.1), 'invalid')
        self.assertRaises(InputTypeError, lambda: py3.func_defaults_checkargs(7, 'qvw'))

        self.assertEqual(get_types(py3.func_defaults_annotations),
                (Tuple[str, Any, Any], str))
        self.assertEqual(pytypes.get_type_hints(py3.func_defaults_annotations),
                {'a': str, 'return': str})
        self.assertEqual(py3.func_defaults_annotations.__annotations__,
                {'a': str, 'return': str})

        pytypes.infer_default_value_types = tmp

    def test_defaults_with_missing_annotations_plain(self):
        # See: https://github.com/Stewori/pytypes/issues/89
        helper = py3.method_defaults_typecheck()
        self.assertEqual(helper.plain_method(1), 1)
        self.assertEqual(helper.plain_method(1, 2), 3)
        self.assertRaises(InputTypeError, lambda: helper.plain_method(1, 'b'))

    def test_defaults_with_missing_annotations_class(self):
        # See: https://github.com/Stewori/pytypes/issues/89
        helper = py3.method_defaults_typecheck()
        self.assertEqual(helper.class_method(1), 1)
        self.assertEqual(helper.class_method(1, 2), 3)
        self.assertRaises(InputTypeError, lambda: helper.class_method(1, 'b'))

    def test_defaults_with_missing_annotations_property(self):
        # See: https://github.com/Stewori/pytypes/issues/89
        helper = py3.method_defaults_typecheck()
        self.assertEqual(helper.property_method, 0)
        helper.property_method = 1
        self.assertEqual(helper.property_method, 2)

    def test_defaults_with_missing_annotations_static(self):
        # See: https://github.com/Stewori/pytypes/issues/89
        # Just being thorough (staticmethod already worked before fixing #89)
        helper = py3.method_defaults_typecheck()
        self.assertEqual(helper.static_method(1), 1)
        self.assertEqual(helper.static_method(1, 2), 3)
        self.assertRaises(InputTypeError, lambda: helper.static_method(1, 'b'))

    def test_typecheck_parent_type(self):
        always_check_parent_types_tmp = pytypes.always_check_parent_types
        pytypes.always_check_parent_types = False

        self.assertRaises(InputTypeError, lambda:
                py3.B_override_check_arg().meth1(17.7))
        self.assertEqual(py3.B_no_override_check_arg().meth1(17.7), 4)
        self.assertRaises(InputTypeError, lambda:
                py3.B_override_typechecked().meth1(17.7))
        self.assertEqual(py3.B_no_override_typechecked().meth1(17.7), 4)
        self.assertEqual(py3.B_override_with_type_check_arg().meth1(17.7), 4)
        self.assertEqual(py3.B_override_with_type_typechecked().meth1(17.7), 4)

        pytypes.always_check_parent_types = True

        self.assertRaises(InputTypeError, lambda:
                py3.B_override_check_arg().meth1(17.7))
        self.assertRaises(InputTypeError, lambda:
                py3.B_no_override_check_arg().meth1(17.7))
        self.assertRaises(InputTypeError, lambda:
                py3.B_override_typechecked().meth1(17.7))
        self.assertRaises(InputTypeError, lambda:
                py3.B_no_override_typechecked().meth1(17.7))
        self.assertEqual(py3.B_override_with_type_check_arg().meth1(17.7), 4)
        self.assertEqual(py3.B_override_with_type_typechecked().meth1(17.7), 4)

        pytypes.always_check_parent_types = always_check_parent_types_tmp
        
        
    def test_typevar_func(self):
        self.assertEqual(py3.tpvar_test1(2, 3), 'hello')
        self.assertRaises(InputTypeError, lambda: py3.tpvar_test1(2, '3'))
        self.assertRaises(InputTypeError, lambda: py3.tpvar_test1(2, 3.5))
        self.assertRaises(InputTypeError, lambda: py3.tpvar_test1(2.5, 3))

        self.assertEqual(py3.tpvar_test2(2, 3), 'hello')
        self.assertRaises(InputTypeError, lambda: py3.tpvar_test2(2, '3'))
        self.assertRaises(InputTypeError, lambda: py3.tpvar_test2(2, 3.5))
        self.assertEqual(py3.tpvar_test2(2.5, 3), 'hello')

        self.assertEqual(py3.tpvar_test3(2, 3), 'hello')
        self.assertRaises(InputTypeError, lambda: py3.tpvar_test3(2, '3'))
        self.assertEqual(py3.tpvar_test3(2, 3.5), 'hello')
        self.assertRaises(InputTypeError, lambda: py3.tpvar_test3(2.5, 3))

        self.assertEqual(py3.tpvar_test4([1.2, 2.6, 3.2], 1), 2.6)
        self.assertRaises(ReturnTypeError, lambda: py3.tpvar_test5([1.2, 2.6, 3.2], 2))
        self.assertEqual(py3.tpvar_test5(['a', 'b', 'c'], 1), 'b')
    
        def test_typevar_class(self):
            self.assertIsNotNone(py3.IntA(5))
            self.assertRaises(InputTypeError, lambda: py3.IntA(4.5))
            self.assertRaises(InputTypeError, lambda: py3.IntA('acb'))
            self.assertIsNotNone(py3.A[int](5))
            self.assertRaises(InputTypeError, lambda: py3.A[int](4.5))
            self.assertRaises(InputTypeError, lambda: py3.A[int]('acb'))
            self.assertIsNotNone(py3.A[float](5))
            self.assertIsNotNone(py3.A[float](4.5))
            self.assertRaises(InputTypeError, lambda: py3.A[float]('acb'))
            self.assertRaises(InputTypeError, lambda: py3.A[str](5))
            self.assertRaises(InputTypeError, lambda: py3.A[str](4.5))
            self.assertIsNotNone(A[str]('acb'))
            
            self.assertIsNone(py3.test_typevar_A(py3.IntA(5)))
            self.assertRaises(InputTypeError, lambda: py3.test_typevar_A(py3.IntA(5.7)))
            self.assertIsNone(py3.test_typevar_A(py3.IntB(5)))
            self.assertRaises(InputTypeError, lambda: py3.test_typevar_A(py3.IntB(5.7)))


@unittest.skipUnless(sys.version_info.major >= 3 and sys.version_info.minor >= 5,
        'Only applicable in Python >= 3.5.')
class TestOverride_Python3_5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global py3
        from testhelpers import typechecker_testhelper_py3 as py3

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

    def test_override_vararg(self):
        cl = py3.override_varargs_class()
        self.assertEqual(cl.method_vararg1(1, 2.3, 4, 5), 2)
        self.assertEqual(cl.method_vararg2(6, 7.8, 'a', 'b', 'c'), 12)
        self.assertEqual(cl.method_vararg3(9, 10.1, 11.2, 12.3), 12)
        self.assertRaises(OverrideError, lambda: cl.method_vararg1_err(3, 4.5, 6, 7))
        self.assertRaises(OverrideError, lambda:
                cl.method_vararg2_err(8, 9.01, 'd', 'e', 'f'))
        self.assertRaises(OverrideError, lambda: cl.method_vararg3_err(4, 5, 6))
        self.assertEqual(cl.method_varkw1(7, 8, m=1.1, n=2.2, x=3.3), 15)
        self.assertEqual(cl.method_varkw2(9, 10, 'g', 'h', x=2.3, y=3.4, z=7.7), 19)
        self.assertRaises(OverrideError, lambda:
                cl.method_varkw1_err(11, 12, q=22, v=33, w=44))
        self.assertRaises(OverrideError, lambda:
                cl.method_varkw2_err(4, 5, 'i', 'j', g=3, h=7))
        self.assertRaises(OverrideError, lambda:
                cl.method_varkw3_err(14, 15, 'k', 'l'))
        self.assertEqual(cl.method_defaults1(21, 22), 43)
        self.assertEqual(cl.method_defaults2(23, 24, 31, 32, 33, 34), 47)
        self.assertRaises(OverrideError, lambda: cl.method_defaults1_err(101, 102))
        self.assertRaises(OverrideError, lambda:
                cl.method_defaults2_err(201, 202, 55.1, 55.2, 55.3))

        # Python 3 only
        self.assertEqual(cl.method_kwonly1(
                1, 2, 3.4, 4.5, q=7.2, xx='ab', xy='cd'), 3)
        self.assertEqual(cl.method_kwonly2(5, 6, 2.4, 5.7, 8.8, q=17), 28)
        self.assertEqual(cl.method_kwonly3(9, 10, 11.2, 22.3, v=9.7, q=27), 46)
        self.assertEqual(cl.method_kwonly4(8.1, 3, 7.4, 33.4, 33.5, 33.6), 4)
        self.assertEqual(cl.method_kwonly5(
                5.1, 5.2, 41, 42, 43, q=17.5, v=19, x=99.1, w=27.9), 4)
        self.assertEqual(cl.method_kwonly6(
                6.3, 7, 16.1, 16.2, 16.3, q=29, l=12, k=23.3, v=47.9), 39)
        self.assertEqual(cl.method_kwonly7(
                61, 62, 63.3, 64, 65.5, 66, q=76, e=11, f=12), 123)
        self.assertRaises(OverrideError, lambda:
                cl.method_kwonly1_err(1, 2, 3.4, 4.5, 6.7, q=17))
        self.assertRaises(OverrideError, lambda:
                cl.method_kwonly2_err(8, 9, 7, 6, 5.4, 3.2))
        self.assertRaises(OverrideError, lambda:
                cl.method_kwonly3_err(10, 11, 12, 13.4, 15.6, q=22, b=23))
        self.assertRaises(OverrideError, lambda:
                cl.method_kwonly4_err(0.5, 2, 0.8, 0.9, 0.1, q=78, v='ijk'))
        self.assertRaises(OverrideError, lambda:
                cl.method_kwonly5_err(12.1, 12.2, 13, 14, q=32, v=33))
        self.assertRaises(OverrideError, lambda:
                cl.method_kwonly6_err(3.1, 4, 5.1, 5.2, 5.3, q=7, y=67, z=68))
        self.assertRaises(OverrideError, lambda:
                cl.method_kwonly7_err(79, 90.7, 1.1, q=2, v=3, h=7, k=11.7))
        self.assertRaises(OverrideError, lambda:
                cl.method_kwonly8_err(100, 100.5, 200, 201, 203.3, nx=7, fl=9))

        # Python 3 using Python 2 type hints
        self.assertEqual(cl.method_kwonly1_py2(
                1, 2, 3.4, 4.5, q=7.2, xx='ab', xy='cd'), 3)
        self.assertEqual(cl.method_kwonly2_py2(5, 6, 2.4, 5.7, 8.8, q=17), 28)
        self.assertEqual(cl.method_kwonly3_py2(9, 10, 11.2, 22.3, v=9.7, q=27), 46)
        self.assertEqual(cl.method_kwonly4_py2(8.1, 3, 7.4, 33.4, 33.5, 33.6), 4)
        self.assertEqual(cl.method_kwonly5_py2(
                5.1, 5.2, 41, 42, 43, q=17.5, v=19, x=99.1, w=27.9), 4)
        self.assertEqual(cl.method_kwonly6_py2(
                6.3, 7, 16.1, 16.2, 16.3, q=29, l=12, k=23.3, v=47.9), 39)
        self.assertEqual(cl.method_kwonly7_py2(
                61, 62, 63.3, 64, 65.5, 66, q=76, e=11, f=12), 123)
        self.assertRaises(OverrideError, lambda:
                cl.method_kwonly1_err_py2(1, 2, 3.4, 4.5, 6.7, q=17))
        self.assertRaises(OverrideError, lambda:
                cl.method_kwonly2_err_py2(8, 9, 7, 6, 5.4, 3.2))
        self.assertRaises(OverrideError, lambda:
                cl.method_kwonly3_err_py2(10, 11, 12, 13.4, 15.6, q=22, b=23))
        self.assertRaises(OverrideError, lambda:
                cl.method_kwonly4_err_py2(0.5, 2, 0.8, 0.9, 0.1, q=78, v='ijk'))
        self.assertRaises(OverrideError, lambda:
                cl.method_kwonly5_err_py2(12.1, 12.2, 13, 14, q=32, v=33))
        self.assertRaises(OverrideError, lambda:
                cl.method_kwonly6_err_py2(3.1, 4, 5.1, 5.2, 5.3, q=7, y=67, z=68))
        self.assertRaises(OverrideError, lambda:
                cl.method_kwonly7_err_py2(79, 90.7, 1.1, q=2, v=3, h=7, k=11.7))
        self.assertRaises(OverrideError, lambda:
                cl.method_kwonly8_err_py2(100, 100.5, 200, 201, 203.3, nx=7, fl=9))

    def test_override_diamond(self):
        self.assertEqual(py3.D_diamond_override().meth1((12.4, 17.7)), 12)
        self.assertRaises(OverrideError, lambda:
                py3.D_diamond_override_err1().meth1((12, 17)))
        self.assertRaises(OverrideError, lambda:
                py3.D_diamond_override_err2().meth1((12, 17)))
        self.assertRaises(OverrideError, lambda:
                py3.D_diamond_override_err3().meth1((12, 17)))

    def test_auto_override(self):
        self.assertEqual(py3.B_auto_override().meth_1('abc', (4, 2)), 1)
        obj = py3.B_auto_override_err()
        self.assertRaises(OverrideError, lambda: obj.meth_1('abc', (4, 2)))
        self.assertEqual(obj.meth_2('defg'), 12)

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
        from testhelpers import override_testhelper_py3 # shall not raise error
        def _test_err_py3():
            from testhelpers import override_testhelper_err_py3
        def _test_err2_py3():
            from testhelpers import override_testhelper_err2_py3

        self.assertRaises(OverrideError, _test_err_py3)
        self.assertRaises(NameError, _test_err2_py3)

        pytypes.check_override_at_class_definition_time = tmp


@unittest.skipUnless(sys.version_info.major >= 3 and sys.version_info.minor >= 5,
        'Only applicable in Python >= 3.5.')
class Test_check_argument_types_Python3_5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global py3
        from testhelpers import typechecker_testhelper_py3 as py3

    def test_function(self):
        self.assertIsNone(py3.testfunc_check_argument_types(2, 3.0, 'qvwx'))
        self.assertRaises(InputTypeError, lambda:
                py3.testfunc_check_argument_types(2.7, 3.0, 'qvwx'))

    def test_methods(self):
        cl = py3.testClass_check_argument_types()
        self.assertIsNone(cl.testMeth_check_argument_types(7))
        self.assertIsNone(cl.testClassmeth_check_argument_types(8))
        self.assertIsNone(cl.testStaticmeth_check_argument_types(9))

        self.assertRaises(InputTypeError, lambda:
                cl.testMeth_check_argument_types('7'))
        self.assertRaises(InputTypeError, lambda:
                cl.testClassmeth_check_argument_types(8.5))
        self.assertRaises(InputTypeError, lambda:
                cl.testStaticmeth_check_argument_types((9,)))

    def test_inner_method(self):
        self.assertEqual(py3.test_inner_method_testf1(), '(3, 6)')
        self.assertRaises(InputTypeError, lambda:
                py3.test_inner_method_testf1_err())

    def test_inner_class(self):
        self.assertEqual(py3.test_inner_class_testf1(), '99')
        self.assertRaises(InputTypeError, lambda:
                py3.test_inner_class_testf1_err())


class Test_utils(unittest.TestCase):
    # See: https://github.com/Stewori/pytypes/issues/36
    def test_resolve_fw_decl(self):
        T = typing.TypeVar('T')

        class Foo(typing.Generic[T]):
            pass

        # No exception.
        resolve_fw_decl(Foo)

    # See: https://github.com/Stewori/pytypes/issues/35
    def test_frozenset(self):
        self.assertTrue(is_of_type(frozenset({1, 2, 'a', None, 'b'}), typing.AbstractSet[typing.Union[str, int, None]]))

    # See: https://github.com/Stewori/pytypes/issues/32
    # See: https://github.com/Stewori/pytypes/issues/33
    def test_empty_values(self):
        self.assertTrue(is_of_type([], typing.Sequence))
        self.assertTrue(is_of_type([], typing.Sequence[int]))

        for interface in (typing.Iterable, typing.Sized, typing.Container):
            self.assertTrue(isinstance(set(), interface), interface)
            self.assertTrue(is_of_type(set(), interface), interface)
            self.assertTrue(isinstance([], interface), interface)
            self.assertTrue(is_of_type([], interface), interface)

    # See: https://github.com/Stewori/pytypes/issues/21
    def test_tuple_ellipsis(self):
        class Foo:
            pass

        self.assertTrue(is_subtype(Tuple[Foo], Tuple[object, ...]))
        self.assertTrue(is_subtype(Tuple[Foo], Tuple[Any, ...]))

    # See: https://github.com/Stewori/pytypes/issues/69
    def test_tuple_ellipsis_check(self):
        @typechecked
        def f():
            # type: () -> Tuple[Any, ...]
            return ()
        self.assertEqual(f(), ())

    # See: https://github.com/Stewori/pytypes/issues/48
    def test_empty_tuple(self):
        self.assertFalse(is_of_type((), List))
        self.assertTrue(is_of_type((), Tuple))
        self.assertTrue(is_of_type((), Sequence))

    # See: https://github.com/Stewori/pytypes/issues/24
    def test_bound_typevars_readonly(self):
        T = typing.TypeVar('T', covariant=True)

        class L(typing.List[T]):
            pass

        C = typing.TypeVar('T', bound=L)

        self.assertTrue(is_subtype(L[float], C))
        self.assertTrue(is_subtype(L[float], C, bound_typevars={}))
        self.assertFalse(is_subtype(L[float], C, bound_typevars_readonly=True, bound_typevars={}))
        self.assertTrue(is_subtype(L[float], C, bound_typevars_readonly=False, bound_typevars={}))

    # See: https://github.com/Stewori/pytypes/issues/22
    def test_forward_declaration(self):
        Wrapper = typing.Union[typing.Sequence['Data']]
        Data = typing.Union[Wrapper, str, bytes, bool, float, int, dict]
        with self.assertRaises(pytypes.ForwardRefError):
            is_subtype(typing.Sequence[float], Wrapper)
        pytypes.resolve_fw_decl(Wrapper)
        self.assertTrue(is_subtype(typing.Sequence[float], Wrapper))
        self.assertTrue(is_subtype(int, Data))
        self.assertTrue(is_subtype(float, Data))
        self.assertFalse(is_subtype(Data, Wrapper))
        self.assertTrue(is_subtype(Wrapper, Data))

    # See: https://github.com/Stewori/pytypes/issues/22
    def test_forward_declaration_infinite_recursion(self):
        Data = typing.Union['Wrapper', float]
        Wrapper = typing.Union[Data, int]
        pytypes.resolve_fw_decl(Data)
        self.assertFalse(is_subtype(list, Wrapper))

    # See: https://github.com/Stewori/pytypes/issues/49
    def test_Generator_is_of_type(self):
        value = (i for i in range(10))
        self.assertFalse(is_of_type(value, int))

        class Foo:
            def bar(self):
                value = (i for i in range(10))
                return is_of_type(value, int)

        self.assertFalse(Foo().bar())

    # See: https://github.com/Stewori/pytypes/issues/65
    def test_has_type_hints_on_slot_wrapper(self):
        self.assertFalse(pytypes.has_type_hints(int.__and__))

    def test_type_bases(self):
        def cmp(bs1, bs2):
            if len(bs1) != len(bs2): return False
            for i in range(len(bs1)):
                if bs1[i] is not bs2[i]:
                    try:
                        if bs1[i].__origin__ is not bs2[i].__origin__: return False
                    except: return False
            return True

        try:
            cabc = collections.abc
        except AttributeError:
            cabc = collections
        # The outcommented tests mostly fail because of something with Generic,
        # collections.abc.Sized vs typing.Sized or they were out-commented because
        # they were not reasonably applicable to all scoped python versions.
        # These slightly different bases shouln'd impact pytypes too much.
        self.assertTrue(cmp(type_bases(cabc.Hashable), (object,)))
        #Not in python2: self.assertTrue(cmp(type_bases(typing.Awaitable), (typing.Generic[T_co],)))
        #Not in python2: self.assertTrue(cmp(type_bases(typing.Coroutine), (typing.Awaitable[V_co], typing.Generic[T_co, T_contra, V_co])))
        #Not in python2: self.assertTrue(cmp(type_bases(typing.AsyncIterable), (typing.Generic[T_co],)))
        #Not in python2: self.assertTrue(cmp(type_bases(typing.AsyncIterator), (typing.AsyncIterable[T_co],)))
        self.assertTrue(cmp(type_bases(typing.Iterable), (typing.Generic[T_co],)))
        self.assertTrue(cmp(type_bases(typing.Iterator), (typing.Iterable[T_co],)))
        #self.assertTrue(cmp(type_bases(typing.Reversible), (typing.Iterable[T_co],)))
        self.assertTrue(cmp(type_bases(cabc.Sized), (object,)))
        self.assertTrue(cmp(type_bases(typing.Container), (typing.Generic[T_co],)))
        #self.assertTrue(cmp(type_bases(typing.Collection), (collections.abc.Sized, typing.Iterable[T_co], typing.Container[T_co])))
        #self.assertTrue(cmp(type_bases(typing.Callable), ()))
        #Not in python2: self.assertTrue(cmp(type_bases(typing.AbstractSet), (typing.Collection[T_co],)))
        self.assertTrue(cmp(type_bases(typing.MutableSet), (typing.AbstractSet[T],)))
        #self.assertTrue(cmp(type_bases(typing.Mapping), (typing.Collection[KT], typing.Generic[KT, VT_co])))
        self.assertTrue(cmp(type_bases(typing.MutableMapping), (typing.Mapping[KT, VT],)))
        #Not in python2: self.assertTrue(cmp(type_bases(typing.Sequence), (typing.Reversible[T_co], typing.Collection[T_co])))
        self.assertTrue(cmp(type_bases(typing.MutableSequence), (typing.Sequence[T],)))
        self.assertTrue(cmp(type_bases(typing.ByteString), (typing.Sequence[int],)))
        self.assertTrue(cmp(type_bases(typing.List), (list, typing.MutableSequence[T])))
        self.assertTrue(cmp(type_bases(typing.Set), (set, typing.MutableSet[T])))
        self.assertTrue(cmp(type_bases(typing.FrozenSet), (frozenset, typing.AbstractSet[T_co])))
        #self.assertTrue(cmp(type_bases(typing.MappingView), (collections.abc.Sized, typing.Iterable[T_co])))
        self.assertTrue(cmp(type_bases(typing.KeysView), (typing.MappingView[KT], typing.AbstractSet[KT])))
        #self.assertTrue(cmp(type_bases(typing.ItemsView), (typing.MappingView[typing.Tuple[KT, VT_co]], typing.AbstractSet[typing.Tuple[KT, VT_co]], typing.Generic[KT, VT_co])))
        #self.assertTrue(cmp(type_bases(typing.ValuesView), (typing.MappingView[VT_co],)))
        #self.assertTrue(cmp(type_bases(typing.ContextManager), (typing.Generic[T_co],)))
        self.assertTrue(cmp(type_bases(typing.Dict), (dict, typing.MutableMapping[KT, VT])))
        #self.assertTrue(cmp(type_bases(typing.DefaultDict), (collections.defaultdict, typing.MutableMapping[KT, VT])))
        #self.assertTrue(cmp(type_bases(typing.Generator), (typing.Iterator[T_co], typing.Generic[T_co, T_contra, V_co])))
        #self.assertTrue(cmp(type_bases(typing.Type), (typing.Generic[CT_co],)))

    # See: https://github.com/Stewori/pytypes/issues/56
    def test_subtype_mapping(self):
        self.assertFalse(is_subtype(type(None), Dict[str, str]))
        self.assertFalse(is_subtype(dict, Dict[str, str]))
        self.assertTrue(is_subtype(Dict[str, str], dict))
        self.assertFalse(is_subtype(List[Dict[str, str]], List[dict]))
        self.assertTrue(is_subtype(List[Dict[str, str]], Sequence[dict]))
        self.assertTrue(is_subtype(type(None), Optional[Dict[str, Any]]))


class Test_combine_argtype(unittest.TestCase):
    def test_exceptions(self):
        # Empty observations not allowed
        with self.assertRaises(AssertionError):
            pytypes.typelogger.combine_argtype([])

        # Non tuple types not allowed
        with self.assertRaises(AssertionError):
            notTuple = typing.List[int]
            pytypes.typelogger.combine_argtype([notTuple])

        with self.assertRaises(AssertionError):
            notTuple = typing.List[int]
            pytypes.typelogger.combine_argtype([typing.Tuple[int], notTuple])

    def test_function(self):
        # If single observation is supplied it should return itself
        self.assertEqual(
            pytypes.typelogger.combine_argtype([typing.Tuple[int]]),
            typing.Tuple[int],
        )
        # Observations should be unioned
        self.assertEqual(
            pytypes.typelogger.combine_argtype([typing.Tuple[int], typing.Tuple[str]]),
            typing.Tuple[typing.Union[int, str]],
        )
        # Number classes should be combined as PEP 484 style numeric tower
        self.assertEqual(
            pytypes.typelogger.combine_argtype([typing.Tuple[int], typing.Tuple[float]]),
            typing.Tuple[float],
        )


def testfunc_agent(v):
    # type: (str) -> int
    return 67


def testfunc_agent_err(v):
    # type: (str) -> int
    return 'abc'


class Test_agent_err_class:
    def __init__(self):
        # type: () -> None
        pass

    def testmeth_agent_err(self):
        # type: () -> int
        return {}

    @classmethod
    def testclassmeth_agent_err(cls):
        # type: () -> int
        return {}


class Test_agent(unittest.TestCase):
    def test_function_agent(self):
        with TypeChecker():
            self.assertEqual(testfunc_agent('abc'), 67)
            self.assertRaises(InputTypeError, lambda: testfunc_agent(12))
            restore_profiler()
            self.assertRaises(ReturnTypeError, lambda: testfunc_agent_err('abc'))

    def test_method_agent_return(self):
        a = Test_agent_err_class()
        with TypeChecker():
            a.testmeth_agent_err
            self.assertRaises(ReturnTypeError, a.testmeth_agent_err)
            restore_profiler()
            self.assertRaises(ReturnTypeError, a.testclassmeth_agent_err)
            restore_profiler()
            self.assertRaises(ReturnTypeError, Test_agent_err_class.testclassmeth_agent_err)
    
    def test_init_agent_return_None(self):
        with TypeChecker():
            Test_agent_err_class()


@unittest.skipUnless(sys.version_info.major >= 3 and sys.version_info.minor >= 5,
        'Only applicable in Python >= 3.5.')
class Test_agent_Python3_5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global py3
        from testhelpers import typechecker_testhelper_py3 as py3

    def test_function_agent(self):
        with TypeChecker():
            self.assertEqual(py3.testfunc_agent('abc'), 69)
            self.assertRaises(InputTypeError, lambda: py3.testfunc_agent(12))
            restore_profiler()
            self.assertRaises(ReturnTypeError, lambda: py3.testfunc_agent_err('abc'))
    
    def test_method_agent_return(self):
        a = py3.Test_agent_err_class()
        with TypeChecker():
            a.testmeth_agent_err
            self.assertRaises(ReturnTypeError, a.testmeth_agent_err)
            restore_profiler()
            self.assertRaises(ReturnTypeError, a.testclassmeth_agent_err)
            restore_profiler()
            self.assertRaises(ReturnTypeError, py3.Test_agent_err_class.testclassmeth_agent_err)

    def test_init_agent_return_None(self):
        with TypeChecker():
            py3.Test_agent_err_class()


if __name__ == '__main__':
    unittest.main()
