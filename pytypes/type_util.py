'''
Created on 13.12.2016

@author: Stefan Richthofer
'''

from inspect import isfunction, ismethod, ismethoddescriptor, isclass, ismodule
import typing; from typing import Tuple, Dict, List, Set, Union, Any, TupleMeta, \
		GenericMeta, CallableMeta, Sequence, Mapping, TypeVar, Container, Generic
from .stubfile_manager import _match_stub_type, as_stub_func_if_any
from .typecomment_parser import _get_typestrings, _funcsigtypesfromstring
from . import util
import  sys, types, pytypes

_annotated_modules = {}
_extra_dict = {}
for tp in typing.__all__:
	tpa = getattr(typing, tp)
	try:
		_extra_dict[tpa.__extra__] = tpa
	except AttributeError:
		pass
if not tuple in _extra_dict:
	_extra_dict[tuple] = Tuple

if sys.version_info.major >= 3:
	_basestring = str
else:
	_basestring = basestring

EMPTY = TypeVar('EMPTY', bound=Container, covariant=True)
class Empty(Generic[EMPTY]):
	pass

def get_generator_yield_type(genr):
	return get_generator_type(genr).__args__[0]

def get_generator_type(genr):
	if 'gen_type' in genr.gi_frame.f_locals:
		return genr.gi_frame.f_locals['gen_type']
	else:
		return _funcsigtypes(genr.gi_code, False, None, genr.gi_frame.f_globals)[1]

def make_Union(arg_tpl):
# Should work now by monkeypatching in pytypes.
# However we leave this sample here for a while...
# Once we remove it, we will also inline make_Union again.
# 	if pytypes.issue351:
# 		if not isinstance(arg_tpl, tuple):
# 			arg_tpl = (arg_tpl,)
# 		for i in range(len(arg_tpl)-1):
# 			for j in range(i+1, len(arg_tpl)):
# 				if arg_tpl[i] == arg_tpl[j] and not \
# 						_issubclass(arg_tpl[i], arg_tpl[j]):
# 					res = Union[str, int]
# 					if any (t is None for t in arg_tpl):
# 						ntp = type(None)
# 						arg_tpl = tuple([ntp if t is None else t for t in arg_tpl])
# 					res.__args__ = arg_tpl
# 					return res
	return Union[arg_tpl]

def make_Tuple(arg_tpl):
	res = Tuple[arg_tpl]
# Should work now by monkeypatching in pytypes.
# However we leave this sample here for a while...
# Once we remove it, we will also inline make_Tuple again.
# 	if pytypes.issue351:
# 		if not isinstance(arg_tpl, tuple):
# 			arg_tpl = (arg_tpl,)
# 		if any (t is None for t in arg_tpl):
# 			ntp = type(None)
# 			arg_tpl = tuple([ntp if t is None else t for t in arg_tpl])
# 		res.__args__ = arg_tpl if len(arg_tpl) > 0 else ((),)
	return res

def get_iterable_itemtype(obj):
	# support further specific iterables on demand
	try:
		if isinstance(obj, range):
			tpl = tuple(deep_type(obj.start), deep_type(obj.stop), deep_type(obj.step))
			return make_Union(tpl)
	except TypeError:
		# We're running Python 2
		pass
	if type(obj) is tuple:
		tpl = tuple(deep_type(t) for t in obj)
		return make_Union(tpl)
	elif type(obj) is types.GeneratorType:
		return get_generator_yield_type(obj)
	else:
		tp = deep_type(obj)
		if isinstance(tp, GenericMeta):
			if issubclass(tp.__origin__, typing.Iterable):
				if len(tp.__args__) == 1:
					return tp.__args__[0]
				return _select_Generic_superclass_parameters(tp, typing.Iterable)[0]
	if is_iterable(obj):
		if type(obj) is str:
			return str
		if hasattr(obj, '__iter__'):
			if has_type_hints(obj.__iter__):
				itrator = _funcsigtypes(obj.__iter__, True, obj.__class__)[1]
				if isinstance(itrator, GenericMeta) and itrator.__origin__ is typing.Iterator:
					return itrator.__args__[0]
		if hasattr(obj, '__getitem__'):
			if has_type_hints(obj.__getitem__):
				itrator =  _funcsigtypes(obj.__getitem__, True, obj.__class__)[1]
				if isinstance(itrator, GenericMeta) and itrator.__origin__ is typing.Iterator:
					return itrator.__args__[0]
		return None # means that type is unknown
	else:
		raise TypeError('Not an iterable: '+str(type(obj)))

