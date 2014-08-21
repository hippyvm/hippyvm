import os, sys
from collections import OrderedDict
from hippy.objects.base import W_Root
from hippy.builtin import (
    wrap, Optional, FileResourceArg, FilenameArg, LongArg,
    BoolArg, StringArg, StreamContextArg, Resource, Nullable)
from hippy.objects.resources.file_resource import W_FileResource
from hippy.objects.resources.dir_resource import W_DirResource
from hippy.objects.resources.stream_context import W_StreamContext
from hippy.sort import _sort
from rpython.rlib.rstring import StringBuilder
from rpython.rlib.objectmodel import we_are_translated
from rpython.rlib import rfile # for side effects
from rpython.rlib import rpath
from rpython.rlib.rfile import create_popen_file


@wrap(['space', StringArg(None), Optional(StringArg(None))])
def basename(space, fname, suffix=None):
    """ basename - Returns trailing name component of path """
    return _basename(space, fname, suffix)


def _basename(space, fname, suffix=None):
    fname = fname.rstrip('/')
    basename = rpath.basename(fname)
    if suffix and basename.endswith(suffix) and len(basename) > len(suffix):
        stop = len(basename) - len(suffix)
        assert stop >= 0
        basename = basename[:stop]
    return space.newstr(basename)


@wrap(['space', FilenameArg(None), W_Root])
def chgrp(space, fname, w_gid):
    """ chgrp - Changes file group """
    if not is_in_basedir(space, 'chgrp', fname):
        return space.w_False

    if w_gid.tp != space.tp_str and w_gid.tp != space.tp_int:
        space.ec.warn("chgrp(): parameter 2 should be "
                      "string or integer, %s given" % space.gettypename(w_gid))
        return space.w_False
    gid = space.int_w(w_gid)
    try:
        os.chown(fname, -1, gid)
        return space.w_True
    except OSError:
        space.ec.warn("chgrp(): No such file or directory")
        return space.w_False


@wrap(['space', FilenameArg(None), LongArg(None)], name="chmod")
def _chmod(space, dirname, mode):
    """ chmod - Changes file mode """
    if not is_in_basedir(space, 'chmod', dirname):
        return space.w_False

    mode = 0x7FFFFFFF & mode
    try:
        os.chmod(dirname, mode)
        return space.w_True
    except OSError:
        space.ec.warn("chmod(): No such file or directory")
        return space.w_False


@wrap(['space', FilenameArg(None), int])
def chown(space, fname, uid):
    """ chown - Changes file owner """
    if not is_in_basedir(space, 'chown', fname):
        return space.w_False

    if not uid:
        space.ec.warn("chown(): parameter 2 should be "
                      "string or integer, null given")
        return space.w_False

    try:
        os.chown(fname, uid, -1)
        return space.w_True
    except OSError:
        space.ec.warn("chown(): No such file or directory")
        return space.w_False


@wrap(['space', Optional(bool), Optional(str)])
def clearstatcache(space, clear_realpath_cache=False, fname=None):
    """ clearstatcache - Clears file status cache """
    pass


@wrap(['space', str, str, Optional(Nullable(StreamContextArg(None)))], name="copy")
def _copy(space, source, dest, w_stream_ctx=None):
    """ copy - Copies file """
    if not is_in_basedir(space, 'copy', source):
        return space.w_False
    if not is_in_basedir(space, 'copy', dest):
        space.ec.warn("copy(%s): failed to open stream: "
                      "Operation not permitted" % dest)
        return space.w_False

    try:
        if os.path.isdir(source):
            space.ec.warn("copy(): The first argument to copy() "
                          "function cannot be a directory")
            return space.w_False
        if os.path.isdir(dest):
            space.ec.warn("copy(): The second argument to copy() "
                          "function cannot be a directory")
            return space.w_False
    except TypeError:
        return space.w_False
    try:
        try:
            if os.path.samefile(source, dest):
                return space.w_False
        except OSError:
            pass

        f1 = open(source, "r")
        f2 = open(dest, "w")
        while True:
            buf = f1.read(4096)
            if buf:
                f2.write(buf)
            else:
                break

        f1.close()
        f2.close()
        return space.w_True
    except OSError, e:
        space.ec.warn("copy(%s): failed to open "
                      "stream: %s" % (source, os.strerror(e.errno)))

        return space.w_False
    except IOError, e:
        if not we_are_translated():
            space.ec.warn("copy(%s): failed to open "
                          "stream: %s" % (source, e.strerror))

            return space.w_False
        raise

""" delete - See unlink or unset """


@wrap(['space', StringArg(None)])
def dirname(space, fname):
    """ dirname - Returns parent directory's path """
    if fname == "":
        return space.newstr("")
    if fname.endswith("/") and len(fname) != 1:
        fname = fname[:-1]
    dirname = rpath.dirname(fname)
    if dirname.find("/") == -1:
        return space.newstr(".")
    if dirname.endswith('//'):
        i = len(dirname)
        while i > 0 and i < len(dirname) and dirname[i] == '/':
            i -= 1
        stop = len(dirname) - i + 1
        assert stop >= 0
        dirname = dirname[:stop]
    return space.newstr(dirname)


def _valid_fname(fname):
    for c in fname:
        if ord(c) < 32:
            return False
    return True


@wrap(['space', str])
def disk_free_space(space, fname):
    """ disk_free_space - Returns available space on
    filesystem or disk partition """
    """ diskfreespace - Alias of disk_free_space """

    if not is_in_basedir(space, 'disk_free_space', fname):
        return space.w_False

    if not _valid_fname(fname):
            space.ec.warn("disk_free_space() expects "
                          "parameter 1 to be a valid path, string given")
            return space.w_Null
    try:
        s = os.statvfs(fname)
        # converting to float avoids overflow issues on 32-bit
        res = float(s.f_bsize) * float(s.f_bavail)
        if res == 0.:
            return space.w_False
        return space.newfloat(res)
    except TypeError:
        return space.w_False
    except OSError:
        space.ec.warn("disk_free_space(): No such file or directory")
        return space.w_False


@wrap(['space', str])
def diskfreespace(space, fname):
    """ disk_free_space - Returns available space on
    filesystem or disk partition """
    """ diskfreespace - Alias of disk_free_space """

    if not is_in_basedir(space, 'diskfreespace', fname):
        return space.w_False

    if not _valid_fname(fname):
        space.ec.warn("diskfreespace() expects "
                      "parameter 1 to be a valid path, string given")
        return space.w_Null

    try:
        s = os.statvfs(fname)
        # converting to float avoids overflow issues on 32-bit
        res = float(s.f_bsize) * float(s.f_bavail)
        if res == 0.:
            return space.w_False
        return space.newfloat(res)
    except TypeError:
        return space.w_False
    except OSError:
        space.ec.warn("diskfreespace(): No such file or directory")
        return space.w_False


