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

# Created on 21.10.2016

from pytypes import typechecked, check_argument_types, annotations, override

try:
    from backports.typing import Generic, TypeVar
except ImportError:
    from typing import Generic, TypeVar


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
        # actually d: float, c: class1) -> int
            return len(c+str(d))

@typechecked
class class2(class1):
    def meth1b(self, a):
    # actually a -> str
        return str(a)

    def meth2b(self, b):
    # actually class1 -> str
        return str(b)

@typechecked
def testfunc_class_in_list(a):
    # actually a: List[class1] -> int
    return len(a)


@typechecked
def testfunc_None_ret(a, b):
    # actually (int, Real) -> None
    pass

@typechecked
def testfunc_None_ret_err(a, b):
    # actually (int, Real) -> None
    return 7

@typechecked
def testfunc_None_arg(a, b):
    # actually (int, None) -> int
    return a*a

@typechecked
def testfunc_Dict_arg(a, b):
    # actually (int, Dict[str, Union[int, str]]) -> None
    assert isinstance(b[str(a)], str) or isinstance(b[str(a)], int)

@typechecked
def testfunc_Mapping_arg(a, b):
    # actually (int, Mapping[str, Union[int, str]]) -> None
    assert isinstance(b[str(a)], str) or isinstance(b[str(a)], int)

@typechecked
def testfunc_Dict_ret(a):
    # actually (str) -> Dict[str, Union[int, str]]
    return {a: len(a), 2*a: a}

@typechecked
def testfunc_Dict_ret_err(a):
    # actually (int) -> Dict[str, Union[int, str]]
    return {a: str(a), 2*a: a}

@typechecked
def testfunc_Seq_arg(a):
    # actually (Sequence[Tuple[int, str]]) -> int
    return len(a)

@typechecked
def testfunc_Seq_ret_List(a, b):
    # actually (int, str) -> Sequence[Union[int, str]]
    return [a, b]

@typechecked
def testfunc_Seq_ret_Tuple(a, b):
    # actually (int, str) -> Sequence[Union[int, str]]
    return a, b

@typechecked
def testfunc_Seq_ret_err(a, b):
    # actually (int, str) -> Sequence[Union[int, str]]
    return {a: str(a), b: str(b)}

@typechecked
def testfunc_Iter_arg(a, b):
    # actually (Iterable[int], str) -> List[int]
    return [r for r in a]

@typechecked
def testfunc_Iter_str_arg(a):
    # actually (Iterable[str]) -> List[int]
    return [ord(r) for r in a]

@typechecked
def testfunc_Iter_ret():
    # actually () -> Iterable[int]
    return [1, 2, 3, 4, 5]

@typechecked
def testfunc_Iter_ret_err():
    # actually () -> Iterable[str]
    return [1, 2, 3, 4, 5]

@typechecked
def testfunc_Callable_arg(a, b):
    # actually (Callable[[str, int], str], str) -> str
    return a(b, len(b))

@typechecked
def testfunc_Callable_call_err(a, b):
    # actually (Callable[[str, int], str], str) -> str
    return a(b, b)

@typechecked
def testfunc_Callable_ret(a, b):
    # actually (int, str) -> Callable[[str, int], str]
    
    def m(x, y):
        # type: (str, int) -> str
        return x+str(y)+b*a

    return m

# Todo: Test regarding wrong-typed Callables
@typechecked
def testfunc_Callable_ret_err():
    # actually () -> Callable[[str, int], str]
    return 5

@typechecked
def testfunc_Generator():
    # actually () -> Generator[int, Union[str, None], Any]
    s = yield
    while not s is None:
        if s == 'fail':
            s = yield 'bad yield'
        s = yield len(s)

@typechecked
def testfunc_Generator_arg(gen):
    # actually (Generator[int, Union[str, None], Any]) -> List[int]
    # should raise error because of illegal use of typing.Generator
    lst = ('ab', 'nmrs', 'u')
    res = [gen.send(x) for x in lst]
    return res

@typechecked
def testfunc_Generator_ret():
    # actually () -> Generator[int, Union[str, None], Any]
    # should raise error because of illegal use of typing.Generator
    res = testfunc_Generator()
    return res


T_1 = TypeVar('T_1')
class Custom_Generic(Generic[T_1]):
    
    def __init__(self, val: T_1) -> None:
        self.val = val

    def v(self) -> T_1:
        return self.val


@typechecked
def testfunc_Generic_arg(x):
    # actually (Custom_Generic[str]) -> str
    return x.v()

@typechecked
def testfunc_Generic_ret(x):
    # actually (int) -> Custom_Generic[int]
    return Custom_Generic[int](x)

@typechecked
def testfunc_Generic_ret_err(x):
    # actually (int) -> Custom_Generic[int]
    return Custom_Generic[str](str(x))