def get_Tuple_params(tpl):
	try:
		return tpl.__tuple_params__
	except AttributeError:
		try:
			if tpl.__args__ is None:
				return None
			# Python 3.6
			return () if tpl.__args__[0] == () else tpl.__args__
		except AttributeError:
			return None

def get_Union_params(un):
	try:
		return un.__union_params__
	except AttributeError:
		# Python 3.6
		return un.__args__

def get_Callable_args_res(clb):
	try:
		return clb.__args__, clb.__result__
	except AttributeError:
		# Python 3.6
		return clb.__args__[:-1], clb.__args__[-1]

def is_iterable(obj):
	'''Tests if an object implements the iterable protocol.
	This function is intentionally not capitalized, because
	it does not check w.r.t. (capital) Iterable class from
	typing or collections.
	'''
	try:
		itr = iter(obj)
		del itr
		return True
	except:
		return False

def is_Union(tp):
	'''Python version independent check if a type is typing.Union.
	Tested with CPython 2.7, 3.5, 3.6 and Jython 2.7.1.
	'''
	if tp is Union:
		return True
	try:
		# Python 3.6
		return tp.__origin__ is Union
	except AttributeError:
		try:
			return isinstance(tp, typing.UnionMeta)
		except AttributeError:
			return False

def deep_type(obj, depth = pytypes.default_typecheck_depth):
	return _deep_type(obj, [], depth)

def _deep_type(obj, checked, depth):
	try:
		res = obj.__orig_class__
	except AttributeError:
		res = type(obj)
	if depth == 0 or obj in checked:
		return res
	else:
		checked.append(obj)
	if res == tuple:
		tpl = tuple(_deep_type(t, checked, depth-1) for t in obj)
		res = make_Tuple(tpl)
	elif res == list:
		if len(obj) == 0:
			return Empty[List]
		tpl = tuple(_deep_type(t, checked, depth-1) for t in obj)
		res = List[make_Union(tpl)]
	elif res == dict:
		if len(obj) == 0:
			return Empty[Dict]
		tpl1 = tuple(_deep_type(t, checked, depth-1) for t in obj.keys())
		tpl2 = tuple(_deep_type(t, checked, depth-1) for t in obj.values())
		res = Dict[make_Union(tpl1), make_Union(tpl2)]
	elif res == set:
		if len(obj) == 0:
			return Empty[Set]
		tpl = tuple(_deep_type(t, checked, depth-1) for t in obj)
		res = Set[make_Union(tpl)]
	elif res == types.GeneratorType:
		res = get_generator_type(obj)
	elif sys.version_info.major == 2 and isinstance(obj, types.InstanceType):
		# For old-style instances return the actual class:
		return obj.__class__
	elif _issubclass_2(res, Container) and len(obj) == 0:
		return Empty[res]
	elif hasattr(res, '__origin__') and \
			_issubclass_2(res.__origin__, Container) and len(obj) == 0:
		return Empty[res.__origin__]
	return res

def is_builtin_type(tp):
	return hasattr(__builtins__, tp.__name__) and tp is getattr(__builtins__, tp.__name__)

def has_type_hints(func0):
	return _has_type_hints(func0)

def _has_type_hints(func0, func_class = None, nesting = None):
	actual_func = util._actualfunc(func0)
	func = as_stub_func_if_any(actual_func, func0, func_class, nesting)
	stub_func = func
	func = util._actualfunc(func)
	tpHints = _tpHints_from_annotations(func0, actual_func, stub_func, func)
	if not tpHints is None:
		return True
	try:
		tpHints = typing.get_type_hints(func)
	except NameError:
		# Some typehint caused this NameError, so typhints are present in some form
		return True
	except TypeError:
		# func seems to be not suitable of having type hints
		return False
	except AttributeError:
		# func seems to be not suitable of having type hints
		return False
	try:
		tpStr = _get_typestrings(func, False)
		return not ((tpStr is None or tpStr[0] is None) and (tpHints is None or not tpHints))
	except TypeError:
		return False

