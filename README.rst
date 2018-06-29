.. Copyright 2017, 2018 Stefan Richthofer

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

.. image:: https://travis-ci.org/Stewori/pytypes.svg?branch=master
    :target: https://travis-ci.org/Stewori/pytypes
    :alt: Build Status

.. image:: https://raw.githubusercontent.com/Stewori/pytypes/master/pytypes_logo_text.png
    :scale: 70%
    :align: left
    :alt: pytypes


Welcome to the pytypes project
==============================

pytypes is a typing toolbox w.r.t. `PEP
484 <https://www.python.org/dev/peps/pep-0484/>`__ (PEP
`526 <https://www.python.org/dev/peps/pep-0526/>`__ on the road map,
later also `544 <https://www.python.org/dev/peps/pep-0544/>`__ if it
gets accepted).

It's main features are currently

- ``@typechecked`` decorator for runtime typechecking with support for `stubfiles <https://www.python.org/dev/peps/pep-0484/#stub-files>`__ and `type comments <https://www.python.org/dev/peps/pep-0484/#suggested-syntax-for-python-2-7-and-straddling-code>`__
- ``@override`` decorator that asserts existence of a type-compatible parent method
- ``@annotations`` decorator to turn type info from stubfiles or from type comments into ``__annotations__``
- ``@typelogged`` decorator observes function and method calls at runtime and generates stubfiles from acquired type info
- service functions to apply these decorators module wide or even globally, i.e. runtime wide
- typechecking can alternatively be done in decorator-free manner (friendlier for debuggers)
- all the above decorators work smoothly with OOP, i.e. with methods, static methods, class methods and properties, even if classes are nested
- converter for stubfiles to Python 2.7 compliant form
- lots of utility functions regarding types, e.g. a Python 2.7 compliant and actually functional implementation of ``get_type_hints``
- full Python 2.7 support for all these features

An additional future goal will be integration with the Java typing system when running on Jython. Along with this, some generator utilities to produce type-safe Java bindings for Python frameworks are planned.

In wider sense, PEP 484-style type annotations can be used to build type safe interfaces to allow also other programming languages to call into Python code (kind of reverse FFI). In this sense the project name refers to 'ctypes', which provides Python-bindings of C.


Python 2.7, 3.5, 3.6
--------------------

All described features of pytypes were carefully implemented such that they are equally workable on CPython 3.5, 3.6, 2.7 and on Jython 2.7.1 (other interpreters might work as well, but were not yet tested).
For Python 2.7, pytypes fully supports type-annotations via `type comments <https://www.python.org/dev/peps/pep-0484/#suggested-syntax-for-python-2-7-and-straddling-code>`__.
It also supports Python 2.7-style type annotations in Python 3.5-code to allow easier 2.7/3.5 multi-version development.


Why write another runtime typecheck decorator?
----------------------------------------------

There have been earlier approaches for runtime-typechecking. However, most of them predate PEP 484 or lack some crucial features like support of Python 2.7 or support of stubfiles. Also, none of them features a typechecking override decorator. There were separate approaches for override decorators, but these usually don't consider PEP 484 at all. So we decided that it's time for a new runtime typechecking framework, designed to support PEP 484 from the roots, including its extensive features like (Python 2.7-style-)type comments and stub files.


Quick manual
============


Typechecking
------------

pytypes provides a rich set of utilities for runtime typechecking.

@typechecked decorator
~~~~~~~~~~~~~~~~~~~~~~

Decorator applicable to functions, methods, properties and classes.
Asserts compatibility of runtime argument and return values of all targeted functions and methods w.r.t. `PEP 484 <https://www.python.org/dev/peps/pep-0484/>`__-style type annotations of these functions and methods.
This supports `stubfiles <https://www.python.org/dev/peps/pep-0484/#stub-files>`__ and `type comments <https://www.python.org/dev/peps/pep-0484/#suggested-syntax-for-python-2-7-and-straddling-code>`__ and is thus workable on Python 2.7.


Disabling typechecking
~~~~~~~~~~~~~~~~~~~~~~

Running Python with the '-O' flag, which also disables ``assert`` statements, turns off typechecking completely.
Alternatively, one can modify the flag ``pytypes.checking_enabled``.

Note that this must be done right after import of pytypes, because it affects the way how ``@typechecked`` decorator works. For modules that were imported with this flag disabled, typechecking cannot be turned on later on within the same runtime.


