#!/usr/bin/env python
# coding: utf-8

import re
import copy
import numbers



class basefilter(object):
    '''Base class for filter objects.'''
    
    def __init__(self, invert=False, limit=None, limit_terminates=True):
        '''Initialize a filter object.'''
        self.inv = invert
        self.limit = limit
        self.limit_terminates = limit_terminates
        
    def invert(self):
        '''Cause the filter to return the inverse of what it otherwise would.'''
        self.inv = not self.inv
    def match(self, token):
        '''Check if the filter matches a token.'''
        result = self.basematch(token)
        return not result if self.inv else result
    def basematch(self, token):
        '''Internal: Should be overridden by inheriting classes.'''
        return False
        
    def copy(self):
        '''Make a copy of the filter.'''
        return copy.deepcopy(self)
        
    def inverted(self):
        '''Return an inverted copy of the filter.'''
        inv = self.copy()
        inv.invert()
        return inv
        
    def eval(self, token, count):
        '''
            Check if the filter matches a token and whether a performing query
            should be terminated.
        '''
        matches = False
        terminate = False
        if self.limit is None:
            matches = self.match(token)
        else:
            if count < self.limit:
                matches = self.match(token)
                if matches: count += 1
            if self.limit_terminates and count >= self.limit:
                terminate = True
        return matches, terminate
        
    def __and__(self, other):
        '''Return a filter representing A AND B.'''
        return boolfilter.all(self, other)
    def __or__(self, other):
        '''Return a filter representing A OR B.'''
        return boolfilter.any(self, other)
    def __xor__(self, other):
        '''Return a filter representing A XOR B.'''
        return boolfilter.one(self, other)
    
    def __invert__(self):
        '''Cause the filter to return the inverse of what it otherwise would.'''
        return self.inverted()
    
    def __contains__(self, token):
        '''Check if the filter matches a token.'''
        return self.match(token)
        
    def __call__(self, token, count):
        '''
            Check if the filter matches a token and whether a performing query
            should be terminated.
        '''
        return self.eval(token, count)
            


