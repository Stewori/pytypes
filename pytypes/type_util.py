'''
Created on 13.12.2016

@author: Stefan Richthofer
'''

import sys, types, inspect
import typing; from typing import Tuple, Dict, List, Set, Union, Any, Generator, Callable, \
		TupleMeta, GenericMeta, CallableMeta, Sequence, Mapping, TypeVar
from .stubfile_manager import _match_stub_type, as_stub_func_if_any
from .typecomment_parser import _get_typestrings, _funcsigtypesfromstring
from . import util
import pytypes

_extra_dict = {}
for tp in typing.__all__:
	tpa = getattr(typing, tp)
	try:
		_extra_dict[tpa.__extra__] = tpa
	except AttributeError:
		pass
if not tuple in _extra_dict:
	_extra_dict[tuple] = Tuple

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
		if tpl.__args__ is None:
			return None
		# Python 3.6
		return () if tpl.__args__[0] == () else tpl.__args__

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
	'''Python-version independent check if a type is typing.Union.
	Tested with CPython 2.7, 3.5 and 3.6.
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
		tpl = tuple(_deep_type(t, checked, depth-1) for t in obj)
		res = List[make_Union(tpl)]
	elif res == dict:
		tpl1 = tuple(_deep_type(t, checked, depth-1) for t in obj.keys())
		tpl2 = tuple(_deep_type(t, checked, depth-1) for t in obj.values())
		res = Dict[make_Union(tpl1), make_Union(tpl2)]
	elif res == set:
		tpl = tuple(_deep_type(t, checked, depth-1) for t in obj)
		res = Set[make_Union(tpl)]
	elif res == types.GeneratorType:
		res = get_generator_type(obj)
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
	try:
		return type_str(tp.__orig_class__)
	except AttributeError:
		pass
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
		prms = get_Tuple_params(args)
		for i in range(slf, len(argNames)):
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

def _funcsigtypes(func0, slf, func_class = None, globs = None):
	# Check for stubfile
	func = as_stub_func_if_any(util._actualfunc(func0), func0, func_class)

	try:
		tpHints = typing.get_type_hints(func)
	except AttributeError:
		tpHints = None
	tpStr = _get_typestrings(func, slf)
	if (tpStr is None or tpStr[0] is None) and (tpHints is None or not tpHints):
		# Maybe raise warning here
		return Any, Any
	if not (tpStr is None or tpStr[0] is None) and tpStr[0].find('...') != 0:
		numArgs = len(util.getargspecs(func).args) - 1 if slf else 0
		while len(tpStr[1]) < numArgs:
			tpStr[1].append(None)
	if globs is None:
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
		resType = (make_Tuple(tuple((tpHints[t] if t in tpHints else Any) for t in argNames)),
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
	if hasattr(subclass, '__orig_bases__'):
		return _find_Generic_super_origin_py36(subclass, superclass_origin)
	stack = [subclass]
	while len(stack) > 0:
		bs = stack.pop()
		if isinstance(bs, GenericMeta):
			if (bs.__origin__ is superclass_origin or \
					(bs.__origin__ is None and bs is superclass_origin)):
				return bs.__parameters__
			stack.extend(bs.__bases__)
	return None

def _find_Generic_super_origin_py36(subclass, superclass_origin):
	# Special version for Python 3.6
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
			stack.extend(bs.__orig_bases__)
	return None

def _select_Generic_superclass_parameters(subclass, superclass_origin):
	if subclass.__origin__ is superclass_origin:
		return subclass.__args__
	prms = _find_Generic_super_origin(subclass, superclass_origin)
	return [subclass.__args__[subclass.__origin__.__parameters__.index(prm)] \
			for prm in prms]

def _issubclass_Generic(subclass, superclass):
	if subclass is None:
		return False
	if subclass in _extra_dict:
		subclass = _extra_dict[subclass]
	if isinstance(subclass, TupleMeta):
		try:
			subclass = Sequence[make_Union(get_Tuple_params(subclass))]
		except AttributeError:
			# Python 3.6
			subclass = Sequence[make_Union(subclass.__args__)]
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

		# Now: origin is None or not _issubclass(subclass.__origin__, origin)
		# Todo: Based on a pytypes-flag, throw TypeError rather than deal with it
		# In this case we must consider origin or subclass.__origin__ to be None
		# Then treat param-values as unknown in the following sense:
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
						# Maybe return False here, depending on some strictness-flag?
						pass
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
					# Maybe return False here, depending on some strictness-flag?
					pass
				else:
					return False
			return True
# 	Formerly: if super(GenericMeta, superclass).__subclasscheck__(subclass):
	if type.__subclasscheck__(superclass, subclass):
		return True
	if superclass.__extra__ is None or isinstance(subclass, GenericMeta):
		return False
	return _issubclass_2(subclass, superclass.__extra__)

def _issubclass_Tuple_py36(subclass, superclass):
	# Intended only for Python 3.6+
	if subclass in _extra_dict:
		subclass = _extra_dict[subclass]
	if not isinstance(subclass, type):
# 		# To TypeError.
		return False
	if not isinstance(subclass, TupleMeta):
		return _issubclass_Generic(subclass, superclass)
	if superclass.__args__ is None:
		return True
	if subclass.__args__ is None:
		return False  # ???
	# Covariance.
	return (len(superclass.__args__) == len(subclass.__args__) and
			all(_issubclass(x, p)
				for x, p in zip(subclass.__args__, superclass.__args__)))

def _issubclass_Union_py36(subclass, superclass): #self, cls):
	# Intended only for Python 3.6+
	if superclass.__args__ is None:
		return is_Union(subclass)
	elif is_Union(subclass):
		if subclass.__args__ is None:
			return False
		return all(_issubclass(c, superclass) for c in (subclass.__args__))
	elif isinstance(subclass, TypeVar):
		if subclass in superclass.__args__:
			return True
		if subclass.__constraints__:
			return _issubclass(make_Union(subclass.__constraints__), superclass)
		return False
	else:
		return any(_issubclass(subclass, t) for t in superclass.__args__)

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
	return _issubclass_2(subclass, superclass)

def _issubclass_2(subclass, superclass):
	if isinstance(superclass, GenericMeta):
		if isinstance(superclass, TupleMeta):
			return _issubclass_Tuple_py36(subclass, superclass)
		# We would rather use issubclass(superclass.__origin__, Mapping), but that's somehow erroneous
		if pytypes.covariant_Mapping and _has_base(superclass.__origin__, Mapping):
			return _issubclass_Mapping_covariant(subclass, superclass)
		else:
			return _issubclass_Generic(subclass, superclass)
	if is_Union(superclass) and hasattr(superclass, '__args__'):
		return _issubclass_Union_py36(subclass, superclass)
	if is_Union(subclass) and hasattr(subclass, '__args__'):
		# Another special treatment for Python 3.6
		return all(_issubclass(t, superclass) for t in subclass.__args__)

	if subclass in _extra_dict:
		subclass = _extra_dict[subclass]

	return issubclass(subclass, superclass)

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
