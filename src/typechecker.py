'''
Created on 20.08.2016

@author: Stefan Richthofer
'''

# import os
import sys
# if os.name == 'java':
# 	sys.path.append("/usr/local/lib/python2.7/dist-packages")

import typing
from typing import Tuple, List, Union, Any
import inspect
from types import MethodType

# checked_modules = set()

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
		return _parse_typecomment_oneline(srclines[funcstart+1]), result[1:] if slf else result
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
		argString = ''.join(('(', ', '.join(['Any' if x is None else x for x in argTypes]), ')'))
	resString = typestring[splt+2:].strip()
	if selfType is None:
		return Tuple[eval(argString, globals)], eval(resString, globals)
	else:
		argTypes = [selfType]
		argTypes += eval(argString, globals)
		return Tuple[tuple(argTypes)], eval(resString, globals)

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

def has_typehints(func):
	# Todo: Respect @no_type_check etc
	tpHints = typing.get_type_hints(func)
	tpStr = _get_typestrings(func, False)
	return not (tpStr[0] is None and tpHints is None)

def _funcsigtypes(func, slf):
	tpHints = typing.get_type_hints(func)
	tpStr = _get_typestrings(func, slf)
	if tpStr[0] is None and (tpHints is None or not tpHints):
		# Maybe raise warning here
		return Any, Any
	globs = sys.modules[func.__module__].__dict__
	if not tpHints is None and tpHints:
		# We're running Python 3
		argNames = inspect.getfullargspec(_actualfunc(func)).args
		if slf:
			argNames = argNames[1:]
		resType = (Tuple[tuple(tpHints[t] for t in argNames)], tpHints['return'])
		if not tpStr[0] is None:
			resType2 = _funcsigtypesfromstring(*tpStr, globals = globs)
			if resType != resType2:
				raise TypeCheckSpecificationError("%s.%s declares incompatible types:\n"
					% (func.__module__, func.__name__)
					+ "Via hints:   %s\nVia comment: %s"
					% (str(resType), str(resType2)))
		return resType
	return _funcsigtypesfromstring(*tpStr, globals = globs)

def getargspecs(func):
	if hasattr(func, "ch_func"):
		return getargspecs(func.ch_func)
	elif hasattr(func, "ov_func"):
		return getargspecs(func.ov_func)
	if hasattr(inspect, 'getfullargspec'):
		return inspect.getfullargspec(func) # Python 3
	else:
		return inspect.getargspec(func)

def override(func):
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
					raise OverrideError("%s.%s.%s does not override any other method.\n"
							% (func.__module__, args[0].__class__.__name__, func.__name__))
				# Not yet support overloading
				# Check arg-count compatibility
				for ovcls in ovmro:
					ovf = getattr(ovcls, func.__name__)
					ovargs = getargspecs(ovf)
					d1 = 0 if ovargs.defaults is None else len(ovargs.defaults)
					d2 = 0 if argSpecs.defaults is None else len(argSpecs.defaults)
					if len(ovargs.args)-d1 < len(argSpecs.args)-d2 or len(ovargs.args) > len(argSpecs.args):
						raise OverrideError("%s.%s.%s cannot override %s.%s.%s:\n"
								% (func.__module__, args[0].__class__.__name__, func.__name__, ovf.__module__, ovcls.__name__, ovf.__name__)
								+ "Mismatching argument count. Base-method: %i+%i   submethod: %i+%i"
								% (len(ovargs.args)-d1, d1, len(argSpecs.args)-d2, d2))
				#check arg/res-type compatibility
				argSig, resSig = _funcsigtypes(func, True)
				if has_typehints(func):
					for ovcls in ovmro:
						ovf = getattr(ovcls, func.__name__)
						ovSig, ovResSig = _funcsigtypes(ovf, True)
						if has_typehints(ovf):
							if not issubclass(ovSig, argSig):
								raise OverrideError("%s.%s.%s cannot override %s.%s.%s.\n"
										% (func.__module__, args[0].__class__.__name__, func.__name__, ovf.__module__, ovcls.__name__, ovf.__name__)
										+ "Incompatible argument types: %s is not a subtype of %s."
										% (str(ovSig), str(argSig)))
							if not issubclass(resSig, ovResSig):
								raise OverrideError("%s.%s.%s cannot override %s.%s.%s.\n"
										% (func.__module__, args[0].__class__.__name__, func.__name__, ovf.__module__, ovcls.__name__, ovf.__name__)
										+ "Incompatible result types: %s is not a subtype of %s."
										% (str(resSig), str(ovResSig)))
			else:
				raise OverrideError("@override was applied to a non-method: %s.%s.\n"
					% (func.__module__, func.__name__)
					+ "that declares 'self' although not a method.")
		else:
			raise OverrideError("@override was applied to a function, not a method: %s.%s.\n"
					% (func.__module__, func.__name__))
		return func(*args, **kw)

	checker_ov.ov_func = func
	checker_ov.__func__ = func
	checker_ov.__name__ = func.__name__ # What sorts of evil might this bring over us?
	if hasattr(func, '__annotations__'):
		checker_ov.__annotations__ = func.__annotations__
	return checker_ov

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
						% (str(argSig), str(tp)))
			else:
				raise InputTypeError("classmethod %s.%s.%s called with incompatible types:\n"
					% (func.__module__, func_class.__name__, func.__name__)
					+ "Expected: %s\nGot:      %s"
					% (str(argSig), str(tp)))
		else:
			raise InputTypeError("%s.%s called with incompatible types:\n"
					% (func.__module__, func.__name__)
					+ "Expected: %s\nGot:      %s"
					% (str(argSig), str(tp)))
	return resSig # provide this by-product for potential future use

def _checkfuncresult(resSig, tp, func, slf, func_class):
	if not issubclass(tp, resSig):
		if slf: #Todo: Clarify if an @override-induced check caused this
			if hasattr(func, "im_class"):
				raise ReturnTypeError("%s.%s.%s returned incompatible type:\n"
						% (func.__module__, func.im_class.__name__, func.__name__)
						+ "Expected: %s\nGot:      %s"
						% (str(resSig), str(tp)))
			else:
				raise ReturnTypeError("classmethod %s.%s.%s returned incompatible type:\n"
						% (func.__module__, func_class.__name__, func.__name__)
						+ "Expected: %s\nGot:      %s"
						% (str(resSig), str(tp)))
		else:
			raise ReturnTypeError("%s.%s returned incompatible type:\n"
					% (func.__module__, func.__name__)
					+ "Expected: %s\nGot:      %s"
					% (str(resSig), str(tp)))

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

def typechecked(func):
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
					if has_typehints(_actualfunc(ffunc)):
						toCheck.append(ffunc)
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
	if hasattr(func, '__annotations__'):
		checker_tp.__annotations__ = func.__annotations__
	if clsm:
		return classmethod(checker_tp)
	elif stat:
		return staticmethod(checker_tp)
	else:
		return checker_tp


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
				print("Warning: non-method declaring self "+func0.__name__)
	return False

def get_types(func):
	clsm = type(func) == classmethod
	func0 = _actualfunc(func)

	# check consistency regarding special case with 'self'-keyword
	slf = is_method(func)
	if not slf:
		argNames = getargspecs(func0).args
		if len(argNames) > 0:
			if clsm:
				if argNames[0] != 'cls':
					print("Warning: classmethod using non-idiomatic argname "+func0.__name__)
	return _funcsigtypes(func0, slf)

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
