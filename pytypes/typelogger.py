'''
Created on 29.04.2017

@author: Stefan Richthofer
'''

from .type_util import deep_type, type_str
from .util import _actualfunc, getargspecs
from typing import Union

_member_cache = {}

def log_type(args_kw, func, slf=False, clsm = False, clss=None, argspecs=None, args_kw_type=None):
	if args_kw_type is None:
		args_kw_type = deep_type(args_kw)
	if argspecs is None:
		argspecs = getargspecs(func)
	if func in _member_cache:
		node = _member_cache[func]
	else:
		node = typed_member(func, slf, clsm, clss, argspecs)
		_member_cache[func] = node
	node.type_observations.append(args_kw_type)

def _print_cache():
	for node in _member_cache:
		print (node)

class typed_member(object):
	def __init__(self, member, slf=False, clsm = False, clss=None, argspecs=None):
		self.member = member
		self.clss = clss
		self.type_observations = []

	def __str__(self):
		return self.member.__str__()+": "+type_str(Union[tuple(self.type_observations)])
