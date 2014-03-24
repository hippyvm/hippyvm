import os
from hippy.builtin import (wrap_method, Optional, ThisUnwrapper,
    handle_as_exception, StreamContextArg, Nullable)
from hippy.objects.instanceobject import W_InstanceObject
from hippy.objects.intobject import W_IntObject
from hippy.objects.resources.file_resource import W_FileResource
from hippy.error import PHPException
from hippy.builtin_klass import (def_class, k_RuntimeException,
    k_LogicException, GetterSetterWrapper)
from hippy.module.standard.file.funcs import (_is_dir, _is_file, _is_link,
    _is_executable, _is_readable, _is_writable, _filetype, _fseek, _fstat,
    _fopen, _basename, FopenError)
from rpython.rlib import rpath
from hippy import consts


class W_SplFileInfo(W_InstanceObject):
    file_name = None
    path_name = None

    def __init__(self, klass, dct_w):
        W_InstanceObject.__init__(self, klass, dct_w)

    def clone(self, interp, contextclass):
        w_res = W_InstanceObject.clone(self, interp, contextclass)
        w_res.file_name = self.file_name
        w_res.path_name = self.path_name
        return w_res


class W_SplFileObject(W_SplFileInfo):
    delimiter = None
    enclosure = None
    open_mode = None

    def __init__(self, klass, dct_w):
        W_InstanceObject.__init__(self, klass, dct_w)

    def clone(self, interp, contextclass):
        w_res = W_InstanceObject.clone(self, interp, contextclass)
        w_res.file_name = self.file_name
        w_res.path_name = self.path_name
        w_res.delimiter = self.delimiter
        w_res.enclosure = self.enclosure
        w_res.open_mode = self.open_mode
        return w_res


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo), str],
             name='SplFileInfo::__construct')
def construct(interp, this, file_name):
    this.file_name = file_name
    this.path_name = rpath.realpath(file_name)


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::__toString')
def spl_toString(interp, this):
    return interp.space.wrap(this.file_name)


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo), Optional(str)],
             name='SplFileInfo::getBasename')
