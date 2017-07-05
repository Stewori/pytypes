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

from numbers import Real

try:
    from backports.typing import Any, TypeVar, Generic, Generator, Iterable, Sequence, \
            Tuple, List, Callable, Dict, Mapping, Union
except ImportError:
    from typing import Any, TypeVar, Generic, Generator, Iterable, Sequence, \
            Tuple, List, Callable, Dict, Mapping, Union

def testfunc1_py2(a, b):
    # type: (int, Real) -> str
    pass


class class1_py2():
    def meth1_py2(self, a, b):
        # type: (float, str) -> str
        pass

    def meth2_py2(self, d, c):
        # type: (Any, str) -> int
        pass

    @staticmethod
    def static_meth_py2(d, c):
        # type: (Any, str) -> int
        pass

    @classmethod
    def class_meth_py2(cls, a, b):
        # type: (str, int) -> float
        pass

    class class1_inner_py2():
        def inner_meth1_py2(self, a, b):
            # type: (float, str) -> int
            pass

        @staticmethod
        def inner_static_meth_py2(d, c):
            # type: (float, str) -> int
            pass

        @classmethod
        def inner_class_meth_py2(cls, a, b):
            # type: (str, int) -> float
            pass


class class2_py2(class1_py2):
    def meth1b_py2(self, a):
        # type: (...) -> str
        pass

    def meth2b_py2(self, b):
        # type: (class1_py2) -> str
        pass

    @classmethod
    def class_methb_py2(cls, a, b):
        # type: (str, class1_py2) -> float
        pass


def testfunc_class_in_list_py2(a):
    # type: (List[class1_py2]) -> int
    pass

def testfunc_None_ret_py2(a, b):
    # type: (int, Real) -> None
    pass

def testfunc_None_ret_err_py2(a, b):
    # type: (int, Real) -> None
    pass

def testfunc_None_arg_py2(a, b):
    # type: (int, None) -> int
    pass

def testfunc_Dict_arg_py2(a, b):
    # type: (int, Dict[str, Union[int, str]]) -> None
    pass

def testfunc_Mapping_arg_py2(a, b):
    # type: (int, Mapping[str, Union[int, str]]) -> None
    pass

def testfunc_Dict_ret_py2(a):
    # type: (str) -> Dict[str, Union[int, str]]
    pass

def testfunc_Dict_ret_err_py2(a):
    # type: (int) -> Dict[str, Union[int, str]]
    pass

def testfunc_Seq_arg_py2(a):
    # type: (Sequence[Tuple[int, str]]) -> int
    pass

def testfunc_Seq_ret_List_py2(a, b):
    # type: (int, str) -> Sequence[Union[int, str]]
    pass

def testfunc_Seq_ret_Tuple_py2(a, b):
    # type: (int, str) -> Sequence[Union[int, str]]
    pass

def testfunc_Seq_ret_err_py2(a, b):
    # type: (int, str) -> Sequence[Union[int, str]]
    pass

def testfunc_Iter_arg_py2(a, b):
    # type: (Iterable[int], str) -> List[int]
    pass

def testfunc_Iter_str_arg_py2(a):
    # type: (Iterable[str]) -> List[int]
    pass

def testfunc_Iter_ret_py2():
    # type: () -> Iterable[int]
    pass

def testfunc_Iter_ret_err_py2():
    # type: () -> Iterable[str]
    pass

def testfunc_Callable_arg_py2(a, b):
    # type: (Callable[[str, int], str], str) -> str
    pass

def testfunc_Callable_call_err_py2(a, b):
    # type: (Callable[[str, int], str], str) -> str
    pass

def testfunc_Callable_ret_py2(a, b):
    # type: (int, str) -> Callable[[str, int], str]
    pass

def testfunc_Callable_ret_err_py2():
    # type: () -> Callable[[str, int], str]
    pass

def testfunc_Generator_py2():
    # type: () -> Generator[int, Union[str, None], Any]
    pass

def testfunc_Generator_arg_py2(gen):
    # type: (Generator[int, Union[str, None], Any]) -> List[int]
    pass

def testfunc_Generator_ret_py2():
    # type: () -> Generator[int, Union[str, None], Any]
    pass

def testfunc_Generic_arg_py2(x):
    # type: (Custom_Generic_py2[str]) -> str
    pass

def testfunc_Generic_ret_py2(x):
    # type: (int) -> Custom_Generic_py2[int]
    pass

def testfunc_Generic_ret_err_py2(x):
    # type: (int) -> Custom_Generic_py2[int]
    pass


class testClass_property_py2(object):

    @property
    def testprop_py2(self):
        # type: () -> int
        pass

    @testprop_py2.setter
    def testprop_py2(self, value):
        # type: (int) -> None
        pass

    @property
    def testprop2_py2(self):
        # type: () -> str
        pass

    @testprop2_py2.setter
    def testprop2_py2(self, value):
        # type: (str) -> None
        pass

    @property
    def testprop3_py2(self):
        # type: () -> Tuple[int, str]
        pass

    @testprop3_py2.setter
    def testprop3_py2(self, value):
        # type: (Tuple[int, str]) -> None
        pass


class testClass_property_class_check_py2(object):
    @property
    def testprop_py2(self):
        # type: () -> int
        pass

    @testprop_py2.setter
    def testprop_py2(self, value):
        # type: (int) -> None
        pass

    @property
    def testprop2_py2(self):
        # type: () -> float
        pass

    @testprop2_py2.setter
    def testprop2_py2(self, value):
        # type: (float) -> None
        pass


def testfunc_varargs1_py2(*argss):
    # type: (*float) -> Tuple[int, float]
    pass

