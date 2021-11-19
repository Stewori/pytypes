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

# Created on 29.01.2017

from pytypes import override
from typing import Tuple, Union, Mapping, Dict, Generator, TypeVar, Generic, \
        Iterable, Iterator, Sequence, Callable, List, Any
import abc; from abc import abstractmethod
from numbers import Real

class testClass(str):

    def testmeth(self, a: int, b: Real) -> str:
        return "-".join((str(a), str(b), self))

    def testmeth2(self, a: int, b: Real) -> str:
        # type: (int, Real) -> str
        return "-".join((str(a), str(b), self))

    @classmethod
    def testmeth_class(cls, a: int, b: Real) -> str:
        # type: (int, Real) -> str
        return "-".join((str(a), str(b), str(cls)))

    @classmethod
    def testmeth_class2(cls, a: int, b: Real) -> str:
        return "-".join((str(a), str(b), str(cls)))

    @classmethod
    def testmeth_class2_err(cls, a: int, b: Real) -> int:
        return "-".join((str(a), str(b), str(cls)))

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

    @staticmethod
    def testmeth_static2(a: int, b: Real) -> str:
        return "-".join((str(a), str(b), "static"))

    # Using not the fully qualified name can screw up typing.get_type_hints
    # under certain circumstances.
    # Todo: Investigate! pytypes.get_type_hints seems to be robust.
    def testmeth_forward(self, a: int, b: 'pytypes.tests.testhelpers.typechecker_testhelper_py3.testClass2') -> int:
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

    @override
    def testmeth3(self, a, b):
        return "-".join((str(a), str(b), self))

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

    def testmeth_err(self, a: int, b: Real) -> int:
        return "-".join((str(a), str(b), self))


class testClass3Base():
    __metaclass__  = abc.ABCMeta

    @abstractmethod
    def testmeth(self, a: int, b: Real) -> Union[str, int]:
        pass


class testClass3(testClass3Base):

    @override
    def testmeth(self, a, b):
        return "-".join((str(a), str(b), str(type(self))))


def testClass2_defTimeCheck():
    class testClass2b(testClass2Base):
        def testmeth0(self, a: int, b: Real) -> str:
            return "-".join((str(a), str(b), self))

        @override
        def testmeth(self, a: int, b: Real) -> str:
            return "-".join((str(a), str(b), self))
    
        def testmeth2c(self, a: int, b: Real) -> Union[str, Real]:
            # type: (int, Real) -> Union[str, Real]
            return "-".join((str(a), str(b), self))

        @override
        def testmeth3(self, a: int, b: Real) -> str:
            # type: (int, Real) -> str
            return "-".join((str(a), str(b), self))

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
    
        @override
        def testmeth(self, a, b):
            return "-".join((str(a), str(b), str(type(self))))


def testfunc(a: int, b: Real, c: str) -> Tuple[int, Real]:
    # type: (int, Real, str) -> Tuple[int, Real]
    return a*a, a*b

def testfunc_err(a: int, b: Real, c: str) -> Tuple[str, Real]:
    # type: (int, Real, str) -> Tuple[str, Real]
    return a*a, a*b

def testfunc2(a: int, b: Real, c: testClass) -> Tuple[int, float]:
    return a*a, a*b

def testfunc_None_ret(a: int, b: Real) -> None:
    pass

def testfunc_None_ret_err(a: int, b: Real) -> None:
    # type: (int, Real) -> None
    # (asserting compatibility between different annotation formats)
    return 7

def testfunc_None_arg(a: int, b: None) -> int:
    return a*a

def testfunc_Dict_arg(a: int, b: Dict[str, Union[int, str]]) -> None:
    assert isinstance(b[str(a)], str) or isinstance(b[str(a)], int)

def testfunc_Mapping_arg(a: int, b: Mapping[str, Union[int, str]]) -> None:
    assert isinstance(b[str(a)], str) or isinstance(b[str(a)], int)

def testfunc_Dict_ret(a: str) -> Dict[str, Union[int, str]]:
    return {a: len(a), 2*a: a}

def testfunc_Dict_ret_err(a: int) -> Dict[str, Union[int, str]]:
    return {a: str(a), 2*a: a}

def testfunc_Seq_arg(a: Sequence[Tuple[int, str]]) -> int:
    return len(a)

def testfunc_Seq_ret_List(a: int, b: str) -> Sequence[Union[int, str]]:
    return [a, b]

def testfunc_Seq_ret_Tuple(a: int, b: str) -> Sequence[Union[int, str]]:
    return a, b

def testfunc_Seq_ret_err(a: int, b: str) -> Sequence[Union[int, str]]:
    return {a: str(a), b: str(b)}

def testfunc_Iter_arg(a: Iterable[int], b: str) -> List[int]:
    return [r for r in a]

def testfunc_Iter_str_arg(a: Iterable[str]) -> List[int]:
    return [ord(r) for r in a]

def testfunc_Iter_ret() -> Iterable[int]:
    return [1, 2, 3, 4, 5]

def testfunc_Iter_ret_err() -> Iterable[str]:
    return [1, 2, 3, 4, 5]

def testfunc_Callable_arg(a: Callable[[str, int], str], b: str) -> str:
    return a(b, len(b))

def testfunc_Callable_call_err(a: Callable[[str, int], str], b: str) -> str:
    return a(b, b)

def testfunc_Callable_ret(a: int, b: str) -> Callable[[str, int], str]:
    def m(x: str, y: int) -> str:
        return x+str(y)+b*a

    return m

def testfunc_Callable_ret_err() -> Callable[[str, int], str]:
    return 5

def pclb(s: str, i: int) -> str:
    return '_'+s+'*'*i

def pclb2(s: str, i: str) -> str:
    return '_'+s+'*'*i

def pclb3(s: str, i: int) -> int:
    return '_'+s+'*'*i

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

def testfunc_Generator_arg(gen: Generator[int, Union[str, None], Any]) -> List[int]:
    # should raise error because of illegal use of typing.Generator
    lst = ('ab', 'nmrs', 'u')
    res = [gen.send(x) for x in lst]
    return res

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

def testfunc_Generic_arg(x: Custom_Generic[str]) -> str:
    return x.v()

def testfunc_Generic_ret(x: int) -> Custom_Generic[int]:
    return Custom_Generic[int](x)

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
