'''
Created on 20.08.2016

@author: Stefan Richthofer
'''

import sys, typing, inspect, types, re, os, imp, subprocess
import warnings, tempfile, hashlib, atexit
from typing import Tuple, List, Set, Dict, Union, Any
from inspect import isclass, ismodule, isfunction, ismethod, ismethoddescriptor

if sys.version_info.major >= 3:
	import builtins
else:
	import __builtin__ as builtins

enabled = False
def set_enabled(flag = True):
	global enabled
	enabled = flag
	return enabled

# This way we glue typechecking to activeness of the assert-statement by default,
# no matter what conditions it depends on (or will depend on, e.g. currently -O flag).
assert(set_enabled())

stub_descr = ('.pyi', 'r', imp.PY_SOURCE)

python3_5_executable = 'python3' # Must be >= 3.5.0

check_override_at_runtime = False
check_override_at_class_definition_time = True

not_type_checked = set()
stub_modules = {}

# Search-path for stubfiles.
stub_path = []

# Directory to collect generated stubs. If None, tempfile.gettempdir() is used.
stub_gen_dir = None

_delayed_checks = []

# Monkeypatch typing.Generic to circumvent type-erasure:
_Generic__new__ = typing.Generic.__new__
def __Generic__new__(cls, *args, **kwds):
	res = _Generic__new__(cls, args, kwds)
	res.__gentype__ = cls
	return res
typing.Generic.__new__ = __Generic__new__

# Monkeypatch import to process forward-declarations after module loading finished:
savimp = builtins.__import__
def newimp(name, *x):
	res = savimp(name, *x)
	_run_delayed_checks(True, name)
	return res
builtins.__import__ = newimp

class _DelayedCheck():
	def __init__(self, func, method, class_name, base_method, base_class_name, exc_info):
		self.func = func
		self.method = method
		self.class_name = class_name
		self.base_method = base_method
		self.base_class_name = base_class_name
		self.exc_info = exc_info
		self.raising_module_name = func.__module__

	def run_check(self, raise_NameError = False):
		if raise_NameError:
			meth_types = _funcsigtypes(self.func, True)
			_check_override_types(self.method, meth_types, self.class_name,
					self.base_method, self.base_class_name)
		else:
			try:
				meth_types = _funcsigtypes(self.func, True)
				_check_override_types(self.method, meth_types, self.class_name,
						self.base_method, self.base_class_name)
			except NameError:
				pass


def _run_delayed_checks(raise_NameError = False, module_name = None):
	global _delayed_checks
	if module_name is None:
		to_run = _delayed_checks
		_delayed_checks = []
	else:
		new_delayed_checks = []
		to_run = []
		for check in _delayed_checks:
			if check.raising_module_name == module_name:
				to_run.append(check)
			else:
				new_delayed_checks.append(check)
		_delayed_checks = new_delayed_checks
	for check in to_run:
		check.run_check(raise_NameError)

atexit.register(_run_delayed_checks, True)

class TypeCheckError(Exception): pass
class TypeCheckSpecificationError(Exception): pass
class InputTypeError(TypeCheckError): pass
class ReturnTypeError(TypeCheckError): pass
class OverrideError(TypeCheckError): pass

def _check_python3_5_version():
	try:
		ver = subprocess.check_output([python3_5_executable, '--version'])
		ver = ver[:-1].split(' ')[-1].split('.')
		return (int(ver[0]) >= 3 and int(ver[1]) >= 5)
	except Exception:
		return False

def _create_Python_2_stub(module_filepath, out_file = None):
	if out_file is None:
		out_file = _gen_stub2_filename(module_filepath)
	dirname = os.path.dirname(__file__)
	sep = __file__[len(dirname)]
	conv_script = dirname+sep+'stubfile_2_converter.py'
	# env = {} is required to prevent pydev from crashing
	subprocess.call([python3_5_executable, conv_script, '-s', '-o', out_file, module_filepath], env = {})

def _match_classes(stub_module, original_module):
	classes = [cl[1] for cl in inspect.getmembers(original_module, isclass)]
	for cl in classes:
		if hasattr(stub_module, cl.__name__):
			# Todo: What if stub_file uses slots? (unlikely (?))
			stub_class = getattr(stub_module, cl.__name__)
			stub_class._match_type = cl
			_match_classes(stub_class, cl)