Usage Python 2
~~~~~~~~~~~~~~

.. code:: python

    from pytypes import typechecked

    @typechecked
    def some_function(a, b, c):
        # type: (int, str, List[Union[str, float]]) -> int
        return a+len(b)+len(c)


Usage Python 3
~~~~~~~~~~~~~~

.. code:: python

    from pytypes import typechecked

    @typechecked
    def some_function(a: int, b: str, c: List[Union[str, float]]) -> int:
        return a+len(b)+len(c)


Overriding methods in type-safe manner
--------------------------------------

The decorators in this section allow type-safe method overriding.

@override decorator
~~~~~~~~~~~~~~~~~~~

Decorator applicable to methods only.
For a version applicable also to classes or modules use ``auto_override``.
Asserts that for the decorated method a parent method exists in its mro.
If both the decorated method and its parent method are type annotated, the decorator additionally asserts compatibility of the annotated types.
Note that the return type is checked in contravariant manner. A successful check guarantees that the child method can always be used in places that support the parent method's signature.
Use ``pytypes.check_override_at_runtime`` and ``pytypes.check_override_at_class_definition_time`` to control whether checks happen at class definition time or at "actual runtime".

The following rules apply for override checking:

- a parent method must exist
- the parent method must have call-compatible signature (e.g. same number of args)
- arg types of parent method must be more or equal specific than arg types of child
- return type behaves contravariant - parent method must have less or equal specific return type than child


Usage Example
~~~~~~~~~~~~~

.. code:: python

    from pytypes import override

    class some_baseclass():
        def some_method1(self, a: int) -> None: ...
        def some_method2(self, a: int) -> None: ...
        def some_method3(self, a: int) -> None: ...
        def some_method4(self) -> int: ...

    class some_subclass(some_baseclass):
        @override
        def some_method1(self, a: float) -> None: ...

        @override
        def some_method2(self, a: str) -> None: ...

        @override
        def some_metd3(self, a: int) -> None: ...

        @override
        def some_method4(self) -> float: ...

- ``some_method1``: override check passes
- ``some_method2``: override check fails because type is not compatible
- ``some_method3``: override check fails because of typo in method name
- ``some_method4``: override check fails because return type must be more or equal specific than parent


@auto_override decorator
~~~~~~~~~~~~~~~~~~~~~~~~

Decorator applicable to methods and classes.
Works like ``override`` decorator on type annotated methods that actually have a type annotated parent method. Has no effect on methods that do not override anything.
In contrast to plain ``override`` decorator, ``auto_override`` can be applied easily on every method in a class or module.
In contrast to explicit ``override`` decorator, ``auto_override`` is not suitable to detect typos in spelling of a child method's name. It is only useful to assert compatibility of type information (note that return type is contravariant).
Use ``pytypes.check_override_at_runtime`` and ``pytypes.check_override_at_class_definition_time`` to control whether checks happen at class definition time or at "actual runtime".

The following rules apply, if a parent method exists:

- the parent method must have call-compatible signature (e.g. same number of args)
- arg types of parent method must be more or equal specific than arg types of child
- return type behaves contravariant - parent method must have less or equal specific return type than child

Compared to ordinary ``override`` decorator, the rule “a parent method must exist” is not applied here.
If no parent method exists, ``auto_override`` silently passes.


Provide info from type comments and stubfiles as ``__annotations__`` for other tools
------------------------------------------------------------------------------------

@annotations decorator
~~~~~~~~~~~~~~~~~~~~~~

Decorator applicable to functions, methods, properties and classes.
Methods with type comment will have type hints parsed from that string and get them attached as ``__annotations__`` attribute. Methods with either a type comment or ordinary type annotations in a stubfile will get that information attached as ``__annotations__`` attribute (also a relevant use case in Python 3).
Behavior in case of collision with previously (manually) attached ``__annotations__`` can be controlled using the flags ``pytypes.annotations_override_typestring`` and ``pytypes.annotations_from_typestring``.


Type logging
------------

@typelogged decorator
~~~~~~~~~~~~~~~~~~~~~

Decorator applicable to functions, methods, properties and classes.
It observes function and method calls at runtime and can generate stubfiles from acquired type info.


Disabling typelogging
~~~~~~~~~~~~~~~~~~~~~

