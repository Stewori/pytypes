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

# Created on 29.04.2017

"""
pytypes.typelogger is a module for automatic creation of
PEP 484 stubfiles based on runtime observations.

Also allows creation of Python 2.7 compatible stubfiles.
"""

import sys
import os
import abc
import datetime
from typing import Union, Any, Tuple, TupleMeta
from inspect import isclass, ismodule, isfunction, ismethod, \
		ismethoddescriptor, getsourcelines, findsource

import pytypes
from .type_util import deep_type, type_str, get_Tuple_params, \
		Empty, simplify_for_Union, _get_types, _has_type_hints, \
		_preprocess_typecheck, get_Union_params, is_Union, \
		get_Generic_itemtype, TypeAgent
from .util import getargspecs, getargnames
from .typechecker import _typeinspect_func
from . import version, default_indent, default_typelogger_path, \
		util

_member_cache = {}
_fully_typelogged_modules = {}
silent = True
use_NoneType = False
simplify = True


def _print(line):
	if not silent:
		print(line)


def log_type(args_kw, ret, func, slf=False, prop_getter=False, clss=None, argspecs=None,
			args_kw_type=None, ret_type = None):
	"""Stores information of a function or method call into a cache, so pytypes can
	create a PEP 484 stubfile from this information later on (see dump_cache).
	"""
	if args_kw_type is None:
		args_kw_type = deep_type(args_kw)
	if ret_type is None:
		ret_type = deep_type(ret)
	if argspecs is None:
		argspecs = getargspecs(func)
	node = _register_logged_func(func, slf, prop_getter, clss, argspecs)
	node.add_observation(args_kw_type, ret_type)


def _register_logged_func(func, slf, prop_getter, clss, argspecs):
	if isinstance(func, property):
		func_key = func.fget if prop_getter else func.fset
	else:
		func_key = func
	if func_key in _member_cache:
		node = _member_cache[func_key]
	else:
		node = _typed_member(func, slf, prop_getter, clss, argspecs)
		_member_cache[func_key] = node
	return node


def combine_argtype(observations):
	"""Combines a list of Tuple types into one.
	Basically these are combined element wise into a Union with some
	additional unification effort (e.g. can apply PEP 484 style numeric tower).
	"""
	assert len(observations) > 0
	assert isinstance(observations[0], TupleMeta)
	if len(observations) > 1:
		prms = [get_Tuple_params(observations[0])]
		ln = len(prms[0])
		for obs in observations[1:]:
			assert isinstance(obs, TupleMeta)
			prms.append(get_Tuple_params(obs))
			assert len(prms[-1]) == ln
		if simplify:
			prms = map(list, zip(*prms))
			if not isinstance(prms, list):
				# special care for Python 3
				prms = list(prms)
			for type_list in prms:
				simplify_for_Union(type_list)
			prms = map(tuple, prms)
		else:
			prms = map(tuple, zip(*prms))
		prms = map(Union.__getitem__, prms)
		return Tuple[tuple(prms)]
	else:
		return observations[0]


def combine_type(observations):
	"""Combines a list of types into one.
	Basically these are combined into a Union with some
	additional unification effort (e.g. can apply PEP 484 style numeric tower).
	"""
	assert len(observations) > 0
	if len(observations) == 1:
		return observations[0]
	else:
		if simplify:
			simplify_for_Union(observations)
		return Union[tuple(observations)]


def _print_cache():
	for key in _member_cache:
		node = _member_cache[key]
		print (node)


