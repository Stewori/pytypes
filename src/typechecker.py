'''
Created on 20.08.2016

@author: Stefan Richthofer
'''

import sys

import typing
from typing import Tuple, List, Union, Any
import inspect
import types
import re

check_override_at_runtime = False
check_override_at_class_definition_time = True

not_type_checked = set()

class TypeCheckError(Exception): pass
class TypeCheckSpecificationError(Exception): pass
class InputTypeError(TypeCheckError): pass
class ReturnTypeError(TypeCheckError): pass
class OverrideError(TypeCheckError): pass

def _striptrailingcomment(s):
	pos = s.find('#')
	if pos > -1:
		return s[:pos].strip()
	else:
		return s.strip()

def _parse_typecomment_oneline(line):
	commStart = line.find('#')
	tp_delim = "type"
	if commStart > -1 and len(line) > commStart+1:
		comment = line[commStart+1:].strip()
		if (comment.startswith(tp_delim) and len(comment) > len(tp_delim)+1):
			comment = comment[len(tp_delim):].strip()
			if (comment.startswith(':')):
				comment = comment[1:].strip()
				if len(comment) > 0:
					return comment
	return None

# def _get_typestring(obj):
# 	srclines = inspect.getsourcelines(obj)[0]
# 	funcstart = 0
# 	startInit = False
# 	for line in srclines:
# 		ln = _striptrailingcomment(line)
# 		if ln.startswith("def "):
# 			startInit = True
# 		if startInit and ln.endswith(":"):
# 			if (ln[:-1].strip().endswith(")")):
# 				break
# 		funcstart += 1
# 	if len(srclines) <= funcstart:
# 		return None
# 	res = _parse_typecomment_oneline(srclines[funcstart])
# 	if not res is None:
# 		return res
# 	if len(srclines) > funcstart+1 and srclines[funcstart+1].strip()[0] == '#':
# 		#return srclines[funcstart+1][srclines[funcstart+1].find(tp_delim)+len(tp_delim):].strip()
# 		return _parse_typecomment_oneline(srclines[funcstart+1])
# 	else:
# 		return None

def _get_typestrings(obj, slf):
	srclines = inspect.getsourcelines(obj)[0]
	funcstart = 0
	startInit = False
	result = []
	for line in srclines:
		ln = _striptrailingcomment(line)
		if len(ln) > 0:
			if ln.startswith("def "):
				startInit = True
			if startInit:
				if ln.endswith(":"):
					if ln[:-1].strip().endswith(")") or ln.find('->') != -1:
						break
				elif not ln[-1] == '(':
					result.append(_parse_typecomment_oneline(line))
		funcstart += 1
	if len(srclines) <= funcstart:
		return None
	res = _parse_typecomment_oneline(srclines[funcstart])
	if not res is None:
		return res, result[1:] if slf else result
	if len(srclines) > funcstart+1 and srclines[funcstart+1].strip()[0] == '#':
		res= _parse_typecomment_oneline(srclines[funcstart+1]), result[1:] if slf else result
		return res
	else:
		return None, result[1:] if slf else result

def _isargsellipsis(argStr):
	return argStr[1:-1].strip() == '...'

def _funcsigtypesfromstring(typestring, argTypes = None, globals = globals(), selfType = None):
	splt = typestring.find('->')
	if splt == -1:
		return None
	argString = typestring[:splt].strip()
	if _isargsellipsis(argString):
# 		useEllipsis = True
		argString = ''.join(('(', ', '.join(['Any' if x is None else x for x in argTypes]), ')'))
# 	else:
# 		useEllipsis = False
	resString = typestring[splt+2:].strip()
	if selfType is None:
		tpl = Tuple[eval(argString, globals)]
	else:
		argTypes = [selfType]
		argTypes += eval(argString, globals)
		tpl =  Tuple[tuple(argTypes)]
# 	if useEllipsis:
# 		tpl.__tuple_use_ellipsis__ = True
	return tpl, eval(resString, globals)

def deep_type(obj):
	res = type(obj)
	if res == tuple:
		res = Tuple[tuple(deep_type(t) for t in obj)]
	elif res == list:
		res = List[Union[tuple(deep_type(t) for t in obj)]]
	return res

def _methargtype(obj):
	assert(type(obj) == tuple)
	return Tuple[tuple(deep_type(t) for t in obj[1:])]

