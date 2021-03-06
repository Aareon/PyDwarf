#!/usr/bin/env python
# coding: utf-8



'''Provides helper functions for common tasks.'''



import os
from logger import log



def rel(base, *parts):
    '''Get a path relative to the directory containing another.'''
    return os.path.join(os.path.dirname(base) if os.path.isfile(base) else base, *parts)
    
    

def findfile(name, paths, recursion=6):
    '''Find a file given paths the file may be located in or near.'''
    log.debug('Looking for file %s.' % name)
    for path in paths:
        if path is not None:
            currentpath = path
            for i in xrange(0, recursion):
                if os.path.isdir(currentpath):
                    log.debug('Checking path %s for file %s.' % (currentpath, name))
                    if name in os.listdir(currentpath):
                        return os.path.join(currentpath, name)
                    else:
                        currentpath = os.path.dirname(currentpath)
                else:
                    break
    return None