def type_str(tp):
	if isinstance(tp, tuple):
		return '('+', '.join([type_str(tp0) for tp0 in tp])+')'
	try:
		return type_str(tp.__orig_class__)
	except AttributeError:
		pass
	tp = _match_stub_type(tp)
	impl = ('__builtin__', 'builtins', '__main__')
	if isclass(tp) and not isinstance(tp, GenericMeta) \
			and not hasattr(typing, tp.__name__):
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
		if hasattr(tp, '__args__') and not tp.__args__ is None:
			params = [type_str(param) for param in tp.__args__]
			prm = '['+', '.join(params)+']'
		return pck+tp.__name__+prm
	elif is_Union(tp):
		try:
			# Python 3.6
			params = [type_str(param) for param in tp.__args__]
		except AttributeError:
			params = [type_str(param) for param in tp.__union_params__]
		return 'Union['+', '.join(params)+']'
	elif isinstance(tp, TupleMeta):
		prms = get_Tuple_params(tp)
		tpl_params = [type_str(param) for param in prms]
		return 'Tuple['+', '.join(tpl_params)+']'
	elif hasattr(tp, '__args__'):
		if tp.__args__ is None:
			return tp.__name__
		params = [type_str(param) for param in tp.__args__]
		if hasattr(tp, '__result__'):
			return tp.__name__+'[['+', '.join(params)+'], '+type_str(tp.__result__)+']'
		elif isinstance(tp, CallableMeta):
			return tp.__name__+'[['+', '.join(params[:-1])+'], '+type_str(params[-1])+']'
		else:
			return tp.__name__+'['+', '.join(params)+']'
	else:
		# Todo: Care for other special types from typing where necessary.
		return str(tp).replace('typing.', '')

def get_types(func):
	return _get_types(func, util.is_classmethod(func), util.is_method(func))

# still experimental, incomplete and hardly tested
def get_member_types(obj, member_name, prop_getter = False):
	cls = obj.__class__
	member = getattr(cls, member_name)
	slf = not (isinstance(member, staticmethod) or isinstance(member, classmethod))
	clsm = isinstance(member, classmethod)
	return _get_types(member, clsm, slf, cls, prop_getter)

def _get_types(func, clsm, slf, clss = None, prop_getter = False,
			unspecified_type = Any, infer_defaults = None):
	func0 = util._actualfunc(func, prop_getter)
	# check consistency regarding special case with 'self'-keyword
	if not slf:
		argNames = util.getargnames(util.getargspecs(func0))
		if len(argNames) > 0:
			if clsm:
				if argNames[0] != 'cls':
					print('Warning: classmethod using non-idiomatic argname '+func0.__name__)
	if clss is None and (slf or clsm):
		if slf:
			assert util.is_method(func) or isinstance(func, property)
		if clsm:
			assert util.is_classmethod(func)
		clss = util.get_class_that_defined_method(func)
		assert hasattr(clss, func.__name__)
	args, res = _funcsigtypes(func, slf or clsm, clss, None, prop_getter,
			unspecified_type = unspecified_type, infer_defaults = infer_defaults)
	return _match_stub_type(args), _match_stub_type(res)

def get_type_hints(func):
	'''Resembles typing.get_type_hints, but is also workable on Python 2.7.
	'''
	if not has_type_hints(func):
		# What about defaults?
		return {}
	return _get_type_hints(func)

def _get_type_hints(func, args = None, res = None, infer_defaults = None):
	if args is None or res is None:
		args2, res2 = _get_types(func, util.is_classmethod(func),
				util.is_method(func), unspecified_type = type(NotImplemented),
				infer_defaults = infer_defaults)
		if args is None:
			args = args2
		if res is None:
			res = res2
	slf = 1 if util.is_method(func) else 0
	argNames = util.getargnames(util.getargspecs(util._actualfunc(func)))
	result = {}
	if not args is Any:
		prms = get_Tuple_params(args)
		for i in range(slf, len(argNames)):
			if not prms[i-slf] is type(NotImplemented):
				result[argNames[i]] = prms[i-slf]
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