def _get_stub_module(module_filepath, original_module):
	module_name = os.path.basename(module_filepath)
	try:
		with open(module_filepath) as module_file:
			with warnings.catch_warnings():
				warnings.simplefilter('ignore')
				stub_module = imp.load_module(module_name, module_file, module_filepath, stub_descr)
				if sys.version_info.major >= 3:
					_match_classes(stub_module, original_module)
				return stub_module
	except SyntaxError:
		return None

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

def _find_stub_files(module_name):
	full_name = _full_module_file_name_nosuffix(module_name)
	file_name = full_name+'.pyi'
	file_name2 = _plain_stub2_filename(file_name)
	return _find_files(file_name, stub_path), _find_files(file_name2, stub_path)

def _plain_stub2_filename(stub_file):
	return stub_file.rpartition('.')[0]+'.pyi2'

def _gen_stub2_filename(stub_file, base_module):
	if os.path.isfile(stub_file):
		bn = os.path.basename(stub_file).rpartition('.')[0]
		if stub_gen_dir is None:
			checksum = _md5(stub_file)
			return tempfile.gettempdir()+os.sep+bn+'__'+checksum+'.pyi2'
		else:
			pck = '' if base_module.__package__ is None else \
					base_module.__package__.replace('.', os.sep)+os.sep
			return os.path.abspath(stub_gen_dir)+os.sep+pck+bn+'.pyi2'
	else:
		# If there is no original file, no generated file(name) can be created:
		return None

def _check_py2_stubmodule(pyi_file, pyi2_module):
	if pyi2_module.__doc__ is None:
		# File was hand-crafted.
		return True
	lines = pyi2_module.__doc__.split('\n')
	if len(lines) < 5 or lines[4] != 'This file was generated by pytypes. Do not edit directly.':
		# File was hand-crafted.
		return True
	if (not pyi_file is None) and os.path.normpath(pyi_file) != os.path.normpath(lines[2]):
		# File wasn't generated from the source we thought it was.
		return False
	in_file = lines[2] if pyi_file is None else pyi_file
	if os.path.isfile(in_file):
		return lines[3].endswith(_md5(in_file))
	else:
		return False

def get_stub_module(func):
	module = sys.modules[func.__module__]
	assert(ismodule(module))
	m_name = module.__name__
	
	if m_name.endswith('.pyi') or m_name.endswith('.pyi2'):
		return None
	m_key = m_name+str(id(module))
	if m_key in stub_modules:
		return stub_modules[m_key]
	module_filepath = module.__file__.rpartition('.')[0]+'.pyi'
	module_filepath2 = _plain_stub2_filename(module.__file__)
	stub_files = _find_stub_files(m_name)
	if os.path.isfile(module_filepath):
		stub_files[0].append(module_filepath)
	if os.path.isfile(module_filepath2):
		stub_files[1].append(module_filepath2)
	module_filepath2_gen = _gen_stub2_filename(module_filepath, module)
	if not (sys.version_info.major >= 3 and sys.version_info.minor >= 5):
		# Python version < 3.5, so try to use a Python 2-style stub.
		# First look for a not-generated one:
		for module_filepath2_plain in stub_files[1]:
			stub_module = _get_stub_module(module_filepath2_plain, module)
			if not stub_module is None:
				stub_modules[m_key] = stub_module
				return stub_module
		# Now for a previously generated one:
		if (not module_filepath2_gen is None) and os.path.isfile(module_filepath2_gen):
			stub_module = _get_stub_module(module_filepath2_gen, module)
			if not stub_module is None:
				# A generated module might be outdated:
				# We only check this and attempt to re-create outdated stub-files
				# for files found under stub_gen_dir.
				for module_filepath in stub_files[0]:
					if _check_py2_stubmodule(module_filepath, stub_module):
						stub_modules[m_key] = stub_module
						return stub_module
				# Otherwise we let the code below re-create the module.
				# Note that we cannot be in tmp-dir mode, since the pyi2-file
				# would not have been kept in that case.
	# Python >= 3.5 or no Python 2-style stub available, so try original stub:
	# Simply try to load one of the stubs in search-folders:
	for module_filepath in stub_files[0]:
		stub_module = _get_stub_module(module_filepath, module)
		if not stub_module is None:
			stub_modules[m_key] = stub_module
			return stub_module
	# Try Python2-style stubs in search-folders, even if running Python 3:
	for module_filepath in stub_files[1]:
		stub_module = _get_stub_module(module_filepath, module)
		if not stub_module is None:
			stub_modules[m_key] = stub_module
			return stub_module
	# Finally try to convert a Python3 stub to Python2-style:
	if not (sys.version_info.major >= 3 and sys.version_info.minor >= 5):
		# Most likely the module-stub could not be loaded due to Python 3.5-syntax
		if _check_python3_5_version():
			for module_filepath in stub_files[0]:
				# We try to use a local Python 3 version to generate a Python 2-style stub:
				_create_Python_2_stub(module_filepath, module_filepath2_gen)
				if os.path.isfile(module_filepath2_gen):
					stub_module = _get_stub_module(module_filepath2_gen, module)
					if stub_gen_dir is None:
						atexit.register(os.remove, module_filepath2_gen)
						atexit.register(os.remove, module_filepath2_gen+'c')
						# Todo: Clean up other potential by-products
					if not stub_module is None:
						stub_modules[m_key] = stub_module
						return stub_module
				#else:
				# Todo: Raise warning in verbose mode.
	# No stub-file available
	stub_modules[m_key] = None
	return None