@wrap(['space', str])
def disk_total_space(space, fname):
    """ disk_total_space - Returns the total size of
    a filesystem or disk partition """
    if not is_in_basedir(space, 'disk_total_space', fname):
        return space.w_False

    if not _valid_fname(fname):
        space.ec.warn("disk_total_space() expects "
                      "parameter 1 to be a valid path, string given")
        return space.w_Null
    try:
        s = os.statvfs(fname)
        return space.newfloat(float(s.f_bsize) * float(s.f_blocks))
    except OSError:
        space.ec.warn("disk_total_space(): No such file or directory")
        return space.w_False
    except TypeError:
        return space.newfloat(0.)


@wrap(['space', FileResourceArg(False)], error=False)
def fclose(space, w_res):
    """ fclose - Closes an open file pointer """
    if w_res.tp == space.tp_bool:
        space.ec.warn("fclose() expects parameter 1 "
                      "to be resource, boolean given")
        return space.w_False
    assert isinstance(w_res, W_FileResource)

    if not w_res.is_valid():
        space.ec.warn("fclose(): %d is not a valid "
                      "stream resource" % w_res.res_id)
        return space.w_False
    assert isinstance(w_res, W_FileResource)
    out = w_res.close()
    return space.newbool(out)


@wrap(['space', FileResourceArg(False)], error=False)
def feof(space, w_res):
    """ feof - Tests for end-of-file on a file pointer """
    if w_res.tp == space.tp_bool:
        space.ec.warn("feof() expects parameter 1 "
                      "to be resource, boolean given")
        return space.w_False
    assert isinstance(w_res, W_FileResource)
    if not w_res.is_valid():
        space.ec.warn("feof(): %d is not a valid "
                      "stream resource" % w_res.res_id)
    return space.newbool(w_res.feof())


@wrap(['space', FileResourceArg(False)], error=False)
def fflush(space, w_res):
    """ fflush - Flushes the output to a file """
    if w_res.tp == space.tp_bool:
        space.ec.warn("fflush() expects parameter 1 "
                      "to be resource, boolean given")
        return space.w_False
    out = w_res.flush()
    return space.newbool(out)


@wrap(['space', FileResourceArg(False)], error=False)
def fgetc(space, w_res):
    """ fgetc - Gets character from file pointer """
    if w_res.tp == space.tp_bool:
        space.ec.warn("fgetc() expects parameter 1 "
                      "to be resource, boolean given")
        return space.w_False
    assert isinstance(w_res, W_FileResource)

    if not w_res.is_valid():
        space.ec.warn("fgetc(): %s is not a valid"
                      " stream resource" % w_res.res_id)
        return space.w_False
    try:
        res = w_res.read(1)
        return space.newstr(res)
    except IOError:
        return space.w_False


@wrap(['space', FileResourceArg(False),
       Optional(LongArg(False)), Optional(StringArg(False)),
       Optional(StringArg(False)), Optional(StringArg(False))])
def fgetcsv(space, w_res, length=0, delimiter=',', enclosure='"', escape='\\'):
    """ fgetcsv - Gets line from file pointer and parse for CSV fields """
    raise NotImplementedError


@wrap(['space', FileResourceArg(False), 'num_args',
       Optional(int)], error=False)
def fgets(space, w_res, num_args, size=0):
    """ fgets - Gets line from file pointer """
    if num_args > 1 and size <= 0:
        space.ec.warn("fgets(): Length parameter must be greater than 0")
        return space.w_False
    if size == 1:
        return space.w_False

    if w_res.tp == space.tp_file_res and not w_res.is_valid():
        assert isinstance(w_res, W_FileResource)
        space.ec.warn("fgets(): %d is not a valid stream resource"
                      % w_res.res_id)
        return space.w_False
    if w_res.tp == space.tp_bool:
        space.ec.warn("fgets() expects parameter 1 to be "
                      "resource, boolean given")
        return space.w_False
    assert isinstance(w_res, W_FileResource)
    if num_args == 1:
        try:
            line = w_res.readline()
            if not line:
                return space.w_False
            return space.newstr(line)
        except IOError:
            return space.w_False
    try:
        idx = 1
        c = w_res.read(1)
        line = StringBuilder()
        line.append(c)
        while c != os.linesep:
            if idx > size - 2:
                break
            idx += 1
            c = w_res.read(1)
            line.append(c)
            if not c:
                w_res.eof = True
        return space.newstr(line.build())
    except IOError:
        return space.w_False


@wrap(['space'])
def fgetss(space):
    """ fgetss - Gets line from file pointer and strip HTML tags """
    raise NotImplementedError()


@wrap(['space', FilenameArg()])
def file_exists(space, fname):
    """ file_exists - Checks whether a file or directory exists """
    if not is_in_basedir(space, 'file_exists', fname):
        return space.w_False
    if not _valid_fname(fname):
        space.ec.warn("file_exists() expects parameter 1 "
                      "to be a valid path, string given")
        return space.w_Null
    try:
        return space.wrap(rpath.exists(fname))
    except TypeError:
        return space.w_False


@wrap(['space', FilenameArg(None), 'num_args', Optional(bool),
       Optional(Nullable(StreamContextArg(None))),
       Optional(int), Optional(int)])
def file_get_contents(space, fname, num_args, use_include_path=False,
                      w_ctx=None, offset=-1, maxlen=0):
    """ file_get_contents - Reads entire file into a string """
    fname, read_filters, write_filters = _parse_wrapper(fname)
    if fname == "" or fname is None:
        space.ec.warn("file_get_contents(): Filename cannot be empty")
        return space.w_False
    if not _valid_fname(fname):
        space.ec.warn("file_get_contents() expects parameter 1 to "
                      "be a valid path, string given")
        return space.w_Null
    if not is_in_basedir(space, 'file_get_contents', fname):
        space.ec.warn("file_get_contents(%s): failed to open stream: %s"
                      % (fname, 'Operation not permitted'))
        return space.w_False

    w_res = None

    try:
        w_res = _fopen(space, fname, 'r', True, w_ctx)
    except FopenError, e:
        for r in e.reasons:
            space.ec.warn("file_get_contents(%s): %s" % (fname, r))
        return space.w_False

    assert isinstance(w_res, W_FileResource)
    res = w_res.read(-1)
    w_res.close()
    if num_args >= 4 and offset >= 0:
        if num_args >= 5:
            if maxlen < 0:
                space.ec.warn("file_get_contents(): length must be "
                              "greater than or equal to zero")
                return space.w_False
            res = res[offset:maxlen + offset]
        else:
            res = res[offset:]

    return space.newstr(res)


@wrap(['space', FilenameArg(None), W_Root,
       Optional(LongArg(None)), Optional(Nullable(StreamContextArg(None)))])
