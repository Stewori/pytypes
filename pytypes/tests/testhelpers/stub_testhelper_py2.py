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

# Created on 08.11.2016

from pytypes import typechecked, check_argument_types, annotations, override

try:
    from backports.typing import Generic, TypeVar
except ImportError:
    from typing import Generic, TypeVar

@typechecked
def testfunc1_py2(a, b):
    # actually (int, int) -> str from stubfile
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
        # actually d: float, c: class1_py2 -> int
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

@typechecked
def testfunc_class_in_list_py2(a):
    # actually a: List[class1_py2] -> int
    return len(a)

@typechecked
def testfunc_None_ret_py2(a, b):
    # actually (int, Real) -> None
    pass

@typechecked
def testfunc_None_ret_err_py2(a, b):
    # actually (int, Real) -> None
    return 7

@typechecked
def testfunc_None_arg_py2(a, b):
    # actually (int, None) -> int
    return a*a

@typechecked
def testfunc_Dict_arg_py2(a, b):
    # actually (int, Dict[str, Union[int, str]]) -> None
    assert isinstance(b[str(a)], str) or isinstance(b[str(a)], int)

@typechecked
def testfunc_Mapping_arg_py2(a, b):
    # actually (int, Mapping[str, Union[int, str]]) -> None
    assert isinstance(b[str(a)], str) or isinstance(b[str(a)], int)

@typechecked
def testfunc_Dict_ret_py2(a):
    # actually (str) -> Dict[str, Union[int, str]]
    return {a: len(a), 2*a: a}

@typechecked
def testfunc_Dict_ret_err_py2(a):
    # actually (int) -> Dict[str, Union[int, str]]
    return {a: str(a), 2*a: a}

@typechecked
def testfunc_Seq_arg_py2(a):
    # actually (Sequence[Tuple[int, str]]) -> int
    return len(a)

@typechecked
def testfunc_Seq_ret_List_py2(a, b):
    # actually (int, str) -> Sequence[Union[int, str]]
    return [a, b]

@typechecked
def testfunc_Seq_ret_Tuple_py2(a, b):
    # actually (int, str) -> Sequence[Union[int, str]]
    return a, b

@typechecked
def testfunc_Seq_ret_err_py2(a, b):
    # actually (int, str) -> Sequence[Union[int, str]]
    return {a: str(a), b: str(b)}

@typechecked
def testfunc_Iter_arg_py2(a, b):
    # actually (Iterable[int], str) -> List[int]
    return [r for r in a]

@typechecked
def testfunc_Iter_str_arg_py2(a):
    # actually (Iterable[str]) -> List[int]
    return [ord(r) for r in a]

@typechecked
def testfunc_Iter_ret_py2():
    # actually () -> Iterable[int]
    return [1, 2, 3, 4, 5]

@typechecked
def testfunc_Iter_ret_err_py2():
    # actually () -> Iterable[str]
    return [1, 2, 3, 4, 5]

@typechecked
def testfunc_Callable_arg_py2(a, b):
    # actually (Callable[[str, int], str], str) -> str
    return a(b, len(b))

@typechecked
def testfunc_Callable_call_err_py2(a, b):
    # actually (Callable[[str, int], str], str) -> str
    return a(b, b)

@typechecked
def testfunc_Callable_ret_py2(a, b):
    # actually (int, str) -> Callable[[str, int], str]
    
    def m(x, y):
        # type: (str, int) -> str
        return x+str(y)+b*a

    return m

# Todo: Test regarding wrong-typed Callables
@typechecked
def testfunc_Callable_ret_err_py2():
    # actually () -> Callable[[str, int], str]
    return 5

@typechecked
def testfunc_Generator_py2():
    # actually () -> Generator[int, Union[str, None], Any]
    s = yield
    while not s is None:
        if s == 'fail':
            s = yield 'bad yield'
        s = yield len(s)

@typechecked
def testfunc_Generator_arg_py2(gen):
    # actually (Generator[int, Union[str, None], Any]) -> List[int]
    # should raise error because of illegal use of typing.Generator
    lst = ('ab', 'nmrs', 'u')
    res = [gen.send(x) for x in lst]
    return res