class testClass_property(object):

    @typechecked
    @property
    def testprop(self):
        # actually () -> int
        return self._testprop

    @typechecked
    @testprop.setter
    def testprop(self, value):
        # actually (int) -> None
        self._testprop = value

    @typechecked
    @property
    def testprop2(self):
        # actually () -> str
        return self._testprop2

    @testprop2.setter
    def testprop2(self, value):
        # actually (str) -> None
        self._testprop2 = value

    @typechecked
    @property
    def testprop3(self):
        # actually () -> Tuple[int, str]
        return self._testprop3

    @testprop3.setter
    def testprop3(self, value):
        # actually (Tuple[int, str]) -> None
        check_argument_types()
        self._testprop3 = value


@typechecked
class testClass_property_class_check(object):
    @property
    def testprop(self):
        # actually () -> int
        return self._testprop

    @testprop.setter
    def testprop(self, value):
        # actually (int) -> None
        self._testprop = value

    @property
    def testprop2(self):
        # actually () -> float
        return 'abc'

    @testprop2.setter
    def testprop2(self, value):
        # actually (float) -> None
        pass


@typechecked
def testfunc_varargs1(*argss):
    res = 1.0
    for arg in argss:
        res *= arg
    return len(argss), res

@typechecked
def testfunc_varargs2(a, b, c, *varg):
    res = 1
    for arg in varg:
        res *= arg
    return res, a*b

