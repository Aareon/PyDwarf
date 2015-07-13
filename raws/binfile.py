import os

import basefile



class binfile(basefile.basefile):
    def __init__(self, content=None, path=None, dir=None, **kwargs):
        self.dir = None
        self.setpath(path, **kwargs)
        self.dir = dir
        self.content = content
        if self.content is None and self.path is not None and os.path.isfile(self.path): self.read(self.path)
        self.kind = 'bin'
        
    def read(self, path=None):
        with open(path if path else self.path, 'rb') as binfile: self.content = binfile.read()
        
    def ref(self, **kwargs):
        raise ValueError('Failed to cast binfile %s to a reffile because it is an invalid conversion.' % self)
    def bin(self, **kwargs):
        for key, value in kwargs.iteritems(): self.__dict__[key] = value
        return self
    def raw(self, **kwargs):
        self.kind = 'raw'
        self.__class__ = rawfile.rawfile
        for key, value in kwargs.iteritems(): self.__dict__[key] = value
        self.read(content=self.content)
        return self
        
    def copy(self):
        copy = binfile()
        copy.path = self.path
        copy.rootpath = self.rootpath
        copy.name = self.name
        copy.ext = self.ext
        copy.loc = self.loc
        copy.content = self.content
        return copy
    
    def __repr__(self):
        return str(self.content)
        
    def __len__(self):
        return len(self.content)
        
    def write(self, path):
        dest = self.dest(path, makedir=True)
        with open(dest, 'wb') as file:
            file.write(self.content)
            
    def add(self, content):
        if self.content is None:
            self.content = str(content)
        else:
            self.content += str(content)



import rawfile