class tokenfilter(basefilter):
    '''
        Basic filter class providing a number of convenient attributes to
        simplify query filtering.
    '''
    
    def __init__(self,
        pretty=None,
        match_token=None, exact_token=None,
        exact_value=None, exact_args=None, exact_arg=None,
        exact_prefix=None, exact_suffix=None,
        re_value=None, re_args=None, re_arg=None, 
        re_prefix=None, re_suffix=None,
        except_value=None,
        value_in=None, value_not_in=None, arg_in=None, arg_not_in=None,
        args_contains=None, args_count=None,
        invert=None,
        limit=None, limit_terminates=True
    ):
        '''
            Constructs an element of a query which either matches or doesn't
            match a given rawstoken. Most arguments default to None. If some
            argument is None then that argument is not matched on.
        '''
        
        '''
            These arguments regard which tokens match and don't match the filter:
            
            pretty: If specified, the string is parsed as a token and its value and arguments are used
                as exact_value and exact_args.
            match_token: If specified, its value and arguments are used as exact_value and exact_args.
            exact_token: If a token is not this exact object, then it doesn't match.
            exact_value: If a token does not have this exact value, then it doesn't match.
            exact_args: If every one of a token's arguments do not exactly match these arguments, then
                it doesn't match. None values within this tuple- or list-like object are treated as
                wildcards. (These None arguments match everything.)
            exact_arg: An iterable containing tuple- or list-like objects where the first element is
                an index and the second element is a string. If for any index/string pair a token's
                argument at the index does not exactly match the string, then the token doesn't match.
            exact_prefix: If a token does not have this exact prefix - meaning the previous token's
                suffix and its own prefix concatenated - then it doesn't match.
            exact_suffix: If a token does not have this exact suffix - meaning its own suffix and the
                next token's prefix concatenated - then it doesn't match.
            re_value: If a token's value does not match this regular expression, then it doesn't match.
            re_args: If every one of a token's arguments do not match these regular expressions, then
                it doesn't match. None values within this tuple- or list-like object are treated as
                wildcards. (These None arguments match everything.)
            re_arg: An iterable containing tuple- or list-like objects where the first element is an
                index and the second element is a regular expression string. If for any index/regex
                pair a token's argument at the index does not match the regular expression, then the
                token doesn't match.
            re_prefix: If a token's prefix - meaning the previous token's suffix and its own prefix 
                concatenated - does not match this regular expression string then it doesn't match.
            re_suffix: If a token's suffix - meaning its own suffix and the next token's prefix
                concatenated - does not match this regular expression string then it doesn't match.
            except_value: If a token has this exact value, then it doesn't match.
            value_in: If a token's value is not contained within this iterable, then it doesn't match.
            value_not_in: If a token's value is contained within this iterable, then it doesn't match.
            arg_in: Handled like exact_arg or re_args, except checks for being contained by a list or
                similar object rather than matching a single string or a regex.
            args_contains: If at least one of a token's arguments is not exactly this string, then it
                doesn't match.
            args_count: If a token's number of arguments is not exactly this, then it doesn't match.
            
            These arguments regard how the filter is treated in queries.
            
            invert: Acts like 'not': Inverts what this filter does and doesn't match.
            limit: After matching this many tokens, the filter will cease to accumulate results. If
                limit is None, then the filter will never cease as long as the query continues.
            limit_terminates: After matching the number of tokens indicated by limit, if this is set
                to True then the query of which this filter is a member is made to terminated. If
                set to False, then this filter will only cease to accumulate results. Defaults to
                True.
        '''
        
        basefilter.__init__(self, invert, limit, limit_terminates)
        
        self.pretty = pretty
        
        if pretty:
            prettytoken = tokenparse.parsesingular(pretty)
            exact_value = prettytoken.value
            if prettytoken.nargs(): exact_args = prettytoken.args
            
        if match_token:
            exact_value = match_token.value
            exact_args = match_token.args
            
        if exact_args is not None and isinstance(exact_args, basestring):
            exact_args = tokenargs.tokenargs(exact_args)
            
        self.exact_token = exact_token
        self.exact_value = exact_value
        self.except_value = except_value
        self.exact_args = exact_args
        self.exact_arg = exact_arg
        self.exact_prefix = exact_prefix
        self.exact_suffix = exact_suffix
        self.re_value = re_value
        self.re_args = re_args
        self.re_arg = re_arg
        self.re_prefix = re_prefix
        self.re_suffix = re_suffix
        self.value_in = value_in
        self.value_not_in = value_not_in
        self.arg_in = arg_in
        self.arg_not_in = arg_not_in
        self.args_contains = args_contains
        self.args_count = args_count
        
        self.prepare()
        
    def prepare(self):
        '''Internal: Extra handling for some attributes.'''
        self.autodepths()
        self.anchor()
        
    def autodepths(self):
        '''Internal: Handle various input types for exact_arg, re_arg, arg_in, arg_not_in.''' 
        self.exact_arg = self.autodepthitem(self.exact_arg)
        self.re_arg = self.autodepthitem(self.re_arg)
        self.arg_in = self.autodepthitem(self.arg_in)
        self.arg_not_in = self.autodepthitem(self.arg_not_in)
        
    def autodepthitem(self, item):
        '''Internal: Used by autodepths method.''' 
        if item is None: 
            return None
        elif isinstance(item, basestring):
            return ( (0, item), )
        elif hasattr(item, '__getitem__'):
            subitem = item[0]
            if isinstance(subitem, numbers.Number):
                return (item,)
            elif hasattr(subitem, '__getitem__') and not isinstance(subitem, basestring):
                return item
            else:
                return ( (0, item), )
        
    def anchor(self):
        '''Internal: Anchor regular expressions.'''
        if self.re_value: self.re_value += '$'
        if self.re_prefix: self.re_prefix += '$'
        if self.re_suffix: self.re_suffix += '$'
        if self.re_args: self.re_args = [(None if a is None else (a + '$')) for a in self.re_args]
        if self.re_arg: self.re_arg = [(None if a is None else (a[0], a[1]+'$')) for a in self.re_arg]
        
    def basematch(self, token):
        '''Internal: Check for a matching token.'''
        if (
            (self.exact_token is not None and self.exact_token is not token) or
            (self.except_value is not None and self.except_value == token.value) or
            (self.exact_value is not None and self.exact_value != token.value) or
            (self.args_count is not None and self.args_count != token.nargs()) or
            (self.value_in is not None and token.value not in self.value_in) or
            (self.value_not_in is not None and token.value in self.value_not_in) or
            (self.re_value is not None and re.match(self.re_value, token.value) == None) or
            (self.args_contains is not None and str(self.args_contains) not in [str(a) for a in token.args])
        ):
            return False
            
        if self.exact_args is not None:
            if not (len(self.exact_args) == token.nargs() and all([self.exact_args[i] == None or str(self.exact_args[i]) == token.args[i] for i in xrange(0, token.nargs())])):
                return False
        if self.re_args is not None:
            if not (len(self.re_args) == token.nargs() and all([self.re_args[i] == None or re.match(self.re_args[i], token.args[i]) for i in xrange(0, token.nargs())])):
                return False
                
        try:
            if self.exact_arg is not None:
                if not all([token.args[a[0]] == str(a[1]) for a in self.exact_arg]):
                    return False
            if self.arg_in is not None:
                if not all([token.args[a[0]] in a[1] for a in self.arg_in]):
                    return False
            if self.arg_not_in is not None:
                if any([token.args[a[0]] in a[1] for a in self.arg_not_in]):
                    return False
            if self.re_arg is not None:
                if not all([re.match(a[1], token.args[a[0]]) for a in self.re_arg]):
                    return False
        except IndexError: # Specified index is out of range of the arguments list
            return False
                
        if self.exact_prefix is not None or self.re_prefix is not None:
            match_prefix = '' if token.prefix is None else str(token.prefix)
            if token.prev is not None and token.prev.suffix is not None: match_prefix = token.prev.suffix + match_prefix
            if (self.exact_prefix is not None and match_prefix != self.exact_prefix) or (self.re_prefix is not None and re.match(self.re_prefix, match_prefix) is None):
                return False
        if self.exact_suffix is not None or self.re_suffix is not None:
            match_suffix = '' if token.suffix is None else str(token.suffix)
            if token.next is not None and token.next.prefix is not None: match_suffix = match_suffix + token.next.prefix
            if (self.exact_suffix is not None and match_suffix != self.exact_suffix) or (self.re_suffix is not None and re.match(self.re_suffix, match_suffix) is None):
                return False
        return True
        
    def __str__(self):
        '''Get a string representation.'''
        parts = []
        for key, value in self.__dict__.iteritems():
            if value is not None and key != 'pretty' and key != 'match_token':
                parts.append('%s %s' % (key, value))
        parts.sort()
        return ', '.join(parts)
        