def file_put_contents(space, fname, w_data, mode=0, w_ctx=None):
    """ file_put_contents - Write a string to a file
        'FILE_USE_INCLUDE_PATH': 1,
        'LOCK_EX': 2,
        'FILE_APPEND': 8,
        """
    if not is_in_basedir(space, 'file_put_contents', fname):
        space.ec.warn("file_put_contents(%s): failed to open stream: %s " %
                      (fname, 'Operation not permitted'))
        return space.w_False
    if not _valid_fname(fname):
        space.ec.warn("file_put_contents() expects parameter 1 "
                      "to be a valid path, string given")
        return space.w_Null

    if fname == "" or fname == '\x00':
        space.ec.warn("file_put_contents(): Filename cannot be empty")
        return space.w_False

    append = mode & 8 != 0
    if w_data.tp == space.tp_stream_context:
        if not w_data.is_valid():
            space.ec.warn("file_put_contents(): supplied resource "
                          "is not a valid stream resource")
            return space.w_False
        else:
            raise NotImplementedError()
    if w_data.tp == space.tp_array:
        w_data = space.array_to_string_conversion(w_data)
    data = w_data.maybe_str(space)
    if data is None:
        return space.w_False
    try:
        if append:
            f = open(fname, 'a+')
        else:
            f = open(fname, 'w+')
        f.write(data)
        f.close()
        return space.newint(len(data))
    except OSError, e:
        space.ec.warn("file_put_contents(%s): failed "
                      "to open stream: %s" % (fname, os.strerror(e.errno)))
        return space.w_False
    except IOError, e:
        if not we_are_translated():
            space.ec.warn("file_put_contents(%s): failed "
            "to open stream: %s" % (fname, e.strerror))
            return space.w_False
        assert False, "unreachable code"


@wrap(['space', FilenameArg(None), Optional(LongArg(None)),
       Optional(Nullable(StreamContextArg(None)))], name="file")
def _file(space, fname, flags=0, w_ctx=None):
    """ file - Reads entire file into an array
        'FILE_USE_INCLUDE_PATH': 1,
        'FILE_IGNORE_NEW_LINES': 2,
        'FILE_SKIP_EMPTY_LINES': 4,
        'FILE_NO_DEFAULT_CONTEXT': 16,

    """
    if not is_in_basedir(space, 'file', fname):
        space.ec.warn("file(%s): failed to open stream: %s " %
                      (fname, 'Operation not permitted'))
        return space.w_False
    if flags > 23 or flags < 0:
        space.ec.warn("file(): '%d' flag is not supported" % flags)
        return space.w_False

    if fname == "":
        space.ec.warn("file(): Filename cannot be empty")
        return space.w_False

    ignore_new_lines = flags & 2 != 0
    skip_empty_lines = flags & 4 != 0
    try:
        _fname = rpath.normpath(fname)
        arr_list = []
        fstream = open(_fname)
        line = fstream.readline()
        while line != '':
            if ignore_new_lines:
                line = line.rstrip('\n')
            if skip_empty_lines and line == "":
                line = fstream.readline()
                continue
            arr_list.append(space.newstr(line))
            line = fstream.readline()
        return space.new_array_from_list(arr_list)
    except OSError:
        space.ec.warn("file(%s): failed to open stream: "
                      "No such file or directory" % fname)
        return space.w_False
    except IOError:
        space.ec.warn("file(%s): failed to open stream: "
                      "No such file or directory" % fname)
        return space.w_False


@wrap(['space', FilenameArg(None)])
def fileatime(space, fname):
    """ fileatime - Gets last access time of file """
    if not is_in_basedir(space, 'fileatime', fname):
        return space.w_False
    if fname == "":
        return space.w_Null
    try:
        res = os.stat(fname).st_atime
        return space.wrap(int(res))
    except OSError:
        space.ec.warn("fileatime(): stat failed for %s" % fname)
        return space.w_False


@wrap(['space', str])
def filectime(space, fname):
    """ filectime - Gets inode change time of file """
    if not is_in_basedir(space, 'filectime', fname):
        return space.w_False
    if fname == "":
        return space.w_Null
    try:
        res = os.stat(fname).st_ctime
        return space.wrap(int(res))
    except OSError:
        space.ec.warn("filectime(): stat failed for %s" % fname)
        return space.w_False


def _filegroup(space, fname):
    if not is_in_basedir(space, 'filegroup', fname):
        return space.w_False
    if not _valid_fname(fname):
        space.ec.warn("filegroup() expects parameter 1 to "
                      "be a valid path, string given")
        return space.w_Null
    if fname == "":
        return space.w_False
    try:
        res = os.stat(fname).st_gid
        return space.wrap(res)
    except OSError:
        space.ec.warn("filegroup(): stat failed for %s" % fname)
        return space.w_False
    except TypeError:
        return space.w_False


@wrap(['space', FilenameArg(None)])
def filegroup(space, fname):
    """ filegroup - Gets file group """
    return _filegroup(space, fname)


def _fileinode(space, fname):
    if not is_in_basedir(space, 'fileinode', fname):
        return space.w_False
    if not _valid_fname(fname):
        space.ec.warn("fileinode() expects parameter 1 to "
                      "be a valid path, string given")
        return space.w_Null
    if fname == "":
        return space.w_False

    try:
        res = os.stat(fname).st_ino
        return space.wrap(res)
    except OSError:
        space.ec.warn("fileinode(): stat failed for %s" % fname)
        return space.w_False
    except TypeError:
        return space.w_False


@wrap(['space', FilenameArg(None)])
def fileinode(space, fname):
    """ fileinode - Gets file inode """
    return _fileinode(space, fname)


@wrap(['space', FilenameArg(None)])
def filemtime(space, fname):
    """ filemtime - Gets file modification time """
    if not is_in_basedir(space, 'filemtime', fname):
        return space.w_False
    if fname == "":
        return space.w_Null
    try:
        res = os.stat(fname).st_mtime
        return space.wrap(int(res))
    except OSError:
        space.ec.warn("filemtime(): stat failed for %s" % fname)
        return space.w_False


@wrap(['space', FilenameArg(None)])
def fileowner(space, fname):
    """ fileowner - Gets file owner """
    if not is_in_basedir(space, 'fileowner', fname):
        return space.w_False
    if not _valid_fname(fname):
        space.ec.warn("fileowner() expects parameter 1 to "
                      "be a valid path, string given")
        return space.w_Null
    if fname == "":
        return space.w_False

    try:
        res = os.stat(fname).st_uid
        return space.wrap(res)
    except OSError:
        space.ec.warn("fileowner(): stat failed for %s" % fname)
        return space.w_False
    except TypeError:
        return space.w_False


@wrap(['space', FilenameArg(None)])
def fileperms(space, fname):
    """ fileperms - Gets file permissions """
    if not is_in_basedir(space, 'fileperms', fname):
        return space.w_False
    if not _valid_fname(fname):
        space.ec.warn("fileperms() expects parameter 1 to "
                      "be a valid path, string given")
        return space.w_Null
    if fname == "":
        return space.w_False

    try:
        res = os.stat(fname).st_mode
        return space.wrap(res)
    except OSError:
        space.ec.warn("fileperms(): stat failed for %s" % fname)
        return space.w_False
    except TypeError:
        return space.w_False