def _dump_module(module_node, path=default_typelogger_path, python2=False, suffix=None):
	if suffix is None:
		suffix = 'pyi2' if python2 else 'pyi'
	basic_name = module_node.get_basic_filename()
	src_fname = module_node.module.__file__
	if src_fname is None:
		src_fname = 'unknown file'
	pck_path = module_node.get_pck_path()
	try:
		checksum = util._md5(src_fname)
	except:
		checksum = 'unknown checksum'
	pck_path = path if pck_path is None else os.sep.join((path, pck_path))
	indent = module_node._indent()
	stubpath = ''.join((pck_path, os.sep, basic_name, '.', suffix))
	if not os.path.exists(pck_path):
		os.makedirs(pck_path)
	nw = datetime.datetime.now()
	try:
		exec_info_lst = [sys.executable]
		if len(sys.argv) > 0:
			exec_info_lst.append(sys.argv[0])
			if len(sys.argv) > 1:
				exec_info_lst.append(' '.join(sys.argv[1:]))
		exec_info = ('\n'+default_indent).join(exec_info_lst)
	except:
		exec_info = 'unknown call'
	with open(stubpath, 'w') as stub_handle:
		lines = [""""",
				'Auto created Python 2.7-compliant stubfile of ' if python2 
						else 'Auto created stubfile of \n',
				src_fname,
				'MD5-Checksum: '+checksum,
				'\nThis file was generated by pytypes.typelogger v'+version,
				'at '+nw.isoformat()+'.\n',
				'Type information is based on runtime observations while running',
				util._python_version_string(),
				exec_info,
				'\nWARNING:',
				'If you edit this file, be aware it was auto generated.',
				'Save your customized version to a distinct place;',
				'this file might get overwritten without notice.',
				""""",
				'',
				#'import typing',
				'from typing import Any, Tuple, List, Union, Generic, Optional, \\',
				2*indent+'TypeVar, Set, FrozenSet, Dict, Generator']
				#'import numbers']
				# todo: Properly create import section

		for i in range(len(lines)):
			lines[i] = lines[i]+'\n'
		lines.append('\n')
		module_node.dump(lines, 0, python2)
		if not python2:
			lines.append('\n')
		_print(''.join(lines))
		stub_handle.writelines(lines)


def dump_cache(path=default_typelogger_path, python2=False, suffix=None):
	"""Writes cached observations by @typelogged into stubfiles.
	Files will be created in the directory provided as 'path'; overwrites
	existing files without notice.
	Uses 'pyi2' suffix if 'python2' flag is given else 'pyi'. Resulting
	files will be Python 2.7 compilant accordingly.
	"""
	if suffix is None:
		suffix = 'pyi2' if python2 else 'pyi'
	modules = {}
	for key in _member_cache:
		node = _member_cache[key]
		mname = node.get_modulename()
		if not mname in modules:
			mnode = _module_node(mname)
			modules[mname] = mnode
		else:
			mnode = modules[mname]
		mnode.append(node)
	for module in modules:
		_dump_module(modules[module], path, python2, suffix)


def _prepare_arg_types(arg_Tuple, argspecs, slf_or_clsm = False, names = None):
	tps = get_Tuple_params(arg_Tuple)
	arg_tps = []
	off = 1 if slf_or_clsm else 0
	i = off-1
	if names is None:
		for i in range(off, len(argspecs.args)):
			arg_tps.append(tps[i-off])
		if slf_or_clsm:
			i -= 1
	else:
		for i in range(off, len(argspecs.args)):
			arg_tps.append(tps[i-off])
			names.append(argspecs.args[i])
		if slf_or_clsm:
			i -= 1
	vararg_tp = None
	if not argspecs.varargs is None:
		i += 1
		if is_Union(tps[i]):
			itm_tps = []
			uprms = get_Union_params(tps[i])
			for uprm in uprms:
				itm_tp = get_Generic_itemtype(uprm, simplify)
				if not itm_tp is None:
					itm_tps.append(itm_tp)
			simplify_for_Union(itm_tps)
			vararg_tp = Union[tuple(itm_tps)]
		else:
			vararg_tp = get_Generic_itemtype(tps[i], simplify)
			if vararg_tp is None:
				vararg_tp = Any
		if not names is None:
			names.append('*'+argspecs.varargs)

	kwonly_tps = None
	try:
		if not argspecs.kwonlyargs is None:
			kwonly_tps = []
			if names is None:
				for _ in range(len(argspecs.kwonlyargs)):
					i += 1
					kwonly_tps.append(tps[i])
			else:
				for j in range(len(argspecs.kwonlyargs)):
					i += 1
					kwonly_tps.append(tps[i])
					names.append(argspecs.kwonlyargs[j])
	except AttributeError:
		pass

	try:
		kw = argspecs.keywords
	except AttributeError:
		kw = argspecs.varkw
	kw_tp = None
	if not kw is None:
		i += 1
		if is_Union(tps[i]):
			itm_tps = []
			uprms = get_Union_params(tps[i])
			for uprm in uprms:
				itm_tp = uprm.__args__[-1]
				if not itm_tp is None:
					itm_tps.append(itm_tp)
			simplify_for_Union(itm_tps)
			kw_tp = Union[tuple(itm_tps)]
		else:
			kw_tp = Any if issubclass(tps[i], Empty) else tps[i].__args__[-1]
		if not names is None:
			names.append('**'+kw)
	return arg_tps, vararg_tp, kw_tp, kwonly_tps


