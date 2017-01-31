'''
Created on 12.12.2016

@author: Stefan Richthofer
'''

import pytypes, subprocess, hashlib, sys, os, types, inspect

_code_callable_dict = {}

def _check_python3_5_version():
	try:
		ver = subprocess.check_output([pytypes.python3_5_executable, '--version'])
		ver = ver[:-1].split(' ')[-1].split('.')
		return (int(ver[0]) >= 3 and int(ver[1]) >= 5)
	except Exception:
		return False

def _md5(fname):
	m = hashlib.md5()
	with open(fname, 'rb') as f:
		for chunk in iter(lambda: f.read(4096), b''):
			m.update(chunk)
	return m.hexdigest()

def _full_module_file_name_nosuffix(module_name):
	module = sys.modules[module_name]
	bn = os.path.basename(module.__file__).rpartition('.')[0]
	if not (module.__package__ is None or module.__package__ == ''):
		return module.__package__.replace('.', os.sep)+os.sep+bn
	else:
		return bn

def _find_files(file_name, search_paths):
	res = []
	if os.path.isfile(file_name):
		res.append(file_name)
	if search_paths is None:
		return res
	for path in search_paths:
		if not path.endswith(os.sep):
			file_path = path+os.sep+file_name
		else:
			file_path = path+file_name
		if os.path.isfile(file_path):
			res.append(file_path)
	return res

def getargspecs(func):
	if hasattr(func, 'ch_func'):
		return getargspecs(func.ch_func)
	elif hasattr(func, 'ov_func'):
		return getargspecs(func.ov_func)
	if hasattr(inspect, 'getfullargspec'):
		return inspect.getfullargspec(func) # Python 3
	else:
		return inspect.getargspec(func)

def _unchecked_backend(func):
	if hasattr(func, 'ov_func'):
		return _unchecked_backend(func.ov_func)
	elif hasattr(func, 'ch_func'):
		return _unchecked_backend(func.ch_func)
	else:
		return func

def _actualfunc(func):
	if type(func) == classmethod or type(func) == staticmethod:
		return _actualfunc(func.__func__)
	# Todo: maybe rename ov_func and ch_func also to __func__
	elif hasattr(func, 'ov_func'):
		return _actualfunc((func.ov_func))
	elif hasattr(func, 'ch_func'):
		return _actualfunc((func.ch_func))
	return func

def _get_class_nesting_list_for_staticmethod(staticmeth, module_or_class, stack, rec_set):
	if hasattr(module_or_class, _actualfunc(staticmeth).__name__):
		val = getattr(module_or_class, _actualfunc(staticmeth).__name__)
		if _unchecked_backend(staticmeth) is _unchecked_backend(val):
			return stack
	classes = [cl[1] for cl in inspect.getmembers(module_or_class, inspect.isclass)]
	mod_name = module_or_class.__module__ if inspect.isclass(module_or_class) \
			else module_or_class.__name__
	for cl in classes:
		if cl.__module__ == mod_name and not cl in rec_set:
			stack.append(cl)
			rec_set.add(cl)
			result = _get_class_nesting_list_for_staticmethod(staticmeth, cl, stack, rec_set)
			if not result is None:
				return result
			stack.pop()
	return None

def _get_class_nesting_list_py2(cls, module_or_class, stack, rec_set):
	classes = [cl[1] for cl in inspect.getmembers(module_or_class, inspect.isclass)]
	mod_name = module_or_class.__module__ if inspect.isclass(module_or_class) \
			else module_or_class.__name__
	for cl in classes:
		if cl.__module__ == mod_name and not cl in rec_set:
			if cl is cls:
				return stack
			stack.append(cl)
			rec_set.add(cl)
			result = _get_class_nesting_list_py2(cls, cl, stack, rec_set)
			if not result is None:
				return result
			stack.pop()
	return None

def _get_class_nesting_list(cls, module_or_class):
	if hasattr(cls, '__qualname__'):
		names = cls.__qualname__.split('.')
		cl = module_or_class
		res = []
		for name in names[:-1]:
			cl = getattr(cl, name)
			res.append(cl)
		return res
	else:
		res = _get_class_nesting_list_py2(cls, module_or_class, [], set())
		return [] if res is None else res

def get_staticmethod_qualname(staticmeth):
	func = _actualfunc(staticmeth)
	module = sys.modules[func.__module__]
	nst = _get_class_nesting_list_for_staticmethod(staticmeth, module, [], set())
	nst = [cl.__name__ for cl in nst]
	return '.'.join(nst)+'.'+func.__name__

def get_class_qualname(cls):
	if hasattr(cls, '__qualname__'):
		return cls.__qualname__
	module = sys.modules[cls.__module__]
	if hasattr(module, cls.__name__) and getattr(module, cls.__name__) is cls:
		return cls.__name__
	else:
		nst = _get_class_nesting_list(cls, module)
		nst.append(cls)
		nst = [cl.__name__ for cl in nst]
		return '.'.join(nst)
	return cls.__name__