@wrap(['space', FilenameArg(None)])
def filesize(space, fname):
    """ filesize - Gets file size """
    if not is_in_basedir(space, 'filesize', fname):
        return space.w_False
    if fname == "":
        return space.w_False

    try:
        assert fname is not None
        res = os.stat(fname).st_size
        return space.wrap(res)
    except OSError:
        space.ec.warn("filesize(): stat failed for %s" % fname)
        return space.w_False
    except TypeError:
        return space.w_False


def _filetype(space, fname):
    _type = "unknown"
    assert fname is not None
    mode = os.lstat(fname).st_mode
    if mode & 0170000 == 0010000:
        _type = "fifo"
    if mode & 0170000 == 0020000:
        _type = "char"
    if mode & 0170000 == 0040000:
        _type = "dir"
    if mode & 0170000 == 0060000:
        _type = "block"
    if mode & 0170000 == 0100000:
        _type = "file"
    if mode & 0170000 == 0120000:
        _type = "link"
    if mode & 0170000 == 0140000:
        _type = "socket"
    return space.wrap(_type)


@wrap(['space', FilenameArg(None)])
def filetype(space, fname):
    """ filetype - Gets file type
    fifo, char, dir, block, link, file, socket and unknown """
    if not is_in_basedir(space, 'filetype', fname):
        return space.w_False
    if fname == "":
        return space.w_False
    try:
        return _filetype(space, fname)
    except OSError:
        space.ec.warn("filetype(): Lstat failed for %s" % fname)
        return space.w_False
    except TypeError:
        return space.w_False


""" flock - Portable advisory file locking """
""" fnmatch - Match fname against a pattern """


class FopenError(Exception):
    def __init__(self, reasons=[]):
        self.reasons = reasons


def _parse_wrapper(fname):
    write_filters = []
    read_filters = []

    if fname == 'php://memory':
        pass
    elif fname == 'php://stdin':
        pass
    elif fname == 'php://stdout':
        pass
    elif fname == 'php://output':
        pass
    elif fname == 'php://stderr':
        pass
    elif fname.startswith('php://temp'):
        # looks like php ingore maxmemory argument
        fname = 'php://temp'
    elif fname.startswith('php://filter/'):
        filters = fname[len('php://filter/'):]
        for f in filters.split('/'):
            if f.startswith('resource='):
                _, fname = f.split('=')
                if fname == "":
                    raise FopenError(['Filename cannot be empty'])
            elif f.startswith('read='):
                _, rfilter = f.split('=')
                read_filters.append(rfilter)
            elif f.startswith('write='):
                _, wfilter = f.split('=')
                write_filters.append(wfilter)
            else:
                read_filters.append(f)
                write_filters.append(f)
    elif fname.startswith('php://fd/'):
        if fname == 'php://':
            raise FopenError(['Invalid php:// URL specified',
                     'failed to open stream: operation failed'])
        path = fname[len('php://fd/'):]
        try:
            int_fname = int(path)
            if int_fname < 0:
                raise FopenError(
                        ["failed to open stream: The file descriptors "
                         "must be non-negative numbers smaller than 22"])
        except ValueError:
            raise FopenError(
                    ["failed to open stream: php://fd/ stream must be "
                     "specified in the form php://fd/<orig fd>"])

    elif fname.startswith('file://'):
        fname = fname[len('file://'):]

    return fname, read_filters, write_filters


def _fopen(space, fname, mode, use_include_path=False, w_ctx=None):
    fname, read_filters, write_filters = _parse_wrapper(fname)

    if fname == "" or fname is None:
        raise FopenError(['Filename cannot be empty'])

    if not _valid_fname(fname):
        raise FopenError(["expects parameter 1 to be a "
                          "valid path, string given"])

    if use_include_path:
        fname = space.ec.interpreter.find_file(fname)

    if mode.startswith("x"):
        if rpath.exists(fname):
            raise FopenError(
                ["failed to open stream: File exists"])
        mode = mode.replace("x", "w")
    try:
        w_res = W_FileResource(space, fname, mode, read_filters, write_filters)
        w_res.open()
        return w_res
    except IOError, e:
        if not we_are_translated():
            raise FopenError(
                ["failed to open stream: %s" % e.strerror])
        assert False  # RPython does not raise IOError
    except OSError:
        return space.w_False


@wrap(['space', FilenameArg(False), str, Optional(BoolArg(False)),
       Optional(StreamContextArg(False))], error=False)
def fopen(space, fname, mode, use_include_path=False, w_ctx=None):
    """ fopen - Opens file or URL """
    if not is_in_basedir(space, 'fopen', fname):
        space.ec.warn("fopen(%s): failed to open stream: "
                      "Operation not permitted" % fname)
        return space.w_False

    try:
        return _fopen(space, fname, mode, use_include_path, w_ctx)
    except FopenError as e:
        for r in e.reasons:
            space.ec.warn("fopen(%s): %s" % (fname, r))
        return space.w_False


@wrap(['space', 'args_w'])
def fpassthru(space, args_w):
    """ fpassthru - Output all remaining data on a file pointer """
    if len(args_w) != 1:
        space.ec.warn("fpassthru() expects exactly "
                      "1 parameter, %d given" % len(args_w))
        return space.w_False
    w_res = args_w[0]
    if w_res.tp != space.tp_file_res:
        space.ec.warn("fpassthru() expects parameter 1 to "
                      "be resource, %s given" % space.get_type_name(w_res.tp))
        return space.w_False
    bytes_throu = w_res.passthru()
    return space.newint(bytes_throu)

""" fputcsv - Format line as CSV and write to file pointer """


@wrap(['space', FileResourceArg(False), int], error=False)
def fread(space, w_res, length):
    """ fread - Binary-safe file read """
    if w_res.tp == space.tp_bool:
        space.ec.warn("fread() expects parameter 1 to be "
                      "resource, boolean given")
        return space.w_False
        #return space.newstr("")
    assert isinstance(w_res, W_FileResource)

    if not w_res.is_valid():
        space.ec.warn("fread(): %d is not a valid "
                      "stream resource" % w_res.int_w(space))
        return space.w_False

    if length < 1:
        space.ec.warn("fread(): Length parameter must be greater than 0")
        return space.w_False
    try:
        _str = w_res.read(length)
        if _str is not None:
            return space.newstr(_str)
        else:
            return space.w_False
    except IOError:
        return space.newstr("")
        #return space.w_False


""" fscanf - Parses input from a file according to a format """


@wrap(['space', FileResourceArg(False), LongArg(False),
       Optional(LongArg(False))], error=False)
def fseek(space, w_res, length, mode=0):
    """ fseek - Seeks on a file pointer """
    if w_res.tp == space.tp_bool:
        space.ec.warn("fseek() expects parameter 1 "
                      "to be resource, boolean given")
        return space.w_False

    if not w_res.is_valid():
        space.ec.warn("fseek(): %d is not a valid "
                      "stream resource" % w_res.int_w(space))
        return space.w_False
    return _fseek(space, w_res, length, mode)


def _fseek(space, w_res, length, mode):
    try:
        w_res.seek(length, mode)
        return space.newint(0)
    except IOError:
        return space.newint(-1)
    except OverflowError:
        return space.newint(-1)