def get_basename(interp, this, suffix=''):
    return _basename(interp.space, this.file_name, suffix)


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::getExtension')
def get_extension(interp, this):
    path = this.file_name
    filename = rpath.split(path)[1]
    name_split = filename.rsplit('.', 1)
    if len(name_split) == 2:
        filename, extension = name_split
    else:
        extension = ''
    return interp.space.wrap(extension)


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::getFilename')
def get_filename(interp, this):
    return _get_filename(interp, this)


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::getPath')
def get_path(interp, this):
    parts = this.file_name.split('/')
    parts.pop()
    path = ''
    for i in parts:
        path += i + '/'
    path = path.rstrip('/')
    return interp.space.wrap(path)


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::getPathname')
def get_pathname(interp, this):
    return interp.space.wrap(this.file_name)


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::getGroup', error_handler=handle_as_exception)
def get_group(interp, this):
    filename = this.file_name
    if not filename:
        return interp.space.w_False
    try:
        res = os.stat(filename).st_gid
        return interp.space.wrap(res)
    except OSError:
        raise PHPException(k_RuntimeException.call_args(
            interp, [interp.space.wrap(
                "SplFileInfo::getGroup(): stat failed for %s" % filename
                )]))


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::getInode', error_handler=handle_as_exception)
def get_inode(interp, this):
    filename = this.file_name
    if not filename:
        return interp.space.w_False
    try:
        res = os.stat(filename).st_ino
        return interp.space.wrap(res)
    except OSError:
        raise PHPException(k_RuntimeException.call_args(
            interp, [interp.space.wrap(
                "SplFileInfo::getInode(): stat failed for %s" % filename)]))


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::getOwner', error_handler=handle_as_exception)
def get_owner(interp, this):
    filename = this.file_name
    if not filename:
        return interp.space.w_False
    try:
        res = os.stat(filename).st_uid
        return interp.space.wrap(res)
    except OSError:
        raise PHPException(k_RuntimeException.call_args(
            interp, [interp.space.wrap(
                "SplFileInfo::getOwner(): stat failed for %s" % filename)]))


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::getPerms', error_handler=handle_as_exception)
def get_perms(interp, this):
    filename = this.file_name
    if not filename:
        return interp.space.w_False
    try:
        res = os.stat(filename).st_mode
        return interp.space.wrap(res)
    except OSError:
        raise PHPException(k_RuntimeException.call_args(
            interp, [interp.space.wrap(
                "SplFileInfo::getPerms(): stat failed for %s" % filename)]))


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::getSize', error_handler=handle_as_exception)
def get_size(interp, this):
    filename = this.file_name
    if not filename:
        return interp.space.w_False
    try:
        res = os.stat(filename).st_size
        return interp.space.wrap(res)
    except OSError:
        raise PHPException(k_RuntimeException.call_args(
            interp, [interp.space.wrap(
                "SplFileInfo::getSize(): stat failed for %s" % filename)]))


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::getType', error_handler=handle_as_exception)
def get_type(interp, this):
    filename = this.file_name
    if not filename:
        return interp.space.w_False
    try:
        return _filetype(interp.space, filename)
    except OSError:
        raise PHPException(k_RuntimeException.call_args(
            interp, [interp.space.wrap(
                "SplFileInfo::getType(): stat failed for %s" % filename)]))


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::isDir')
def is_dir(interp, this):
    filename = this.file_name
    assert filename is not None
    return _is_dir(interp.space, filename)


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::isLink')
def is_link(interp, this):
    filename = this.file_name
    assert filename is not None
    return _is_link(interp.space, filename)


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::isExecutable')
def is_executable(interp, this):
    return _is_executable(interp.space, this.file_name)


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::isFile')
def is_file(interp, this):
    return _is_file(interp.space, this.file_name)


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::isReadable')
def is_readable(interp, this):
    return _is_readable(interp.space, this.file_name)


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::isWritable')
def is_writable(interp, this):
    return _is_writable(interp.space, this.file_name)


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::getATime', error_handler=handle_as_exception)
def getatime(interp, this):
    filename = this.file_name
    assert filename is not None
    try:
        res = os.stat(filename).st_atime
        return interp.space.wrap(int(res))
    except OSError:
        raise PHPException(k_RuntimeException.call_args(
            interp, [interp.space.wrap(
                "SplFileInfo::getATime(): "
                "stat failed for %s" % this.file_name)]))


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::getCTime', error_handler=handle_as_exception)
def getctime(interp, this):
    filename = this.file_name
    assert filename is not None
    try:
        res = os.stat(filename).st_ctime
        return interp.space.wrap(int(res))
    except OSError:
        raise PHPException(k_RuntimeException.call_args(
            interp, [interp.space.wrap(
                "SplFileInfo::getCTime(): "
                "stat failed for %s" % this.file_name)]))


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::getMTime', error_handler=handle_as_exception)
def getmtime(interp, this):
    filename = this.file_name
    assert filename is not None
    try:
        res = os.stat(filename).st_mtime
        return interp.space.wrap(int(res))
    except OSError:
        raise PHPException(k_RuntimeException.call_args(
            interp, [interp.space.wrap(
                "SplFileInfo::getMTime(): "
                "stat failed for %s" % this.file_name)]))


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::getRealPath')
def get_realpath(interp, this):
    try:
        path = rpath.realpath(this.file_name)
        return interp.space.wrap(path)
    except OSError:
        return interp.space.w_False


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::getLinkTarget',
             error_handler=handle_as_exception)
def get_linktarget(interp, this):
    filename = this.file_name
    assert filename is not None
    try:
        return interp.space.wrap(os.readlink(filename))
    except OSError, e:
        raise PHPException(k_RuntimeException.call_args(
            interp, [interp.space.wrap(
                "SplFileInfo::getLinkTarget(): %s" % os.strerror(e.errno))]))


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo), Optional(str),
              Optional(bool), Optional(Nullable(StreamContextArg(None)))],
             name='SplFileInfo::openFile', error_handler=handle_as_exception)