def has_type_hints(func):
	tpHints = typing.get_type_hints(func)
	tpStr = _get_typestrings(func, False)
	return not (tpStr[0] is None and (tpHints is None or not tpHints))

def _funcsigtypes(func, slf):
	tpHints = typing.get_type_hints(func)
	tpStr = _get_typestrings(func, slf)
	if tpStr[0] is None and (tpHints is None or not tpHints):
		# Maybe raise warning here
		return Any, Any
	if not tpStr[0] is None and tpStr[0].find('...') != 0:
		numArgs = len(getargspecs(func).args) - 1 if slf else 0
		while len(tpStr[1]) < numArgs:
			tpStr[1].append(None)
	globs = sys.modules[func.__module__].__dict__
	if not tpHints is None and tpHints:
		# We're running Python 3
		argNames = inspect.getfullargspec(_actualfunc(func)).args
		if slf:
			argNames = argNames[1:]
		resType = (Tuple[tuple((tpHints[t] if t in tpHints else Any) for t in argNames)],
				tpHints['return'])
		if not tpStr[0] is None:
			resType2 = _funcsigtypesfromstring(*tpStr, globals = globs)
			if resType != resType2:
				raise TypeCheckSpecificationError("%s.%s declares incompatible types:\n"
					% (func.__module__, func.__name__)
					+ "Via hints:   %s\nVia comment: %s"
					% (_type_str(resType), _type_str(resType2)))
		return resType
	res = _funcsigtypesfromstring(*tpStr, globals = globs)
	return res

def getargspecs(func):
	if hasattr(func, "ch_func"):
		return getargspecs(func.ch_func)
	elif hasattr(func, "ov_func"):
		return getargspecs(func.ov_func)
	if hasattr(inspect, 'getfullargspec'):
		return inspect.getfullargspec(func) # Python 3
	else:
		return inspect.getargspec(func)

def _check_override_types(method, meth_types, class_name, base_method, base_class_name):
	base_types = _funcsigtypes(base_method, True)
	if has_type_hints(base_method):
		if not issubclass(base_types[0], meth_types[0]):
			raise OverrideError("%s.%s.%s cannot override %s.%s.%s.\n"
					% (method.__module__, class_name, method.__name__, base_method.__module__, base_class_name, base_method.__name__)
					+ "Incompatible argument types: %s is not a subtype of %s."
					% (_type_str(base_types[0]), _type_str(meth_types[0])))
		if not issubclass(meth_types[1], base_types[1]):
			raise OverrideError("%s.%s.%s cannot override %s.%s.%s.\n"
					% (method.__module__, class_name, method.__name__, base_method.__module__, base_class_name, base_method.__name__)
					+ "Incompatible result types: %s is not a subtype of %s."
					% (_type_str(meth_types[1]), _type_str(base_types[1])))

def _check_override_argspecs(method, argSpecs, class_name, base_method, base_class_name):
	ovargs = getargspecs(base_method)
	d1 = 0 if ovargs.defaults is None else len(ovargs.defaults)
	d2 = 0 if argSpecs.defaults is None else len(argSpecs.defaults)
	if len(ovargs.args)-d1 < len(argSpecs.args)-d2 or len(ovargs.args) > len(argSpecs.args):
		raise OverrideError("%s.%s.%s cannot override %s.%s.%s:\n"
				% (method.__module__, class_name, method.__name__, base_method.__module__, base_method.__name__, base_class_name)
				+ "Mismatching argument count. Base-method: %i+%i   submethod: %i+%i"
				% (len(ovargs.args)-d1, d1, len(argSpecs.args)-d2, d2))

def _no_base_method_error(method):
	return OverrideError("%s in %s does not override any other method.\n"
					% (method.__name__, method.__module__))

def _function_instead_of_method_error(method):
	return OverrideError("@override was applied to a function, not a method: %s.%s.\n"
					% (method.__module__, method.__name__))

def override(func):
	if check_override_at_class_definition_time:
		# We need some trickery here, because details of the class are not yet available
		# as it is just getting defined. Luckily we can get base-classes via inspect.stack():