def testfunc_varargs2_py2(a, b, c, *varg):
    # type: (str, int, None, *int) -> Tuple[int, str]
    pass

def testfunc_varargs3_py2(*args, **kwds):
    # type: (*int, **float) -> Tuple[str, float]
    pass

def testfunc_varargs4_py2(**kwds):
    # type: (**float) -> float
    pass

def testfunc_varargs5_py2(a1, a2, *vargss, **vkwds):
    # type: (int, str, *float, **int) -> List[int]
    pass

def testfunc_varargs_err_py2(a1, a2, *vargss, **vkwds):
    # type: (int, str, *float, **int) -> List[int]
    pass

class testclass_vararg_py2():
    def testmeth_varargs1_py2(self, *vargs):
        # type: (*Tuple[str, int]) -> int
        pass

    def testmeth_varargs2_py2(self, q1, q2, *varargs, **varkw):
        # type: (int, str, *float, **int) -> List[int]
        pass
    
    @staticmethod
    def testmeth_varargs_static1_py2(*vargs_st):
        # type: (*float) -> Tuple[int, float]
        pass

    @staticmethod
    def testmeth_varargs_static2_py2(q1_st, q2_st, *varargs_st, **varkw_st):
        # type: (int, str, *float, **int) -> List[int]
        pass

    @classmethod
    def testmeth_varargs_class1_py2(cls, *vargs_cls):
        # type: (*Tuple[str, int]) -> int
        pass

    @classmethod
    def testmeth_varargs_class2_py2(cls, q1_cls, q2_cls, *varargs_cls, **varkw_cls):
        # type: (int, str, *float, **int) -> List[int]
        pass

    @property
    def prop1_py2(self):
        # type: () -> str
        pass

    @prop1_py2.setter
    def prop1_py2(self, *vargs_prop):
        # type: (*str) -> None
        pass

def testfunc_varargs_ca1_py2(*argss):
    # type: (*float) -> Tuple[int, float]
    pass

def testfunc_varargs_ca2_py2(a, b, c, *varg):
    # type: (str, int, None, *int) -> Tuple[int, str]
    pass

def testfunc_varargs_ca3_py2(*args, **kwds):
    # type: (*int, **float) -> Tuple[str, float]
    pass

def testfunc_varargs_ca4_py2(**kwds):
    # type: (**float) -> float
    pass

def testfunc_varargs_ca5_py2(a1, a2, *vargss, **vkwds):
    # type: (int, str, *float, **int) -> List[int]
    pass

class testclass_vararg_ca_py2():
    def testmeth_varargs_ca1_py2(self, *vargs):
        # type: (*Tuple[str, int]) -> int
        pass

    def testmeth_varargs_ca2_py2(self, q1, q2, *varargs, **varkw):
        # type: (int, str, *float, **int) -> List[int]
        pass
    
    @staticmethod
    def testmeth_varargs_static_ca1_py2(*vargs_st):
        # type: (*float) -> Tuple[int, float]
        pass

    @staticmethod
    def testmeth_varargs_static_ca2_py2(q1_st, q2_st, *varargs_st, **varkw_st):
        # type: (int, str, *float, **int) -> List[int]
        pass

    @classmethod
    def testmeth_varargs_class_ca1_py2(cls, *vargs_cls):
        # type: (*Tuple[str, int]) -> int
        pass

    @classmethod
    def testmeth_varargs_class_ca2_py2(cls, q1_cls, q2_cls, *varargs_cls, **varkw_cls):
        # type: (int, str, *float, **int) -> List[int]
        pass

    @property
    def prop_ca1_py2(self):
        # type: () -> str
        pass

    @prop_ca1_py2.setter
    def prop_ca1_py2(self, *vargs_prop):
        # type: (*str) -> None
        pass


def func_defaults_typecheck_py2(a, b, c, d):
    # type: (str) -> str
    pass

def func_defaults_checkargs_py2(a, b, c, d):
    # type: (str) -> str
    pass

def func_defaults_annotations_py2(a, b, c):
    # type: (str) -> str
    pass

def testfunc_annotations_from_stubfile_by_decorator_py2(a, b):
    # type: (str, int) -> int
    pass


class A_check_parent_types_py2(object):
    def meth1_py2(self, a):
        # type: (int) -> int
        pass

class B_override_with_type_check_arg_py2(A_check_parent_types_py2):
    def meth1_py2(self, a):
        # type: (float) -> int
        pass

class B_override_with_type_typechecked_py2(A_check_parent_types_py2):
    def meth1_py2(self, a):
        # type: (float) -> int
        pass


class A_diamond_override_py2(object):
    def meth1_py2(self, a):
        # type: (Tuple[int, int]) -> int
        pass

class B_diamond_override_py2(A_diamond_override_py2):
    def meth1_py2(self, a):
        # type: (Tuple[int, float]) -> int
        pass

class C_diamond_override_py2(A_diamond_override_py2):
    def meth1_py2(self, a):
        # type: (Tuple[float, int]) -> int
        pass

class D_diamond_override_py2(B_diamond_override_py2, C_diamond_override_py2):
    def meth1_py2(self, a):
        # type: (Tuple[float, float]) -> int
        pass

class D_diamond_override_err1_py2(B_diamond_override_py2, C_diamond_override_py2):
    def meth1_py2(self, a):
        # type: (Tuple[float, int]) -> int
        pass

class D_diamond_override_err2_py2(B_diamond_override_py2, C_diamond_override_py2):
    def meth1_py2(self, a):
        # type: (Tuple[int, float]) -> int
        pass

class D_diamond_override_err3_py2(B_diamond_override_py2, C_diamond_override_py2):
    def meth1_py2(self, a):
        # type: (Tuple[int, int]) -> int
        pass