def openfile(interp, this, open_mode='r', use_include_path=False, w_ctx=None):
    if open_mode == '':
        raise PHPException(k_RuntimeException.call_args(
            interp, [interp.space.wrap(
                    "SplFileInfo::openFile(): Invalid parameters")]))

    args = [interp.space.wrap(this.file_name), interp.space.wrap(open_mode),
             interp.space.wrap(use_include_path)]
    if w_ctx:
        if not interp.space.is_resource(w_ctx):
            raise PHPException(k_RuntimeException.call_args(
                interp, [interp.space.wrap(
                    "SplFileInfo::openFile() expects "
                    "parameter 3 to be resource, %s given"
                    % interp.space.get_type_name(w_ctx.tp).lower())]))
        args.append(w_ctx)
    try:
        file_object = SplFileObjectClass.call_args(interp, args)
        return file_object
    except OSError, e:
        raise PHPException(k_RuntimeException.call_args(
            interp, [interp.space.wrap(
                "SplFileInfo::openFile(): %s" % os.strerror(e.errno))]))


def _get_pathname(interp, this):
    return interp.space.wrap(this.path_name)


def _set_pathname(interp, this, value):
    raise NotImplementedError()


def _get_filename(interp, this):
    if this.file_name:
        i = this.file_name.rfind('/') + 1
        assert i >= 0
        return interp.space.wrap(this.file_name[i:])


def _set_filename(interp, this, value):
    raise NotImplementedError()


SplFileInfoClass = def_class(
        'SplFileInfo',
    methods=[construct,
             spl_toString,
             get_basename,
             get_extension,
             get_filename,
             get_path,
             get_pathname,
             get_group,
             get_inode,
             get_owner,
             get_perms,
             get_size,
             get_type,
             is_dir,
             is_link,
             is_executable,
             is_file,
             is_readable,
             is_writable,
             getatime,
             getctime,
             getmtime,
             get_realpath,
             get_linktarget,
             openfile],
    properties=[GetterSetterWrapper(_get_pathname, _set_pathname,
                                    "pathName", consts.ACC_PRIVATE),
                GetterSetterWrapper(_get_filename, _set_filename,
                                    "fileName", consts.ACC_PRIVATE), ],
        instance_class=W_SplFileInfo
        )


SFO_DROP_NEW_LINE = 1
SFO_READ_AHEAD = 2
SFO_SKIP_EMPTY = 4
SFO_READ_CSV = 8


def _sfo_readline(interp, sfo):
    if sfo.open_mode not in ('w', 'a', 'x', 'c'):
        return sfo.w_res.readline(sfo.flags & SFO_DROP_NEW_LINE)
    else:
        raise PHPException(k_RuntimeException.call_args(
            interp, [interp.space.wrap("SplFileObject: File cannot be read")]))


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject), str, Optional(str),
              Optional(bool), Optional(Nullable(StreamContextArg(None)))],
             name='SplFileObject::__construct',
             error_handler=handle_as_exception)
def sfo_construct(interp, this, filename, open_mode='r',
                  use_include_path=False, w_ctx=None):
    this.file_name = filename
    this.path_name = rpath.realpath(filename)
    this.delimiter = ","
    this.enclosure = '"'
    this.flags = 0
    this.open_mode = open_mode
    this.use_include_path = use_include_path
    this.w_res = None
    this.max_line_len = 0

    if w_ctx:
        if not interp.space.is_resource(w_ctx):
            raise PHPException(k_RuntimeException.call_args(
                interp, [interp.space.wrap(
                    "SplFileObject::__construct() expects "
                    "parameter 4 to be resource, %s given"
                    % interp.space.get_type_name(w_ctx.tp).lower())]))

    assert filename is not None
    if os.path.isdir(filename):
        raise PHPException(k_LogicException.call_args(
            interp, [interp.space.wrap(
                "Cannot use SplFileObject with directories"
                )]))
    try:
        this.w_res = _fopen(interp.space, filename, this.open_mode,
                            use_include_path, w_ctx)
        if this.w_res == interp.space.w_False:
            raise PHPException(k_RuntimeException.call_args(
                interp, [interp.space.wrap(
                "SplFileObject::__construct(): Failed to open stream")]))
    except FopenError as e:
        raise PHPException(k_RuntimeException.call_args(interp,
            [interp.space.wrap(e.reasons.pop())]))


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject)],
             name='SplFileObject::rewind')
