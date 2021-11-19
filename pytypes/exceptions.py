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


class TypeCheckError(TypeError):
    """Error type to indicate all errors regarding runtime typechecking.
    """
    pass


class InputTypeError(TypeCheckError):
    """Error type to indicate errors regarding failing typechecks of
    function or method parameters.
    """
    pass


class ReturnTypeError(TypeCheckError):
    """Error type to indicate errors regarding failing typechecks of
    function or method return values.
    """
    pass


class TypeWarning(RuntimeWarning):
    """Warning type to indicate errors regarding failing typechecks.
    """
    pass


class InputTypeWarning(TypeWarning):
    """Warning type to indicate errors regarding failing typechecks of
    function or method parameters.
    """
    pass


class ReturnTypeWarning(TypeWarning):
    """Warning type to indicate errors regarding failing typechecks of
    function or method return values.
    """
    pass


class OverrideError(TypeError):
    """Error type to indicate errors regarding failing checks of
    method's override consistency.
    """
    pass


class TypeSyntaxError(TypeError):
    """Error type to indicate errors regarding ill-formated typestrings.
    """
    pass


class ForwardRefError(TypeError):
    """Error type to indicate errors regarding forward references.
    """
    pass