@typechecked
def testfunc_Generator_ret_py2():
    # actually () -> Generator[int, Union[str, None], Any]
    # should raise error because of illegal use of typing.Generator
    res = testfunc_Generator_py2()
    return res


T_1_py2 = TypeVar('T_1_py2')
class Custom_Generic_py2(Generic[T_1_py2]):
    
    def __init__(self, val):
        # type: (T_1_py2) -> None
        self.val = val

    def v(self):
        # type: () -> T_1_py2
        return self.val


@typechecked
def testfunc_Generic_arg_py2(x):
    # actually (Custom_Generic_py2[str]) -> str
    return x.v()

@typechecked
def testfunc_Generic_ret_py2(x):
    # actually (int) -> Custom_Generic[int]
    return Custom_Generic_py2[int](x)

@typechecked
def testfunc_Generic_ret_err_py2(x):
    # actually (int) -> Custom_Generic[int]
    return Custom_Generic_py2[str](str(x))


class testClass_property_py2(object):

    @typechecked
    @property
    def testprop_py2(self):
        # actually () -> int
        return self._testprop_py2

    @typechecked
    @testprop_py2.setter
    def testprop_py2(self, value):
        # actually (int) -> None
        self._testprop_py2 = value

    @typechecked
    @property
    def testprop2_py2(self):
        # actually () -> str
        return self._testprop2_py2

    @testprop2_py2.setter
    def testprop2_py2(self, value):
        # actually (str) -> None
        self._testprop2_py2 = value

    @typechecked
    @property
    def testprop3_py2(self):
        # actually () -> Tuple[int, str]
        return self._testprop3_py2

    @testprop3_py2.setter
    def testprop3_py2(self, value):
        # actually (Tuple[int, str]) -> None
        check_argument_types()
        self._testprop3_py2 = value


@typechecked
class testClass_property_class_check_py2(object):
    @property
    def testprop_py2(self):
        # actually () -> int
        return self._testprop_py2

    @testprop_py2.setter
    def testprop_py2(self, value):
        # actually (int) -> None
        self._testprop_py2 = value

    @property
    def testprop2_py2(self):
        # actually () -> float
        return 'abc'

    @testprop2_py2.setter
    def testprop2_py2(self, value):
        # actually (float) -> None
        pass


@typechecked
def testfunc_varargs1_py2(*argss):
    # actually (float) -> Tuple[int, float]
    res = 1.0
    for arg in argss:
        res *= arg
    return len(argss), res

@typechecked
def testfunc_varargs2_py2(a, b, c, *varg):
    # actually (str, int, None, int) -> Tuple[int, str]
    res = 1
    for arg in varg:
        res *= arg
    return res, a*b