def sfo_rewind(interp, this):
    try:
        this.w_res.rewind()
    except OSError, e:
        raise PHPException(k_RuntimeException.call_args(
            interp, [interp.space.wrap(
                "SplFileObject::rewind(): %s" % os.strerror(e.errno))]))
    if this.flags & SFO_READ_AHEAD:
        _sfo_readline(interp, this)


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject)],
             name='SplFileObject::valid')
def sfo_valid(interp, this):
    return interp.space.newbool(not this.w_res.feof())


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject), int],
             name='SplFileObject::seek')
def sfo_seek(interp, this, line_pos):
    if line_pos < 0:
        raise PHPException(k_LogicException.call_args(
            interp, [interp.space.wrap(
                "SplFileObject::seek(): Can't seek file %s "
                "to negative line %d" % (this.file_name, line_pos))]))
    this.w_res.seek_to_line(line_pos, this.flags & SFO_DROP_NEW_LINE)


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject)],
             name='SplFileObject::getChildren')
def sfo_get_children(interp, this):
    return interp.space.w_Null


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject)],
             name='SplFileObject::hasChildren')
def sfo_has_children(interp, this):
    return interp.space.w_False


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject), str, Optional(int)],
             name='SplFileObject::fwrite')
def sfo_fwrite(interp, this, data, length=-1):
    try:
        if length > 0:
            n = this.w_res.write(data, length)
        else:
            n = this.w_res.writeall(data)
        this.w_res.flush()
        return interp.space.newint(n)
    except IOError:
        return interp.space.w_Null
    except ValueError:
        return interp.space.w_Null


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject)],
             name='SplFileObject::fgetc')
def sfo_fgetc(interp, this):
    w_res = this.w_res
    assert isinstance(w_res, W_FileResource)
    res = w_res.read(1)
    if w_res.feof():
        return interp.space.w_False
    if res == os.linesep:
        w_res.cur_line_no += 1
    return interp.space.newstr(res)


def _fgets(interp, this):
    line = _sfo_readline(interp, this)
    w_res = this.w_res
    assert isinstance(w_res, W_FileResource)
    if not line:
        w_res.eof = True
        return interp.space.w_False
    return interp.space.newstr(line)


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject), 'args_w'],
             name='SplFileObject::fgets',
             error_handler=handle_as_exception)
def sfo_fgets(interp, this, args_w=[]):
    if len(args_w) != 0:
        interp.space.ec.warn("SplFileObject::fgets() expects exactly 0 "
            "parameters, %d given" % len(args_w))
        return interp.space.w_Null
    try:
        return _fgets(interp, this)
    except IOError:
        raise PHPException(k_RuntimeException.call_args(
            interp, [interp.space.wrap(
                "SplFileObject::fgets(): File cannot be read")]))


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject)],
             name='SplFileObject::getCurrentLine',
             error_handler=handle_as_exception)
def sfo_get_current_line(interp, this):
    try:
        return _fgets(interp, this)
    except IOError:
        raise PHPException(k_RuntimeException.call_args(
            interp, [interp.space.wrap(
                "SplFileObject::fgets(): File cannot be read")]))


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject)],
             name='SplFileObject::key')
def sfo_key(interp, this):
    w_res = this.w_res
    assert isinstance(w_res, W_FileResource)
    return interp.space.newint(w_res.cur_line_no)


def _current(interp, this):
    w_res = this.w_res
    assert isinstance(w_res, W_FileResource)
    res = w_res.cur_line
    if not res:
        res = _sfo_readline(interp, this)
    return interp.space.wrap(res)


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject)],
             name='SplFileObject::current')
def sfo_current(interp, this):
    return _current(interp, this)


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject)],
             name='SplFileObject::__toString')
def sfo_tostring(interp, this):
    return _current(interp, this)


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject)],
             name='SplFileObject::next')
def sfo_next(interp, this):
    w_res = this.w_res
    assert isinstance(w_res, W_FileResource)
    w_res.cur_line = None
    if this.flags & SFO_READ_AHEAD:
        _sfo_readline(interp, this)
    w_res.cur_line_no += 1


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject)],
             name='SplFileObject::eof')
def sfo_eof(interp, this):
    return interp.space.newbool(this.w_res.feof())


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject)],
             name='SplFileObject::fflush')
def sfo_fflush(interp, this):
    res = this.w_res.flush()
    return interp.space.newbool(res)


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject)],
             name='SplFileObject::fstat')