One can disable typelogging via the flag ``pytypes.typelogging_enabled``.

Note that this must be done right after import of pytypes, because it affects the way how ``@typelogged`` decorator works. For modules that were imported with this flag disabled, typelogging cannot be turned on later on within the same runtime.


Usage example with decorator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Assume you run a file ./script.py like this:

.. code:: python

    from pytypes import typelogged

    @typelogged
    def logtest(a, b, c=7, *var, **kw): return 7, a, b

    @typelogged
    class logtest_class(object):
        def logmeth(self, b): return 2*b

        @classmethod
        def logmeth_cls(cls, c): return len(c)

        @staticmethod
        def logmeth_static(c): return len(c)

        @property
        def log_prop(self): return self._log_prop

        @log_prop.setter
        def log_prop(self, val): self._log_prop = val

    logtest(3, 2, 5, 6, 7, 3.1, y=3.2, x=9)
    logtest(3.5, 7.3, 5, 6, 7, 3.1, y=3.2, x=9)
    logtest('abc', 7.3, 5, 6, 7, 3.1, y=2, x=9)
    lcs = logtest_class()
    lcs.log_prop = (7.8, 'log')
    lcs.log_prop
    logtest_class.logmeth_cls('hijk')
    logtest_class.logmeth_static(range(3))

    pytypes.dump_cache()


Usage example with profiler
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Alternatively you can use the `TypeLogger` profiler:

.. code:: python

    from pytypes import TypeLogger

    def logtest(a, b, c=7, *var, **kw): return 7, a, b

    class logtest_class(object):
        def logmeth(self, b): return 2*b

        @classmethod
        def logmeth_cls(cls, c): return len(c)

        @staticmethod
        def logmeth_static(c): return len(c)

        @property
        def log_prop(self): return self._log_prop

        @log_prop.setter
        def log_prop(self, val): self._log_prop = val

    with TypeLogger():
    	logtest(3, 2, 5, 6, 7, 3.1, y=3.2, x=9)
    	logtest(3.5, 7.3, 5, 6, 7, 3.1, y=3.2, x=9)
    	logtest('abc', 7.3, 5, 6, 7, 3.1, y=2, x=9)
    	lcs = logtest_class()
    	lcs.log_prop = (7.8, 'log')
    	lcs.log_prop
    	logtest_class.logmeth_cls('hijk')
    	logtest_class.logmeth_static(range(3))

Note that this will produce more stubs, i.e. also for indirectly used modules, because
the profiler will handle every function call. To scope a specific module at a time use
`pytypes.typelogged` on that module or its name. This should be called on a
module after it is fully loaded. To use it inside the scoped module (e.g. for `__main__`)
apply it right after all classes and functions are defined.


Output
~~~~~~

Any of the examples above will create the following file in ./typelogger\_output:

script.pyi:

.. code:: python

    from typing import Tuple, Union

    def logtest(a: Union[float, str], b: float, c: int, *var: float, **kw: Union[float, int]) -> Union[Tuple[int, float, float], Tuple[int, str, float]]: ...

    class logtest_class(object):
        def logmeth(self, b: int) -> int: ...

        @classmethod
        def logmeth_cls(cls, c: str) -> int: ...

        @staticmethod
        def logmeth_static(c: range) -> int: ...

        @property
        def log_prop(self) -> Tuple[float, str]: ...

        @log_prop.setter
        def log_prop(self, val: Tuple[float, str]) -> None: ...

Use ``pytypes.dump_cache(python2=True)`` to produce a Python 2.7 compliant stubfile.


Writing typelog at exit
~~~~~~~~~~~~~~~~~~~~~~~

By default, pytypes performs ``pytypes.dump_cache()`` at exit, i.e. writes typelog as a Python 3 style stubfile.
Use ``pytypes.dump_typelog_at_exit`` to control this behavior.
Use ``pytypes.dump_typelog_at_exit_python2`` to write typelog as a Python 2 style stubfile.


Global mode and module wide mode
--------------------------------

Note that global mode is experimental.

The pytypes decorators ``@typechecked``, ``@auto_override``, ``@annotations`` and ``@typelogged`` can be applied module wide by explicitly calling them on a module object or a module name contained in ``sys.modules``. In such a case, the decorator is applied to all functions and classes in that module and recursively to all methods, properties and inner classes too.

