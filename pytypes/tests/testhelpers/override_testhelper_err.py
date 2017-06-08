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
Designed to cause an OverrideError on import.
(unless typechecker.check_override_at_runtime == False)
"""

from pytypes import override

class TestClass():
    def test_meth0(self, a):
        # type: (int) -> str
        pass

    def test_meth1(self, a):
        # type: (TestArg1) -> str
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
        # type: (TestArg2) -> str
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