# 		print("check_override_on_class_definition_time...")

		stack = inspect.stack()
		try:
			base_classes = re.search(r'class.+\((.+)\)\s*\:', stack[2][4][0]).group(1)
		except IndexError:
			raise _function_instead_of_method_error(func)
		meth_cls_name = stack[1][3]

		# handle multiple inheritance
		base_classes = [s.strip() for s in base_classes.split(',')]
		if not base_classes:
			raise ValueError('@override: unable to determine base class') 
	
		# stack[0]=overrides, stack[1]=inside class def'n, stack[2]=outside class def'n
		derived_class_locals = stack[2][0].f_locals
		derived_class_globals = stack[2][0].f_globals
	
		# replace each class name in base_classes with the actual class type
		for i, base_class in enumerate(base_classes):
			if '.' not in base_class:
				if base_class in derived_class_locals:
					base_classes[i] = derived_class_locals[base_class]
				else:
					base_classes[i] = derived_class_globals[base_class]
			else:
				components = base_class.split('.')
				# obj is either a module or a class
				if components[0] in derived_class_locals:
					obj = derived_class_locals[components[0]]
				else:
					obj = derived_class_globals[components[0]]
				for c in components[1:]:
					assert(inspect.ismodule(obj) or inspect.isclass(obj))
					obj = getattr(obj, c)
				base_classes[i] = obj

		found = False
		meth_types = _funcsigtypes(func, True) if has_type_hints(func) else None
		argSpecs = getargspecs(func)
		for cls in base_classes:
			if hasattr(cls, func.__name__):
				found = True
				base_method = getattr(cls, func.__name__)
				_check_override_argspecs(func, argSpecs, meth_cls_name, base_method, cls.__name__)
				if not meth_types is None:
					_check_override_types(func, meth_types, meth_cls_name, base_method, cls.__name__)
		if not found:
			raise _no_base_method_error(func)

	if check_override_at_runtime:
		def checker_ov(*args, **kw):
			argSpecs = getargspecs(func)
			if len(argSpecs.args) > 0 and argSpecs.args[0] == 'self':
				if hasattr(args[0].__class__, func.__name__) and \
						inspect.ismethod(getattr(args[0], func.__name__)):
					ovmro = []
					for mc in args[0].__class__.__mro__[1:]:
						if hasattr(mc, func.__name__):
							ovf = getattr(mc, func.__name__)
							ovmro.append(mc)
					if len(ovmro) == 0:
						raise _no_base_method_error(func)
					# Not yet support overloading
					# Check arg-count compatibility
					for ovcls in ovmro:
						ovf = getattr(ovcls, func.__name__)
						_check_override_argspecs(func, argSpecs, args[0].__class__.__name__, ovf, ovcls.__name__)
					#check arg/res-type compatibility
					meth_types = _funcsigtypes(func, True)
					if has_type_hints(func):
						for ovcls in ovmro:
							ovf = getattr(ovcls, func.__name__)
							_check_override_types(func, meth_types, args[0].__class__.__name__, ovf, ovcls.__name__)
				else:
					raise OverrideError("@override was applied to a non-method: %s.%s.\n"
						% (func.__module__, func.__name__)
						+ "that declares 'self' although not a method.")
			else:
				raise _function_instead_of_method_error(func)
			return func(*args, **kw)
	
		checker_ov.ov_func = func
		checker_ov.__func__ = func
		checker_ov.__name__ = func.__name__ # What sorts of evil might this bring over us?
		checker_ov.__module__ = func.__module__
		if hasattr(func, '__annotations__'):
			checker_ov.__annotations__ = func.__annotations__
		if hasattr(func, '__qualname__'):
			checker_ov.__qualname__ = func.__qualname__
		return checker_ov
	else:
		return func

def _type_str(tp):
	return str(tp).replace("typing.", "")

def _checkfunctype(tp, func, slf, func_class):
	argSig, resSig = _funcsigtypes(func, slf)
	if not issubclass(tp, argSig):
		if slf: #Todo: Clarify if an @override-induced check caused this
			#assert(hasattr(func, "im_class") or type(func) == classmethod)
			# Todo: Python3 misconcepts method as classmethod here, because it doesn't
			# detect it as bound method, because ov_checker or tp_checker obfuscate it
			if hasattr(func, "im_class"):
				raise InputTypeError("%s.%s.%s called with incompatible types:\n"
						% (func.__module__, func.im_class.__name__, func.__name__)
						+ "Expected: %s\nGot:      %s"
						% (_type_str(argSig), _type_str(tp)))
			else:
				raise InputTypeError("classmethod %s.%s.%s called with incompatible types:\n"
					% (func.__module__, func_class.__name__, func.__name__)
					+ "Expected: %s\nGot:      %s"
					% (_type_str(argSig), _type_str(tp)))
		else:
			raise InputTypeError("%s.%s called with incompatible types:\n"
					% (func.__module__, func.__name__)
					+ "Expected: %s\nGot:      %s"
					% (_type_str(argSig), _type_str(tp)))
	return resSig # provide this by-product for potential future use