def _tpHints_from_annotations(*args):
	for func in args:
		if not func is None and hasattr(func, '__annotations__'):
			res = func.__annotations__
			if not res is None and len(res) > 0:
				return res
	return None

# Only intended for use with __annotations__.
# For typestrings, _funcsigtypesfromstring can directly insert defaults
def _handle_defaults(sig_types, arg_specs, unspecified_indices = None):
	if arg_specs.defaults is None:
		return sig_types
	prms = get_Tuple_params(sig_types[0])
	if len(prms) < len(arg_specs.args):
		# infer missing types from defaults...
		df = len(arg_specs.args)-len(prms)
		if df <= len(arg_specs.defaults):
			resType = [prm for prm in prms]
			for obj in arg_specs.defaults[-df:]:
				resType.append(deep_type(obj))
			if unspecified_indices is None:
				res = Tuple[tuple(resType)], sig_types[1]
				return res
		elif not unspecified_indices is None:
			resType = [prm for prm in prms]
	elif not unspecified_indices is None:
		resType = [prm for prm in prms]
	if not unspecified_indices is None and len(unspecified_indices) > 0:
		off = len(arg_specs.args)-len(arg_specs.defaults)
		for i in unspecified_indices:
			if i >= off:
				resType[i] = deep_type(arg_specs.defaults[i-off])
		res = Tuple[tuple(resType)], sig_types[1]
		return res
	return sig_types

def _funcsigtypes(func0, slf, func_class = None, globs = None, prop_getter = False,
		unspecified_type = Any, infer_defaults = None):
	if infer_defaults is None:
		infer_defaults = pytypes.infer_default_value_types
	# Check for stubfile
	actual_func = util._actualfunc(func0, prop_getter)
	func = as_stub_func_if_any(actual_func, func0, func_class)
	stub_func = None
	if isinstance(func, property):
		stub_func = func
		func = util._actualfunc(func, prop_getter)
	try:
		tpHints = typing.get_type_hints(func)
	except AttributeError:
		tpHints = None
	tpStr = _get_typestrings(func, slf)
	argSpecs = util.getargspecs(actual_func)
	hints_from_annotations = False
	if tpHints is None or not tpHints:
		tpHints = _tpHints_from_annotations(func0, actual_func, stub_func, func)
		hints_from_annotations = True
	if (tpStr is None or tpStr[0] is None) and tpHints is None:
		# What about defaults?
		return Any, Any
	if not (tpStr is None or tpStr[0] is None) and tpStr[0].find('...') != -1:
		numArgs = len(argSpecs.args) - 1 if slf else 0
		while len(tpStr[1]) < numArgs:
			tpStr[1].append(None)
	if globs is None:
		if func.__module__.endswith('.pyi') or func.__module__.endswith('.pyi2'):
			globs = {}
			globs.update(sys.modules[func.__module__].__dict__)
			globs.update(sys.modules[func.__module__.rsplit('.', 1)[0]].__dict__)
		else:
			globs = sys.modules[func.__module__].__dict__
	argNames = util.getargnames(argSpecs)
	if slf:
		argNames = argNames[1:]
	if not tpHints is None and tpHints:
		if hints_from_annotations:
			tmp = tpHints
			tpHints = {}
			for key in tmp:
				val = tmp[key]
				if val is None:
					val = type(None)
				elif isinstance(val, _basestring):
					val = eval(val, globs)
				tpHints[key] = val
		# We're running Python 3 or have custom __annotations__ in Python 2.7
		retTp = tpHints['return'] if 'return' in tpHints else Any
		unspecIndices = []
		for i in range(len(argNames)):
			if not argNames[i] in tpHints:
				unspecIndices.append(i)
		resType = (make_Tuple(tuple((tpHints[t] if t in tpHints else unspecified_type) \
				for t in argNames)), retTp if not retTp is None else type(None))
		if infer_defaults:
			resType = _handle_defaults(resType, argSpecs, unspecIndices)
		if not pytypes.annotations_override_typestring and not (tpStr is None or tpStr[0] is None):
			if pytypes.strict_annotation_collision_check:
				raise TypeError('%s.%s has multiple type declarations.'
						% (func.__module__, func.__name__))
			else:
				resType2 = _funcsigtypesfromstring(*tpStr, argspec = argSpecs, globals = globs,
						argCount = len(argNames), unspecified_type = unspecified_type,
						defaults = argSpecs.defaults if infer_defaults else None,
						func = actual_func, func_class = func_class, slf = slf)
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
	res = _funcsigtypesfromstring(*tpStr, globals = globs, argspec = argSpecs,
			argCount = len(argNames),
			defaults = argSpecs.defaults if infer_defaults else None,
			unspecified_type = unspecified_type, func = actual_func,
			func_class = func_class, slf = slf)
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
	if pytypes.annotations_from_typestring:
		if not hasattr(func0, '__annotations__') or len(func0.__annotations__) == 0:
			if not infer_defaults:
				func0.__annotations__ = _get_type_hints(func0, res[0], res[1])
			else:
				res2 = _funcsigtypesfromstring(*tpStr, argspec = argSpecs, globals = globs,
						argCount = len(argNames), unspecified_type = unspecified_type,
						func = actual_func, func_class = func_class, slf = slf)
				func0.__annotations__ = _get_type_hints(func0, res2[0], res2[1])
	return res