@wrap(['space', FileResourceArg(False)], error=False)
def fstat(space, w_res):
    """ fstat - Gets information about a file using an open file pointer """
    if w_res.tp == space.tp_bool:
        space.ec.warn("fstat() expects parameter 1 "
                      "to be resource, boolean given")
        return space.w_False
    return _fstat(space, w_res)


def _fstat(space, w_res):
    assert isinstance(w_res, W_FileResource)

    if not w_res.is_valid():
        space.ec.warn("fstat(): %d is not a valid "
                      "stream resource" % w_res.int_w(space))
        return space.w_False
    sr = os.stat(w_res.filename)
    rdict_w = OrderedDict()
    stats = [
        ("dev", space.newint(int(sr.st_dev))),
        ("ino", space.newint(int(sr.st_ino))),
        ("mode", space.newint(int(sr.st_mode))),
        ("nlink", space.newint(int(sr.st_nlink))),
        ("uid", space.newint(int(sr.st_uid))),
        ("gid", space.newint(int(sr.st_gid))),
        ("rdev", space.newint(int(sr.st_rdev))),
        ("size", space.newint(int(sr.st_size))),
        ("atime", space.newint(int(sr.st_atime))),
        ("mtime", space.newint(int(sr.st_mtime))),
        ("ctime", space.newint(int(sr.st_ctime))),
        ("blksize", space.newint(int(sr.st_blksize))),
        ("blocks", space.newint(int(sr.st_blocks)))]
    for i, s in enumerate(stats):
        _, stat = s
        rdict_w[str(i)] = stat
    for label, stat in stats:
        rdict_w[label] = stat
    return space.new_array_from_rdict(rdict_w)


@wrap(['space', FileResourceArg(False)], error=False)
def ftell(space, w_res):
    """ ftell - Returns the current position of the file read/write pointer """
    if w_res.tp == space.tp_bool:
        space.ec.warn("ftell() expects parameter 1 "
                      "to be resource, boolean given")
        return space.w_False

    if not w_res.is_valid():
        space.ec.warn("ftell(): %d is not a valid "
                      "stream resource" % w_res.int_w(space))
        return space.w_False
    pos = w_res.tell()
    return space.newint(pos)


@wrap(['space', FileResourceArg(False), int], error=False)
def ftruncate(space, w_res, size):
    """ ftruncate - Truncates a file to a given length """
    if w_res.tp == space.tp_bool:
        space.ec.warn("ftruncate() expects parameter 1 "
                      "to be resource, boolean given")
        return space.w_False
    if not w_res.is_valid():
        space.ec.warn("ftruncate(): %d is not a valid "
                      "stream resource" % w_res.int_w(space))
        return space.w_False
    try:
        res = w_res.truncate(size)
        return space.newbool(res)
    except IOError:
        return space.w_False
    except OSError:
        return space.w_False


@wrap(['space', FileResourceArg(False), W_Root, 'num_args', Optional(int)],
      aliases=["fputs"], error=False)
def fwrite(space, w_res, w_data, num_args, length=0):
    """ fwrite - Binary-safe file write """
    """ fputs - Alias of fwrite """
    if w_res.tp == space.tp_bool:
        space.ec.warn("fwrite() expects parameter 1 to "
                      "be resource, boolean given")
        return space.w_False
    if w_res.tp != space.tp_file_res:
        return space.newint(0)
    if w_data.tp == space.tp_array:
        space.ec.warn("fwrite() expects parameter 2 to be string, array given")
        return space.w_False

    data = space.str_w(w_data)
    assert isinstance(w_res, W_FileResource)
    if num_args == 3:
        if length <= 0:
            return space.newint(0)

    if not w_res.is_valid():
        space.ec.warn("fwrite(): %d is not a valid "
                      "stream resource" % w_res.res_id)
        return space.w_False

    try:
        if num_args == 3:
            n = w_res.write(data, length)
        else:
            n = w_res.writeall(data)
            w_res.flush()
        return space.newint(n)
    except IOError:
        return space.newint(0)
    except ValueError:
        return space.newint(0)

""" glob - Find pathnames matching a pattern """


@wrap(['space', FilenameArg(None)])
def is_dir(space, dname):
    """ is_dir - Tells whether the fname is a directory """
    if not is_in_basedir(space, 'is_dir', dname):
        return space.w_False
    if not _valid_fname(dname):
        space.ec.warn("is_dir() expects parameter 1 to "
                      "be a valid path, string given")
        return space.w_Null
    return _is_dir(space, dname)


def _is_dir(space, dname):
    try:
        assert dname is not None
        res = os.path.isdir(dname)
    except TypeError:
        res = False
    return space.wrap(res)


@wrap(['space', FilenameArg(None)])
def is_executable(space, fname):
    """ is_executable - Tells whether the fname is executable """
    if not is_in_basedir(space, 'is_executable', fname):
        return space.w_False
    if not _valid_fname(fname):
        space.ec.warn("is_executable() expects parameter 1 to "
                      "be a valid path, string given")
        return space.w_Null
    return _is_executable(space, fname)


def _is_executable(space, fname):
    try:
        assert fname is not None
        return space.wrap(os.access(fname, os.X_OK))
    except OSError:
        return space.w_False
    except TypeError:
        return space.w_False


def _is_file(space, fname):
    if not _valid_fname(fname):
        space.ec.warn("is_file() expects parameter 1 to "
                      "be a valid path, string given")
        return space.w_Null
    try:
        assert fname is not None
        return space.wrap(os.path.isfile(fname))
    except OSError:
        return space.w_False
    except TypeError:
        return space.w_False


@wrap(['space', FilenameArg(None)])
def is_file(space, fname):
    """ is_file - Tells whether the fname is a regular file """
    if not is_in_basedir(space, 'is_file', fname):
        return space.w_False
    return _is_file(space, fname)


@wrap(['space', FilenameArg(None)])
def is_link(space, fname):
    """ is_link - Tells whether the fname is a symbolic link """
    if not is_in_basedir(space, 'is_link', fname):
        return space.w_False
    return _is_link(space, fname)


def _is_link(space, fname):
    try:
        return space.wrap(os.path.islink(fname))
    except OSError:
        return space.w_False


def _is_readable(space, fname):
    if not is_in_basedir(space, 'is_readable', fname):
        return space.w_False
    if not _valid_fname(fname):
        space.ec.warn("is_readable() expects parameter 1 to "
                      "be a valid path, string given")
        return space.w_Null
    try:
        assert fname is not None
        return space.wrap(os.access(fname, os.R_OK))
    except OSError:
        return space.w_False
    except TypeError:
        return space.w_False


@wrap(['space', FilenameArg(None)])
def is_readable(space, fname):
    """ is_readable - Tells whether a file exists and is readable """
    return _is_readable(space, fname)


""" is_uploaded_file - Tells whether the file was uploaded via HTTP POST """


