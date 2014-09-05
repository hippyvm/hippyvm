
import os, sys, time
from hippy.phpcompiler import compile_php
from hippy.rpath import abspath

TIMEOUT = 1.0

class BytecodeCache(object):
    def __init__(self, timeout=TIMEOUT):
        self.cached_files = {}
        self.timeout = timeout

    # again, abs_filename is None for stdin
    def _really_compile(self, space, abs_fname):

        if abs_fname is None:
            f = os.fdopen(0) # open stdin
        else:
            f = open(abs_fname)

        data = f.read(-1)

        bc = compile_php(abs_fname, data, space)

        if abs_fname is not None: # if not stdin, cache bytecode
            f.close() # also don't close if stdin
            tstamp = os.stat(abs_fname).st_mtime
            self.cached_files[abs_fname] = (bc, tstamp)

        return bc

    # pass fname as None for stdin
    def compile_file(self, fname, space):
        now = time.time()

        if fname is None: # you can't cache stdin
            return self._really_compile(space, fname)
        else:
            # otherwise this really is a filename
            absname = abspath(fname)
            assert absname is not None
            try:
                bc, tstamp = self.cached_files[absname]
                if now - tstamp >= self.timeout:
                    mtime = os.stat(absname).st_mtime
                    if mtime > tstamp:
                        raise KeyError
                return bc
            except KeyError:
                return self._really_compile(space, fname)