def _striptrailingcomment(s):
	pos = s.find('#')
	if pos > -1:
		return s[:pos].strip()
	else:
		return s.strip()

def _parse_typecomment_oneline(line):
	commStart = line.find('#')
	tp_delim = 'type'
	if commStart > -1 and len(line) > commStart+1:
		comment = line[commStart+1:].strip()
		if (comment.startswith(tp_delim) and len(comment) > len(tp_delim)+1):
			comment = comment[len(tp_delim):].strip()
			if (comment.startswith(':')):
				comment = comment[1:].strip()
				if len(comment) > 0:
					return comment
	return None

def _get_typestrings(obj, slf):
	srclines = inspect.getsourcelines(obj)[0]
	funcstart = 0
	startInit = False
	result = []
	for line in srclines:
		ln = _striptrailingcomment(line)
		if len(ln) > 0:
			if ln.startswith('def '):
				startInit = True
			if startInit:
				if ln.endswith(':'):
					if ln[:-1].strip().endswith(')') or ln.find('->') != -1:
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

def _match_stub_type(stub_type):
	if not (sys.version_info.major >= 3):
		return stub_type
	# Todo: Only apply if stub-module is involved
	# Todo: Somehow cache results
	if hasattr(stub_type, '__tuple_params__'):
		res = Tuple[tuple(_match_stub_type(t) for t in stub_type.__tuple_params__)]
	elif hasattr(stub_type, '__union_params__'):
		res = Union[tuple(_match_stub_type(t) for t in stub_type.__union_params__)]
# 	elif res == list:
# 		res = List[Union[tuple(_match_stub_type(t) for t in obj)]]
# 	elif sys.version_info.major == 2 and isinstance(obj, types.InstanceType):
# 		# For old-style instances return the actual class:
# 		return obj.__class__
	elif isclass(stub_type):
		res = stub_type._match_type if hasattr(stub_type, '_match_type') else stub_type
	else:
		res = stub_type
	return res

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

def _methargtype(obj):
	assert(type(obj) == tuple)
	return Tuple[tuple(deep_type(t) for t in obj[1:])]

def as_stub_func_if_any(func0, decorated_func = None, func_class = None):
	# Check for stubfile
	module = get_stub_module(func0)
	if not module is None:
		if hasattr(module, func0.__name__):
			return getattr(module, func0.__name__)
		elif not decorated_func is None and ismethod(decorated_func):
			cls = get_class_that_defined_method(decorated_func)
			if hasattr(module, cls.__name__):
				cls2 = getattr(module, cls.__name__)
				if hasattr(cls2, func0.__name__):
					return getattr(cls2, func0.__name__)
		elif not func_class is None:
			if hasattr(module, func_class.__name__):
				cls2 = getattr(module, func_class.__name__)
				if hasattr(cls2, func0.__name__):
					return getattr(cls2, func0.__name__)
			else:
				nesting = _get_class_nesting_list(func_class, sys.modules[func_class.__module__])
				if not nesting is None:
					mcls = module
					try:
						for cl in nesting:
							mcls = getattr(mcls, cl.__name__)
						mcls = getattr(mcls, func_class.__name__)
						return getattr(mcls, func0.__name__)
					except AttributeError:
						pass
		else:
			nesting = _get_class_nesting_list_for_staticmethod(decorated_func,
					sys.modules[func0.__module__], [], set())
			if not nesting is None:
					mcls = module
					try:
						for cl in nesting:
							mcls = getattr(mcls, cl.__name__)
						return getattr(mcls, func0.__name__)
					except AttributeError:
						pass
	return func0

