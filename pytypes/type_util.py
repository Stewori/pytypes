'''
Created on 13.12.2016

@author: Stefan Richthofer
'''

import sys, types, inspect
import typing; from typing import Tuple, Dict, List, Set, Union, Any, Generator
from .stubfile_manager import _match_stub_type, as_stub_func_if_any
from .typecomment_parser import _get_typestrings, _funcsigtypesfromstring
from . import util
import pytypes

def deep_type(obj):
	return _deep_type(obj, [])

def _deep_type(obj, checked):
	res = type(obj)
	if obj in checked:
		return res
	else:
		checked.append(obj)
	if hasattr(obj, '__gentype__'):
		return obj.__gentype__
	if res == tuple:
		res = Tuple[tuple(_deep_type(t, checked) for t in obj)]
	elif res == list:
		res = List[Union[tuple(_deep_type(t, checked) for t in obj)]]
	elif res == dict:
		res = Dict[Union[tuple(_deep_type(t, checked) for t in obj.keys())],
				Union[tuple(_deep_type(t, checked) for t in obj.values())]]
	elif res == set:
		res = Set[Union[tuple(_deep_type(t, checked) for t in obj)]]
	elif sys.version_info.major == 2 and isinstance(obj, types.InstanceType):
		# For old-style instances return the actual class:
		return obj.__class__
	return res

def is_builtin_type(tp):
	return hasattr(__builtins__, tp.__name__) and tp is getattr(__builtins__, tp.__name__)

def has_type_hints(func0):
	func = as_stub_func_if_any(util._actualfunc(func0), func0)
	try:
		tpHints = typing.get_type_hints(func)
	except NameError:
		# Some typehint caused this NameError, so typhints are present in some form
		return True
	tpStr = _get_typestrings(func, False)
	return not ((tpStr is None or tpStr[0] is None) and (tpHints is None or not tpHints))

def type_str(tp):
	tp = _match_stub_type(tp)
	impl = ('__builtin__', 'builtins', '__main__')
	if inspect.isclass(tp) and not hasattr(typing, tp.__name__):
		if not tp.__module__ in impl:
			module = sys.modules[tp.__module__]
			if not (module.__package__ is None or module.__package__ == ''
					or tp.__module__.startswith(module.__package__)):
				pck = module.__package__+'.'+tp.__module__+'.'
			else:
				pck = tp.__module__+'.'
		else:
			pck = ''
		prm = ''
		if hasattr(tp, '__args__'):
			params = [type_str(param) for param in tp.__args__]
			prm = '['+', '.join(params)+']'
		return pck+tp.__name__+prm
	elif hasattr(tp, '__args__'):
		params = [type_str(param) for param in tp.__args__]
		return tp.__name__+'['+', '.join(params)+']'
	elif hasattr(tp, '__tuple_params__'):
		tpl_params = [type_str(param) for param in tp.__tuple_params__]
		return 'Tuple['+', '.join(tpl_params)+']'
	else:
		# Todo: Care for other special types from typing where necessary.
		return str(tp).replace('typing.', '')

def get_types(func):
	return _get_types(func, util.is_classmethod(func), util.is_method(func))

def _get_types(func, clsm, slf):
	func0 = util._actualfunc(func)

	# check consistency regarding special case with 'self'-keyword
	if not slf:
		argNames = util.getargspecs(func0).args
		if len(argNames) > 0:
			if clsm:
				if argNames[0] != 'cls':
					print('Warning: classmethod using non-idiomatic argname '+func0.__name__)
	clss = None
	if slf or clsm:
		if slf:
			assert util.is_method(func)
		if clsm:
			assert util.is_classmethod(func)
		clss = util.get_class_that_defined_method(func)
		assert hasattr(clss, func.__name__)
	args, res = _funcsigtypes(func, slf or clsm, clss)
	return _match_stub_type(args), _match_stub_type(res)

def get_type_hints(func):
	'''
	Resembles typing.get_type_hints, but is also workable on Python 2.7.
	'''
	typing.get_type_hints
	if not has_type_hints(func):
		return {}
	slf = 1 if util.is_method(func) else 0
	args, res = get_types(func)
	argNames = util.getargspecs(util._actualfunc(func)).args
	result = {}
	if not args is Any:
		for i in range(slf, len(argNames)):
			result[argNames[i]] = args.__tuple_params__[i-slf]
	result['return'] = res
	return result

def _make_invalid_type_msg(descr, func_name, tp):
	msg = 'Invalid %s in %s:\n    %s is not a type.' % (descr, func_name, str(tp))
	if isinstance(tp, tuple):
		mask = '\n  You might rather want to use typing.Tuple:\n      Tuple[%s]'
		try:
			msg += mask % (', '.join(type_str(t) for t in tp))
		except:
			msg += mask % (', '.join(str(t) for t in tp))
	return msg