class boolfilter(basefilter):
    '''Logical filter for combining other filters.'''
    
    def __init__(self, 
        subs, operand=None, invert=None,
        limit=None, limit_terminates=True
    ):
        '''Initialize a filter object.'''
        basefilter.__init__(self, invert, limit, limit_terminates)
        self.subs = subs
        self.operand = operand
        
    def basematch(self, token):
        '''Internal: Check for a matching token.'''
        if self.operand == 'one':
            count = 0
            for sub in self.subs:
                count += sub.match(token)
                if count > 1: return False
            return count == 1
        elif self.operand == 'any':
            for sub in self.subs:
                if sub.match(token): return True
        elif self.operand == 'all':
            for sub in self.subs:
                if not sub.match(token): return False
            return True
        return False
            
    @staticmethod
    def one(*subs):
        '''Initialize a filter which matches only when one of its subordinates matches.'''
        return boolfilter(subs, 'one')
    @staticmethod
    def any(*subs):
        '''Initialize a filter which matches only when at least one of its subordinates matches.'''
        return boolfilter(subs, 'any')
    @staticmethod
    def all(*subs):
        '''Initialize a filter which matches only when all of its subordinates match.'''
        return boolfilter(subs, 'all')
    @staticmethod
    def none(*subs):
        '''Initialize a filter which matches only when none of its subordinates match.'''
        return boolfilter(subs, 'all', invert=True)
    
    def __str__(self):
        '''Get a string representation.'''
        return '%s%s of (%s)' % ('not ' if self.inv else '', self.operand, ', '.join(self.subs))
    


import tokenparse
import tokenargs