def _is_writable(space, fname):
    if not is_in_basedir(space, 'is_writable', fname):
        return space.w_False
    if not _valid_fname(fname):
        space.ec.warn("is_writeable() expects parameter 1 to "
                      "be a valid path, string given")
        return space.w_Null
    try:
        assert fname is not None
        return space.wrap(os.access(fname, os.W_OK))
    except OSError:
        return space.w_False
    except TypeError:
        return space.w_False


@wrap(['space', FilenameArg(None)], aliases=["is_writable"])
def is_writeable(space, fname):
    """ is_writable - Tells whether the fname is writable """
    """ is_writeable - Alias of is_writable """
    return _is_writable(space, fname)


""" lchgrp - Changes group ownership of symlink """
""" lchown - Changes user ownership of symlink """


@wrap(['space', FilenameArg(None), FilenameArg(None)], name="link")
def _link(space, source, dest):
    """ link - Create a hard link """
    if not is_in_basedir(space, 'link', rpath.realpath(dest)):
        return space.w_False
    if not is_in_basedir(space, 'link', rpath.realpath(source)):
        return space.w_False
    try:
        os.link(source, dest)
        return space.w_True
    except OSError, e:
        space.ec.warn("link(): %s" % os.strerror(e.errno))

        return space.w_False


@wrap(['space', FilenameArg(None)])
def linkinfo(space, fname):
    """ linkinfo - Gets information about a link """
    if not is_in_basedir(space, 'linkinfo', rpath.realpath(fname)):
        return space.w_False
    if fname == '':
        space.ec.warn("linkinfo(): No such file or directory")
        return space.newint(-1)
        #return space.w_False
    try:
        sr = os.lstat(fname)
        return space.newint(int(sr.st_dev))
    except OSError, e:
        space.ec.warn("linkinfo(): %s" % os.strerror(e.errno))
        return space.newint(-1)

""" lstat - Gives information about a file or symbolic link """


def _recursive_mkdir(path, mode):
    if not rpath.exists(path):
        head, tail = rpath.split(path)
        to_create = []
        if tail:
            to_create = [tail]
        while head:
            head, tail = rpath.split(head)
            if not tail:
                to_create.append(head)
                break
            to_create.append(tail)
        to_create.reverse()
        td = ""
        for p in to_create:
            td += p + '/'
            if not rpath.exists(td):
                os.mkdir(td, mode)


@wrap(['space', FilenameArg(None), Optional(LongArg(None)),
       Optional(BoolArg(None)), Optional(StreamContextArg(None))],
      name="mkdir", error=False)
def _mkdir(space, dirname, mode=0777, recursive=False, w_ctx=None):
    """ mkdir - Makes directory """
    mode = 0x7FFFFFFF & mode

    if not _valid_fname(dirname):
        space.ec.warn("mkdir() expects parameter 1 to "
                      "be a valid path, string given")
        return space.w_False

    if not is_in_basedir(space, 'mkdir', rpath.realpath(dirname)):
        return space.w_False

    try:
        if not os.path.isdir(dirname):
            if recursive:
                _recursive_mkdir(dirname, mode)
            else:
                os.mkdir(dirname, mode)
            return space.w_True
        else:
            space.ec.warn("mkdir(): No such file or directory")
            return space.w_False
    except OSError, e:
        space.ec.warn("mkdir(): %s" % os.strerror(e.errno))
        return space.w_False
    except TypeError:
        return space.w_False

""" move_uploaded_file - Moves an uploaded file to a new location """
""" parse_ini_file - Parse a configuration file """
""" parse_ini_string - Parse a configuration string """


@wrap(['space', str, Optional(W_Root)])
def pathinfo(space, path, w_mode=None):
    """ pathinfo - Returns information about a file path
    mode:
        'PATHINFO_DIRNAME': 1,
        'PATHINFO_BASENAME': 2,
        'PATHINFO_EXTENSION': 4,
        'PATHINFO_FILENAME': 8,
    """

    import math
    if w_mode is not None:
        if w_mode.tp == space.tp_int:
            mode = space.int_w(w_mode)
        elif w_mode.tp == space.tp_float:
            mode = space.float_w(w_mode)
            if mode < 1:
                mode = int(math.ceil(mode))
            else:
                mode = int(mode)
        elif w_mode.tp == space.tp_bool:
            if space.is_true(w_mode):
                mode = 1
            else:
                return space.newstr("")
        elif w_mode.tp == space.tp_null:
            return space.newstr("")
        else:
            space.ec.warn("pathinfo() expects parameter 2 "
                          "to be long, %s given"
                          % space.get_type_name(w_mode.tp))
            return space.w_Null
    else:
        mode = 0
    while path.endswith("//"):
        path = path[:-1]

    if path.endswith("/") and len(path) != 1:
        path = path[:-1]

    dirname = rpath.dirname(path)
    if dirname == "" and path != "":
        dirname = "."

    basename = rpath.basename(path)
    name_split = basename.rsplit('.', 1)
    if len(name_split) == 2:
        filename, extension = name_split
    else:
        filename, = name_split
        extension = ''

    if basename == ".":
        filename = ""

    if basename == "..":
        filename = "."

    if basename == "...":
        filename = ".."

    if mode & 1:
        return space.newstr(dirname)
    elif mode & 2:
        return space.newstr(basename)
    elif mode & 4:
        return space.newstr(extension)
    elif mode & 8:
        return space.newstr(filename)
    elif mode == 0:
        rdct_w = OrderedDict()
        if path != "":
            rdct_w['dirname'] = space.newstr(dirname)
        rdct_w['basename'] = space.newstr(basename)
        if extension != "" or basename.endswith("."):
            rdct_w['extension'] = space.newstr(extension)
        rdct_w['filename'] = space.newstr(filename)
        return space.new_array_from_rdict(rdct_w)
    return space.newstr("")


@wrap(['space', FileResourceArg(False)], error=False)
def pclose(space, w_res):
    """ pclose - Closes process file pointer """
    assert isinstance(w_res, W_FileResource)
    w_res.close()
    return space.newint(0)


@wrap(['space', str, str])
def popen(space, command, mode):
    """ popen - Opens process file pointer """
    try:
        r_pfile = create_popen_file(command, mode)
        w_res = W_FileResource(space, '<proc>', 'w+')
        w_res.resource = r_pfile
        w_res.state = 1
        return w_res
    except OSError:
        space.ec.warn("popen(%s,%s):" % (command, mode))
        return space.w_False


@wrap(['space', FilenameArg(False), Optional(BoolArg(False)),
      Optional(Nullable(StreamContextArg(False)))], error=False)
def readfile(space, fname, use_include_path=False, w_ctx=None):
    """ readfile - Outputs a file """
    fname, read_filters, write_filters = _parse_wrapper(fname)

    if fname == "" or fname is None:
        space.ec.warn("readfile(): Filename cannot be empty")
        return space.w_False
    if not _valid_fname(fname):
        space.ec.warn("readfile() expects parameter 1 to "
                      "be a valid path, string given")
        return space.w_Null
    if not is_in_basedir(space, 'readfile', fname):
        space.ec.warn("readfile(%s): failed to open stream: %s"
                      % (fname, 'Operation not permitted'))
        return space.w_False

    w_res = None
    try:
        w_res = _fopen(space, fname, 'r', use_include_path, w_ctx)
    except FopenError, e:
        for r in e.reasons:
            space.ec.warn("readfile(%s): %s" % (fname, r))
        return space.w_False

    l = w_res.passthru()
    assert isinstance(w_res, W_FileResource)
    w_res.close()
    return space.newint(l)


