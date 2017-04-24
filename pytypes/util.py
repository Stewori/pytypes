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

def get_required_kwonly_args(argspecs):
	try:
		kwonly = argspecs.kwonlyargs
		if argspecs.kwonlydefaults is None:
			return kwonly
		res = []
		for name in kwonly:
			if not name in argspecs.kwonlydefaults:
				res.append(name)
		return res
	except AttributeError:
		return []

def getargnames(argspecs):
	args = argspecs.args
	vargs = argspecs.varargs
	try:
		kw = argspecs.keywords
	except AttributeError:
		kw = argspecs.varkw
	try:
		kwonly = argspecs.kwonlyargs
	except AttributeError:
		kwonly = None
	res = []
	if not args is None:
		res.extend(args)
	if not vargs is None:
		res.append(vargs)
	if not kwonly is None:
		res.extend(kwonly)
	if not kw is None:
		res.append(kw)
	return res

def getargskw(args, kw, argspecs):
	return _getargskw(args, kw, argspecs)[0]

def _getargskw(args, kw, argspecs):
	res = []
	err = False
	try:
		kwds = argspecs.keywords
	except AttributeError:
		kwds = argspecs.varkw
	if not kwds is None:
		used = set()
	if len(args) > len(argspecs.args):
		if not argspecs.varargs is None:
			# include the remaining args as varargs
			res.extend(args[:len(argspecs.args)])
			res.append(args[len(argspecs.args):])
		else:
			# note an err, but still add all args for tracking
			err = True
			res.extend(args)
	elif len(args) < len(argspecs.args):
		res.extend(args)
		# we'll try to get the remaining args from kw or defaults
		ipos = -len(args)+len(res)
		for name in argspecs.args[len(args):]:
			if name in kw:
				res.append(kw[name])
				if not kwds is None:
					used.add(name)
			elif not argspecs.defaults is None:
				# Todo: Guard failure here and set err accordingly
				res.append(argspecs.defaults[ipos])
			else:
				err = True
			ipos += 1
		if not argspecs.varargs is None:
			res.append(tuple())
	else:
		res.extend(args)
		if not argspecs.varargs is None:
			res.append(tuple())
	try:
		# eventually process kw-only args
		ipos = -len(argspecs.kwonlyargs)
		for name in argspecs.kwonlyargs:
			if name in kw:
				res.append(kw[name])
				if not kwds is None:
					used.add(name)
			else:
				# Todo: Guard failure here and set err accordingly
#				This assumed kwonlydefaults to be a list:
#				if not argspecs.kwonlydefaults is None and \
#						len(argspecs.kwonlydefaults) > ipos:
#					res.append(argspecs.kwonlydefaults[ipos])
				if not argspecs.kwonlydefaults is None and \
						name in argspecs.kwonlydefaults:
					res.append(argspecs.kwonlydefaults[name])
				else:
					err = True
			ipos += 1
	except AttributeError:
		pass
	except TypeError:
		err = True
	if not kwds is None:
		if len(used) > 0:
			kw2 = {}
			if len(used) < len(kw):
				for name in kw:
					if not name in used:
						kw2[name] = kw[name]
			res.append(kw2)
		else:
			res.append(kw)
	return tuple(res), err

def fromargskw(argskw, argspecs, slf_or_clsm = False):
	res_args = argskw
	try:
		kwds = argspecs.keywords
	except AttributeError:
		kwds = argspecs.varkw
	if not kwds is None:
		res_kw = argskw[-1]
		res_args = argskw[:-1]
	else:
		res_kw = None
	if not argspecs.varargs is None:
		vargs_pos = (len(argspecs.args)-1) \
				if slf_or_clsm else len(argspecs.args)
		if vargs_pos > 0:
			res_lst = list(argskw[:vargs_pos])
			res_lst.extend(argskw[vargs_pos])
			res_args = tuple(res_lst)
		else:
			res_args = argskw[0]
	try:
		if len(argspecs.kwonlyargs) > 0:
			res_kw = {} if res_kw is None else dict(res_kw)
			ipos = -len(argspecs.kwonlyargs) - (0 if kwds is None else 1)
			for name in argspecs.kwonlyargs:
				res_kw[name] = argskw[ipos]
				ipos += 1
	except AttributeError:
		pass
	if res_kw is None:
		res_kw = {}
	return res_args, res_kw

def _unchecked_backend(func):
	if hasattr(func, 'ov_func'):
		return _unchecked_backend(func.ov_func)
	elif hasattr(func, 'ch_func'):
		return _unchecked_backend(func.ch_func)
	else:
		return func