def _prepare_arg_types_list(arg_Tuple, argspecs, slf_or_clsm = False, names=None):
	arg_tps, vararg_tp, kw_tp, kwonly_tps = _prepare_arg_types(
			arg_Tuple, argspecs, slf_or_clsm, names)
	res = []
	res.extend(arg_tps)
	if not vararg_tp is None:
		res.append(vararg_tp)
	if not kwonly_tps is None:
		res.extend(kwonly_tps)
	if not kw_tp is None:
		res.append(kw_tp)
	return res


def _prepare_arg_types_str(arg_Tuple, argspecs, slf_or_clsm = False, names=None):
	arg_tps, vararg_tp, kw_tp, kwonly_tps = _prepare_arg_types(
			arg_Tuple, argspecs, slf_or_clsm, names)
	res = []
	res.extend(type_str(tp) for tp in arg_tps)
	if not vararg_tp is None:
		res.append('*'+type_str(vararg_tp))
	if not kwonly_tps is None:
		res.extend(type_str(tp) for tp in kwonly_tps)
	if not kw_tp is None:
		res.append('**'+type_str(kw_tp))
	return ''.join(('(', ', '.join(res), ')'))


# currently not used; kept here as potential future feature
def get_indentation(func):
	"""Extracts a function's indentation as a string,
	In contrast to an inspect.indentsize based implementation,
	this function preserves tabs if present.
	"""
	src_lines = getsourcelines(func)[0]
	for line in src_lines:
		if not (line.startswith('@') or line.startswith('def') or line.lstrip().startswith('#')):
			return line[:len(line) - len(line.lstrip())]
	return default_indent


def _node_get_line(node):
	return node.get_line()


class _base_node(object):
	__metaclass__  = abc.ABCMeta

	def _indent(self):
		idn = self._idn
		if not idn is None:
			return idn
		idn = default_indent
		self._idn = idn
		return idn

	@abc.abstractmethod
	def dump(self, dest, indents = 0, python2 = False, props = None):
		pass

	def is_property(self):
		return False

	def append(self, node):
		raise ValueError('append is not supported by %s.' % self.__class__.__name__)

	def get_line(self):
		return 0


