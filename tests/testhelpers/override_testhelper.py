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

# Created on 01.12.2016

"""
This file causes NameErrors if forward-declarations
of Types are not supported properly.
(unless typechecker.check_override_at_runtime == False)
"""
from pytypes import override

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
        # type: (...) -> str
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

# var-kw tests:
    def method_varkw1(self, a, b, **kw):
        # type: (int, int, **int) -> int
        return a+b

    def method_varkw2(self, a, b, *arg, **kw):
        # type: (int, int, *str, **int) -> int
        return a+b

# default tests:
    def method_defaults1(self, a, b):
        # type: (int, int) -> int
        return a+b

    def method_defaults2(self, a, b, *vargs):
        # type: (int, int, *int) -> int
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

# var-kw tests:
    @override
    def method_varkw1(self, a, b, **kw):
        # type: (int, int, **float) -> int
        return a+b

    @override
    def method_varkw2(self, a, b, *arg, **kw):
        # type: (int, int, *str, **float) -> int
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