def has_type_hints(func0):
	func = as_stub_func_if_any(_actualfunc(func0), func0)
	try:
		tpHints = typing.get_type_hints(func)
	except NameError:
		# Some typehint caused this NameError, so typhints are present in some form
		return True
	tpStr = _get_typestrings(func, False)
	return not ((tpStr is None or tpStr[0] is None) and (tpHints is None or not tpHints))

def _funcsigtypes(func0, slf, func_class = None):
	# Check for stubfile
	func = as_stub_func_if_any(_actualfunc(func0), func0, func_class)

	tpHints = typing.get_type_hints(func)
	tpStr = _get_typestrings(func, slf)
	if (tpStr is None or tpStr[0] is None) and (tpHints is None or not tpHints):
		# Maybe raise warning here
		return Any, Any
	if not (tpStr is None or tpStr[0] is None) and tpStr[0].find('...') != 0:
		numArgs = len(getargspecs(func).args) - 1 if slf else 0
		while len(tpStr[1]) < numArgs:
			tpStr[1].append(None)
	if func.__module__.endswith('.pyi') or func.__module__.endswith('.pyi2'):
		globs = {}
		globs.update(sys.modules[func.__module__].__dict__)
		globs.update(sys.modules[func.__module__.rsplit('.')[0]].__dict__)
	else:
		globs = sys.modules[func.__module__].__dict__
	if not tpHints is None and tpHints:
		# We're running Python 3
		argNames = inspect.getfullargspec(func).args
		if slf:
			argNames = argNames[1:]
		resType = (Tuple[tuple((tpHints[t] if t in tpHints else Any) for t in argNames)],
				tpHints['return'])
		if not (tpStr is None or tpStr[0] is None):
			resType2 = _funcsigtypesfromstring(*tpStr, globals = globs)
			if resType != resType2:
				raise TypeCheckSpecificationError('%s.%s declares incompatible types:\n'
					% (func.__module__, func.__name__)
					+ 'Via hints:   %s\nVia comment: %s'
					% (_type_str(resType), _type_str(resType2)))
		return resType
	res = _funcsigtypesfromstring(*tpStr, globals = globs)
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

def _check_override_types(method, meth_types, class_name, base_method, base_class_name):
	base_types = _match_stub_type(_funcsigtypes(base_method, True))
	meth_types = _match_stub_type(meth_types)
	if has_type_hints(base_method):
		if not issubclass(base_types[0], meth_types[0]):
			raise OverrideError('%s.%s.%s cannot override %s.%s.%s.\n'
					% (method.__module__, class_name, method.__name__, base_method.__module__, base_class_name, base_method.__name__)
					+ 'Incompatible argument types: %s is not a subtype of %s.'
					% (_type_str(base_types[0]), _type_str(meth_types[0])))
		if not issubclass(meth_types[1], base_types[1]):
			raise OverrideError('%s.%s.%s cannot override %s.%s.%s.\n'
					% (method.__module__, class_name, method.__name__, base_method.__module__, base_class_name, base_method.__name__)
					+ 'Incompatible result types: %s is not a subtype of %s.'
					% (_type_str(meth_types[1]), _type_str(base_types[1])))

def _check_override_argspecs(method, argSpecs, class_name, base_method, base_class_name):
	ovargs = getargspecs(base_method)
	d1 = 0 if ovargs.defaults is None else len(ovargs.defaults)
	d2 = 0 if argSpecs.defaults is None else len(argSpecs.defaults)
	if len(ovargs.args)-d1 < len(argSpecs.args)-d2 or len(ovargs.args) > len(argSpecs.args):
		raise OverrideError('%s.%s.%s cannot override %s.%s.%s:\n'
				% (method.__module__, class_name, method.__name__, base_method.__module__, base_method.__name__, base_class_name)
				+ 'Mismatching argument count. Base-method: %i+%i   submethod: %i+%i'
				% (len(ovargs.args)-d1, d1, len(argSpecs.args)-d2, d2))