*Warning: If A decorator is applied to a partly imported module, only functions and classes that were already defined are affected. After the module imported completely, the decorator is applied to the remaining functions and classes. In the meantime, internal code of that module can circumvent the decorator, e.g. can make module-internal calls that are not typechecked.*


Global mode via profilers
~~~~~~~~~~~~~~~~~~~~~~~~~

The pytypes decorators ``@typechecked`` and ``@typelogged`` have corresponding profiler implementations ``TypeChecker`` and ``TypeLogger``.
You can conveniently install them globally via ``enable_global_typechecked_profiler()`` and ``enable_global_typelogged_profiler()``.

Alternatively you can apply them in a ``with``-context:

.. code:: python

    from pytypes import TypeChecker

    def agnt_test(v):
        # type: (str) -> int
        return 67

    with TypeChecker():
        agnt_test(12)


One glitch is to consider in case you want to catch ``TypeCheckError`` (i.e. ``ReturnTypeError`` or ``InputTypeError`` as well) and continue execution afterwards. The ``TypeChecker`` would be suspended unless you call ``restore_profiler``, e.g.:

.. code:: python

    from pytypes import TypeChecker, restore_profiler

    def agnt_test(v):
        # type: (str) -> int
        return 67

    with TypeChecker():
        try:
            agnt_test(12)
        except TypeCheckError:
            restore_profiler()
            # handle error....


Note that the call to ``restore_profiler`` must be performed by the thread that raised the error.