def _checkfuncresult(resSig, tp, func, slf, func_class):
	if not issubclass(tp, resSig):
		if slf: #Todo: Clarify if an @override-induced check caused this
			if hasattr(func, "im_class"):
				raise ReturnTypeError("%s.%s.%s returned incompatible type:\n"
						% (func.__module__, func.im_class.__name__, func.__name__)
						+ "Expected: %s\nGot:      %s"
						% (_type_str(resSig), _type_str(tp)))
			else:
				raise ReturnTypeError("classmethod %s.%s.%s returned incompatible type:\n"
						% (func.__module__, func_class.__name__, func.__name__)
						+ "Expected: %s\nGot:      %s"
						% (_type_str(resSig), _type_str(tp)))
		else:
			raise ReturnTypeError("%s.%s returned incompatible type:\n"
					% (func.__module__, func.__name__)
					+ "Expected: %s\nGot:      %s"
					% (_type_str(resSig), _type_str(tp)))

def _actualfunc(func):
	if type(func) == classmethod or type(func) == staticmethod:
		return _actualfunc(func.__func__)
	# Todo: maybe rename ov_func and ch_func also to __func__
	if hasattr(func, "ov_func"):
		return _actualfunc(func.ov_func)
	elif hasattr(func, "ch_func"):
		return _actualfunc(func.ch_func)
	else:
		return func

def typechecked_func(func, force = False):
	assert(inspect.isfunction(func) or inspect.ismethod(func) or inspect.ismethoddescriptor(func))
	if not force and is_no_type_check(func):
		return func
	clsm = type(func) == classmethod
	stat = type(func) == staticmethod
	func0 = _actualfunc(func)

	if hasattr(func, "ov_func"):
		checkParents = True
	else:
		checkParents = False

	def checker_tp(*args, **kw):
		# check consistency regarding special case with 'self'-keyword
		slf = False
		argNames = getargspecs(func0).args
		if len(argNames) > 0:
			if clsm:
				if argNames[0] != 'cls':
					print("Warning: classmethod using non-idiomatic argname "+func0.__name__)
				tp = _methargtype(args)
			elif argNames[0] == 'self':
				if hasattr(args[0].__class__, func0.__name__) and \
						inspect.ismethod(getattr(args[0], func0.__name__)):
					tp = _methargtype(args)
					slf = True
				else:
					print("Warning: non-method declaring self "+func0.__name__)
					tp = deep_type(args)
			else:
				tp = deep_type(args)
		else:
			tp = deep_type(args)
			
		if checkParents:
			if not slf:
				raise OverrideError("@override with non-instancemethod not supported: %s.%s.%s.\n"
					% (func0.__module__, args[0].__class__.__name__, func0.__name__))
			toCheck = []
			for cls in args[0].__class__.__mro__:
				if hasattr(cls, func0.__name__):
					ffunc = getattr(cls, func0.__name__)
					if has_type_hints(_actualfunc(ffunc)):
						toCheck.append(_actualfunc(ffunc))
		else:
			toCheck = (func0,)
		resSigs = []
		for ffunc in toCheck:
			resSigs.append(_checkfunctype(tp, ffunc, slf or clsm, args[0].__class__))

		# perform backend-call:
		if clsm or stat:
			res = func.__func__(*args, **kw)
		else:
			res = func(*args, **kw)

		tp = deep_type(res)
		for i in range(len(resSigs)):
			_checkfuncresult(resSigs[i], tp, toCheck[i], slf, args[0].__class__)
		return res

	checker_tp.ch_func = func
	checker_tp.__func__ = func
	checker_tp.__name__ = func0.__name__ # What sorts of evil might this bring over us?
	checker_tp.__module__ = func0.__module__
	if hasattr(func, '__annotations__'):
		checker_tp.__annotations__ = func.__annotations__
	if hasattr(func, '__qualname__'):
		checker_tp.__qualname__ = func.__qualname__
	if clsm:
		return classmethod(checker_tp)
	elif stat:
		return staticmethod(checker_tp)
	else:
		return checker_tp

