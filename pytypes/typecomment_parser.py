'''
Created on 13.12.2016

@author: Stefan Richthofer
'''

import inspect
import pytypes
from typing import Any

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
	try:
		srclines = inspect.getsourcelines(obj)[0]
	except IOError:
		return None
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
	if len(srclines) > funcstart+1:
		strp = srclines[funcstart+1].strip()
		if len(strp) > 0 and strp[0] == '#':
			res = _parse_typecomment_oneline(srclines[funcstart+1]), result[1:] if slf else result
			return res
	return None, result[1:] if slf else result

def _isargsellipsis(argStr):
	return argStr[1:-1].strip() == '...'

def _funcsigtypesfromstring(typestring, argTypes = None, globals = globals(),
		selfType = None, argCount = None, unspecified_type = Any, defaults = None):
	splt = typestring.find('->')
	if splt == -1:
		return None
	argString = typestring[:splt].strip()
	if _isargsellipsis(argString):
# 		useEllipsis = True
		if not argTypes is None:
			argString = ''.join(('(', ', '.join(['Any' if x is None else x for x in argTypes]), ')'))
# 	else:
# 		useEllipsis = False
	argTypes0 = argTypes
	resString = typestring[splt+2:].strip()
	argTp = eval(argString, globals)
	if selfType is None:
		argTypes = []
	else:
		argTypes = [selfType]
	try:
		argTypes += argTp
	except TypeError:
		argTypes.append(argTp)
	uc = 0
	if not argCount is None:
		if argTypes0 is None or len(argTypes0) <= len(argTypes):
			while len(argTypes) < argCount:
				argTypes.append(unspecified_type)
				uc += 1
		else:
			while len(argTypes) < argCount:
				if len(argTypes) < len(argTypes0):
					argTypes.append(argTypes0[len(argTypes)])
				else:
					argTypes.append(unspecified_type)
					uc += 1
	if not defaults is None:
		if len(defaults) < uc:
			uc = len(defaults)
		for i in range(uc):
			argTypes[-1-i] = pytypes.deep_type(defaults[-1-i])
	# Note: Tuple constructor automatically normalizes None to NoneType
	tpl = pytypes.make_Tuple(tuple(argTypes))
# 	if useEllipsis:
# 		tpl.__tuple_use_ellipsis__ = True

	# Normalize occurrence of None to type(None).
	# (Doing this in pre-eval manner/text-mode is easier than going
	#  through maybe nested type-vars, etc)
	# To avoid that this creates type(type(None)) if type(None) is already in place:
	resString = resString.replace('type(None)', 'None')
	resString = resString.replace('None', 'type(None)')	
	
	resType = eval(resString, globals)
	return tpl, resType
