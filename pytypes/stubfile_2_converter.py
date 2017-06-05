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

# Created on 25.10.2016

"""
Creates Python 2.7-style stubfiles from Python 3.5-style stubfiles.
Conversion process needs Python 3.5, but resulting files can be
distributed for use with Python 2.7.
Only works if no Python 3.5 specific code was used to construct
type variables and such.

So far the conversion is somewhat naive and a hand-crafted
Python 2.7. stub-file might be required for advanced use-cases.
Such a file should be stored like the usual stub-file, but
using the suffix 'pyi2'. If such a file exists, pytypes will take
it as override of the pyi-file when running on Python 2.7.
"""

import sys
import imp
import inspect
import numbers
import os
import typing
from typing import Any
from pytypes import util, typelogger, type_util

if __name__ == '__main__':
	sys.path.append(sys.path[0]+os.sep+'..')


silent = False
indent = '\t'
stub_open_mode = "U"
stub_descr = (".pyi", stub_open_mode, imp.PY_SOURCE)


def _print(line):
	if not silent:
		print(line)


def _typestring(_types, argspecs, slf_or_clsm=False):
	if _types[0] is Any:
		argstr = '...'
	else:
		args = type_util._preprocess_typecheck(_types[0], argspecs, slf_or_clsm)
		argstr = typelogger._prepare_arg_types_str(args, argspecs, slf_or_clsm)
	retstr = type_util.type_str(_types[1])
	return (argstr+' -> '+retstr).replace('NoneType', 'None')


def _typecomment(_types, argspec, slf_or_clsm=False):
	return '# type: '+_typestring(_types, argspec, slf_or_clsm)


def typecomment(func, argspec=None, slf_or_clsm=False):
	if argspec is None:
		argspec = util.getargspecs(func)
	return _typecomment(type_util.get_types(func), argspec, slf_or_clsm)


def signature(func):
	argstr = ', '.join(util.getargnames(util.getargspecs(func), True))
	return 'def '+func.__name__+'('+argstr+'):'


def _write_func(func, lines, inc=0, decorators=None, slf_or_clsm=False):
	if not decorators is None:
		for dec in decorators:
			lines.append(inc*indent+'@'+dec)
	lines.append(inc*indent+signature(func))
	if type_util.has_type_hints(func):
		lines.append((inc+1)*indent+typecomment(func, slf_or_clsm=slf_or_clsm))
	lines.append((inc+1)*indent+'pass')


def _write_property(prop, lines, inc=0, decorators=None):
	if not decorators is None:
		for dec in decorators:
			lines.append(inc*indent+'@'+dec)
	if not prop.fget is None:
		_write_func(prop.fget, lines, inc, ['property'], True)
	if not prop.fset is None:
		if not prop.fget is None:
			lines.append('')
		_write_func(prop.fset, lines, inc, ['%s.setter'%prop.fget.__name__], True)


def signature_class(clss):
	base_names = [base.__name__ for base in clss.__bases__]
	return 'class '+clss.__name__+'('+', '.join(base_names)+'):'


def _write_class(clss, lines, inc = 0):
	_print("write class: "+str(clss))
	anyElement = False
	lines.append(inc*indent+signature_class(clss))
	mb = inspect.getmembers(clss, lambda t: inspect.isfunction(t) or \
			inspect.isclass(t) or inspect.ismethoddescriptor(t))
	# todo: Care for overload-decorator
	for elem in mb:
		if elem[0] in clss.__dict__:
			el = clss.__dict__[elem[0]]
			if inspect.isfunction(el):
				lines.append('')
				_write_func(el, lines, inc+1, slf_or_clsm=True)
				anyElement = True
			elif inspect.isclass(el):
				lines.append('')
				_write_class(el, lines, inc+1)
				anyElement = True
			elif inspect.ismethoddescriptor(el) and type(el) is staticmethod:
				lines.append('')
				_write_func(el.__func__, lines, inc+1, ['staticmethod'])
				anyElement = True

	# classmethods are not obtained via inspect.getmembers.
	# We have to look into __dict__ for that.
	# Same for properties.
	for key in clss.__dict__:
		attr = getattr(clss, key)
		if inspect.ismethod(attr):
			lines.append('')
			_write_func(attr, lines, inc+1, ['classmethod'], True)
			anyElement = True
		elif isinstance(attr, property):
			lines.append('')
			_write_property(attr, lines, inc+1)
			anyElement = True

	if not anyElement:
		lines.append((inc+1)*indent+'pass')


def convert(in_file, out_file = None):
	_print('in_file: '+in_file)
	assert(os.path.isfile(in_file))
	checksum = util._md5(in_file)
	if out_file is None:
		out_file = in_file+'2'
	_print('out_file: '+out_file)

	with open(in_file, stub_open_mode) as module_file:
		module_name = os.path.basename(in_file)
		stub_module = imp.load_module(
				module_name, module_file, in_file, stub_descr)

	funcs = [func[1] for func in inspect.getmembers(stub_module, inspect.isfunction)]
	cls = [cl[1] for cl in inspect.getmembers(stub_module, inspect.isclass)]

	directory = os.path.dirname(out_file)
	if not os.path.exists(directory):
		os.makedirs(directory)

	with open(out_file, 'w') as out_file_handle:
		lines = ['"""',
				'Python 2.7-compliant stubfile of ',
				in_file,
				'with MD5-Checksum: '+checksum,
				'This file was generated by pytypes. Do not edit directly.',
				'"""',
				'',
				'import typing',
				'from typing import Any, Tuple, List, Union, Generic, Optional, \\',
				2*indent+'TypeVar, Set, FrozenSet, Dict, Generator',
				'import numbers']
		for func in funcs:
			lines.append('')
			_write_func(func, lines)

		for cl in cls:
			if not (hasattr(numbers, cl.__name__) or hasattr(typing, cl.__name__)):
				lines.append('\n')
				_write_class(cl, lines)

		for i in range(len(lines)):
			_print(lines[i])
			lines[i] = lines[i]+'\n'
		lines.append('\n')
		out_file_handle.writelines(lines)


def err_no_in_file():
	print("Error: No in_file given! Use -h for help.")
	sys.exit(os.EX_USAGE)


def print_usage():
	print("stubfile_2_converter usage:")
	print("python3 -m pytypes.stubfile_2_converter.py [options/flags] [in_file]")
	print("Supported options/flags:")
	print("-o [out_file] : custom output-file")
	print("-s            : silent mode")
	print("-h            : usage")


if __name__ == '__main__':
	if '-h' in sys.argv:
		print_usage()
		sys.exit(0)
	in_file = sys.argv[-1]
	if len(sys.argv) < 2 or in_file.startswith('-'):
		err_no_in_file()
	out_file = None
	if '-s' in sys.argv:
		silent = True
	try:
		index_o = sys.argv.index('-o')
		if index_o == len(sys.argv)-2:
			err_no_in_file()
		out_file = sys.argv[index_o+1]
	except ValueError:
		pass
	convert(in_file, out_file)