def _issubclass_Mapping_covariant(subclass, superclass):
	# This subclass-check treats Mapping-values as covariant
	if isinstance(subclass, GenericMeta):
		if not issubclass(subclass.__origin__, Mapping):
			return False
		if not _issubclass(subclass.__args__[0], superclass.__args__[0]):
			return False
		if not _issubclass(subclass.__args__[1], superclass.__args__[1]):
			return False
		return True
	return issubclass(subclass, superclass)

def _find_Generic_super_origin(subclass, superclass_origin):
	stack = [subclass]
	param_map = {}
	while len(stack) > 0:
		bs = stack.pop()
		if isinstance(bs, GenericMeta):
			if (bs.__origin__ is superclass_origin or \
					(bs.__origin__ is None and bs is superclass_origin)):
				prms = []
				prms.extend(bs.__parameters__)
				for i in range(len(prms)):
					while prms[i] in param_map:
						prms[i] = param_map[prms[i]]
				return prms
			if not bs.__origin__ is None and len(bs.__origin__.__parameters__) > 0:
				for i in range(len(bs.__parameters__)):
					ors = bs.__origin__.__parameters__[i]
					if bs.__parameters__[i] != ors:
						param_map[ors] = bs.__parameters__[i]
			try:
				stack.extend(bs.__orig_bases__)
			except AttributeError:
				stack.extend(bs.__bases__)
	return None

def _select_Generic_superclass_parameters(subclass, superclass_origin):
	if subclass.__origin__ is superclass_origin:
		return subclass.__args__
	prms = _find_Generic_super_origin(subclass, superclass_origin)
	return [subclass.__args__[subclass.__origin__.__parameters__.index(prm)] \
			for prm in prms]

