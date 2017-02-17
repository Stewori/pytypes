![pytypes Logo](https://raw.githubusercontent.com/Stewori/pytypes/4ed74b0f7e89588bb9818576aa9a84c4aed3a6cd/pytypes_logo_text.jpg)


Welcome to the pytypes project.
-------------------------------

pytypes is a typing toolbox w.r.t. [PEP 484](https://www.python.org/dev/peps/pep-0484/). As an additional future goal it will also feature generator utilities to produce language bindings to allow other programming languages to call into Python code (kind of reverse FFI). In this sense the project name refers to 'ctypes', which provides Python-bindings to C.
Especially Jython will be the first target and pytypes' typing-utilities will allow to generate type-safe Java-bindings to Python frameworks as far as PEP 484-style type annotations are provided.


Typing-utility
--------------

Besides various other useful typing-related functions pytypes so far features an actually functional Python 2.7 compliant version of typing.get_type_hints (the original version always returns None for Python 2.7).

Further it provides a typecheck-decorator for runtime typechecking and an override-decorator for runtime-assertion of consistent method-overriding w.r.t. type-annotations. In combination these decorators can also perform type-checking on overridden methods even if only the parent method was type-annotated.


Python 2.7, 3.5, 3.6
--------------------

All described features of pytypes were carefully implemented such that they are equally workable on Python 3.5, 3.6 and 2.7. For Python 2.7 pytypes fully supports type-annotations as described in https://www.python.org/dev/peps/pep-0484/#suggested-syntax-for-python-2-7-and-straddling-code. As far as we know this support is currently a unique feature compared to other runtime-type-checking frameworks.
It also supports Python 2.7-style type annotations in Python 3.5-code to allow easier 2.7/3.5 multi-version development. If a function or method is type-annotated in Python 2.7 and 3.5 style at the same time pytypes automatically asserts equality of the annotations.


Why write another runtime typecheck-decorator?
----------------------------------------------

There have been earlier approaches for runtime-typechecking. However, most of them predate PEP 484 or lack some crucial
features like support of Python 2.7 and support of stub files. Also none of them features a typechecking override
decorator. There were separate approaches for override-decorators, but these usually don't consider PEP 484 at all.
Given all these facts, we decided that it's time for a new runtime typechecking framework, designed to support PEP 484
from the roots, including its extensive features like (Python 2.7-style-)type comments and stub files.


Next steps
----------

As of this writing pytypes doesn't yet support

- method overloading: https://www.python.org/dev/peps/pep-0484/#function-method-overloading
- async-related constructs from typing


License
-------

pytypes is released under the PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2.
A copy is provided in the file LICENSE.


Contact
-------

For now write to stefan.richthofer@jyni.org.