Alternatively you can enable ``pytypes.warning_mode = True`` to raise warnings rather than errors. (This only helps if you don't use ``filterwarnings("error")`` or likewise.)


Global mode via decorators
~~~~~~~~~~~~~~~~~~~~~~~~~~

The pytypes decorators ``@typechecked``, ``@auto_override``, ``@annotations`` and ``@typelogged`` can be applied globally to all loaded modules and subsequently loaded modules.
Modules that were loaded while typechecking or typelogging was disabled will not be affected. Apart from that this will affect every module in the way described above.
Note that we recommend to use the profilers explained in the previous section if global typechecking or typelogging is required.
Use this feature with care as it is still experimental and can notably slow down your python runtime. In any case, it is intended for debugging and testing phase only.

- To apply ``@typechecked`` globally, use ``pytypes.set_global_typechecked_decorator``
- To apply ``@auto_override`` globally, use ``pytypes.set_global_auto_override_decorator``
- To apply ``@annotations`` globally, use ``pytypes.set_global_annotations_decorator``
- To apply ``@typelogged`` globally, use ``pytypes.set_global_typelogged_decorator``

*Warning: If the module that performs the ``pytypes.set_global_xy_decorator``-call is not yet fully imported, the warning regarding module-wide decorators (see above) applies to that module in the same sense. I.e. functions and classes that were not yet defined, will be covered only once the module-import has fully completed.*


OOP support
-----------

All the above decorators work smoothly with OOP. You can safely apply ``@typechecked``, ``@annotations`` and ``@typelogged`` on methods, abstract methods, static methods, class methods and properties.
``@override`` is – already by semantics – only applicable to methods,
``@auto_override`` is additionally applicable to classes and modules.

pytypes also takes care of inner classes and resolves name space properly.
Make sure to apply decorators from pytypes *on top of* ``@staticmethod``, ``@classmethod``, ``@property`` or ``@abstractmethod`` rather than the other way round. This is because OOP support involves some special treatment internally, so OOP decorators must be visible to pytypes decorators. This also applies to old-style classes.


No @override on ``__init__``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For now, ``@override`` cannot be applied to ``__init__``, because ``__init__`` typically extends the list of initialization parameters and usually uses ``super`` to explicitly serve a parent's signature.
The purpose of ``@override`` is to avoid typos and to guarantee that the child method can always be used as a fill in for the parent in terms of signature and type information. Both aspects are hardly relevant for ``__init__``:

- a typo is unlikely and would show up quickly for various reasons
- when creating an instance the caller usually knows the exact class to instantiate and thus its signature

For special cases where this might be relevant, ``@typechecked`` can be used to catch most errors.


Utilities
---------

Utility functions described in this section can be directly imported from the pytypes module. Only the most important utility functions are listed here.


get_type_hints(func)
~~~~~~~~~~~~~~~~~~~~

Resembles ``typing.get_type_hints``, but is also workable on Python 2.7 and searches stubfiles for type information. Also on Python 3, this takes `type comments <https://www.python.org/dev/peps/pep-0484/#suggested-syntax-for-python-2-7-and-straddling-code>`__ into account if present.


get_types(func)
~~~~~~~~~~~~~~~

Works like ``get_type_hints``, but returns types as a sequence rather than a dictionary. Types are returned in declaration order of the corresponding arguments.


check_argument_types(cllable=None, call_args=None, clss=None, caller_level=0)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This function mimics `typeguard <https://github.com/agronholm/typeguard>`__ syntax and semantics. It can be applied within a function or method to check argument values to comply with type annotations.
It behaves similar to ``@typechecked`` except that it is not a decorator and does not check the return type.
A decorator less way for argument checking yields less interference with some debuggers.


check_return_type(value, cllable=None, clss=None, caller_level=0)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This function works like ``check_argument_types``, but applies to the return value.
Because it is impossible for pytypes to automatically figure out the value to be returned in a function, it must be explicitly provided as the ``value``-parameter.


is_of_type(obj, cls, bound_Generic=None)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Works like ``isinstance``, but supports PEP 484 style types from typing module.

If ``cls`` contains unbound ``TypeVar`` s and ``bound_Generic`` is provided, this function attempts to
retrieve corresponding values for the unbound ``TypeVar`` s from ``bound_Generic``.


is_subtype(subtype, supertype, bound_Generic=None)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Works like ``issubclass``, but supports PEP 484 style types from typing module.

If ``subclass`` or ``superclass`` contains unbound ``TypeVar`` s and ``bound_Generic`` is
provided, this function attempts to retrieve corresponding values for the
unbound ``TypeVar`` s from ``bound_Generic``.


deep_type(obj, depth=None, max_sample=None)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tries to construct a type for a given value. In contrast to ``type(...)``, ``deep_type`` does its
best to fit structured types from ``typing`` as close as possible to the given value.
E.g. ``deep_type((1, 2, 'a'))`` will return ``Tuple[int, int, str]`` rather than just ``tuple``.
Supports various types from ``typing``, but not yet all.
Also detects nesting up to given depth (uses ``pytypes.default_typecheck_depth`` if no value is given).
If a value for ``max_sample`` is given, this number of elements is probed from lists, sets and dictionaries to determine the element type. By default, all elements are probed. If there are fewer elements than ``max_sample``, all existing elements are probed.


type_str(tp, assumed_globals=None, update_assumed_globals=None, implicit_globals=None, bound_Generic=None)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Generates a nicely readable string representation of the given type.
The returned representation is workable as a source code string and would reconstruct the given type if handed to eval, provided that globals/locals are configured appropriately (e.g. assumes that various types from ``typing`` have been imported).
Used as type-formatting backend of ptypes' code generator abilities in modules ``typelogger`` and ``stubfile_2_converter``.
If ``tp`` contains unbound ``TypeVar`` s and ``bound_Generic`` is provided, this function attempts to
retrieve corresponding values for the unbound ``TypeVar`` s from ``bound_Generic``.


dump_cache(path=default_typelogger_path, python2=False, suffix=None)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Writes cached observations by ``@typelogged`` into stubfiles.

Files will be created in the directory provided as 'path'; overwrites existing files without notice. Uses 'pyi2' suffix if 'python2' flag is given else 'pyi'. Resulting files will be Python 2.7 compliant accordingly.


get_Generic_itemtype(sq, simplify=True)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Retrieves the item type from a PEP 484 generic or subclass of such.
``sq`` must be a ``typing.Tuple`` or (subclass of) ``typing.Iterable`` or ``typing.Container``.
Consequently this also works with ``typing.List``, ``typing.Set`` and ``typing.Dict``.
Note that for ``typing.Dict`` and mapping types in general, the key type is regarded as item type.
For ``typing.Tuple`` all contained types are returned as a ``typing.Union``.
If ``simplify == True`` some effort is taken to eliminate redundancies in such a union.


get_Mapping_key_value(mp)
~~~~~~~~~~~~~~~~~~~~~~~~~

Retrieves the key and value types from a PEP 484 mapping or subclass of such.
``mp`` must be a (subclass of) ``typing.Mapping``.


get_arg_for_TypeVar(typevar, generic)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Retrieves the parameter value of a given ``TypeVar`` from a ``Generic``.
Returns ``None`` if the generic does not contain an appropriate value.
Note that the ``TypeVar`` is compared by instance and not by name.
E.g. using a local ``TypeVar`` ``T`` would yield different results than
using ``typing.T`` despite the equal name.


resolve_fw_decl(in_type, module_name=None, globs=None, level=0, search_stack_depth=2)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Resolves forward references in ``in_type``.

``globs`` should be a dictionary containing values for the names
that must be resolved in ``in_type``. If ``globs`` is not provided, it
will be created by ``__globals__`` from the module named ``module_name``,
plus ``__locals__`` from the last ``search_stack_depth`` stack frames,
beginning at the calling function. This is to resolve cases where ``in_type`` and/or
types it fw-references are defined inside a function.

To prevent walking the stack, set ``search_stack_depth=0``.
Ideally provide a proper ``globs`` for best efficiency.
See ``util.get_function_perspective_globals`` for obtaining a ``globs`` that can be
cached. ``util.get_function_perspective_globals`` works like described above.


Python 2.7 compliant stubfiles
------------------------------

Currently pytypes uses the python runtime, i.e. ``import``, ``eval``, ``dir`` and inspect to parse stubfiles and type comments. A runtime independent parser for stubfiles is a desired future feature, but is not yet available. This means that conventional PEP 484 stubfiles would not work on Python 2.7. To resolve this gap, pytypes features a converter script that can convert conventional stubfiles into Python 2.7 compliant form.
More specifically it converts parameter annotations into type comments and converts ``...`` syntax into ``pass``.

As of this writing it does not yet support stubfiles containing the ``@overload`` decorator. Also, it does not yet convert type annotations of attributes and variables.


'pyi2' suffix
~~~~~~~~~~~~~

pytypes uses the suffix 'pyi2' for Python 2.7 compliant stubfiles, but does not require it. Plain 'pyi' is also an acceptable suffix (as far as pytypes is concerned), because Python 2.7 compliant stubfiles can also be used in Python 3.

The main purpose of 'pyi2' suffix is to avoid name conflicts when conventional stubfiles and Python 2.7 compliant stubfiles coexist for the same module. In that case the pyi2 file will override the pyi file when running on Python 2.7.


stubfile\_2\_converter
~~~~~~~~~~~~~~~~~~~~~~

Run stubfile\_2\_converter.py to leverage pytypes' stubfile converter capabilities:

``python3 -m pytypes.stubfile_2_converter [options/flags] [in_file]``

Use ``python3 -m pytypes.stubfile_2_converter -h`` to see detailed usage.

By default the out file will be created in the same folder as the in file, but with 'pyi2' suffix.


Next steps
==========

- support `PEP 526 <https://www.python.org/dev/peps/pep-0526>`__
- support `overloading <https://www.python.org/dev/peps/pep-0484/#function-method-overloading>`__
- support named tuple
- support async-related constructs from typing
- support notation for `Positional-only arguments <https://www.python.org/dev/peps/pep-0484/#positional-only-arguments>`__
- runtime independent parser for stubfiles


Contributors
============

pytypes was created in 2016/17 by `Stefan Richthofer <https://github.com/Stewori>`__.

Contributors (no specific order, names as provided on github)
-------------------------------------------------------------

* `Alex Grönholm <https://github.com/agronholm>`__
* `Mitar <https://github.com/mitar>`__
* `Ilya Kulakov <https://github.com/Kentzo>`__
* `Jonas <https://github.com/elcombato>`__
* `MinJune Kim <https://github.com/qria>`__


License
=======

pytypes is released under Apache 2.0 license.
A copy is provided in the file LICENSE.

| 
| Copyright 2017, 2018 Stefan Richthofer
| 
| Licensed under the Apache License, Version 2.0 (the "License");
| you may not use this file except in compliance with the License.
| You may obtain a copy of the License at
| 
| `http://www.apache.org/licenses/LICENSE-2.0 <http://www.apache.org/licenses/LICENSE-2.0>`__
| 
| Unless required by applicable law or agreed to in writing, software
| distributed under the License is distributed on an "AS IS" BASIS,
| WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
| See the License for the specific language governing permissions and
| limitations under the License.


Contact
=======

stefan.richthofer@jyni.org