@typechecked
def testfunc_varargs3_py2(*args, **kwds):
    # actually (int, float) -> Tuple[str, float]
    longest = ''
    for key in kwds:
        if len(key) > len(longest):
            longest = key
    return longest*(args[0]//len(args)), kwds[longest]

@typechecked
def testfunc_varargs4_py2(**kwds):
    # actually (float) -> float
    longest = ''
    for key in kwds:
        if len(key) > len(longest):
            longest = key
    return 0 if longest == '' else kwds[longest]

@typechecked
def testfunc_varargs5_py2(a1, a2, *vargss, **vkwds):
    # actually (int, str, float, int) -> List[int]
    return [len(vargss), len(str(vargss[a1])), vkwds[a2]]

@typechecked
def testfunc_varargs_err_py2(a1, a2, *vargss, **vkwds):
    # actually (int, str, float, int) -> List[int]
    return [len(vargss), str(vargss[a1]), vkwds[a2]]

@typechecked
class testclass_vararg_py2(object):
    def testmeth_varargs1_py2(self, *vargs):
        # actually (Tuple[str, int]) -> int
        res = 1
        for arg in vargs:
            res += len(arg[0])*arg[1]
        return res-len(self.__class__.__name__)

    def testmeth_varargs2_py2(self, q1, q2, *varargs, **varkw):
        # actually (int, str, float, int) -> List[int]
        return [len(varargs), len(str(varargs[q1])), varkw[q2],
                len(self.__class__.__name__)]
    
    @staticmethod
    def testmeth_varargs_static1_py2(*vargs_st):
        # actually (float) -> Tuple[int, float]
        res = 1.0
        for arg in vargs_st:
            res *= arg
        return len(vargs_st), res

    @staticmethod
    def testmeth_varargs_static2_py2(q1_st, q2_st, *varargs_st, **varkw_st):
        # actually (int, str, float, int) -> List[int]
        return [len(varargs_st), len(str(varargs_st[q1_st])), varkw_st[q2_st]]

    @classmethod
    def testmeth_varargs_class1_py2(cls, *vargs_cls):
        # actually (Tuple[str, int]) -> int
        res = 1
        for arg in vargs_cls:
            res += len(arg[0])*arg[1]
        return res-len(cls.__name__)

    @classmethod
    def testmeth_varargs_class2_py2(cls, q1_cls, q2_cls, *varargs_cls, **varkw_cls):
        # actually (int, str, float, int) -> List[int]
        return [len(varargs_cls), len(str(varargs_cls[q1_cls])),
                varkw_cls[q2_cls], len(cls.__name__)]

    @property
    def prop1_py2(self):
        # actually () -> str
        return self._prop1_py2

    @prop1_py2.setter
    def prop1_py2(self, *vargs_prop):
        # actually (str) -> None
        self._prop1_py2 = vargs_prop[0]

def testfunc_varargs_ca1_py2(*argss):
    # actually (float) -> Tuple[int, float]
    check_argument_types()
    res = 1.0
    for arg in argss:
        res *= arg
    return len(argss), res

def testfunc_varargs_ca2_py2(a, b, c, *varg):
    # actually (str, int, None, int) -> Tuple[int, str]
    check_argument_types()
    res = 1
    for arg in varg:
        res *= arg
    return res, a*b

def testfunc_varargs_ca3_py2(*args, **kwds):
    # actually (int, float) -> Tuple[str, float]
    check_argument_types()
    longest = ''
    for key in kwds:
        if len(key) > len(longest):
            longest = key
    return longest*(args[0]//len(args)), kwds[longest]

def testfunc_varargs_ca4_py2(**kwds):
    # actually (float) -> float
    check_argument_types()
    longest = ''
    for key in kwds:
        if len(key) > len(longest):
            longest = key
    return 0 if longest == '' else kwds[longest]

def testfunc_varargs_ca5_py2(a1, a2, *vargss, **vkwds):
    # actually (int, str, float, int) -> List[int]
    check_argument_types()
    return [len(vargss), len(str(vargss[a1])), vkwds[a2]]

class testclass_vararg_ca_py2(object):
    def testmeth_varargs_ca1_py2(self, *vargs):
        # actually (Tuple[str, int]) -> int
        check_argument_types()
        res = 1
        for arg in vargs:
            res += len(arg[0])*arg[1]
        return res-len(self.__class__.__name__)

    def testmeth_varargs_ca2_py2(self, q1, q2, *varargs, **varkw):
        # actually (int, str, float, int) -> List[int]
        check_argument_types()
        return [len(varargs), len(str(varargs[q1])), varkw[q2],
                len(self.__class__.__name__)]
    
    @staticmethod
    def testmeth_varargs_static_ca1_py2(*vargs_st):
        # actually (float) -> Tuple[int, float]
        check_argument_types()
        res = 1.0
        for arg in vargs_st:
            res *= arg
        return len(vargs_st), res

    @staticmethod
    def testmeth_varargs_static_ca2_py2(q1_st, q2_st, *varargs_st, **varkw_st):
        # actually (int, str, float, int) -> List[int]
        check_argument_types()
        return [len(varargs_st), len(str(varargs_st[q1_st])), varkw_st[q2_st]]

    @classmethod
    def testmeth_varargs_class_ca1_py2(cls, *vargs_cls):
        # actually (Tuple[str, int]) -> int
        check_argument_types()
        res = 1
        for arg in vargs_cls:
            res += len(arg[0])*arg[1]
        return res-len(cls.__name__)

    @classmethod
    def testmeth_varargs_class_ca2_py2(cls, q1_cls, q2_cls, *varargs_cls, **varkw_cls):
        # actually (int, str, float, int) -> List[int]
        check_argument_types()
        return [len(varargs_cls), len(str(varargs_cls[q1_cls])),
                varkw_cls[q2_cls], len(cls.__name__)]

    @property
    def prop_ca1_py2(self):
        # actually () -> str
        check_argument_types()
        return self._prop_ca1_py2

    @prop_ca1_py2.setter
    def prop_ca1_py2(self, *vargs_prop):
        # actually (str) -> None
        check_argument_types()
        self._prop_ca1_py2 = vargs_prop[0]


@typechecked
def func_defaults_typecheck_py2(a, b, c=4, d=2.5):
    # actually (str) -> str
    try:
        return a+b*c
    except TypeError:
        return 'invalid'

def func_defaults_checkargs_py2(a, b, c=4, d=2.5):
    # actually (str) -> str
    check_argument_types()
    try:
        return a+b*c
    except TypeError:
        return 'invalid'

@annotations
def func_defaults_annotations_py2(a, b, c=4):
    # actually (str) -> str
    b = 'abc'
    return a+b*c

@annotations
def testfunc_annotations_from_stubfile_by_decorator_py2(a, b):
    # actually (str, int) -> int
    return len(a)/b


class A_check_parent_types_py2(object):
    def meth1_py2(self, a):
        # actually (int) -> int
        return len(str(a))

class B_override_check_arg_py2(A_check_parent_types_py2):
    @override
    def meth1_py2(self, a):
        check_argument_types()
        return len(str(a))

class B_no_override_check_arg_py2(A_check_parent_types_py2):
    def meth1_py2(self, a):
        check_argument_types()
        return len(str(a))

class B_override_typechecked_py2(A_check_parent_types_py2):
    @typechecked
    @override
    def meth1_py2(self, a):
        check_argument_types()
        return len(str(a))

class B_no_override_typechecked_py2(A_check_parent_types_py2):
    @typechecked
    def meth1_py2(self, a):
        check_argument_types()
        return len(str(a))

class B_override_with_type_check_arg_py2(A_check_parent_types_py2):
    @override
    def meth1_py2(self, a):
        # actually (float) -> int
        check_argument_types()
        return len(str(a))

class B_override_with_type_typechecked_py2(A_check_parent_types_py2):
    @typechecked
    @override
    def meth1_py2(self, a):
        # actually (float) -> int
        check_argument_types()
        return len(str(a))


class A_diamond_override_py2(object):
    def meth1_py2(self, a):
        # actually (Tuple[int, int]) -> int
        return len(str(a))

class B_diamond_override_py2(A_diamond_override_py2):
    @override
    def meth1_py2(self, a):
        # actually (Tuple[int, float]) -> int
        return len(str(a))

class C_diamond_override_py2(A_diamond_override_py2):
    @override
    def meth1_py2(self, a):
        # actually (Tuple[float, int]) -> int
        return len(str(a))

class D_diamond_override_py2(B_diamond_override_py2, C_diamond_override_py2):
    @override
    def meth1_py2(self, a):
        # actually (Tuple[float, float]) -> int
        check_argument_types()
        return len(str(a))

class D_diamond_override_err1_py2(B_diamond_override_py2, C_diamond_override_py2):
    @override
    def meth1_py2(self, a):
        # actually (Tuple[float, int]) -> int
        return len(str(a))

class D_diamond_override_err2_py2(B_diamond_override_py2, C_diamond_override_py2):
    @override
    def meth1_py2(self, a):
        # actually (Tuple[int, float]) -> int
        return len(str(a))

class D_diamond_override_err3_py2(B_diamond_override_py2, C_diamond_override_py2):
    @override
    def meth1_py2(self, a):
        # actually (Tuple[int, int]) -> int
        return len(str(a))
