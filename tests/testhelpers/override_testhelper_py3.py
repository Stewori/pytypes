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

# Created on 01.12.2016

"""
This file causes NameErrors if forward-declarations
of Types are not supported properly.
(unless typechecker.check_override_at_runtime == False)

todo: involve something like [str, int, 'TestClass2']
"""
from pytypes import override

class TestClass():
    def test_meth0(self, a: int) -> str:
        pass

    def test_meth1(self, a: 'TestArg2') -> str:
        pass

    def test_meth2(self, a: int) -> 'TestResult1':
        pass

class TestClass2(TestClass):
    @override
    def test_meth0(self, a: int) -> str:
        pass

    @override
    def test_meth1(self, a: 'TestArg1') -> str:
        pass

    @override
    def test_meth2(self, a: int) -> 'TestResult2':
        pass

class TestClass3(TestClass):
    @override
    def test_meth1(self, a: 'TestArg1') -> str:
        pass

    @override
    def test_meth2(self, a: int) -> 'TestResult2':
        pass

class TestArg1():
    pass

class TestResult1():
    pass

class TestClass3(TestClass):
    @override
    def test_meth1(self, a: TestArg1) -> str:
        pass

    @override
    def test_meth2(self, a: int) -> 'TestResult2':
        pass

class TestArg2(TestArg1):
    pass

class TestResult2(TestResult1):
    pass

class override_varargs_class_base(object):
# var-arg tests:
    def method_vararg1(self, a: int, b: int, *args: int) -> int:
        return a+b

    def method_vararg2(self, a: int, b: int) -> int:
        return a+b

    def method_vararg3(self, a: int, b: int, c: float) -> int:
        return a+b

# var-kw tests:
    def method_varkw1(self, a: int, b: int, **kw: int) -> int:
        return a+b

    def method_varkw2(self, a: int, b: int, *arg: str, **kw: int) -> int:
        return a+b

# default tests:
    def method_defaults1(self, a: int, b: int) -> int:
        return a+b

    def method_defaults2(self, a: int, b: int, *vargs: int) -> int:
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
        return a+b+q+v

    def method_kwonly7(self, a: int, b: float, *vargs: float, q: int, v: int, **kw: int) -> int:
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
        return a+b+q+v

    def method_kwonly7_py2(self, a, b, *vargs, q, v, **kw):
        # type: (int, float, *float, int, int, **int) -> int
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

# var-kw tests:
    @override
    def method_varkw1(self, a: int, b: int, **kw: float) -> int:
        return a+b

    @override
    def method_varkw2(self, a: int, b: int, *arg: str, **kw: float) -> int:
        return a+b

# default tests:
    @override
    def method_defaults1(self, a: int, b: int, c=4.6) -> int:
        return a+b

    @override
    def method_defaults2(self, a: int, b: int, c: float = 4, *args: int) -> int:
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
        return a+b+q+v

    @override
    def method_kwonly7(self, a: int, b: float, *vargs: float, q: float, **kw: int) -> int:
        # child can drop kw-only in favor of var-kw
        return a+b

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
        return a+b+q+v

    @override
    def method_kwonly7_py2(self, a, b, *vargs, q, **kw):
        # type: (int, float, *float, float, **int) -> int
        # child can drop kw-only in favor of var-kw
        return a+b