def _actualfunc(func, prop_getter = False):
	if type(func) == classmethod or type(func) == staticmethod:
		return _actualfunc(func.__func__, prop_getter)
	if isinstance(func, property):
		if prop_getter: # force getter
			return _actualfunc(func.fget, prop_getter)
		else: # auto decide
			return _actualfunc(func.fget if func.fset is None else func.fset, prop_getter)
	# Todo: maybe rename ov_func and ch_func also to __func__
	elif hasattr(func, 'ov_func'):
		return _actualfunc((func.ov_func), prop_getter)
	elif hasattr(func, 'ch_func'):
		return _actualfunc((func.ch_func), prop_getter)
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
	argNames = getargnames(getargspecs(func0))
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
	return _get_current_function_fq(1+caller_level)[0][0]

def _get_current_function_fq(caller_level = 0):
	stck = inspect.stack()
	code = stck[1+caller_level][0].f_code
	res = get_callable_fq_for_code(code)
	if res[0] is None and len(stck) > 2:
		res = get_callable_fq_for_code(code, stck[2+caller_level][0].f_locals)
	return res, code

def get_current_args(caller_level = 0, func = None, argNames = None):
	if argNames is None:
		argNames = getargnames(getargspecs(func))
	if func is None:
		func = get_current_function(caller_level+1)
	if isinstance(func, property):
		func = func.fget if func.fset is None else func.fset
	stck = inspect.stack()
	lcs = stck[1+caller_level][0].f_locals
	return tuple([lcs[t] for t in argNames])

def get_callable_fq_for_code(code, locals_dict = None):
	if code in _code_callable_dict:
		res = _code_callable_dict[code]
		if not res[0] is None or locals_dict is None:
			return res
	md = inspect.getmodule(code, code.co_filename)
	if not md is None:
		nesting = []
		res, slf = _get_callable_fq_for_code(code, md, md, False, nesting)
		if res is None and not locals_dict is None:
			nesting = []
			res, slf = _get_callable_from_locals(code, locals_dict, md, False, nesting)
		else:
			_code_callable_dict[code] = (res, nesting, slf)
		return res, nesting, slf
	else:
		return None, None, None

def _get_callable_from_locals(code, locals_dict, module, slf, nesting):
	keys = [key for key in locals_dict]
	for key in keys:
		slf2 = slf
		obj = locals_dict[key]
		if inspect.isfunction(obj):
			try:
				if obj.__module__ == module.__name__ and _code_matches_func(obj, code):
					return obj, slf2
			except AttributeError:
				try:
					if obj.__func__.__module__ == module.__name__ and \
							_code_matches_func(obj, code):
						return obj, slf2
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

def _get_callable_fq_for_code(code, module_or_class, module, slf, nesting):
	keys = [key for key in module_or_class.__dict__]
	for key in keys:
		slf2 = slf
		obj = module_or_class.__dict__[key]
		if inspect.isfunction(obj) or inspect.ismethod(obj) \
				or inspect.ismethoddescriptor(obj) or isinstance(obj, property):
			if isinstance(obj, classmethod) or isinstance(obj, staticmethod):
				obj = obj.__func__
				slf2 = False
			elif isinstance(obj, property):
				slf2 = True
				if not obj.fset is None:
					try:
						if obj.fset.__module__ == module.__name__ and \
								_code_matches_func(obj.fset, code):
							return getattr(module_or_class, key), slf2
					except AttributeError:
						try:
							if obj.fset.__func__.__module__ == module.__name__ and \
									_code_matches_func(obj.fset, code):
								return getattr(module_or_class, key), slf2
						except AttributeError:
							pass
				obj = obj.fget
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

def old_mro(clss, dest = []):
	if not clss in dest:
		dest.append(clss)
		for clss2 in clss.__bases__:
			old_mro(clss2, dest)
	return dest

def new_mro(clss, dest = []):
	# not very efficient, but should be rarely used anyway
	if not clss in dest:
		dest.append(clss)
	for clss2 in clss.__bases__:
		if not clss2 in dest:
			dest.append(clss2)
	for clss2 in clss.__bases__:
		new_mro(clss2, dest)
	return dest

def mro(clss):
	try:
		return clss.__mro__
	except AttributeError:
		return old_mro(clss)

def _has_base_method(meth, cls):
	meth0 = _actualfunc(meth)
	for cls in mro(cls):
		if hasattr(cls, meth0.__name__):
			fmeth = getattr(cls, meth0.__name__)
			if inspect.ismethod(fmeth) or inspect.ismethoddescriptor(fmeth):
				return True
	return False
