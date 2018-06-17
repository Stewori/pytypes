# Copyright 2017 Stefan Richthofer
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

# Created on 12.09.2016

import abc
from abc import abstractmethod
from numbers import Real

import pytypes
import testhelpers
from pytypes import typechecked, override, check_argument_types, auto_override

try:
    from backports.typing import Tuple, Union, Mapping, Dict, Generator, TypeVar, Generic, \
        Iterable, Iterator, Sequence, Callable, List, Any
except ImportError:
    from typing import Tuple, Union, Mapping, Dict, Generator, TypeVar, Generic, Iterable, \
        Iterator, Sequence, Callable, List, Any, Optional


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

    # Using not the fully qualified name can screw up typing.get_type_hints
    # under certain circumstances.
    # Todo: Investigate! pytypes.get_type_hints seems to be robust.
    @typechecked
    def testmeth_forward(self, a: int, b: 'testhelpers.typechecker_testhelper_py3.testClass2') -> int:
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

@typechecked
def testfunc_Dict_arg(a: int, b: Dict[str, Union[int, str]]) -> None:
    assert isinstance(b[str(a)], str) or isinstance(b[str(a)], int)

@typechecked
def testfunc_Mapping_arg(a: int, b: Mapping[str, Union[int, str]]) -> None:
    assert isinstance(b[str(a)], str) or isinstance(b[str(a)], int)

@typechecked
def testfunc_Dict_ret(a: str) -> Dict[str, Union[int, str]]:
    return {a: len(a), 2*a: a}

@typechecked
def testfunc_Dict_ret_err(a: int) -> Dict[str, Union[int, str]]:
    return {a: str(a), 2*a: a}

@typechecked
def testfunc_Seq_arg(a: Sequence[Tuple[int, str]]) -> int:
    return len(a)

@typechecked
def testfunc_Seq_ret_List(a: int, b: str) -> Sequence[Union[int, str]]:
    return [a, b]

@typechecked
def testfunc_Seq_ret_Tuple(a: int, b: str) -> Sequence[Union[int, str]]:
    return a, b

@typechecked
def testfunc_Seq_ret_err(a: int, b: str) -> Sequence[Union[int, str]]:
    return {a: str(a), b: str(b)}

@typechecked
def testfunc_Iter_arg(a: Iterable[int], b: str) -> List[int]:
    return [r for r in a]

@typechecked
def testfunc_Iter_str_arg(a: Iterable[str]) -> List[int]:
    return [ord(r) for r in a]

@typechecked
def testfunc_Iter_ret() -> Iterable[int]:
    return [1, 2, 3, 4, 5]

@typechecked
def testfunc_Iter_ret_err() -> Iterable[str]:
    return [1, 2, 3, 4, 5]

@typechecked
def testfunc_Callable_arg(a: Callable[[str, int], str], b: str) -> str:
    return a(b, len(b))

@typechecked
def testfunc_Callable_call_err(a: Callable[[str, int], str], b: str) -> str:
    return a(b, b)

@typechecked
def testfunc_Callable_ret(a: int, b: str) -> Callable[[str, int], str]:
    
    def m(x: str, y: int) -> str:
        return x+str(y)+b*a

    return m

@typechecked
def testfunc_Callable_ret_err() -> Callable[[str, int], str]:
    return 5

def pclb(s: str, i: int) -> str:
    return '_'+s+'*'*i

def pclb2(s: str, i: str) -> str:
    return '_'+s+'*'*i

def pclb3(s: str, i: int) -> int:
    return '_'+s+'*'*i

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

T_1_py3 = TypeVar('T_1_py3')
class Custom_Generic(Generic[T_1_py3]):
    
    def __init__(self, val: T_1_py3) -> None:
        self.val = val

    def v(self) -> T_1_py3:
        return self.val

@typechecked
def testfunc_Generic_arg(x: Custom_Generic[str]) -> str:
    return x.v()

@typechecked
def testfunc_Generic_ret(x: int) -> Custom_Generic[int]:
    return Custom_Generic[int](x)