class _typed_member(_base_node):
	def __init__(self, member, slf=False, prop_getter=False, clss=None, argspecs=None):
		self.member = member
		clsm = isinstance(member, classmethod)
		stat = isinstance(member, staticmethod)
		prop = isinstance(member, property)
		if prop:
			self.name = member.fget.__name__  if prop_getter else member.fset.__name__
		else:
			self.name = member.__func__.__name__ if clsm or stat else member.__name__
		self.argspecs = argspecs
		self.clss = clss
		self.arg_type_observations = []
		self.ret_type_observations = []
		self._idn = None
		self.slf = slf
		self.clsm = clsm
		self.stat = stat
		self.prop = prop
		self.prop_getter = prop_getter
		self._added_type_hints = False

	def add_observation(self, args_kw_type, ret_type):
		self.arg_type_observations.append(args_kw_type)
		self.ret_type_observations.append(ret_type)

	def _add_observation_from_type_info(self):
		if pytypes.typelogger_include_typehint and \
				_has_type_hints(self.member, self.clss, nesting = None):
			self._added_type_hints = True
			args, ret = _get_types(self.member, self.clsm, self.slf, self.clss,
					self.prop_getter)
			args = _preprocess_typecheck(args, self.argspecs, self.slf or self.clsm)
			self.add_observation(args, ret)

	def _type_str(self):
		arg_str =  _prepare_arg_types_str(combine_argtype(self.arg_type_observations),
				self.argspecs, self.slf or self.clsm)
		return ''.join((arg_str, ' -> ', type_str(combine_type(self.ret_type_observations))))

	def _type_comment(self):
		return '# type: '+self._type_str()

	def _signature(self):
		# For now we prefer getargnames over inspect.formatargspec, because of easier
		# bridging of Python 2 and 3.
		arg_names = getargnames(self.argspecs, True)
		return ''.join(('(', ', '.join(arg_names), ')'))

	def _annotated_signature(self):
		# inspect.formatargspec would only work in Python 3 with annotations
		sig_lst = []
		tp_lst = _prepare_arg_types_list(combine_argtype(self.arg_type_observations),
				self.argspecs, self.slf or self.clsm, sig_lst)
		if not use_NoneType:
			ntp = type(None)
			for i in range(len(sig_lst)):
				sig_lst[i] += ': '+('None' if tp_lst[i] == ntp else type_str(tp_lst[i]))
		else:
			for i in range(len(sig_lst)):
				sig_lst[i] += ': '+type_str(tp_lst[i])
		if self.slf:
			sig_lst.insert(0, 'self')
		elif self.clsm:
			sig_lst.insert(0, 'cls')
		rtp = combine_type(self.ret_type_observations)
		if not use_NoneType:
			ntp = type(None)
			res_tp = 'None' if rtp == ntp else type_str(rtp)
		else:
			res_tp = type_str(rtp)
		return ''.join(('(', ', '.join(sig_lst), ') -> ', res_tp))

	def _declaration(self, indents = 0, annotated=False):
		base_idn = self._indent()*indents
		return ''.join((base_idn, 'def ', self.name,
				self._annotated_signature() if annotated else self._signature(), ':'))

	def _stub_src_tpypestring(self, indents = 0, props = None):
		idn = self._indent()
		bs = '\n'+idn*(indents+1)
		elements = [self._declaration(indents), bs, self._type_comment(), bs, 'pass']
		if self.clsm:
			elements.insert(0, idn*indents+'@classmethod\n')
		elif self.stat:
			elements.insert(0, idn*indents+'@staticmethod\n')
		elif self.prop:
			idn = self._indent()
			if self.prop_getter:
				elements.insert(0, idn*indents+'@property\n')
			else:
				elements.insert(0, idn*indents+'@%s.setter\n' % self.member.fget.__name__)
				if not self.member in props:
					elements.insert(0, idn*(indents+1)+'pass\n')
					elements.insert(0, idn*indents+'def '+self.name+'(self):\n')
					elements.insert(0, idn*indents+'@property\n')
		res = ''.join(elements)
		return res if use_NoneType else res.replace('NoneType', 'None')

	def _stub_src_annotations(self, indents = 0, props = None):
		elements = [self._declaration(indents, True), ' ...']
		if self.clsm:
			idn = self._indent()
			elements.insert(0, idn*indents+'@classmethod\n')
		elif self.stat:
			idn = self._indent()
			elements.insert(0, idn*indents+'@staticmethod\n')
		elif self.prop:
			idn = self._indent()
			if self.prop_getter:
				elements.insert(0, idn*indents+'@property\n')
			else:
				elements.insert(0, idn*indents+'@%s.setter\n' % self.member.fget.__name__)
				if not self.member in props:
					elements.insert(0, idn*indents+'def '+self.name+'(self): ...\n')
					elements.insert(0, idn*indents+'@property\n')
		return ''.join(elements)

	def dump(self, dest, indents = 0, python2 = False, props = None):
		if not self._added_type_hints:
			self._add_observation_from_type_info()
		if python2:
			dest.append(self._stub_src_tpypestring(indents, props))
		else:
			dest.append(self._stub_src_annotations(indents, props))
		dest.append('\n\n' if python2 else '\n')

	def __str__(self):
		return ''.join((self.member.__str__(), ': ',
				type_str(combine_argtype(self.arg_type_observations)),
				' -> ', type_str(combine_type(self.ret_type_observations))))

	def get_key(self):
		if self.prop:
			return ''.join((self.name, '/getter' if self.prop_getter else '/setter'))
		else:
			return self.name

	def get_modulename(self):
		if self.prop:
			return self.member.fget.__module__ if self.prop_getter \
					else self.member.fset.__module__
		else:
			return self.member.__func__.__module__ if self.clsm or self.stat else \
					self.member.__module__

	def is_property(self):
		return self.prop_getter

	def get_line(self):
		try:
			return self.member.__code__.co_firstlineno
		except:
			pass
		if self.prop:
			return self.member.fget.__code__.co_firstlineno if self.prop_getter \
					else self.member.fset.__code__.co_firstlineno
		else:
			return self.member.__func__.__code__.co_firstlineno


