# vim:fileencoding=UTF-8

import inspect

import objects
import filters
import tokenlist



class rawsqueryable(object):
    '''Classes which contain raws tokens should inherit from this in order to provide querying functionality.'''
    
    query_tokeniter_docstring = '''
        tokeniter: The query runs along this iterable until either a filter has hit
            its limit or the tokens have run out.'''
    
    quick_query_args_docstring = '''
        pretty: Convenience argument which acts as a substitute for directly
            assigning a filter's exact_value and exact_args arguments. Some methods
            also accept an until_pretty argument which acts as a substitute for
            until_exact_value and until_exact_args.
        %s
        **kwargs: If no tokeniter is specified, then arguments which correspond to
            named arguments of the object's tokens method will be passed to that
            method. All other arguments will be passed to the appropriate filters,
            and for accepted arguments you should take a look at the rawstokenfilter
            constructor's docstring. Some quick query methods support arguments
            prepended with 'until_' to distinguish tokens that should be matched
            from tokens that should terminate the query. (These methods are getuntil,
            getlastuntil, and alluntil. The arguments for the until method should be
            named normally.)
    ''' % query_tokeniter_docstring
            
    def __iter__(self):
        return self.tokens()
    
    def __contains__(self, item):
        if isinstance(item, basestring):
            return self.get(pretty=pretty) is not None
        elif isinstance(item, rawsqueryable):
            return item in self.tokens()
    
    def __getitem__(self, item):
        '''Overrides object[...] behavior. Accepts a number of different types for the item argument, each resulting in different behavior.
        
        object[...]
            Returns the same as object.list().
        object[str]
            Returns the same as object.get(str).
        object[int]
            Returns the same as object.index(int).
        object[slice]
            Returns the same as object.slice(slice).
        object[iterable]
            Returns a flattened list containing object[member] in order for each member of iterable.
        object[anything else]
            Raises an exception.
        '''
        if item is Ellipsis:
            return self.list()
        elif isinstance(item, basestring):
            return self.get(pretty=item)
        elif isinstance(item, int):
            return self.index(item)
        elif isinstance(item, slice):
            return self.slice(item)
        elif hasattr(item, '__iter__') or hasattr(item, '__getitem__'):
            return self.getitems(items)
        else:
            raise ValueError('Failed to get item because the argument was of an unrecognized type.')
            
    def getitems(self, items):
        result = []
        for item in items:
            ext = self.__getitem__(item)
            (result.extend if isinstance(ext, list) else result.append)(ext)
        return result
        
    def slice(self, slice):
        return tokenlist.tokenlist(self.islice(slice))
        
    def islice(self, slice):
        root = self.index(slice.start)
        tail = self.index(slice.stop)
        if root is not None and tail is not None:
            for token in root.tokens(include_self=True, step=slice.step, until_token=tail, reverse=root.follows(tail)):
                yield token
        else:
            return
            
    def removefirst(self, *args, **kwargs):
        token = self.get(*args, **kwargs)
        if token is not None: token.remove()
        return token
    def removelast(self, *args, **kwargs):
        token = self.getlast(*args, **kwargs)
        if token is not None: token.remove()
        return token
    def removeuntil(self, *args, **kwargs):
        token = self.until(*args, **kwargs)
        if token is not None: token.remove()
        return token
    def removefirstuntil(self, *args, **kwargs):
        token = self.getuntil(*args, **kwargs)
        if token is not None: token.remove()
        return token
    def removelastuntil(self, *args, **kwargs):
        token = self.getlastuntil(*args, **kwargs)
        if token is not None: token.remove()
        return token
        
    def removeall(self, *args, **kwargs):
        tokens = self.all(*args, **kwargs)
        for token in tokens: token.remove()
        return tokens
    def removeuntil(self, *args, **kwargs):
        tokens = self.until(*args, **kwargs)
        for token in tokens: token.remove()
        return tokens
    def removealluntil(self, *args, **kwargs):
        tokens = self.alluntil(*args, **kwargs)
        for token in tokens: token.remove()
        return tokens
        
    def removeprop(self, *args, **kwargs):
        token = self.getprop(*args, **kwargs)
        if token is not None: token.remove()
        return token
    def removelastprop(self, *args, **kwargs):
        token = self.getlastprop(*args, **kwargs)
        if token is not None: token.remove()
        return token
    def removeallprop(self, *args, **kwargs):
        tokens = self.allprop(*args, **kwargs)
        for token in tokens: token.remove()
        return tokens
    
    def query(self, filters, tokeniter=None, **kwargs): # TODO: make it possible to use an iterable also
        '''Executes a query on some iterable containing tokens.
        
        filters: A dict or other iterable containing rawstokenfilter-like objects.
        %s
        **kwargs: If tokeniter is not given, then the object's token method will be
            called with these arguments and used instead.
        ''' % rawsqueryable.query_tokeniter_docstring
        
        if tokeniter is None: tokeniter = self.tokens(**kwargs)
        filteriter = (filters.itervalues() if isinstance(filters, dict) else filters)
        limit = False
        for filter in filteriter: filter.result = tokenlist.tokenlist() # TODO: don't do this
        for token in tokeniter:
            for filter in filteriter:
                if (not filter.limit) or len(filter.result) < filter.limit:
                    if filter(token): filter.result.append(token)
                    if filter.limit_terminates and len(filter.result) == filter.limit: limit = True; break
            if limit: break
        return filters
        
    def get(self, pretty=None, tokeniter=None, **kwargs):
        '''Get the first matching token.
        
        %s
        ''' % rawsqueryable.quick_query_args_docstring
        
        filter_args, tokens_args = self.argstokens(tokeniter, kwargs)
        queryfilters = (
            filters.rawstokenfilter(pretty=pretty, limit=1, **filter_args)
        ,)
        result = self.query(queryfilters, tokeniter, **tokens_args)[0].result
        return result[0] if result and len(result) else None
    
    def getlast(self, pretty=None, tokeniter=None, **kwargs):
        '''Get the last matching token.
        
        %s
        ''' % rawsqueryable.quick_query_args_docstring
        
        filter_args, tokens_args = self.argstokens(tokeniter, kwargs)
        queryfilters = (
            filters.rawstokenfilter(pretty=pretty, **filter_args)
        ,)
        result = self.query(queryfilters, tokeniter, **tokens_args)[0].result
        return result[-1] if result and len(result) else None
    
    def all(self, pretty=None, tokeniter=None, **kwargs):
        '''Get a list of all matching tokens.
        
        %s
        ''' % rawsqueryable.quick_query_args_docstring
        
        filter_args, tokens_args = self.argstokens(tokeniter, kwargs)
        queryfilters = (
            filters.rawstokenfilter(pretty=pretty, **filter_args)
        ,)
        return self.query(queryfilters, tokeniter, **tokens_args)[0].result
    
    def until(self, pretty=None, tokeniter=None, **kwargs):
        '''Get a list of all tokens up to a match.
        
        %s
        ''' % rawsqueryable.quick_query_args_docstring
        
        filter_args, tokens_args = self.argstokens(tokeniter, kwargs)
        queryfilters = (
            filters.rawstokenfilter(pretty=pretty, limit=1, **filter_args),
            filters.rawstokenfilter()
        )
        return self.query(queryfilters, tokeniter, **tokens_args)[1].result
        
    def getuntil(self, pretty=None, until=None, tokeniter=None, **kwargs):
        '''Get the first matching token, but abort when a token matching arguments prepended with 'until_' is encountered.
        
        %s
        ''' % rawsqueryable.quick_query_args_docstring
        
        filter_args, tokens_args = self.argstokens(tokeniter, kwargs)
        until_args, condition_args = self.argsuntil(filter_args)
        queryfilters = (
            filters.rawstokenfilter(pretty=until, limit=1, **until_args),
            filters.rawstokenfilter(pretty=pretty, limit=1, **condition_args)
        )
        result = self.query(queryfilters, tokeniter, **tokens_args)[1].result
        return result[0] if result and len(result) else None
    
    def getlastuntil(self, pretty=None, until=None, tokeniter=None, **kwargs):
        '''Get the last matching token, up until a token matching arguments prepended with 'until_' is encountered.
        
        %s
        ''' % rawsqueryable.quick_query_args_docstring
        
        filter_args, tokens_args = self.argstokens(tokeniter, kwargs)
        until_args, condition_args = self.argsuntil(filter_args)
        queryfilters = (
            filters.rawstokenfilter(pretty=until, limit=1, **until_args),
            filters.rawstokenfilter(pretty=pretty, **condition_args)
        )
        result = self.query(queryfilters, tokeniter, **tokens_args)[1].result
        return result[-1] if result and len(result) else None
     
    def alluntil(self, pretty=None, until=None, tokeniter=None, **kwargs):
        '''Get a list of all matching tokens, but abort when a token matching
        arguments prepended with 'until_' is encountered.
        
        %s
        ''' % rawsqueryable.quick_query_args_docstring
        
        filter_args, tokens_args = self.argstokens(tokeniter, kwargs)
        until_args, condition_args = self.argsuntil(filter_args)
        queryfilters = (
            filters.rawstokenfilter(pretty=until, limit=1, **until_args),
            filters.rawstokenfilter(pretty=pretty, **condition_args)
        )
        return self.query(queryfilters, tokeniter, **tokens_args)[1].result
    
    def getprop(self, *args, **kwargs):
        '''Gets the first token matching the arguments, but stops at the next
        token with the same value as this one. Should be sufficient in almost
        all cases to get a token representing a property of an object, when
        this method is called for a token representing an object. **kwargs
        are passed to the getuntil method.
        '''
        
        until_exact_value, until_re_value, until_value_in = self.argsprops()
        return self.getuntil(*args, until_exact_value=until_exact_value, until_re_value=until_re_value, until_value_in=until_value_in, **kwargs)
        
    def getlastprop(self, *args, **kwargs):
        '''Gets the last token matching the arguments, but stops at the next
        token with the same value as this one. Should be sufficient in almost
        all cases to get a token representing a property of an object, when
        this method is called for a token representing an object. **kwargs
        are passed to the getlastuntil method.
        '''
        
        until_exact_value, until_re_value, until_value_in = self.argsprops()
        return self.getlastuntil(*args, until_exact_value=until_exact_value, until_re_value=until_re_value, until_value_in=until_value_in, **kwargs)
            
    def allprop(self, *args, **kwargs):
        '''Gets the all tokens matching the arguments, but stops at the next
        token with the same value as this one. Should be sufficient in almost
        all cases to get a token representing a property of an object, when
        this method is called for a token representing an object. **kwargs are
        passed to the alluntil method.
        '''
        
        until_exact_value, until_re_value, until_value_in = self.argsprops()
        return self.alluntil(*args, until_exact_value=until_exact_value, until_re_value=until_re_value, until_value_in=until_value_in, **kwargs)
            
    def propdict(self, always_list=True, value_keys=True, full_keys=True, **kwargs):
        '''Returns a dictionary with token values mapped as keys to the tokens
        themselves. If always_list is True then every item in the dict will be
        a list. If it's False then items in the dict where only one token was
        found will be given as individual rawstoken instances rather than as
        lists. **kwargs are passed to the alluntil method.
        '''
        
        until_exact_value, until_re_value, until_value_in = self.argsprops()
        props = self.alluntil(until_exact_value=until_exact_value, until_re_value=until_re_value, until_value_in=until_value_in, **kwargs)
        pdict = {}
        for prop in props:
            for key in (prop.value if value_keys else None, str(prop)[1:-1] if full_keys else None):
                if key is not None:
                    if key not in pdict:
                        if always_list:
                            pdict[key] = tokenlist.tokenlist()
                            pdict[key].append(prop)
                        else:
                            pdict[key] = prop
                    elif prop not in pdict[key]:
                        if isinstance(pdict[key], list):
                            pdict[key].append(prop)
                        else:
                            pdict[key] = tokenlist.tokenlist()
                            pdict[key].append(prop)
                            pdict[key].append(pdict[key], prop)
        return pdict
        
    def list(self, *args, **kwargs):
        '''Convenience method acts as a shortcut for raws.tokenlist.tokenlist(obj.tokens(*args, **kwargs)).
        '''
        return tokenlist.tokenlist(self.tokens(*args, **kwargs))
    
    def argsuntil(self, kwargs):
        '''Internal: Utility function for handling arguments of getuntil and alluntil methods.'''
        until_args, condition_args = {}, {}
        for arg, value in kwargs.iteritems():
            if arg.startswith('until_'):
                until_args[arg[6:]] = value
            else:
                condition_args[arg] = value
        return until_args, condition_args
        
    def argstokens(self, tokeniter, kwargs):
        '''Internal: Utility function for separating arguments to pass on to a tokens iterator from arguments to pass to filters.'''
        if tokeniter is None and hasattr(self, 'tokens'):
            filter_args, tokens_args = {}, {}
            args = inspect.getargspec(self.tokens)[0]
            for argname, argvalue in kwargs.iteritems():
                (tokens_args if argname in args else filter_args)[argname] = argvalue
            return filter_args, tokens_args
        else:
            return kwargs, {}
            
    def argsprops(self):
        '''Internal: Utility function for handling arguments of getprop, allprop, and propdict methods.'''
        # TODO: refactor a bit so that the obviated until_exact_value and until_re_value are no longer returned
        until_exact_value = None
        until_re_value = None
        until_value_in = objects.objectsforheader(objects.headerforobject(self.value))
        return until_exact_value, until_re_value, until_value_in