@typechecked
def testfunc_Generic_ret_err(x: int) -> Custom_Generic[int]:
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

    def __iter__(self) -> Iterator[int]:
        return test_iter(self)


class testClass_check_argument_types(object):

    def testMeth_check_argument_types(self, a: int) -> None:
        check_argument_types()

    @classmethod
    def testClassmeth_check_argument_types(cls, a: int) -> None:
        check_argument_types()

    @staticmethod
    def testStaticmeth_check_argument_types(a: int) -> None:
        check_argument_types()

def testfunc_check_argument_types(a: int, b: float, c: str) -> None:
    check_argument_types()

def testfunc_check_argument_types2(a: Sequence[float]) -> None:
    check_argument_types()

def test_inner_method_testf1():
    def testf2(x: Tuple[int, float]) -> str:
        pytypes.check_argument_types()
        return str(x)
    return testf2((3, 6))

def test_inner_method_testf1_err():
    def testf2(x: Tuple[int, float]) -> str:
        pytypes.check_argument_types()
        return str(x)
    return testf2((3, '6'))

def test_inner_class_testf1():
    class test_class_in_func(object):
        def testm1(self, x: int) -> str:
            pytypes.check_argument_types()
            return str(x)
    return test_class_in_func().testm1(99)

def test_inner_class_testf1_err():
    class test_class_in_func(object):
        def testm1(self, x: int) -> str:
            pytypes.check_argument_types()
            return str(x)
    return test_class_in_func().testm1(99.5)


class testClass_property(object):

    @typechecked
    @property
    def testprop(self) -> int:
        return self._testprop

    @typechecked
    @testprop.setter
    def testprop(self, value: int) -> None:
        self._testprop = value

    @typechecked
    @property
    def testprop2(self) -> str:
        return self._testprop2

    @testprop2.setter
    def testprop2(self, value: str) -> None:
        self._testprop2 = value

    @typechecked
    @property
    def testprop3(self) -> Tuple[int, str]:
        return self._testprop3

    @testprop3.setter
    def testprop3(self, value: Tuple[int, str]) -> None:
        check_argument_types()
        self._testprop3 = value


@typechecked
class testClass_property_class_check(object):
    @property
    def testprop(self) -> int:
        return self._testprop

    @testprop.setter
    def testprop(self, value: int) -> None:
        self._testprop = value

    @property
    def testprop2(self) -> float:
        return 'abc'

    @testprop2.setter
    def testprop2(self, value: float) -> None:
        pass


@typechecked
def testfunc_varargs1(*argss: float) -> Tuple[int, float]:
    res = 1.0
    for arg in argss:
        res *= arg
    return len(argss), res

@typechecked
def testfunc_varargs2(a: str, b: int, c: None,
        *varg: int) -> Tuple[int, str]:
    res = 1
    for arg in varg:
        res *= arg
    return res, a*b