class _module_node(_base_node):
	def __init__(self, mname):
		self.name = mname
		self.module = sys.modules[mname]
		self.classes = {}
		self.others = {}
		self._idn = None
		
	def get_basic_filename(self):
		if self.name == '__main__':
			return self.module.__file__.rsplit(os.sep, 1)[-1].split('.', 1)[0]
		else:
			return self.name

	def get_pck_path(self):
		if self.module.__package__ is None:
			return None
		else:
			return self.module.__package__.replace('.', os.sep)

	def get_filename(self):
		return self.module.__file__.rsplit(os.sep, 1)[-1]

	def dump(self, dest, indents = 0, python2 = False):
		dump_lst = []
		dump_lst.extend(self.classes.values())
		dump_lst.extend(self.others.values())
		dump_lst.sort(key=_node_get_line)
		for elm in dump_lst:
			elm.dump(dest, indents, python2)

	def append(self, typed_member):
		if typed_member.clss is None and not typed_member.stat:
			typed_member._idn = self._indent()
			self.others[typed_member.get_key()] = typed_member
		else:
			if not typed_member.stat:
				nst_lst = util._get_class_nesting_list(typed_member.clss, self.module)
				tp_cls = typed_member.clss
			else:
				nst_lst = util._get_class_nesting_list_for_staticmethod(
						typed_member.member, self.module, [], set())
				tp_cls = nst_lst[0]
				nst_lst = nst_lst[1:]
			clss_node = self
			for cls in nst_lst:
				if cls.__name__ in clss_node.classes:
					clss_node = clss_node.classes[cls.__name__]
				else:
					clss_node1 = _class_node(cls)
					clss_node1._idn = self._indent()
					clss_node.classes[cls.__name__] = clss_node1
					clss_node = clss_node1
			if tp_cls.__name__ in clss_node.classes:
				clss_node = clss_node.classes[tp_cls.__name__]
			else:
				clss_node1 = _class_node(tp_cls)
				clss_node1._idn = self._indent()
				clss_node.classes[clss_node1.name] = clss_node1
				clss_node = clss_node1
			clss_node.append(typed_member)


class _class_node(_base_node):
	def __init__(self, clss):
		self.name = clss.__name__
		self.clss = clss
		self.classes = {}
		self.others = {}
		self._idn = None

	def dump(self, dest, indents = 0, python2 = False, props=None):
		dest.append('\n')
		idn = self._indent()
		bases = [cls.__name__ for cls in self.clss.__bases__]
		if not python2:
			bases.remove('object')
		dest.append(''.join((indents*idn, 'class ', self.name, '(', ', '.join(bases),'):\n')))
		dump_lst = []
		dump_lst.extend(self.classes.values())
		dump_lst.extend(self.others.values())
		dump_lst.sort(key=_node_get_line)
		props = set()
		for elm in dump_lst:
			if elm.is_property():
				props.add(elm.member)
			elm.dump(dest, indents+1, python2, props)

	def append(self, member):
		member._idn = self._indent()
		self.others[member.get_key()] = member

	def get_line(self):
		return findsource(self.clss)[1]