def _issubclass_Generic(subclass, superclass):
	# this method is based on code from typing module 3.5.2.2
	if subclass is None:
		return False
	if subclass in _extra_dict:
		subclass = _extra_dict[subclass]
	if isinstance(subclass, TupleMeta):
		tpl_prms = get_Tuple_params(subclass)
		if not tpl_prms is None and len(tpl_prms) == 0:
			# (This section is required because Empty shall not be
			# used on Tuples.)
			# an empty Tuple is any Sequence, regardless of type
			# note that we needn't consider superclass beeing a tuple,
			# because that should have been checked in _issubclass_Tuple
			return issubclass(typing.Sequence, superclass.__origin__)
		subclass = Sequence[make_Union(tpl_prms)]
	if isinstance(subclass, GenericMeta):
		# For a class C(Generic[T]) where T is co-variant,
		# C[X] is a subclass of C[Y] iff X is a subclass of Y.
		origin = superclass.__origin__
		#Formerly: if origin is not None and origin is subclass.__origin__:
		if origin is not None and _issubclass(subclass.__origin__, origin):
			assert len(superclass.__args__) == len(origin.__parameters__)
			if len(subclass.__args__) == len(origin.__parameters__):
				sub_args = subclass.__args__
			else:
				# We select the relevant subset of args by TypeVar-matching
				sub_args = _select_Generic_superclass_parameters(subclass, superclass.__origin__)
				assert len(sub_args) == len(origin.__parameters__)
			for p_self, p_cls, p_origin in zip(superclass.__args__,
											sub_args,
											origin.__parameters__):
				if isinstance(p_origin, TypeVar):
					if p_origin.__covariant__:
						# Covariant -- p_cls must be a subclass of p_self.
						if not _issubclass(p_cls, p_self):
							break
					elif p_origin.__contravariant__:
						# Contravariant.  I think it's the opposite. :-)
						if not _issubclass(p_self, p_cls):
							break
					else:
						# Invariant -- p_cls and p_self must equal.
						if p_self != p_cls:
							break
				else:
					# If the origin's parameter is not a typevar,
					# insist on invariance.
					if p_self != p_cls:
						break
			else:
				return True
			# If we break out of the loop, the superclass gets a chance.

		# I.e.: origin is None or not _issubclass(subclass.__origin__, origin)
		# In this case we must consider origin or subclass.__origin__ to be None
		# We treat param-values as unknown in the following sense:
		#   for covariant params: treat unknown more-or-equal specific than Any
		#   for contravariant param: Any more-or-equal specific than Unknown
		#   for invariant param: unknown never passes
		# if both are unknown:
		#   return False (?) (or NotImplemented? Or let a flag decide behavior?)
		if origin is None:
			if not pytypes.check_unbound_types:
				raise TypeError("Attempted to check unbound type(supeclass: "+str(superclass))
			if not subclass.__origin__ is None:
				if not type.__subclasscheck__(superclass, subclass.__origin__):
					return False
				prms = _find_Generic_super_origin(subclass.__origin__, superclass)
				args = _select_Generic_superclass_parameters(subclass, superclass)
				for i in range(len(prms)):
					if prms[i].__covariant__:
						if pytypes.strict_unknown_check:
							return False
					elif prms[i].__contravariant__:
						# Subclass-value must be wider than or equal to Any, i.e. must be Any:
						if not args[i] is Any:
							return False
					else:
						return False
				return True
			#else:
				# nothing to do here... (?)
		elif subclass.__origin__ is None:
			if not pytypes.check_unbound_types:
				raise TypeError("Attempted to check unbound type (subclass): "+str(subclass))
			if not type.__subclasscheck__(superclass.__origin__, subclass):
				return False
			prms = superclass.__origin__.__parameters__
			for i in range(len(prms)):
				if prms[i].__covariant__:
					# subclass-arg here is unknown, so in superclass only Any can pass:
					if not superclass.__args__[i] is Any:
						return False
				elif prms[i].__contravariant__:
					if pytypes.strict_unknown_check:
						return False
				else:
					return False
			return True
# 	Formerly: if super(GenericMeta, superclass).__subclasscheck__(subclass):
	if type.__subclasscheck__(superclass, subclass):
		return True
	if superclass.__extra__ is None or isinstance(subclass, GenericMeta):
		return False
	return _issubclass_2(subclass, superclass.__extra__)

def _issubclass_Tuple(subclass, superclass):
	# this method is based on code from typing module 3.5.2.2
	if subclass in _extra_dict:
		subclass = _extra_dict[subclass]
	if not isinstance(subclass, type):
		# To TypeError.
		return False
	if not isinstance(subclass, TupleMeta):
		if isinstance(subclass, GenericMeta):
			return _issubclass_Generic(subclass, superclass)
		elif is_Union(subclass):
			return all(_issubclass_Tuple(t, superclass)
					for t in get_Union_params(subclass))
	super_args = get_Tuple_params(superclass)
	if super_args is None:
		return True
	sub_args = get_Tuple_params(subclass)
	if sub_args is None:
		return False  # ???
	# Covariance.
	return (len(super_args) == len(sub_args) and
			all(_issubclass(x, p)
				for x, p in zip(sub_args, super_args)))

def _issubclass_Union(subclass, superclass):
	# this method is based on code from typing module 3.5.2.2
	super_args = get_Union_params(superclass)
	if super_args is None:
		return is_Union(subclass)
	elif is_Union(subclass):
		sub_args = get_Union_params(subclass)
		if sub_args is None:
			return False
		return all(_issubclass(c, superclass) for c in (sub_args))
	elif isinstance(subclass, TypeVar):
		if subclass in super_args:
			return True
		if subclass.__constraints__:
			return _issubclass(make_Union(subclass.__constraints__), superclass)
		return False
	else:
		return any(_issubclass(subclass, t) for t in super_args)

