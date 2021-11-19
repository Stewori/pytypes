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

from pytypes import override, no_type_check

import typing; from typing import Tuple, List, Union, Any, Dict, Generator, TypeVar, \
        Generic, Iterable, Iterator, Sequence, Callable, Mapping
from numbers import Real
import abc; from abc import abstractmethod

class testClass(str):
    def testmeth(self, a, b):
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

    @staticmethod
    def testmeth_static_raw(a, b):
        # type: (int, Real) -> str
        return '-'.join((str(a), str(b), 'static'))

    @classmethod
    def testmeth_class_raw(cls, a, b):
        # type: (int, Real) -> str
        return '-'.join((str(a), str(b), 'static'))

    @staticmethod
    def testmeth_static2(a, b):
        # type: (int, Real) -> str
        return '-'.join((str(a), str(b), 'static'))

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

    @override
    def testmeth3(self, a, b):
        # type: (int, Real) -> str
        return '-'.join((str(a), str(b), self))

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
    @override
    def testmeth(self, a, b):
        return '-'.join((str(a), str(b), str(type(self))))


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


class testClass5_base(object):
    def testmeth_cls5(self, a, b):
        # type: (int, Real) -> str
        return 'Dummy implementation 5'


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

        @override
        def testmeth3(self, a, b):
            # type: (int, Real) -> str
            return '-'.join((str(a), str(b), self))

        @override
        def testmeth3b(self, a, b):
            return '-'.join((str(a), str(b), self))

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
        @override
        def testmeth(self, a, b):
            return '-'.join((str(a), str(b), str(type(self))))

def testClass2_defTimeCheck_init_ov():
    class testClass2_defTime_init_ov(testClass2Base):
        @override
        def __init__(self): # should fail because of invalid use of @override
            pass


def testfunc(a, # type: int
            b,  # type: Real
            c   # type: str
            ):
    # type: (...) -> Tuple[int, Real]
    return a*a, a*b

def testfunc_err(
            a, # type: int
            b, # type: Real
            c  # type: str
            ):
    # type: (...) -> Tuple[str, Real]
    return a*a, a*b

def testfunc2(a, b, c):
    # type: (int, Real, testClass) -> Tuple[int, float]
    return a*a, a*b

def testfunc4(a, b, c):
    return a*a, a*b

def testfunc_None_ret(a, b):
    # type: (int, Real) -> None
    pass

def testfunc_None_ret_err(a, b):
    # type: (int, Real) -> None
    return 7

def testfunc_None_arg(a, b):
    # type: (int, None) -> int
    return a*a

def testfunc_Dict_arg(a, b):
    # type: (int, Dict[str, Union[int, str]]) -> None
    assert isinstance(b[str(a)], str) or isinstance(b[str(a)], int)

def testfunc_Mapping_arg(a, b):
    # type: (int, Mapping[str, Union[int, str]]) -> None
    assert isinstance(b[str(a)], str) or isinstance(b[str(a)], int)

def testfunc_Dict_ret(a):
    # type: (str) -> Dict[str, Union[int, str]]
    return {a: len(a), 2*a: a}

def testfunc_Dict_ret_err(a):
    # type: (int) -> Dict[str, Union[int, str]]
    return {a: str(a), 2*a: a}

def testfunc_Seq_arg(a):
    # type: (Sequence[Tuple[int, str]]) -> int
    return len(a)

def testfunc_Seq_ret_List(a, b):
    # type: (int, str) -> Sequence[Union[int, str]]
    return [a, b]

def testfunc_Seq_ret_Tuple(a, b):
    # type: (int, str) -> Sequence[Union[int, str]]
    return a, b

def testfunc_Seq_ret_err(a, b):
    # type: (int, str) -> Sequence[Union[int, str]]
    return {a: str(a), b: str(b)}

def testfunc_Iter_arg(a, b):
    # type: (Iterable[int], str) -> List[int]
    return [r for r in a]

def testfunc_Iter_str_arg(a):
    # type: (Iterable[str]) -> List[int]
    return [ord(r) for r in a]

def testfunc_Iter_ret():
    # type: () -> Iterable[int]
    return [1, 2, 3, 4, 5]

def testfunc_Iter_ret_err():
    # type: () -> Iterable[str]
    return [1, 2, 3, 4, 5]

def testfunc_Callable_arg(a, b):
    # type: (Callable[[str, int], str], str) -> str
    return a(b, len(b))

def testfunc_Callable_call_err(a, b):
    # type: (Callable[[str, int], str], str) -> str
    return a(b, b)

def testfunc_Callable_ret(a, b):
    # type: (int, str) -> Callable[[str, int], str]
    
    def m(x, y):
        # type: (str, int) -> str
        return x+str(y)+b*a

    return m

def testfunc_Callable_ret_err():
    # type: () -> Callable[[str, int], str]
    return 5

def testfunc_Generator():
    # type: () -> Generator[int, Union[str, None], Any]
    s = yield
    while not s is None:
        if s == 'fail':
            s = yield 'bad yield'
        s = yield len(s)

def testfunc_Generator_arg(gen):
    # type: (Generator[int, Union[str, None], Any]) -> List[int]
    # should raise error because of illegal use of typing.Generator
    lst = ('ab', 'nmrs', 'u')
    res = [gen.send(x) for x in lst]
    return res

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

def testfunc_Generic_arg(x):
    # type: (Custom_Generic[str]) -> str
    return x.v()

def testfunc_Generic_ret(x):
    # type: (int) -> Custom_Generic[int]
    return Custom_Generic[int](x)

def testfunc_Generic_ret_err(x):
    # type: (int) -> Custom_Generic[int]
    return Custom_Generic[str](str(x))

def testfunc_numeric_tower_float(x):
    # type: (float) -> str
    return str(x)

def testfunc_numeric_tower_complex(x):
    # type: (complex) -> str
    return str(x)

def testfunc_numeric_tower_tuple(x):
    # type: (Tuple[float, str]) -> str
    return str(x)

def testfunc_numeric_tower_return(x):
    # type: (str) -> float
    return len(x)

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