def _funcsigtypes(func0, slf, func_class = None):
	# Check for stubfile
	func = as_stub_func_if_any(util._actualfunc(func0), func0, func_class)

	tpHints = typing.get_type_hints(func)
	tpStr = _get_typestrings(func, slf)
	if (tpStr is None or tpStr[0] is None) and (tpHints is None or not tpHints):
		# Maybe raise warning here
		return Any, Any
	if not (tpStr is None or tpStr[0] is None) and tpStr[0].find('...') != 0:
		numArgs = len(util.getargspecs(func).args) - 1 if slf else 0
		while len(tpStr[1]) < numArgs:
			tpStr[1].append(None)
	if func.__module__.endswith('.pyi') or func.__module__.endswith('.pyi2'):
		globs = {}
		globs.update(sys.modules[func.__module__].__dict__)
		globs.update(sys.modules[func.__module__.rsplit('.', 1)[0]].__dict__)
	else:
		globs = sys.modules[func.__module__].__dict__
	if not tpHints is None and tpHints:
		# We're running Python 3
		argNames = inspect.getfullargspec(func).args
		if slf:
			argNames = argNames[1:]
		retTp = tpHints['return'] if 'return' in tpHints else Any
		resType = (Tuple[tuple((tpHints[t] if t in tpHints else Any) for t in argNames)],
				retTp if not retTp is None else type(None))
		if not (tpStr is None or tpStr[0] is None):
			resType2 = _funcsigtypesfromstring(*tpStr, globals = globs)
			if resType != resType2:
				raise TypeError('%s.%s declares incompatible types:\n'
					% (func.__module__, func.__name__)
					+ 'Via hints:   %s\nVia comment: %s'
					% (type_str(resType), type_str(resType2)))
		try:
			typing._type_check(resType[0], '') # arg types
		except TypeError:
			raise TypeError(_make_invalid_type_msg('arg types',
					util._fully_qualified_func_name(func, slf, func_class), resType[0]))
		try:
			typing._type_check(resType[1], '') # return type
		except TypeError:
			raise TypeError(_make_invalid_type_msg('return type',
					util._fully_qualified_func_name(func, slf, func_class), resType[1]))
		return resType
	res = _funcsigtypesfromstring(*tpStr, globals = globs)
	try:
		typing._type_check(res[0], '') # arg types
	except TypeError:
		raise TypeError(_make_invalid_type_msg('arg types',
				util._fully_qualified_func_name(func, slf, func_class), res[0]))
	try:
		typing._type_check(res[1], '') # return type
	except TypeError:
		raise TypeError(_make_invalid_type_msg('return type',
				util._fully_qualified_func_name(func, slf, func_class), res[1]))
	return res

def _issubclass(sub, super):
	# Will be a Python 3.6 workable version soon
	return issubclass(sub, super)

def _isinstance(obj, cls):
	# Will be a Python 3.6 workable version soon
	return _issubclass(deep_type(obj), cls)

def _make_generator_error_message(tp, gen, expected_tp, incomp_text):
	_cmp_msg_format = 'Expected: %s\nReceived: %s'
	# todo: obtain fully qualified generator name
	return gen.__name__+' '+incomp_text+':\n'+_cmp_msg_format \
				% (type_str(expected_tp), type_str(tp))

def generator_checker_py3(gen, yield_type, send_type, return_type):
	initialized = False
	sn = None
	try:
		while True:
			a = gen.send(sn)
			if initialized or not a is None:
				if not yield_type is Any and not _isinstance(a, yield_type):
					raise pytypes.ReturnTypeError(_make_generator_error_message(deep_type(a), gen,
							yield_type, 'has incompatible yield type'))
			initialized = True
			sn = yield a
			if not send_type is Any and not _isinstance(sn, send_type):
				raise pytypes.InputTypeError(_make_generator_error_message(deep_type(sn), gen,
						send_type, 'has incompatible send type'))
	except StopIteration as st:
		# Python 3:
		# todo: Check if st.value is always defined (i.e. as None if not present)
		if not return_type is Any and not _isinstance(st.value, return_type):
				raise pytypes.ReturnTypeError(_make_generator_error_message(deep_type(st.value), gen,
						return_type, 'has incompatible return type'))
		raise st

def generator_checker_py2(gen, yield_type, send_type):
	initialized = False
	sn = None
	while True:
		a = gen.send(sn)
		if initialized or not a is None:
			if not yield_type is Any and not _isinstance(a, yield_type):
				raise pytypes.ReturnTypeError(_make_generator_error_message(deep_type(a), gen,
						yield_type, 'has incompatible yield type'))
		initialized  = True
		sn = yield a
		if not send_type is Any and not _isinstance(sn, send_type):
			raise pytypes.InputTypeError(_make_generator_error_message(deep_type(sn), gen,
					send_type, 'has incompatible send type'))

def _checkinstance(obj, cls, is_args, func):
	# todo: Complete this function
	if hasattr(cls, '__tuple_params__'):
		if len(obj) != len(cls.__tuple_params__):
			return False, obj
		lst = []
		if isinstance(obj, tuple):
			for i in range(len(obj)):
				res, obj2 = _checkinstance(obj[i], cls.__tuple_params__[i], is_args, func)
				if not res:
					return False, obj
				else:
					lst.append(obj2)
			return True, tuple(lst)
		else:
			return False, obj
	# Tthis (optionally) turns some types into a checked version, e.g. generators or callables (todo)
	if pytypes.check_generators and hasattr(cls, '__origin__') and cls.__origin__ is Generator:
		if is_args or not inspect.isgeneratorfunction(func):
			# todo: Insert fully qualified function name
			raise pytypes.TypeCheckError(
					'typing.Generator must only be used as result type of generator functions.')
		if isinstance(obj, types.GeneratorType):
			if obj.__name__.startswith('generator_checker_py'):
				return True, obj
			if sys.version_info.major == 2:
				wrgen = generator_checker_py2(obj, cls.__args__[0], cls.__args__[1])
			else:
				wrgen = generator_checker_py3(obj, cls.__args__[0], cls.__args__[1], cls.__args__[2])
				#wrgen.__name__ = obj.__name__
				wrgen.__qualname__ = obj.__qualname__
			return True, wrgen
		else:
			return False, obj
	return _isinstance(obj, cls), obj