# This is just a crutch, because issubclass sometimes tries to be too smart.
# Note that this doesn't consider __subclasshook__ etc, so use with care!
def _has_base(cls, base):
	if cls is base:
		return True
	elif cls is None:
		return False
	for bs in cls.__bases__:
		if _has_base(bs, base):
			return True
	return False

def _issubclass(subclass, superclass):
	if superclass is Any:
		return True
	if subclass is Any:
		return superclass is Any
	if pytypes.apply_numeric_tower:
		if superclass is float and subclass is int:
			return True
		elif superclass is complex and \
				(subclass is int or subclass is float):
			return True
	if superclass in _extra_dict:
		superclass = _extra_dict[superclass]
	try:
		if _issubclass_2(subclass, Empty):
			if _issubclass_2(superclass, Container):
				return _issubclass_2(subclass.__args__[0], superclass)
			try:
				if _issubclass_2(superclass.__origin__, Container):
					return _issubclass_2(subclass.__args__[0], superclass.__origin__)
			except TypeError:
				pass
	except TypeError:
		pass
	return _issubclass_2(subclass, superclass)

def _issubclass_2(subclass, superclass):
	if isinstance(superclass, TupleMeta):
		return _issubclass_Tuple(subclass, superclass)
	if isinstance(superclass, GenericMeta):
		# We would rather use issubclass(superclass.__origin__, Mapping), but that's somehow erroneous
		if pytypes.covariant_Mapping and _has_base(superclass.__origin__, Mapping):
			return _issubclass_Mapping_covariant(subclass, superclass)
		else:
			return _issubclass_Generic(subclass, superclass)
	if is_Union(superclass):
		return _issubclass_Union(subclass, superclass)
	if is_Union(subclass):
		return all(_issubclass(t, superclass) for t in get_Union_params(subclass))
	if subclass in _extra_dict:
		subclass = _extra_dict[subclass]
	try:
		return issubclass(subclass, superclass)
	except TypeError:
		raise TypeError("Invalid type declaration: %s, %s" %
				(type_str(subclass), type_str(superclass)))

def _isinstance_Callable(obj, cls, check_callables = True):
	# todo: Let pytypes somehow create a Callable-scoped error message,
	# e.g. instead of
	#	Expected: Tuple[Callable[[str, int], str], str]
	#	Received: Tuple[function, str]
	# make
	#	Expected: Tuple[Callable[[str, int], str], str]
	#	Received: Tuple[Callable[[str, str], str], str]
	if not hasattr(obj, '__call__'):
		return False
	if has_type_hints(obj):
		slf_or_cls = util.is_method(obj) or util.is_classmethod(obj)
		parent_cls = util.get_class_that_defined_method(obj) if slf_or_cls else None
		argSig, resSig = _funcsigtypes(obj, slf_or_cls, parent_cls)
		argSig = _match_stub_type(argSig)
		resSig = _match_stub_type(resSig)
		clb_args, clb_res = get_Callable_args_res(cls)
		if not _issubclass(make_Tuple(clb_args), argSig):
			return False
		if not _issubclass(resSig, clb_res):
			return False
		return True
	return not check_callables

def _isinstance(obj, cls):
	# Special treatment if cls is Iterable[...]
	if isinstance(cls, GenericMeta) and cls.__origin__ is typing.Iterable:
		if not is_iterable(obj):
			return False
		itp = get_iterable_itemtype(obj)
		if itp is None:
			return not pytypes.check_iterables
		else:
			return _issubclass(itp, cls.__args__[0])
	if isinstance(cls, CallableMeta):
		return _isinstance_Callable(obj, cls)
	if obj == {}:
		return issubclass(typing.Dict, cls.__origin__)
	return _issubclass(deep_type(obj), cls)

def _make_generator_error_message(tp, gen, expected_tp, incomp_text):
	_cmp_msg_format = 'Expected: %s\nReceived: %s'
	# todo: obtain fully qualified generator name
	return gen.__name__+' '+incomp_text+':\n'+_cmp_msg_format \
				% (type_str(expected_tp), type_str(tp))