def _no_base_method_error(method):
	return OverrideError('%s in %s does not override any other method.\n'
					% (method.__name__, method.__module__))

def _function_instead_of_method_error(method):
	return OverrideError('@override was applied to a function, not a method: %s.%s.\n'
					% (method.__module__, method.__name__))

def override(func):
	if not enabled:
		return func
	if check_override_at_class_definition_time:
		# We need some trickery here, because details of the class are not yet available
		# as it is just getting defined. Luckily we can get base-classes via inspect.stack():

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
					assert(ismodule(obj) or isclass(obj))
					obj = getattr(obj, c)
				base_classes[i] = obj

		found = False
		argSpecs = getargspecs(func)
		for cls in base_classes:
			if hasattr(cls, func.__name__):
				found = True
				base_method = getattr(cls, func.__name__)
				_check_override_argspecs(func, argSpecs, meth_cls_name, base_method, cls.__name__)
				if has_type_hints(func):
					#meth_types = _funcsigtypes(func, True)
						#method, meth_types, class_name, base_method, base_class_name
					try:
						_check_override_types(func, _funcsigtypes(func, True), meth_cls_name,
								base_method, cls.__name__)
					except NameError:
						_delayed_checks.append(_DelayedCheck(func, func, meth_cls_name, base_method,
								cls.__name__, sys.exc_info()))
		if not found:
			raise _no_base_method_error(func)

	if check_override_at_runtime:
		def checker_ov(*args, **kw):
			argSpecs = getargspecs(func)
			if len(argSpecs.args) > 0 and argSpecs.args[0] == 'self':
				if hasattr(args[0].__class__, func.__name__) and \
						ismethod(getattr(args[0], func.__name__)):
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
					# Check arg/res-type compatibility
					meth_types = _funcsigtypes(func, True)
					if has_type_hints(func):
						for ovcls in ovmro:
							ovf = getattr(ovcls, func.__name__)
							_check_override_types(func, meth_types, args[0].__class__.__name__, ovf, ovcls.__name__)
				else:
					raise OverrideError('@override was applied to a non-method: %s.%s.\n'
						% (func.__module__, func.__name__)
						+ "that declares 'self' although not a method.")
			else:
				raise _function_instead_of_method_error(func)
			return func(*args, **kw)
	
		checker_ov.ov_func = func
		if hasattr(func, '__func__'):
			checker_ov.__func__ = func.__func__
		checker_ov.__name__ = func.__name__ # What sorts of evil might this bring over us?
		checker_ov.__module__ = func.__module__
		checker_ov.__globals__.update(func.__globals__)
		if hasattr(func, '__annotations__'):
			checker_ov.__annotations__ = func.__annotations__
		if hasattr(func, '__qualname__'):
			checker_ov.__qualname__ = func.__qualname__
		# Todo: Check what other attributes might be needed (e.g. by debuggers).
		return checker_ov
	else:
		return func

def no_type_erasure(func):
	pass

def _type_str(tp):
	tp = _match_stub_type(tp)
	impl = ('__builtin__', 'builtins', '__main__')
	if isclass(tp) and not hasattr(typing, tp.__name__):
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
			params = [_type_str(param) for param in tp.__args__]
			prm = '['+', '.join(params)+']'
		return pck+tp.__name__+prm
	elif hasattr(tp, '__args__'):
		params = [_type_str(param) for param in tp.__args__]
		return tp.__name__+'['+', '.join(params)+']'
	elif hasattr(tp, '__tuple_params__'):
		tpl_params = [_type_str(param) for param in tp.__tuple_params__]
		return 'Tuple['+', '.join(tpl_params)+']'
	else:
		# Todo: Care for other special types from typing where necessary.
		return str(tp).replace('typing.', '')