def typechecked_class(cls, force = False, force_recursive = False):
	assert(inspect.isclass(cls))
	if not force and is_no_type_check(cls):
		return cls
	# To play it safe we avoid to modify the dict while iterating over it,
	# so we previously cache keys.
	# For this we don't use keys() because of Python 3.
	keys = [key for key in cls.__dict__]
	for key in keys:
		obj = cls.__dict__[key]
		if force_recursive or not is_no_type_check(obj):
			if inspect.isfunction(obj) or inspect.ismethod(obj) or inspect.ismethoddescriptor(obj):
				setattr(cls, key, typechecked_func(obj, force_recursive))
			elif inspect.isclass(obj):
				setattr(cls, key, typechecked_class(obj, force_recursive, force_recursive))
	return cls

# Todo: Write tests for this
def typechecked_module(md, force_recursive = False):
	'''
	Intended to typecheck modules that were not annotated with @typechecked without
	modifying their code.
	'''
	assert(inspect.ismodule(md))
	# To play it safe we avoid to modify the dict while iterating over it,
	# so we previously cache keys.
	# For this we don't use keys() because of Python 3.
	keys = [key for key in md.__dict__]
	for key in keys:
		obj = md.__dict__[key]
		if force_recursive or not is_no_type_check(obj):
			if inspect.isfunction(obj) or inspect.ismethod(obj) or inspect.ismethoddescriptor(obj):
				setattr(md, key, typechecked_func(obj, force_recursive))
			elif inspect.isclass(obj):
				setattr(md, key, typechecked_class(obj, force_recursive, force_recursive))

def typechecked(obj):
	if is_no_type_check(obj):
		return obj
	if inspect.isfunction(obj) or inspect.ismethod(obj) or inspect.ismethoddescriptor(obj):
		return typechecked_func(obj)
	if inspect.isclass(obj):
		return typechecked_class(obj)
	return obj

def no_type_check(obj):
	try:
		return typing.no_type_check(obj)
	except(AttributeError):
		not_type_checked.add(obj)
		return obj

def is_no_type_check(obj):
	return (hasattr(obj, "__no_type_check__") and obj.__no_type_check__) or obj in not_type_checked

def get_class_that_defined_method(meth):
	if hasattr(meth, "im_class"):
		return meth.im_class
	elif hasattr(meth, "__qualname__"):
		cls = getattr(inspect.getmodule(meth),
				meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])
		if isinstance(cls, type):
			return cls
	raise ValueError(str(meth)+" is not a method.")

def is_method(func):
	func0 = _actualfunc(func)
	argNames = getargspecs(func0).args
	if len(argNames) > 0:
		if argNames[0] == 'self':
			if inspect.ismethod(func):
				return True
			elif sys.version_info.major >= 3:
				# In Python3 there are no unbound methods, so we count as method,
				# if first arg is called 'self' 
				return True
			else:
				print("Warning (is_method): non-method declaring self "+func0.__name__)
	return False

def is_class(obj):
	if sys.version_info.major >= 3:
		return isinstance(obj, type)
	else:
		return isinstance(obj, (types.TypeType, types.ClassType))

def is_classmethod(meth):
	if not inspect.ismethod(meth):
		return False
	if not is_class(meth.__self__):
		return False
	if not hasattr(meth.__self__, meth.__name__):
		return False
	return meth == getattr(meth.__self__, meth.__name__)

def get_types(func):
	return _get_types(func, is_classmethod(func), is_method(func))

def _get_types(func, clsm, slf):
	func0 = _actualfunc(func)

	# check consistency regarding special case with 'self'-keyword
	if not slf:
		argNames = getargspecs(func0).args
		if len(argNames) > 0:
			if clsm:
				if argNames[0] != 'cls':
					print("Warning: classmethod using non-idiomatic argname "+func0.__name__)
	return _funcsigtypes(func0, slf or clsm)

def get_type_hints(func):
	'''
	Resembles typing.get_type_hints, but is also workable on Python 2.
	'''
	slf = 1 if is_method(func) else 0
	args, res = get_types(func)
	argNames = getargspecs(func).args
	result = {}
	for i in range(slf, len(argNames)):
		result[argNames[i]] = args.__tuple_params__[i-slf]
	result['return'] = res
	return result