@typechecked
def testfunc_varargs3(*args, **kwds):
    longest = ''
    for key in kwds:
        if len(key) > len(longest):
            longest = key
    return longest*(args[0]//len(args)), kwds[longest]

@typechecked
def testfunc_varargs4(**kwds):
    longest = ''
    for key in kwds:
        if len(key) > len(longest):
            longest = key
    return 0 if longest == '' else kwds[longest]

@typechecked
def testfunc_varargs5(a1, a2, *vargss, **vkwds):
    return [len(vargss), len(str(vargss[a1])), vkwds[a2]]

@typechecked
def testfunc_varargs6(a1, a2, *vargss, b1, b2, **vkwds):
    return [len(vargss), len(str(vargss[a1])), vkwds[a2], b1, len(b2)]

@typechecked
def testfunc_varargs6b(a1, a2, *vargss, b1, b2, **vkwds):
    return [len(vargss), len(str(vargss[a1])), vkwds[a2], b1, len(b2)]

@typechecked
def testfunc_varargs_err(a1, a2, *vargss, **vkwds):
    return [len(vargss), str(vargss[a1]), vkwds[a2]]

@typechecked
class testclass_vararg():
    def testmeth_varargs1(self, *vargs):
        res = 1
        for arg in vargs:
            res += len(arg[0])*arg[1]
        return res-len(self.__class__.__name__)

    def testmeth_varargs2(self, q1, q2, *varargs, **varkw):
        return [len(varargs), len(str(varargs[q1])), varkw[q2],
                len(self.__class__.__name__)]

    def testmeth_varargs3(self, q1, q2, *varargs, w1, w2, **varkw):
        return [len(varargs), len(str(varargs[q1])), varkw[q2],
                len(self.__class__.__name__), int(w1*w2[0]), len(w2[1])]

    def testmeth_varargs_3b(self, q1, q2, *varargs, w1, w2, **varkw):
        return [len(varargs), len(str(varargs[q1])), varkw[q2],
                len(self.__class__.__name__), int(w1*w2[0]), len(w2[1])]

    @staticmethod
    def testmeth_varargs_static1(*vargs_st):
        res = 1.0
        for arg in vargs_st:
            res *= arg
        return len(vargs_st), res

    @staticmethod
    def testmeth_varargs_static2(q1_st, q2_st, *varargs_st, **varkw_st):
        return [len(varargs_st), len(str(varargs_st[q1_st])), varkw_st[q2_st]]

    @classmethod
    def testmeth_varargs_class1(cls, *vargs_cls):
        res = 1
        for arg in vargs_cls:
            res += len(arg[0])*arg[1]
        return res-len(cls.__name__)

    @classmethod
    def testmeth_varargs_class2(cls, q1_cls, q2_cls, *varargs_cls,
            **varkw_cls):
        return [len(varargs_cls), len(str(varargs_cls[q1_cls])),
                varkw_cls[q2_cls], len(cls.__name__)]

    @property
    def prop1(self):
        return self._prop1

    @prop1.setter
    def prop1(self, *vargs_prop):
        self._prop1 = vargs_prop[0]

def testfunc_varargs_ca1(*argss):
    check_argument_types()
    res = 1.0
    for arg in argss:
        res *= arg
    return len(argss), res

def testfunc_varargs_ca2(a, b, c, *varg):
    check_argument_types()
    res = 1
    for arg in varg:
        res *= arg
    return res, a*b

def testfunc_varargs_ca3(*args, **kwds):
    check_argument_types()
    longest = ''
    for key in kwds:
        if len(key) > len(longest):
            longest = key
    return longest*(args[0]//len(args)), kwds[longest]

def testfunc_varargs_ca4(**kwds):
    check_argument_types()
    longest = ''
    for key in kwds:
        if len(key) > len(longest):
            longest = key
    return 0 if longest == '' else kwds[longest]

def testfunc_varargs_ca5(a1, a2, *vargss, **vkwds):
    check_argument_types()
    return [len(vargss), len(str(vargss[a1])), vkwds[a2]]

def testfunc_varargs_ca6(a1, a2, *vargss, b1, b2, **vkwds):
    check_argument_types()
    return [len(vargss), len(str(vargss[a1])), vkwds[a2], b1, len(b2)]

def testfunc_varargs_ca6b(a1, a2, *vargss, b1, b2, **vkwds):
    check_argument_types()
    return [len(vargss), len(str(vargss[a1])), vkwds[a2], b1, len(b2)]

class testclass_vararg_ca():
    def testmeth_varargs_ca1(self, *vargs):
        check_argument_types()
        res = 1
        for arg in vargs:
            res += len(arg[0])*arg[1]
        return res-len(self.__class__.__name__)

    def testmeth_varargs_ca2(self, q1, q2, *varargs, **varkw):
        check_argument_types()
        return [len(varargs), len(str(varargs[q1])), varkw[q2],
                len(self.__class__.__name__)]

    def testmeth_varargs_ca3(self, q1, q2, *varargs, w1, w2, **varkw):
        check_argument_types()
        return [len(varargs), len(str(varargs[q1])), varkw[q2],
                len(self.__class__.__name__), int(w1*w2[0]), len(w2[1])]

    def testmeth_varargs_ca3b(self, q1, q2, *varargs, w1, w2, **varkw):
        check_argument_types()
        return [len(varargs), len(str(varargs[q1])), varkw[q2],
                len(self.__class__.__name__), int(w1*w2[0]), len(w2[1])]

    @staticmethod
    def testmeth_varargs_static_ca1(*vargs_st):
        check_argument_types()
        res = 1.0
        for arg in vargs_st:
            res *= arg
        return len(vargs_st), res

    @staticmethod
    def testmeth_varargs_static_ca2(q1_st, q2_st, *varargs_st, **varkw_st):
        check_argument_types()
        return [len(varargs_st), len(str(varargs_st[q1_st])), varkw_st[q2_st]]

    @classmethod
    def testmeth_varargs_class_ca1(cls, *vargs_cls):
        check_argument_types()
        res = 1
        for arg in vargs_cls:
            res += len(arg[0])*arg[1]
        return res-len(cls.__name__)

    @classmethod
    def testmeth_varargs_class_ca2(cls, q1_cls, q2_cls,
            *varargs_cls, **varkw_cls):
        check_argument_types()
        return [len(varargs_cls), len(str(varargs_cls[q1_cls])),
                varkw_cls[q2_cls], len(cls.__name__)]

    @property
    def prop_ca1(self):
        check_argument_types()
        return self._prop_ca1

    @prop_ca1.setter
    def prop_ca1(self, *vargs_prop):
        check_argument_types()
        self._prop_ca1 = vargs_prop[0]


@typechecked
def func_defaults_typecheck(a, b, c=4, d=2.5):
    try:
        return a+b*c
    except TypeError:
        return 'invalid'

def func_defaults_checkargs(a, b, c=4, d=2.5):
    check_argument_types()
    try:
        return a+b*c
    except TypeError:
        return 'invalid'

@annotations
def func_defaults_annotations(a, b, c=4):
    b = 'abc'
    return a+b*c

@annotations
def testfunc_annotations_from_stubfile_by_decorator(a, b):
    return len(a)/b


class A_check_parent_types():
    def meth1(self, a):
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
        check_argument_types()
        return len(str(a))

class B_override_with_type_typechecked(A_check_parent_types):
    @typechecked
    @override
    def meth1(self, a):
        check_argument_types()
        return len(str(a))


class A_diamond_override(object):
    def meth1(self, a):
        return len(str(a))

class B_diamond_override(A_diamond_override):
    @override
    def meth1(self, a):
        return len(str(a))

class C_diamond_override(A_diamond_override):
    @override
    def meth1(self, a):
        return len(str(a))

class D_diamond_override(B_diamond_override, C_diamond_override):
    @override
    def meth1(self, a):
        check_argument_types()
        return len(str(a))

class D_diamond_override_err1(B_diamond_override, C_diamond_override):
    @override
    def meth1(self, a):
        return len(str(a))

class D_diamond_override_err2(B_diamond_override, C_diamond_override):
    @override
    def meth1(self, a):
        return len(str(a))

class D_diamond_override_err3(B_diamond_override, C_diamond_override):
    @override
    def meth1(self, a):
        return len(str(a))
