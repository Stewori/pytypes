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