@wrap(['space', FilenameArg(None)])
def readlink(space, linkname):
    """ readlink - Returns the target of a symbolic link """
    if not is_in_basedir(space, 'readlink', linkname):
        return space.w_False

    if not _valid_fname(linkname):
        space.ec.warn("readlink() expects parameter 1 "
                      "to be a valid path, string given")
        return space.w_False
    try:
        return space.wrap(os.readlink(linkname))
    except OSError, e:
        space.ec.warn("readlink(): %s" % os.strerror(e.errno))
        return space.w_False

""" realpath_cache_get - Get realpath cache entries """
""" realpath_cache_size - Get realpath cache size """


@wrap(['space', FilenameArg(None)])
def realpath(space, fname):
    """ realpath - Returns canonicalized absolute pathname """
    if not is_in_basedir(space, 'realpath', fname):
        return space.w_False
    try:
        path = rpath.realpath(fname)
        if rpath.exists(path):
            return space.wrap(path)
        return space.w_False
    except OSError:
        space.ec.warn("realpath(): No such file or directory")
        return space.w_False


@wrap(['space', FilenameArg(False), FilenameArg(False),
       Optional(StreamContextArg(False))], error=False)
def rename(space, source, dest, w_ctx=None):
    """ rename - Renames a file or directory """
    if not is_in_basedir(space, 'rename', source):
        return space.w_False
    if not is_in_basedir(space, 'rename', dest):
        return space.w_False

    if not _valid_fname(source):
        space.ec.warn("rename() expects parameter 1 "
                      "to be a valid path, string given")
        return space.w_False
    if not _valid_fname(dest):
        space.ec.warn("rename() expects parameter 1 "
                      "to be a valid path, string given")
        return space.w_False

    try:
        os.rename(source, dest)
        return space.w_True
    except OSError, e:
        space.ec.warn("rename(%s,%s): %s" %
                      (source, dest, os.strerror(e.errno)))
        return space.w_False
    except TypeError:
        return space.w_False


@wrap(['space', FileResourceArg(False)], error=False)
def rewind(space, w_res):
    """ rewind - Rewind the position of a file pointer """
    if w_res.tp == space.tp_bool:
        space.ec.warn("rewind() expects parameter 1 "
                      "to be resource, boolean given")
        return space.w_False

    if not w_res.is_valid():
        space.ec.warn("rewind(): %d is not a valid "
                      "stream resource" % w_res.int_w(space))
        return space.w_False
    w_res.rewind()
    return space.w_True


@wrap(['space', FilenameArg(None), Optional(StreamContextArg(False))],
      name="rmdir", error=False)
def _rmdir(space, dirname, w_ctx=None):
    """ rmdir - Removes directory """
    if not is_in_basedir(space, 'rmdir', dirname):
        return space.w_False

    if not _valid_fname(dirname):
        space.ec.warn("rmdir(): No such file or directory")
        return space.w_False

    try:
        os.rmdir(dirname)
        return space.w_True
    except OSError, e:
        space.ec.warn("rmdir(%s): %s" % (dirname, os.strerror(e.errno)))
        return space.w_False
    except TypeError:
        return space.w_False

""" set_file_buffer - Alias of stream_set_write_buffer """


def _stat(space, fname):
    if fname == '':
        return space.w_False
    sr = os.stat(fname)
    rdict_w = OrderedDict()
    stats = [
        ("dev", space.newint(int(sr.st_dev))),
        ("ino", space.newint(int(sr.st_ino))),
        ("mode", space.newint(int(sr.st_mode))),
        ("nlink", space.newint(int(sr.st_nlink))),
        ("uid", space.newint(int(sr.st_uid))),
        ("gid", space.newint(int(sr.st_gid))),
        ("rdev", space.newint(int(sr.st_rdev))),
        ("size", space.newint(int(sr.st_size))),
        ("atime", space.newint(int(sr.st_atime))),
        ("mtime", space.newint(int(sr.st_mtime))),
        ("ctime", space.newint(int(sr.st_ctime))),
        ("blksize", space.newint(int(sr.st_blksize))),
        ("blocks", space.newint(int(sr.st_blocks)))
        ]
    for i, s in enumerate(stats):
        _, stat = s
        rdict_w[str(i)] = stat
    for label, stat in stats:
        rdict_w[label] = stat
    return space.new_array_from_rdict(rdict_w)


@wrap(['space', FilenameArg(None)])
def stat(space, fname):
    """ stat - Gives information about a file """
    if not is_in_basedir(space, 'stat', fname):
        return space.w_False

    try:
        return _stat(space, fname)
    except OSError:
        space.ec.warn("stat(): stat failed for %s" % fname)
        return space.w_False


@wrap(['space', FilenameArg(None)])
def lstat(space, fname):
    """ stat - Gives information about a file """
    if not is_in_basedir(space, 'lstat', fname):
        return space.w_False

    try:
        return _stat(space, fname)
    except OSError:
        space.ec.warn("lstat(): Lstat failed for %s" % fname)
        return space.w_False


@wrap(['space', FilenameArg(None), FilenameArg(None)])
def symlink(space, source, dest):
    """ symlink - Creates a symbolic link """
    if not is_in_basedir(space, 'symlink', rpath.realpath(source)):
        return space.w_False
    if not is_in_basedir(space, 'symlink', rpath.realpath(dest)):
        return space.w_False
    try:
        os.symlink(source, dest)
        return space.w_True
    except OSError,  e:
        space.ec.warn("symlink(): %s" % os.strerror(e.errno))
        return space.w_False


@wrap(['space', FilenameArg(None), FilenameArg(None)])
def tempnam(space, dname, prefix):
    """ tempnam - Create file with unique file name """
    if not is_in_basedir(space, 'tempnam', dname):
        return space.w_False
    if not _valid_fname(dname):
        space.ec.warn("tempnam() expects parameter 1 "
                      "to be a valid path, string given")
        return space.w_Null

    tmpname = os.tmpnam().split(os.path.sep)[-1]
    res = None
    try:
        if os.path.isdir(dname):
            res = rpath.join(dname, [prefix + tmpname])
        else:
            res = rpath.join("/tmp", [prefix + tmpname])
    except TypeError:
        return space.w_False
    if not is_in_basedir(space, 'tempname', res):
        return space.w_False

    try:
        w_res = W_FileResource(space, res, 'w+')
        w_res.open()
        w_res.chmod(0600)
        w_res.close()
        del w_res
    except TypeError:
        return space.w_False
    except IOError:
        return space.w_False

    return space.newstr(res)