def sfo_fstat(interp, this):
    return _fstat(interp.space, this.w_res)


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject)],
             name='SplFileObject::ftell')
def sfo_ftell(interp, this):
    pos = this.w_res.tell()
    return interp.space.newint(pos)


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject), int],
             name='SplFileObject::ftruncate')
def sfo_ftruncate(interp, this, size):
    res = this.w_res.truncate(size)
    return interp.space.newbool(res)


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject), int, Optional(int)],
             name='SplFileObject::fseek')
def sfo_fseek(interp, this, offset, whence=0):
    return _fseek(interp.space, this.w_res, offset, whence)


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo), int, Optional(int)],
             name='SplFileObject::fpassthru')
def sfo_fpassthru(interp, this, offset, whence=0):
    bytes_thru = this.w_res.passthru()
    return interp.space.newint(bytes_thru)


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileObject::getMaxLineLen')
def sfo_get_max_line_len(interp, this):
    return interp.space.newint(this.max_line_len)


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject), int],
             name='SplFileObject::setMaxLineLen',
             error_handler=handle_as_exception)
def sfo_set_max_line_len(interp, this, max_len):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject)],
             name='SplFileObject::fgetss')
def sfo_fgetss(interp, this):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject)],
             name='SplFileObject::fgetcsv')
def sfo_fgetcsv(interp, this):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject)],
             name='SplFileObject::fputcsv')
def sfo_fputcsv(interp, this):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject)],
             name='SplFileObject::flock')
def sfo_flock(interp, this):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject)],
             name='SplFileObject::fscanf')
def sfo_fscanf(interp, this):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject)],
             name='SplFileObject::getCsvControl')
def sfo_get_csv_control(interp, this):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject)],
             name='SplFileObject::setCsvControl')
def sfo_set_csv_control(interp, this):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject)],
             name='SplFileObject::getFlags')
def sfo_get_flags(interp, this):
    return interp.space.wrap(this.flags)


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject), int],
             name='SplFileObject::setFlags')
def sfo_set_flags(interp, this, flags):
    this.flags = flags


def _get_openmode(interp, this):
    return interp.space.wrap(this.open_mode)


def _set_openmode(interp, this, w_value):
    raise NotImplementedError()


def _get_delimiter(interp, this):
    return interp.space.wrap(this.delimiter)


def _set_delimiter(interp, this, w_value):
    raise NotImplementedError()


def _get_enclosure(interp, this):
    return interp.space.wrap(this.enclosure)


def _set_enclosure(interp, this, w_value):
    raise NotImplementedError()


SplFileObjectClass = def_class(
    'SplFileObject',
    [sfo_construct, sfo_rewind, sfo_valid, sfo_key, sfo_current, sfo_next,
     sfo_seek, sfo_get_children, sfo_has_children, sfo_fwrite, sfo_eof,
     sfo_fgets, sfo_fgetc, sfo_tostring, sfo_get_max_line_len, sfo_fgetss,
     sfo_set_max_line_len, sfo_fflush, sfo_fgetcsv, sfo_flock, sfo_fputcsv,
     sfo_fscanf, sfo_fseek, sfo_fstat, sfo_ftell, sfo_ftruncate,
     sfo_get_csv_control, sfo_set_csv_control, sfo_get_flags, sfo_set_flags,
     sfo_get_current_line, sfo_fpassthru],
    properties=[GetterSetterWrapper(_get_openmode, _set_openmode,
                                    "openMode", consts.ACC_PRIVATE),
                GetterSetterWrapper(_get_delimiter, _set_delimiter,
                                    "delimiter", consts.ACC_PRIVATE),
                GetterSetterWrapper(_get_enclosure, _set_enclosure,
                                    "enclosure", consts.ACC_PRIVATE), ],
    constants=[(
        'DROP_NEW_LINE', W_IntObject(1)), ('READ_AHEAD', W_IntObject(2)),
        ('SKIP_EMPTY', W_IntObject(4)), ('READ_CSV', W_IntObject(8))],
    implements=["RecursiveIterator", "SeekableIterator"],
    instance_class=W_SplFileObject,
    extends='SplFileInfo',)