def generator_checker_py3(gen, gen_type):
	initialized = False
	sn = None
	try:
		while True:
			a = gen.send(sn)
			if initialized or not a is None:
				if not gen_type.__args__[0] is Any and not _isinstance(a, gen_type.__args__[0]):
					raise pytypes.ReturnTypeError(_make_generator_error_message(deep_type(a), gen,
							gen_type.__args__[0], 'has incompatible yield type'))
			initialized = True
			sn = yield a
			if not gen_type.__args__[1] is Any and not _isinstance(sn, gen_type.__args__[1]):
				raise pytypes.InputTypeError(_make_generator_error_message(deep_type(sn), gen,
						gen_type.__args__[1], 'has incompatible send type'))
	except StopIteration as st:
		# Python 3:
		# todo: Check if st.value is always defined (i.e. as None if not present)
		if not gen_type.__args__[2] is Any and not _isinstance(st.value, gen_type.__args__[2]):
				raise pytypes.ReturnTypeError(_make_generator_error_message(deep_type(st.value), gen,
						gen_type.__args__[2], 'has incompatible return type'))
		raise st

def generator_checker_py2(gen, gen_type):
	initialized = False
	sn = None
	while True:
		a = gen.send(sn)
		if initialized or not a is None:
			if not gen_type.__args__[0] is Any and not _isinstance(a, gen_type.__args__[0]):
				raise pytypes.ReturnTypeError(_make_generator_error_message(deep_type(a), gen,
						gen_type.__args__[0], 'has incompatible yield type'))
		initialized  = True
		sn = yield a
		if not gen_type.__args__[1] is Any and not _isinstance(sn, gen_type.__args__[1]):
			raise pytypes.InputTypeError(_make_generator_error_message(deep_type(sn), gen,
					gen_type.__args__[1], 'has incompatible send type'))

def _find_typed_base_method(meth, cls):
	meth0 = util._actualfunc(meth)
	for cls1 in util.mro(cls):
		if hasattr(cls1, meth0.__name__):
			fmeth = getattr(cls1, meth0.__name__)
			if has_type_hints(util._actualfunc(fmeth)):
				return fmeth, cls1
	return None, None

def annotations_func(func):
	'''Intended as decorator.
	'''
	if not has_type_hints(func):
		# What about defaults?
		func.__annotations__ =  {}
	func.__annotations__ = _get_type_hints(func,
			infer_defaults = False)
	return func

def annotations_class(cls):
	assert(isclass(cls))
	# To play it safe we avoid to modify the dict while iterating over it,
	# so we previously cache keys.
	# For this we don't use keys() because of Python 3.
	# Todo: Better use inspect.getmembers here
	keys = [key for key in cls.__dict__]
	for key in keys:
		memb = cls.__dict__[key]
		if (isfunction(memb) or ismethod(memb) or ismethoddescriptor(memb) or \
				isinstance(memb, property)):
			annotations_func(memb)
		elif isclass(memb):
			annotations_class(memb)
	return cls

def annotations_module(md):
	'''Intended to typecheck modules that were not annotated
	with @typechecked without modifying their code.
	md must be a module or a module name contained in sys.modules.
	'''
	if isinstance(md, str):
		if md in sys.modules:
			md = sys.modules[md]
			if md is None:
				return md
	assert(ismodule(md))
	if md.__name__ in _annotated_modules and \
			_annotated_modules[md.__name__] == len(md.__dict__):
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
			annotations_func(memb)
		elif isclass(memb) and memb.__module__ == md.__name__:
			annotations_class(memb)
	_annotated_modules[md.__name__] = len(md.__dict__)
	return md

def annotations(memb):
	'''Intended as decorator.
	'''
	if isfunction(memb) or ismethod(memb) or ismethoddescriptor(memb) or isinstance(memb, property):
		return annotations_func(memb)
	if isclass(memb):
		return annotations_class(memb)
	if ismodule(memb):
		return annotations_module(memb)
	return memb

def _catch_up_global_annotations():
	for mod_name in sys.modules:
		if not mod_name in _annotated_modules:
			try:
				md = sys.modules[mod_name]
			except KeyError:
				md = None
			if not md is None and ismodule(md):
				annotations_module(mod_name)