def get_class_that_defined_method(meth):
	if is_classmethod(meth):
		return meth.__self__
	if hasattr(meth, 'im_class'):
		return meth.im_class
	elif hasattr(meth, '__qualname__'):
		cls = getattr(inspect.getmodule(meth),
				meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])
		if isinstance(cls, type):
			return cls
	raise ValueError(str(meth)+' is not a method.')

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
				print('Warning (is_method): non-method declaring self '+func0.__name__)
		else:
			return inspect.ismethod(func)
	return False

def is_class(obj):
	if sys.version_info.major >= 3:
		return isinstance(obj, type)
	else:
		return isinstance(obj, (types.TypeType, types.ClassType))

def is_classmethod(meth):
	if inspect.ismethoddescriptor(meth):
		return isinstance(meth, classmethod)
	if not inspect.ismethod(meth):
		return False
	if not is_class(meth.__self__):
		return False
	if not hasattr(meth.__self__, meth.__name__):
		return False
	return meth == getattr(meth.__self__, meth.__name__)

def _fully_qualified_func_name(func, slf_or_clsm, func_class, cls_name = None):
	func0 = _actualfunc(func)
	# Todo: separate classmethod/static method prefix from qualified_func_name
	if slf_or_clsm:
		# Todo: This can be simplified
		if (not func_class is None) and (not type(func) is classmethod) \
				and (not is_classmethod(func)):
			func = getattr(func_class, func.__name__)
		if ((not cls_name is None) or hasattr(func, 'im_class')) and not is_classmethod(func):
			return ('%s.%s.%s') % (func0.__module__,
					cls_name if not cls_name is None else get_class_qualname(func.im_class),
					func0.__name__)
		else:
			assert (not func_class is None or not cls_name is None)
			prefix = 'classmethod ' if is_classmethod(func) else ''
			return (prefix+'%s.%s.%s') % (func0.__module__,
					cls_name if not cls_name is None else get_class_qualname(func_class),
					func0.__name__)
	elif type(func) == staticmethod:
		return ('static method %s.%s') % (func0.__module__,
				get_staticmethod_qualname(func))
	else:
		return ('%s.%s') % (func0.__module__, func0.__name__)

def get_current_function(caller_level = 0):
	stck = inspect.stack()
	return get_callable_fq_for_code(stck[1+caller_level][0].f_code)[0]

def get_current_function_fq(caller_level = 0):
	stck = inspect.stack()
	return get_callable_fq_for_code(stck[1+caller_level][0].f_code)

def get_current_args(caller_level = 0):
	func = get_current_function(caller_level+1)
	stck = inspect.stack()
	lcs = stck[1+caller_level][0].f_locals
	return tuple([lcs[t] for t in getargspecs(func)[0]])

def get_callable_fq_for_code(code):
	if code in _code_callable_dict:
		return _code_callable_dict[code]
	md = inspect.getmodule(code, code.co_filename)
	if not md is None:
		nesting = []
		res, slf = _get_callable_fq_for_code(code, md, md, False, nesting)
		_code_callable_dict[code] = (res, nesting, slf)
		return res, nesting, slf
	else:
		return None, None, None

def _get_callable_fq_for_code(code, module_or_class, module, slf, nesting):
	keys = [key for key in module_or_class.__dict__]
	for key in keys:
		slf2 = slf
		obj = module_or_class.__dict__[key]
		if inspect.isfunction(obj) or inspect.ismethod(obj) or inspect.ismethoddescriptor(obj):
			if isinstance(obj, classmethod) or isinstance(obj, staticmethod):
				obj = obj.__func__
				slf2 = False
			try:
				if obj.__module__ == module.__name__ and _code_matches_func(obj, code):
					return getattr(module_or_class, key), slf2
			except AttributeError:
				try:
					if obj.__func__.__module__ == module.__name__ and \
							_code_matches_func(obj, code):
						return getattr(module_or_class, key), slf2
				except AttributeError:
					pass
		elif inspect.isclass(obj) and obj.__module__ == module.__name__:
			nesting.append(obj)
			res, slf2 = _get_callable_fq_for_code(code, obj, module, True, nesting)
			if not res is None:
				return res, slf2
			else:
				nesting.pop()
	return None, False

def _code_matches_func(func, code):
	if func.__code__ == code:
		return True
	else:
		try:
			return _code_matches_func(func.ch_func, code)
		except AttributeError:
			try:
				return _code_matches_func(func.ov_func, code)
			except AttributeError:
				try:
					return _code_matches_func(func.__func__, code)
				except AttributeError:
					return False