def typelogged_func(func):
	"""Works like typelogged, but is only applicable to functions,
	methods and properties.
	"""
	if not pytypes.typelogging_enabled:
		return func
	if hasattr(func, 'do_logging'):
		func.do_logging = True
		return func
	elif hasattr(func, 'do_typecheck'):
		# actually shouldn't happen
		return _typeinspect_func(func, func.do_typecheck, True)
	else:
		return _typeinspect_func(func, False, True)


def typelogged_class(cls):
	"""Works like typelogged, but is only applicable to classes.
	"""
	if not pytypes.typelogging_enabled:
		return cls
	assert(isclass(cls))
	# To play it safe we avoid to modify the dict while iterating over it,
	# so we previously cache keys.
	# For this we don't use keys() because of Python 3.
	# Todo: Better use inspect.getmembers here
	keys = [key for key in cls.__dict__]
	for key in keys:
		memb = cls.__dict__[key]
		if (isfunction(memb) or ismethod(memb) or \
				ismethoddescriptor(memb)) or  isinstance(memb, property):
			setattr(cls, key, typelogged_func(memb))
		elif isclass(memb):
			typelogged_class(memb)
	return cls


def typelogged_module(md):
	"""Works like typelogged, but is only applicable to modules by explicit call).
	md must be a module or a module name contained in sys.modules.
	"""
	if not pytypes.typelogging_enabled:
		return md
	if isinstance(md, str):
		if md in sys.modules:
			md = sys.modules[md]
			if md is None:
				return md
	assert(ismodule(md))
	if md.__name__ in _fully_typelogged_modules and \
			_fully_typelogged_modules[md.__name__] == len(md.__dict__):
		return md
	# To play it safe we avoid to modify the dict while iterating over it,
	# so we previously cache keys.
	# For this we don't use keys() because of Python 3.
	# Todo: Better use inspect.getmembers here
	keys = [key for key in md.__dict__]
	for key in keys:
		memb = md.__dict__[key]
		if (isfunction(memb) or ismethod(memb) or ismethoddescriptor(memb)) \
				and memb.__module__ == md.__name__:
			setattr(md, key, typelogged_func(memb))
		elif isclass(memb) and memb.__module__ == md.__name__:
			typelogged_class(memb)
	_fully_typelogged_modules[md.__name__] = len(md.__dict__)
	return md


def typelogged(memb):
	"""Decorator applicable to functions, methods, properties,
	classes or modules (by explicit call).
	If applied on a module, memb must be a module or a module name contained in sys.modules.
	See pytypes.set_global_typelogged_decorator to apply this on all modules.
	Observes function and method calls at runtime and allows pytypes to generate stubfiles
	from the acquired type information.
	Use dump_cache to write a stubfile in this manner.
	"""
	if not pytypes.typelogging_enabled:
		return memb
	if isfunction(memb) or ismethod(memb) or ismethoddescriptor(memb) or isinstance(memb, property):
		return typelogged_func(memb)
	if isclass(memb):
		return typelogged_class(memb)
	if ismodule(memb):
		return typelogged_module(memb, True)
	return memb


def _catch_up_global_typelogged_decorator():
	for mod_name in sys.modules:
		if not mod_name in _fully_typelogged_modules:
			try:
				md = sys.modules[mod_name]
			except KeyError:
				md = None
			if not md is None and ismodule(md):
				typelogged_module(mod_name)


class TypeLogger(TypeAgent):

	def __init__(self, all_threads = True):
		TypeAgent.__init__(self, all_threads)
		self._logging_enabled = True
