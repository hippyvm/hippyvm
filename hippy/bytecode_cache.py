
import os
import time
from hippy.phpcompiler import compile_php
from rpython.rlib.rpath import abspath

TIMEOUT = 1.0

class BytecodeCache(object):
    def __init__(self, timeout=TIMEOUT):
        self.cached_files = {}
        self.timeout = timeout

    def compile_file(self, fname, space):
        absname = abspath(fname)
        now = time.time()
        try:
            bc, tstamp = self.cached_files[absname]
            if now - tstamp >= self.timeout:
                mtime = os.stat(absname).st_mtime
                if mtime > tstamp:
                    raise KeyError
        except KeyError:
            f = open(absname)
            data = f.read(-1)
            f.close()
            tstamp = os.stat(absname).st_mtime
            bc = compile_php(absname, data, space)
            self.cached_files[absname] = (bc, tstamp)
        return bc
