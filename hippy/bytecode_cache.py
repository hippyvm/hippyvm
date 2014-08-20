
import os
import time
from hippy.phpcompiler import compile_php
from rpython.rlib.rpath import exists, dirname, join, abspath

TIMEOUT = 1.0

class BytecodeCache(object):
    def __init__(self, timeout=TIMEOUT):
        self.cached_files = {}
        self.cached_filenames = {}
        self.timeout = timeout

    def find_file(self, interp, fname):
        try:
            return self.cached_filenames[fname]
        except KeyError:
            actual_name = self._find_file(interp, fname)
            self.cached_filenames[fname] = actual_name
            return actual_name

    def _find_file(self, interp, fname):
        if not exists(fname):
            for path in interp.include_path:
                if exists(join(path, [fname])):
                    return abspath(join(path, [fname]))
        # this is stupid, but...
        actual_code_dir = dirname(interp.global_frame.bytecode.filename)
        if exists(join(actual_code_dir, [fname])):
            return abspath(join(actual_code_dir, [fname]))
        return abspath(fname)

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