@typechecked
def testfunc_varargs3(*args: int, **kwds: float) -> Tuple[str, float]:
    longest = ''
    for key in kwds:
        if len(key) > len(longest):
            longest = key
    return longest*(args[0]//len(args)), kwds[longest]

@typechecked
def testfunc_varargs4(**kwds: float) -> float:
    longest = ''
    for key in kwds:
        if len(key) > len(longest):
            longest = key
    return 0 if longest == '' else kwds[longest]

@typechecked
def testfunc_varargs5(a1: int, a2: str, *vargss: float,
        **vkwds: int) -> List[int]:
    return [len(vargss), len(str(vargss[a1])), vkwds[a2]]

@typechecked
def testfunc_varargs6(a1: int, a2: str, *vargss: float,
        b1: int, b2: str, **vkwds: int) -> List[int]:
    return [len(vargss), len(str(vargss[a1])), vkwds[a2], b1, len(b2)]

@typechecked
def testfunc_varargs6b(a1, a2, *vargss, b1, b2, **vkwds):
    # type: (int, str, *float, int, str, **int) -> List[int]
    return [len(vargss), len(str(vargss[a1])), vkwds[a2], b1, len(b2)]

@typechecked
def testfunc_varargs_err(a1: int, a2: str, *vargss: float,
        **vkwds: int) -> List[int]:
    return [len(vargss), str(vargss[a1]), vkwds[a2]]

@typechecked
class testclass_vararg():
    def testmeth_varargs1(self, *vargs: Tuple[str, int]) -> int:
        res = 1
        for arg in vargs:
            res += len(arg[0])*arg[1]
        return res-len(self.__class__.__name__)

    def testmeth_varargs2(self, q1: int, q2: str, *varargs: float,
            **varkw: int) -> List[int]:
        return [len(varargs), len(str(varargs[q1])), varkw[q2],
                len(self.__class__.__name__)]

    def testmeth_varargs3(self, q1: int, q2: str, *varargs: float,
            w1: float, w2: Tuple[int, str], **varkw: int) -> List[int]:
        return [len(varargs), len(str(varargs[q1])), varkw[q2],
                len(self.__class__.__name__), int(w1*w2[0]), len(w2[1])]

    def testmeth_varargs_3b(self, q1, q2, *varargs, w1, w2, **varkw):
        # type: (int, str, float, float, Tuple[int, str], int) -> List[int]
        return [len(varargs), len(str(varargs[q1])), varkw[q2],
                len(self.__class__.__name__), int(w1*w2[0]), len(w2[1])]

    @staticmethod
    def testmeth_varargs_static1(*vargs_st: float) -> Tuple[int, float]:
        res = 1.0
        for arg in vargs_st:
            res *= arg
        return len(vargs_st), res

    @staticmethod
    def testmeth_varargs_static2(q1_st: int, q2_st: str, *varargs_st: float,
            **varkw_st: int) -> List[int]:
        return [len(varargs_st), len(str(varargs_st[q1_st])), varkw_st[q2_st]]

    @classmethod
    def testmeth_varargs_class1(cls, *vargs_cls: Tuple[str, int]) -> int:
        res = 1
        for arg in vargs_cls:
            res += len(arg[0])*arg[1]
        return res-len(cls.__name__)

    @classmethod
    def testmeth_varargs_class2(cls, q1_cls: int, q2_cls: str,
            *varargs_cls: float, **varkw_cls: int) -> List[int]:
        return [len(varargs_cls), len(str(varargs_cls[q1_cls])),
                varkw_cls[q2_cls], len(cls.__name__)]

    @property
    def prop1(self) -> str:
        return self._prop1

    @prop1.setter
    def prop1(self, *vargs_prop: str) -> None:
        self._prop1 = vargs_prop[0]

def testfunc_varargs_ca1(*argss: float) -> Tuple[int, float]:
    check_argument_types()
    res = 1.0
    for arg in argss:
        res *= arg
    return len(argss), res

def testfunc_varargs_ca2(a: str, b: int, c: None,
        *varg: int) -> Tuple[int, str]:
    check_argument_types()
    res = 1
    for arg in varg:
        res *= arg
    return res, a*b

def testfunc_varargs_ca3(*args: int, **kwds: float) -> Tuple[str, float]:
    check_argument_types()
    longest = ''
    for key in kwds:
        if len(key) > len(longest):
            longest = key
    return longest*(args[0]//len(args)), kwds[longest]

def testfunc_varargs_ca4(**kwds: float) -> float:
    check_argument_types()
    longest = ''
    for key in kwds:
        if len(key) > len(longest):
            longest = key
    return 0 if longest == '' else kwds[longest]

def testfunc_varargs_ca5(a1: int, a2: str, *vargss: float,
        **vkwds: int) -> List[int]:
    check_argument_types()
    return [len(vargss), len(str(vargss[a1])), vkwds[a2]]

def testfunc_varargs_ca6(a1: int, a2: str, *vargss: float,
        b1: int, b2: str, **vkwds: int) -> List[int]:
    check_argument_types()
    return [len(vargss), len(str(vargss[a1])), vkwds[a2], b1, len(b2)]

def testfunc_varargs_ca6b(a1, a2, *vargss, b1, b2, **vkwds):
    # type: (int, str, *float, int, str, **int) -> List[int]
    check_argument_types()
    return [len(vargss), len(str(vargss[a1])), vkwds[a2], b1, len(b2)]

class testclass_vararg_ca():
    def testmeth_varargs_ca1(self, *vargs: Tuple[str, int]) -> int:
        check_argument_types()
        res = 1
        for arg in vargs:
            res += len(arg[0])*arg[1]
        return res-len(self.__class__.__name__)

    def testmeth_varargs_ca2(self, q1: int, q2: str,
            *varargs: float, **varkw: int) -> List[int]:
        check_argument_types()
        return [len(varargs), len(str(varargs[q1])), varkw[q2],
                len(self.__class__.__name__)]

    def testmeth_varargs_ca3(self, q1: int, q2: str, *varargs: float,
            w1: float, w2: Tuple[int, str], **varkw: int) -> List[int]:
        check_argument_types()
        return [len(varargs), len(str(varargs[q1])), varkw[q2],
                len(self.__class__.__name__), int(w1*w2[0]), len(w2[1])]

    def testmeth_varargs_ca3b(self, q1, q2, *varargs, w1, w2, **varkw):
        # type: (int, str, *float, float, Tuple[int, str], **int) -> List[int]
        check_argument_types()
        return [len(varargs), len(str(varargs[q1])), varkw[q2],
                len(self.__class__.__name__), int(w1*w2[0]), len(w2[1])]

    @staticmethod
    def testmeth_varargs_static_ca1(*vargs_st: float) -> Tuple[int, float]:
        check_argument_types()
        res = 1.0
        for arg in vargs_st:
            res *= arg
        return len(vargs_st), res

    @staticmethod
    def testmeth_varargs_static_ca2(q1_st: int, q2_st: str,
            *varargs_st: float, **varkw_st: int) -> List[int]:
        check_argument_types()
        return [len(varargs_st), len(str(varargs_st[q1_st])), varkw_st[q2_st]]

    @classmethod
    def testmeth_varargs_class_ca1(cls, *vargs_cls: Tuple[str, int]) -> int:
        check_argument_types()
        res = 1
        for arg in vargs_cls:
            res += len(arg[0])*arg[1]
        return res-len(cls.__name__)

    @classmethod
    def testmeth_varargs_class_ca2(cls, q1_cls: int, q2_cls: str,
            *varargs_cls: float, **varkw_cls: int) -> List[int]:
        check_argument_types()
        return [len(varargs_cls), len(str(varargs_cls[q1_cls])),
                varkw_cls[q2_cls], len(cls.__name__)]

    @property
    def prop_ca1(self) -> str:
        check_argument_types()
        return self._prop_ca1

    @prop_ca1.setter
    def prop_ca1(self, *vargs_prop: str) -> None:
        check_argument_types()
        self._prop_ca1 = vargs_prop[0]

@typechecked
def func_defaults_typecheck(a: str, b, c=4, d=2.5) -> str:
    try:
        return a+b*c
    except TypeError:
        return 'invalid'

@typechecked
def func_defaults_typecheck2(a: str, b: float, c: Optional[int]=1, d: bool=False) -> str:
    try:
        return a+str(b*c)+str(d)
    except TypeError:
        return 'invalid'

def func_defaults_checkargs(a: str, b, c=4, d=2.5) -> str:
    check_argument_types()
    try:
        return a+b*c
    except TypeError:
        return 'invalid'

@pytypes.annotations
def func_defaults_annotations(a: str, b, c=4) -> str:
    b = 'abc'
    return a+b*c

class override_varargs_class_base(object):
# var-arg tests:
    def method_vararg1(self, a: int, b: int, *args: int) -> int:
        return a+b

    def method_vararg2(self, a: int, b: int) -> int:
        return a+b

    def method_vararg3(self, a: int, b: int, c: float) -> int:
        return a+b

    def method_vararg1_err(self, a: int, b: int, *args: float) -> int:
        return a+b

    def method_vararg2_err(self, a: float, b: int) -> int:
        return a+b

    def method_vararg3_err(self, a: int, b: int, c: float) -> int:
        return a+b

# var-kw tests:
    def method_varkw1(self, a: int, b: int, **kw: int) -> int:
        return a+b

    def method_varkw2(self, a: int, b: int, *arg: str, **kw: int) -> int:
        return a+b

    def method_varkw1_err(self, a: int, b: int, **kw: float) -> int:
        return a+b

    def method_varkw2_err(self, a: int, b: int, *arg: str, **kw: float) -> int:
        return a+b

    def method_varkw3_err(self, a: int, b: int, *arg: str, **kw: str) -> int:
        return a+b

# default tests:
    def method_defaults1(self, a: int, b: int) -> int:
        return a+b

    def method_defaults2(self, a: int, b: int, *vargs: int) -> int:
        return a+b

    def method_defaults1_err(self, a: int, b: float) -> int:
        return a+b

    def method_defaults2_err(self, a: int, b: int, *vargs: float) -> int:
        return a+b

# kw-only tests (Python 3 only):
    def method_kwonly1(self, a: int, b: int, *vargs: float, q: int) -> int:
        return a+b+q

    def method_kwonly2(self, a: int, b: int, *vargs: float, q: int) -> int:
        return a+b+q

    def method_kwonly3(self, a: int, b: int, *vargs: float, q: int, v: float) -> int:
        return a+b+q

    def method_kwonly4(self, a: float, b: int, *vargs: float, q: int) -> int:
        return b+q

    def method_kwonly5(self, a: float, b: float, *vargs: int, q: int, v: int, **kw: int) -> int:
        return q+v+len(kw)

    def method_kwonly6(self, a: float, b: int, *vargs: float, q: int, v: int) -> int:
        return b+q+v

    def method_kwonly7(self, a: int, b: float, *vargs: float, q: int, v: int, **kw: int) -> int:
        return a+b+q+v

    def method_kwonly1_err(self, a: int, b: int, *vargs: float, q: float) -> int:
        return a+b+q

    def method_kwonly2_err(self, a: int, b: int, *vargs: float, q: int) -> int:
        return a+b+q

    def method_kwonly3_err(self, a: int, b: int, *vargs: float, q: int) -> int:
        return a+b+q

    def method_kwonly4_err(self, a: float, b: int, *vargs: float, q: int) -> int:
        return b+q

    def method_kwonly5_err(self, a: float, b: float, *vargs: int, q: int, v: int, **kw: int) -> int:
        return q+v

    def method_kwonly6_err(self, a: float, b: int, *vargs: float, q: float, v: int) -> int:
        return b+v

    def method_kwonly7_err(self, a: int, b: float, *vargs: float, q: int, v: float, **kw: float) -> int:
        return a+q

    def method_kwonly8_err(self, a: int, b: float, *vargs: float, q: int, v: int, **kw: float) -> int:
        return a+b+q+v

# kw-only tests (Python 2 type hints):
    def method_kwonly1_py2(self, a, b, *vargs, q):
        # type: (int, int, *float, int) -> int
        return a+b+q

    def method_kwonly2_py2(self, a, b, *vargs, q):
        # type: (int, int, *float, int) -> int
        return a+b+q

    def method_kwonly3_py2(self, a, b, *vargs, q, v):
        # type: (int, int, *float, int, float) -> int
        return a+b+q

    def method_kwonly4_py2(self, a, b, *vargs, q):
        # type: (float, int, *float, int) -> int
        return b+q

    def method_kwonly5_py2(self, a, b, *vargs, q, v, **kw):
        # type: (float, float, *int, int, int, **int) -> int
        return q+v+len(kw)

    def method_kwonly6_py2(self, a, b, *vargs, q, v):
        # type: (float, int, *float, int, int) -> int
        return b+q+v

    def method_kwonly7_py2(self, a, b, *vargs, q, v, **kw):
        # type: (int, float, *float, int, int, **int) -> int
        return a+b+q+v

    def method_kwonly1_err_py2(self, a, b, *vargs, q):
        # type: (int, int, *float, float) -> int
        return a+b+q

    def method_kwonly2_err_py2(self, a, b, *vargs, q):
        # type: (int, int, *float, int) -> int
        return a+b+q

    def method_kwonly3_err_py2(self, a, b, *vargs, q):
        # type: (int, int, *float, int) -> int
        return a+b+q

    def method_kwonly4_err_py2(self, a, b, *vargs, q):
        # type: (float, int, *float, int) -> int
        return a+b+q

    def method_kwonly5_err_py2(self, a, b, *vargs, q, v, **kw):
        # type: (float, float, *int, int, int, **int) -> int
        return a+b+q+v

    def method_kwonly6_err_py2(self, a, b, *vargs, q, v):
        # type: (float, int, *float, float, int) -> int
        return a+b+q+v

    def method_kwonly7_err_py2(self, a, b, *vargs, q, v, **kw):
        # type: (int, float, *float, int, float, **float) -> int
        return a+b+q+v

    def method_kwonly8_err_py2(self, a, b, *vargs, q, v, **kw):
        # type: (int, float, *float, int, int, **float) -> int
        return a+b+q+v

class override_varargs_class(override_varargs_class_base):
    @override
    def method_vararg1(self, a: int, b: float, *args: int) -> int:
        return len(args)

    @override
    def method_vararg2(self, a: int, b: float, *vargs: str) -> int:
        return a+len(str(b))+len(vargs)

    @override
    def method_vararg3(self, a: int, *vgs: float) -> int:
        return a+len(vgs)

    @override
    def method_vararg1_err(self, a: int, b: float, *args: int) -> int:
        return len(args)

    @override
    def method_vararg2_err(self, a: int, b: float, *vargs: str) -> int:
        return a+len(str(b))+len(vargs)

    @override
    def method_vararg3_err(self, a: int, *vgs: int) -> int:
        return a+len(vgs)

# var-kw tests:
    @override
    def method_varkw1(self, a: int, b: int, **kw: float) -> int:
        return a+b

    @override
    def method_varkw2(self, a: int, b: int, *arg: str, **kw: float) -> int:
        return a+b

    @override
    def method_varkw1_err(self, a: int, b: int, **kw: int) -> int:
        return a+b

    @override
    def method_varkw2_err(self, a: int, b: int, *arg: str, **kw: int) -> int:
        return a+b

    @override
    def method_varkw3_err(self, a: int, b: int, *arg: str) -> int:
        return a+b

# default tests:
    @override
    def method_defaults1(self, a: int, b: int, c=4.6) -> int:
        return a+b

    @override
    def method_defaults2(self, a: int, b: int, c: float = 4, *args: int) -> int:
        return a+b

    @override
    def method_defaults1_err(self, a: int, b: int, c=2) -> int:
        return a+b

    @override
    def method_defaults2_err(self, a: int, b: int, c: int = 3, *vargs: float) -> int:
        return a+b

# kw-only tests (Python 3 only):
    @override
    def method_kwonly1(self, a: int, b: int, *vargs: float, q: float, **vkw: str) -> int:
        # child can add var-kw
        return a+b

    @override
    def method_kwonly2(self, a: int, b: int, *vargs: float, q: int, v=17) -> int:
        # child can add default kw-only
        return a+b+q

    @override
    def method_kwonly3(self, a: int, b: int, *vargs: float, v: float, q: int) -> int:
        # child can reorder kw-only
        return a+b+q

    @override
    def method_kwonly4(self, a: float, b: int, q: float, *vargs: float) -> int:
        # child can move kw-only to ordinary arg
        return len(str(a+b+q))

    @override
    def method_kwonly5(self, a: float, b: float, *vargs: int, q: float, v: int, **kw: float) -> int:
        # child must also have var-kw
        return len(str(a+b+v))

    @override
    def method_kwonly6(self, a: float, b: int, *vargs: float, q: int, **kwargs: float) -> int:
        # child can drop kw-only in favor of var-kw
        return b+q+len(kwargs)

    @override
    def method_kwonly7(self, a: int, b: float, *vargs: float, q: float, **kw: int) -> int:
        # child can drop kw-only in favor of var-kw
        return a+b

    @override
    def method_kwonly1_err(self, a: int, b: int, *vargs: float, q: int) -> int:
        # child has wrong type in kw-only
        return a+b+q

    @override
    def method_kwonly2_err(self, a: int, b: int, *vargs: float) -> int:
        # child lacks kw-only
        return a+b+q

    @override
    def method_kwonly3_err(self, a: int, *vargs: float, q: int, b: int) -> int:
        # child moves ordinary arg to kw-only
        return a+b+q

    @override
    def method_kwonly4_err(self, a: float, b: int, *vargs: float, q: int, v: str) -> int:
        # child adds required kw-only
        return a+b+q

    @override
    def method_kwonly5_err(self, a: float, b: float, *vargs: int, q: int, v: int) -> int:
        # child lacks var-kw
        return a+b+q+v

    @override
    def method_kwonly6_err(self, a: float, b: int, *vargs: float, q: int, **varkw: int) -> int:
        # child drops kw-only in favor of wrong-typed (vs kwonly) var-kw
        return a+b+q+v

    @override
    def method_kwonly7_err(self, a: int, b: float, *vargs: float, q: int, v: int, **kw: float) -> int:
        # child drops kw-only in favor of wrong-typed (vs kwonly) var-kw
        return a+b+q+v

    @override
    def method_kwonly8_err(self, a: int, b: float, *vargs: float, **kw: int) -> int:
        # child drops kw-only in favor of wrong-typed (vs var-kw) var-kw
        return a+b+q+v

# kw-only tests (Python 2 type hints):
    @override
    def method_kwonly1_py2(self, a, b, *vargs, q, **vkw):
        # type: (int, int, *float, float, **str) -> int
        # child can add var-kw
        return a+b

    @override
    def method_kwonly2_py2(self, a, b, *vargs, q, v=17):
        # type: (int, int, *float, int) -> int
        # child can add default kw-only
        return a+b+q

    @override
    def method_kwonly3_py2(self, a, b, *vargs, v, q):
        # type: (int, int, *float, float, int) -> int
        # child can reorder kw-only
        return a+b+q

    @override
    def method_kwonly4_py2(self, a, b, q, *vargs):
        # type: (float, int, float, *float) -> int
        # child can move kw-only to ordinary arg
        return len(str(a+b+q))

    @override
    def method_kwonly5_py2(self, a, b, *vargs, q, v, **kw):
        # type: (float, float, *int, float, int, **float) -> int
        # child must also have var-kw
        return len(str(a+b+v))

    @override
    def method_kwonly6_py2(self, a, b, *vargs, q, **kwargs):
        # type: (float, int, *float, int, **float) -> int
        # child can drop kw-only in favor of var-kw
        return b+q+len(kwargs)

    @override
    def method_kwonly7_py2(self, a, b, *vargs, q, **kw):
        # type: (int, float, *float, float, **int) -> int
        # child can drop kw-only in favor of var-kw
        return a+b

    @override
    def method_kwonly1_err_py2(self, a, b, *vargs, q):
        # type: (int, int, *float, int) -> int
        # child has wrong type in kw-only
        return a+b+q

    @override
    def method_kwonly2_err_py2(self, a, b, *vargs):
        # type: (int, int, *float) -> int
        # child lacks kw-only
        return a+b+q

    @override
    def method_kwonly3_err_py2(self, a, *vargs, q, b):
        # type: (int, *float, int, int) -> int
        # child moves ordinary arg to kw-only
        return a+b+q

    @override
    def method_kwonly4_err_py2(self, a, b, *vargs, q, v):
        # type: (float, int, *float, int, str) -> int
        # child adds required kw-only
        return a+b+q

    @override
    def method_kwonly5_err_py2(self, a, b, *vargs, q, v):
        # type: (float, float, *int, int, int) -> int
        # child lacks var-kw
        return a+b+q+v

    @override
    def method_kwonly6_err_py2(self, a, b, *vargs, q, **varkw):
        # type: (float, int, *float, int, **int) -> int
        # child drops kw-only in favor of wrong-typed (vs kwonly) var-kw
        return a+b+q+v

    @override
    def method_kwonly7_err_py2(self, a, b, *vargs, q, v, **kw):
        # type: (int, float, *float, int, int, **float) -> int
        # child drops kw-only in favor of wrong-typed (vs kwonly) var-kw
        return a+b+q+v

    @override
    def method_kwonly8_err_py2(self, a, b, *vargs, **kw):
        # type: (int, float, *float, **int) -> int
        # child drops kw-only in favor of wrong-typed (vs var-kw) var-kw
        return a+b+q+v

class varagrs_call_class_base(object):
    def testmeth1(self, a: int, b: float) -> float:
        return a+b

    def testmeth2(self, a: int, b: float) -> float:
        return a+b

    def testmeth3(self, a: int, b: float) -> float:
        return a+b

    def testmeth4(self, a: int, b: float) -> float:
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


class A_check_parent_types():
    def meth1(self, a: int) -> int:
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
    def meth1(self, a: float) -> int:
        check_argument_types()
        return len(str(a))

class B_override_with_type_typechecked(A_check_parent_types):
    @typechecked
    @override
    def meth1(self, a: float) -> int:
        check_argument_types()
        return len(str(a))


class A_diamond_override(object):
    def meth1(self, a: Tuple[int, int]) -> int:
        return len(str(a))

class B_diamond_override(A_diamond_override):
    @override
    def meth1(self, a: Tuple[int, float]) -> int:
        return len(str(a))

class C_diamond_override(A_diamond_override):
    @override
    def meth1(self, a: Tuple[float, int]) -> int:
        return len(str(a))

class D_diamond_override(B_diamond_override, C_diamond_override):
    @override
    def meth1(self, a: Tuple[float, float]) -> int:
        check_argument_types()
        return len(str(a))

class D_diamond_override_err1(B_diamond_override, C_diamond_override):
    @override
    def meth1(self, a: Tuple[float, int]) -> int:
        return len(str(a))

class D_diamond_override_err2(B_diamond_override, C_diamond_override):
    @override
    def meth1(self, a: Tuple[int, float]) -> int:
        return len(str(a))

class D_diamond_override_err3(B_diamond_override, C_diamond_override):
    @override
    def meth1(self, a: Tuple[int, int]) -> int:
        return len(str(a))


class A_auto_override():
    def meth_1(self, a: str, b: Tuple[int, float]) -> int:
        pass


@auto_override
class B_auto_override(A_auto_override):
    def meth_1(self, a: str, b: Tuple[float, float]) -> int:
        return len(str(len(a)+b[0]-b[1]))

    def meth_2(self, c: str) -> int:
        return 3*len(c)


@auto_override
class B_auto_override_err(A_auto_override):
    def meth_1(self, a: str, b: Tuple[int, int]) -> int:
        return len(str(len(a)+b[0]-b[1]))

    def meth_2(self, c: str) -> int:
        return 3*len(c)


T_ct = TypeVar('T_ct', contravariant=True)
T_cv = TypeVar('T_cv', covariant=True)
T_ = TypeVar('T_')

@typechecked
def tpvar_test1(a: T_, b: T_) -> str:
    return 'hello'

@typechecked
def tpvar_test2(a: T_cv, b: T_cv) -> str:
    return 'hello'

@typechecked
def tpvar_test3(a: T_ct, b: T_ct) -> str:
    return 'hello'

@typechecked
def tpvar_test4(lst: List[T_], idx: int) -> T_:
    return lst[idx]

@typechecked
def tpvar_test5(lst: List[T_], idx: int) -> T_:
    return str(lst[idx])

T2 = TypeVar('T2', covariant=True)

@typechecked
class A(Generic[T2]):
    def __init__(self, obj: T2) -> None:
        super(A, self).__init__()
        self.obj = obj		

class IntA(A[int]): pass
class IntB(IntA): pass

@typechecked
def test_typevar_A(x: A[int]) -> None:
    pass

def testfunc_agent(v: str) -> int:
    return 69

def testfunc_agent_err(v: str) -> int:
    return 'abc'