def _make_type_error_message(tp, func, slf, func_class, expected_tp, incomp_text):
	_cmp_msg_format = 'Expected: %s\nReceived: %s'
	func0 = _actualfunc(func)
	if slf:
		#Todo: Clarify if an @override-induced check caused this
		# Todo: Python3 misconcepts method as classmethod here, because it doesn't
		# detect it as bound method, because ov_checker or tp_checker obfuscate it
		if not func_class is None and not type(func) is classmethod:
			func = getattr(func_class, func.__name__)
		if hasattr(func, 'im_class'):
			return ('%s.%s.%s '+incomp_text+':\n') \
				% (func0.__module__, get_class_qualname(func.im_class), func0.__name__) \
				+ _cmp_msg_format \
				% (_type_str(expected_tp), _type_str(tp))
		else:
			return ('classmethod %s.%s.%s '+incomp_text+':\n') \
				% (func0.__module__, get_class_qualname(func_class), func0.__name__) \
				+ _cmp_msg_format \
				% (_type_str(expected_tp), _type_str(tp))
	elif type(func) == staticmethod:
		return ('static method %s.%s '+incomp_text+':\n') \
				% (func0.__module__, get_staticmethod_qualname(func)) \
				+ _cmp_msg_format \
				% (_type_str(expected_tp), _type_str(tp))
	else:
		return ('%s.%s '+incomp_text+':\n') \
				% (func0.__module__, func0.__name__) \
				+ _cmp_msg_format \
				% (_type_str(expected_tp), _type_str(tp))

def _checkfunctype(tp, func, slf, func_class):
	argSig, resSig = _funcsigtypes(func, slf, func_class)
	if not issubclass(tp, _match_stub_type(argSig)):
		raise InputTypeError(_make_type_error_message(tp, func, slf, func_class,
				argSig, 'called with incompatible types'))
	return _match_stub_type(resSig) # provide this by-product for potential future use

def _checkfuncresult(resSig, tp, func, slf, func_class):
	if not issubclass(tp, _match_stub_type(resSig)):
		raise ReturnTypeError(_make_type_error_message(tp, func, slf, func_class,
				resSig, 'returned incompatible type'))

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

def typechecked_func(func, force = False):
	if not enabled:
		return func
	assert(isfunction(func) or ismethod(func) or ismethoddescriptor(func))
	if not force and is_no_type_check(func):
		return func
	clsm = type(func) == classmethod
	stat = type(func) == staticmethod
	func0 = _actualfunc(func)

	if hasattr(func, 'ov_func'):
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
					print('Warning: classmethod using non-idiomatic argname '+func0.__name__)
				tp = _methargtype(args)
			elif argNames[0] == 'self':
				if hasattr(args[0].__class__, func0.__name__) and \
						ismethod(getattr(args[0], func0.__name__)):
					tp = _methargtype(args)
					slf = True
				else:
					print('Warning: non-method declaring self '+func0.__name__)
					tp = deep_type(args)
			else:
				tp = deep_type(args)
		else:
			tp = deep_type(args)
			
		if checkParents:
			if not slf:
				raise OverrideError('@override with non-instancemethod not supported: %s.%s.%s.\n'
					% (func0.__module__, args[0].__class__.__name__, func0.__name__))
			toCheck = []
			for cls in args[0].__class__.__mro__:
				if hasattr(cls, func0.__name__):
					ffunc = getattr(cls, func0.__name__)
					if has_type_hints(_actualfunc(ffunc)):
						toCheck.append(ffunc)
		else:
			toCheck = (func,)

		parent_class = None
		if slf:
			parent_class = args[0].__class__
		elif clsm:
			parent_class = args[0]

		resSigs = []
		for ffunc in toCheck:
			resSigs.append(_checkfunctype(tp, ffunc, slf or clsm, parent_class))

		# perform backend-call:
		if clsm or stat:
			res = func.__func__(*args, **kw)
		else:
			res = func(*args, **kw)
		
		tp = deep_type(res)
		for i in range(len(resSigs)):
			_checkfuncresult(resSigs[i], tp, toCheck[i], slf or clsm, parent_class)
		return res

	checker_tp.ch_func = func
	if hasattr(func, '__func__'):
		checker_tp.__func__ = func.__func__
	checker_tp.__name__ = func0.__name__ # What sorts of evil might this bring over us?
	checker_tp.__module__ = func0.__module__
	checker_tp.__globals__.update(func0.__globals__)
	if hasattr(func, '__annotations__'):
		checker_tp.__annotations__ = func.__annotations__
	if hasattr(func, '__qualname__'):
		checker_tp.__qualname__ = func.__qualname__
	# Todo: Check what other attributes might be needed (e.g. by debuggers).
	if clsm:
		return classmethod(checker_tp)
	elif stat:
		return staticmethod(checker_tp)
	else:
		return checker_tp