@wrap(['space'])
def tmpfile(space):
    """ tmpfile - Creates a temporary file """
    w_res = W_FileResource(space, 'php://temp', 'w+')
    return w_res


@wrap(['space', FilenameArg(None), Optional(LongArg(None)),
       Optional(LongArg(None))])
def touch(space, fname, mtime=-1, atime=-1):
    """ touch - Sets access and modification time of file """
    if not is_in_basedir(space, 'touch', fname):
        return space.w_False

    if atime == -1 and mtime != -1:
        atime = mtime
    if atime != -1 and mtime == -1:
        mtime = atime
    if fname == "":
        return space.w_False
    try:
        if not rpath.exists(fname):
            open(fname, 'w').close()
        if atime != -1:
            os.utime(fname, (atime, mtime))
        return space.w_True
    except OSError as e:
        space.ec.warn("touch(): Unable to create file "
                      "%s because %s"
                      % (fname, os.strerror(e.errno)))
        return space.w_False
    except IOError, e:
        if not we_are_translated():
            space.ec.warn("touch(): Unable to create file "
                                "%s because %s"
            % (fname, os.strerror(e.errno)))
            return space.w_False
        assert False  # dead code

""" umask - Changes the current umask """


@wrap(['space', FilenameArg(None), Optional(StreamContextArg(False))],
      name="unlink", error=False)
def _unlink(space, fname, w_ctx=None):
    """ unlink - Deletes a file """
    if not is_in_basedir(space, 'unlink', fname):
        return space.w_False

    try:
        os.remove(fname)
        return space.w_True
    except OSError, e:
        space.ec.warn("unlink(%s): %s" % (fname, os.strerror(e.errno)))
        return space.w_False
    except TypeError:
        return space.w_False


########################### DIR FUNCS ############################

@wrap(['space', FilenameArg(False)], name="chdir", error=False)
def _chdir(space, dname):
    """ chdir - Change directory """
    if not is_in_basedir(space, 'chdir', dname):
        return space.w_False
    try:
        if not os.path.isdir(dname):
            space.ec.warn("chdir(): Not a directory (errno 20)")
        os.chdir(dname)
        return space.w_True
    except OSError:
        return space.w_False


@wrap(['space', FilenameArg(None)])
def chroot(space, dname):
    """ chroot - Change the root directory """
    if not is_in_basedir(space, 'chroot', dname):
        return space.w_False
    try:
        path = rpath.join(os.getcwd(), [dname])
        assert path is not None
        w_res = space.wrap(os.chroot(path))
        os.chdir('/')
        return w_res
    except OSError:
        return space.w_False


@wrap(['space', Optional(Resource(W_DirResource, True))])
def closedir(space, w_dir=None):
    """ closedir - Close directory handle """
    if w_dir:
        w_dir.close()
    else:
        last_res = space.ec.interpreter.last_dir_resource
        if last_res:
            last_res.close()
    return space.w_Null

""" dir - Return an instance of the Directory class """


@wrap(['space'], name="getcwd")
def _getcwd(space):
    """ getcwd - Gets the current working directory """
    return space.wrap(os.getcwd())


@wrap(['space', FilenameArg(None, expect="string"),
       Optional(Resource(W_DirResource, False))])
def opendir(space, dname, w_res=None):
    """ opendir - Open directory handle """
    if not is_in_basedir(space, 'opendir', dname):
        space.ec.warn("opendir(%s): failed to open dir: %s"
                      % (dname, 'Operation not permitted'))
        return space.w_False

    if dname == "":
        return space.w_False

    w_dir = W_DirResource(space, dname)
    w_res = w_dir.open()
    return w_res


@wrap(['space', Optional(Resource(W_DirResource, True))])
def readdir(space, w_dir=None):
    """ readdir - Read entry from directory handle """
    if w_dir is None:
        w_dir = space.ec.interpreter.last_dir_resource
    if not w_dir.is_valid():
        space.ec.warn("readdir(): %d is not a valid Directory resource"
                      % w_dir.res_id)
        return space.w_False

    else:
        return w_dir.read()


@wrap(['space', Optional(Resource(W_DirResource, True))])
def rewinddir(space, w_dir=None):
    """ rewinddir - Rewind directory handle """
    if w_dir is None:
        w_dir = space.ec.interpreter.last_dir_resource
    if not w_dir.is_valid():
        space.ec.warn("rewinddir(): %d is not a valid Directory resource"
                      % w_dir.res_id)
        return space.w_False

    else:
        w_dir.rewind()
        return space.w_Null


@wrap(['space', FilenameArg(None), Optional(LongArg(None)),
       Optional(StreamContextArg(None))])
def scandir(space, dname, sort=0, w_ctx=None):
    """ scandir - List files and directories inside the specified path """
    if not is_in_basedir(space, 'scandir', dname):
        space.ec.warn("scandir(%s): failed to open dir: "
                      "Operation not permitted" % dname)
        space.ec.warn("scandir(): (errno 1): Operation not permitted")
        return space.w_False

    if dname == "":
        space.ec.warn("scandir(): Directory name cannot be empty")
        return space.w_False
    try:
        w_lines = []
        for line in [".", ".."] + os.listdir(dname):
            w_lines.append(space.newstr(line))

        _sort(space, w_lines)
        if sort != 0:
            w_lines.reverse()

        arr_list = []
        for l in w_lines:
            arr_list.append(l)
        return space.new_array_from_list(arr_list)
    except OSError:
        space.ec.warn("scandir(%s): failed to open dir: "
                      "No such file or directory" % dname)
        space.ec.warn("scandir(): (errno 2): No such file "
                      "or directory")
        return space.w_False

########################### STREAM ###############################


@wrap(['space', 'args_w'])
def stream_context_create(space, args_w):
    return W_StreamContext(space)


@wrap(['space', W_Root])
def get_resource_type(space, w_obj):
    if space.is_resource(w_obj):
        return space.newstr(w_obj.get_resource_type())
    else:
        space.ec.warn("get_resource_type() expects parameter 1 "
                      "to be resource, %s given"
                      % space.get_type_name(w_obj.tp).lower())

    return space.w_Null


def is_in_basedir(space, func_name, path):
    interp = space.ec.interpreter
    basedir = interp.config.get_ini_str("open_basedir")
    if basedir:
        maxl = space.int_w(interp.locate_constant("PHP_MAXPATHLEN"))
        if len(path) > maxl:
            msg = ("%s(): File name is longer than the maximum allowed path "
                   "length on this platform (%d): %s" % (func_name, maxl, path))
            interp.warn(msg)
            return False

        res = 0
        dirs = basedir.split(";")
        for b in dirs:
            if rpath.realpath(path).startswith(rpath.realpath(b)):
                res += 1
            else:
                res -= 1
        if len(dirs) == res:
            return True
        if abs(res) <= len(dirs):
            interp.warn("%s(): open_basedir restriction in effect. "
                          "File(%s) is not within the allowed "
                          "path(s): (%s)" % (func_name, path, basedir))
            return False
    return True