def typechecked_class(cls, force = False, force_recursive = False):
	if not enabled:
		return cls
	assert(isclass(cls))
	if not force and is_no_type_check(cls):
		return cls
	# To play it safe we avoid to modify the dict while iterating over it,
	# so we previously cache keys.
	# For this we don't use keys() because of Python 3.
	keys = [key for key in cls.__dict__]
	for key in keys:
		obj = cls.__dict__[key]
		if force_recursive or not is_no_type_check(obj):
			if isfunction(obj) or ismethod(obj) or ismethoddescriptor(obj):
				setattr(cls, key, typechecked_func(obj, force_recursive))
			elif isclass(obj):
				setattr(cls, key, typechecked_class(obj, force_recursive, force_recursive))
	return cls

# Todo: Write tests for this
def typechecked_module(md, force_recursive = False):
	'''
	Intended to typecheck modules that were not annotated with @typechecked without
	modifying their code.
	'''
	if not enabled:
		return md
	assert(ismodule(md))
	# To play it safe we avoid to modify the dict while iterating over it,
	# so we previously cache keys.
	# For this we don't use keys() because of Python 3.
	keys = [key for key in md.__dict__]
	for key in keys:
		obj = md.__dict__[key]
		if force_recursive or not is_no_type_check(obj):
			if isfunction(obj) or ismethod(obj) or ismethoddescriptor(obj):
				setattr(md, key, typechecked_func(obj, force_recursive))
			elif isclass(obj):
				setattr(md, key, typechecked_class(obj, force_recursive, force_recursive))

def typechecked(obj):
	if not enabled:
		return obj
	if is_no_type_check(obj):
		return obj
	if isfunction(obj) or ismethod(obj) or ismethoddescriptor(obj):
		return typechecked_func(obj)
	if isclass(obj):
		return typechecked_class(obj)
	return obj

def no_type_check(obj):
	try:
		return typing.no_type_check(obj)
	except(AttributeError):
		not_type_checked.add(obj)
		return obj

def is_no_type_check(obj):
	return (hasattr(obj, '__no_type_check__') and obj.__no_type_check__) or obj in not_type_checked

def _get_class_nesting_list_for_staticmethod(staticmeth, module_or_class, stack, rec_set):
	if hasattr(module_or_class, _actualfunc(staticmeth).__name__):
		val = getattr(module_or_class, _actualfunc(staticmeth).__name__)
		if _unchecked_backend(staticmeth) is _unchecked_backend(val):
			return stack
	classes = [cl[1] for cl in inspect.getmembers(module_or_class, isclass)]
	mod_name = module_or_class.__module__ if isclass(module_or_class) \
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
	classes = [cl[1] for cl in inspect.getmembers(module_or_class, isclass)]
	mod_name = module_or_class.__module__ if isclass(module_or_class) \
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
			if ismethod(func):
				return True
			elif sys.version_info.major >= 3:
				# In Python3 there are no unbound methods, so we count as method,
				# if first arg is called 'self' 
				return True
			else:
				print('Warning (is_method): non-method declaring self '+func0.__name__)
	return False

def is_class(obj):
	if sys.version_info.major >= 3:
		return isinstance(obj, type)
	else:
		return isinstance(obj, (types.TypeType, types.ClassType))

def is_classmethod(meth):
	if not ismethod(meth):
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
					print('Warning: classmethod using non-idiomatic argname '+func0.__name__)
	args, res = _funcsigtypes(func, slf or clsm)
	return _match_stub_type(args), _match_stub_type(res)

def get_type_hints(func):
	'''
	Resembles typing.get_type_hints, but is also workable on Python 2.7.
	'''
	typing.get_type_hints
	if not has_type_hints(func):
		return {}
	slf = 1 if is_method(func) else 0
	args, res = get_types(func)
	argNames = getargspecs(_actualfunc(func)).args
	result = {}
	if not args is Any:
		for i in range(slf, len(argNames)):
			result[argNames[i]] = args.__tuple_params__[i-slf]
	result['return'] = res
	return result

# Some exemplary overrides for this modules's global settings:

# Set custom Python3-executable like this:
#python3_5_executable = '/data/workspace/linux/Python-3.5.2/python'

# Set custom directory to store generated stubfiles like this:
# Unlike in tmp-directory mode, these are kept over distinct runs.
#stub_gen_dir = '../py2_stubs'
