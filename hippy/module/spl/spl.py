import os
from hippy.builtin import (wrap_method, Optional, ThisUnwrapper,
    handle_as_exception, StreamContextArg, Nullable)
from hippy.objects.instanceobject import W_InstanceObject
from hippy.objects.intobject import W_IntObject
from hippy.objects.resources.file_resource import W_FileResource
from hippy.objects.resources.dir_resource import W_DirResource
from hippy.error import PHPException
from hippy.builtin_klass import (def_class, k_RuntimeException,
    k_LogicException, k_UnexpectedValueException, GetterSetterWrapper)
from hippy.module.spl.interface import k_SeekableIterator, k_RecursiveIterator
from hippy.module.standard.file.funcs import (_is_dir, _is_file, _is_link,
    _is_executable, _is_readable, _is_writable, _filetype, _fseek, _fstat,
    _fopen, _basename, FopenError)
from rpython.rlib import rpath
from hippy import consts


class W_SplFileInfo(W_InstanceObject):
    def clone(self, interp, contextclass):
        w_res = W_InstanceObject.clone(self, interp, contextclass)
        assert isinstance(w_res, W_SplFileInfo)
        w_res.file_name = self.file_name
        w_res.path_name = self.path_name
        return w_res


class W_SplFileObject(W_SplFileInfo):
    def clone(self, interp, contextclass):
        w_res = W_InstanceObject.clone(self, interp, contextclass)
        assert isinstance(w_res, W_SplFileObject)
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


def _extension(interp, filename):
    name_split = filename.rsplit('.', 1)
    if len(name_split) == 2:
        filename, extension = name_split
    else:
        extension = ''
    return interp.space.wrap(extension)


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::getExtension')
def get_extension(interp, this):
    path = this.file_name
    filename = rpath.split(path)[1]
    return _extension(interp, filename)


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


def _get_group(interp, filename):
    res = os.stat(filename).st_gid
    return interp.space.wrap(res)


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::getGroup', error_handler=handle_as_exception)
def get_group(interp, this):
    filename = this.file_name
    if not filename:
        return interp.space.w_False
    try:
        return _get_group(interp, filename)
    except OSError:
        raise PHPException(k_RuntimeException.call_args(
            interp, [interp.space.wrap(
                "SplFileInfo::getGroup(): stat failed for %s" % filename)]))


def _get_inode(interp, filename):
    res = os.stat(filename).st_ino
    return interp.space.wrap(res)


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::getInode', error_handler=handle_as_exception)
def get_inode(interp, this):
    filename = this.file_name
    if not filename:
        return interp.space.w_False
    try:
        return _get_inode(interp, filename)
    except OSError:
        raise PHPException(k_RuntimeException.call_args(
            interp, [interp.space.wrap(
                "SplFileInfo::getInode(): stat failed for %s" % filename)]))


def _get_owner(interp, filename):
    res = os.stat(filename).st_uid
    return interp.space.wrap(res)


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::getOwner', error_handler=handle_as_exception)
def get_owner(interp, this):
    filename = this.file_name
    if not filename:
        return interp.space.w_False
    try:
        return _get_owner(interp, filename)
    except OSError:
        raise PHPException(k_RuntimeException.call_args(
            interp, [interp.space.wrap(
                "SplFileInfo::getOwner(): stat failed for %s" % filename)]))


def _get_perms(interp, filename):
    res = os.stat(filename).st_mode
    return interp.space.wrap(res)


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::getPerms', error_handler=handle_as_exception)
def get_perms(interp, this):
    filename = this.file_name
    if not filename:
        return interp.space.w_False
    try:
        return _get_perms(interp, filename)
    except OSError:
        raise PHPException(k_RuntimeException.call_args(
            interp, [interp.space.wrap(
                "SplFileInfo::getPerms(): stat failed for %s" % filename)]))


def _get_size(interp, filename):
    res = os.stat(filename).st_size
    return interp.space.wrap(res)


@wrap_method(['interp', ThisUnwrapper(W_SplFileInfo)],
             name='SplFileInfo::getSize', error_handler=handle_as_exception)
def get_size(interp, this):
    filename = this.file_name
    if not filename:
        return interp.space.w_False
    try:
        return _get_size(interp, filename)
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
                "stat failed for %s" % filename)]))


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


k_SplFileInfo = def_class(
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
    instance_class=W_SplFileInfo)


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
                "Cannot use SplFileObject with directories")]))
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


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject), int, Optional(int)],
             name='SplFileObject::fpassthru')
def sfo_fpassthru(interp, this, offset, whence=0):
    bytes_thru = this.w_res.passthru()
    return interp.space.newint(bytes_thru)


@wrap_method(['interp', ThisUnwrapper(W_SplFileObject)],
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
                                    "enclosure", consts.ACC_PRIVATE)],
    constants=[
        ('DROP_NEW_LINE', W_IntObject(SFO_DROP_NEW_LINE)),
        ('READ_AHEAD', W_IntObject(SFO_READ_AHEAD)),
        ('SKIP_EMPTY', W_IntObject(SFO_SKIP_EMPTY)),
        ('READ_CSV', W_IntObject(SFO_READ_CSV))],
    implements=[k_RecursiveIterator, k_SeekableIterator],
    instance_class=W_SplFileObject,
    extends=k_SplFileInfo,)


class W_DirectoryIterator(W_SplFileInfo):
    w_dir_res = None

    def clone(self, interp, contextclass):
        w_res = W_InstanceObject.clone(self, interp, contextclass)
        assert isinstance(w_res, W_DirectoryIterator)
        w_res.path_name = self.path_name
        w_res.w_dir_res = self.w_dir_res
        return w_res


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator), str],
             name='DirectoryIterator::__construct',
             error_handler=handle_as_exception)
def di_construct(interp, this, path):
    if path == "":
        raise PHPException(k_RuntimeException.call_args(
            interp, [interp.space.wrap(
                "Directory name must not be empty.")]))
    this.path = path
    this.file_name = path
    this.index = 0
    if not os.path.isdir(path):
        raise PHPException(k_UnexpectedValueException.call_args(
            interp, [interp.space.wrap(
                "DirectoryIterator::__construct(%s): failed to open dir: No "
                "such file or directory" % path)]))
    try:
        w_dir = W_DirResource(interp.space, path)
        w_dir_res = w_dir.open()
        if not isinstance(w_dir_res, W_DirResource):
            raise OSError   # rare case, but annotation fix
        this.w_dir_res = w_dir_res
        this.path_name = _di_pathname(this)
    except OSError:
        raise PHPException(k_RuntimeException.call_args(
            interp, [interp.space.wrap(
                "DirectoryIterator::__construct(): error while opening stream"
            )]))


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::__toString')
def di_tostring(interp, this):
    return interp.space.newstr(this.w_dir_res.items[this.w_dir_res.index])


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::current')
def di_current(interp, this):
    return this


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::key')
def di_key(interp, this):
    return interp.space.newint(this.w_dir_res.index)


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::next')
def di_next(interp, this):
    this.w_dir_res.read()


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::rewind')
def di_rewind(interp, this):
    return this.w_dir_res.rewind()


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator), int],
             name='DirectoryIterator::seek')
def di_seek(interp, this, pos):
    this.w_dir_res.seek_to_item(pos)


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::valid')
def di_valid(interp, this):
    if this.w_dir_res.index < this.w_dir_res.no_of_items:
        return interp.space.w_True
    else:
        return interp.space.w_False


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::getFilename')
def di_get_filename(interp, this):
    if this.w_dir_res.index < this.w_dir_res.no_of_items:
        res = this.w_dir_res.items[this.w_dir_res.index]
    else:
        res = ''
    return interp.space.newstr(res)


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator), Optional(str)],
             name='DirectoryIterator::getBasename')
def di_get_basename(interp, this, suffix=''):
    if this.w_dir_res.index < this.w_dir_res.no_of_items:
        filename = this.w_dir_res.items[this.w_dir_res.index]
        return _basename(interp.space, filename, suffix)
    else:
        return interp.space.newstr('')


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::getExtension')
def di_get_extension(interp, this):
    if this.w_dir_res.index < this.w_dir_res.no_of_items:
        filename = this.w_dir_res.items[this.w_dir_res.index]
        return _extension(interp, filename)
    else:
        return interp.space.newstr('')

@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::getPath')
def di_get_path(interp, this):
    path = this.path
    return interp.space.newstr(path)


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::getPathname')
def di_get_pathname(interp, this):
    if this.w_dir_res.index < this.w_dir_res.no_of_items:
        return interp.space.newstr(_di_pathname(this))
    else:
        return interp.space.w_False


def _di_pathname(di):
    return di.path + '/' + di.w_dir_res.items[di.w_dir_res.index]


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::getGroup')
def di_get_group(interp, this):
    path = this.path
    assert path is not None
    return _get_group(interp, path)


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::getInode')
def di_get_inode(interp, this):
    path = this.path
    assert path is not None
    return _get_inode(interp, path)


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::getOwner')
def di_get_owner(interp, this):
    path = this.path
    assert path is not None
    return _get_owner(interp, path)


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::getPerms')
def di_get_perms(interp, this):
    path = this.path
    assert path is not None
    return _get_perms(interp, path)


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::getSize')
def di_get_size(interp, this):
    path = this.path
    assert path is not None
    return _get_size(interp, path)


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::getType')
def di_get_type(interp, this):
    if this.w_dir_res.index < this.w_dir_res.no_of_items:
        item = _di_pathname(this)
    else:
        item = this.path
    return _filetype(interp.space, item)


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::isDir')
def di_is_dir(interp, this):
    if this.w_dir_res.index < this.w_dir_res.no_of_items:
        item = _di_pathname(this)
    else:
        item = this.path
    assert item is not None
    return _is_dir(interp.space, item)


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::isDot')
def di_is_dot(interp, this):
    if this.w_dir_res.index < this.w_dir_res.no_of_items:
        if this.w_dir_res.items[this.w_dir_res.index] in ('.', '..'):
            return interp.space.w_True
    return interp.space.w_False


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::isFile')
def di_is_file(interp, this):
    if this.w_dir_res.index < this.w_dir_res.no_of_items:
        item = _di_pathname(this)
    else:
        item = this.path
    return _is_file(interp.space, item)


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::isExecutable')
def di_is_executable(interp, this):
    if this.w_dir_res.index < this.w_dir_res.no_of_items:
        item = _di_pathname(this)
    else:
        item = this.path
    return _is_executable(interp.space, item)


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::isReadable')
def di_is_readable(interp, this):
    if this.w_dir_res.index < this.w_dir_res.no_of_items:
        item = _di_pathname(this)
    else:
        item = this.path
    return _is_readable(interp.space, item)


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::isWritable')
def di_is_writable(interp, this):
    if this.w_dir_res.index < this.w_dir_res.no_of_items:
        item = _di_pathname(this)
    else:
        item = this.path
    return _is_writable(interp.space, item)


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::isLink')
def di_is_link(interp, this):
    if this.w_dir_res.index < this.w_dir_res.no_of_items:
        item = _di_pathname(this)
    else:
        item = this.path
    assert item is not None
    return _is_link(interp.space, item)


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::getATime')
def di_getatime(interp, this):
    if this.w_dir_res.index < this.w_dir_res.no_of_items:
        item = _di_pathname(this)
    else:
        item = this.path
    assert item is not None
    try:
        res = os.stat(item).st_atime
        return interp.space.wrap(int(res))
    except OSError:
        return interp.space.w_False


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::getCTime')
def di_getctime(interp, this):
    if this.w_dir_res.index < this.w_dir_res.no_of_items:
        item = _di_pathname(this)
    else:
        item = this.path
    assert item is not None
    try:
        res = os.stat(item).st_ctime
        return interp.space.wrap(int(res))
    except OSError:
        return interp.space.w_False


@wrap_method(['interp', ThisUnwrapper(W_DirectoryIterator)],
             name='DirectoryIterator::getMTime')
def di_getmtime(interp, this):
    if this.w_dir_res.index < this.w_dir_res.no_of_items:
        item = _di_pathname(this)
    else:
        item = this.path
    assert item is not None
    try:
        res = os.stat(item).st_mtime
        return interp.space.wrap(int(res))
    except OSError:
        return interp.space.w_False


k_DirectoryIterator = def_class(
    'DirectoryIterator',
    [di_construct,
     di_current,
     di_key,
     di_next,
     di_rewind,
     di_seek,
     di_valid,
     di_get_filename,
     di_get_basename,
     di_get_extension,
     di_get_path,
     di_get_pathname,
     di_get_group,
     di_get_inode,
     di_get_owner,
     di_get_perms,
     di_get_size,
     di_get_type,
     di_is_dir,
     di_is_dot,
     di_is_file,
     di_is_link,
     di_is_executable,
     di_is_readable,
     di_is_writable,
     di_getatime,
     di_getctime,
     di_getmtime,
     di_tostring],
    implements=[k_SeekableIterator],
    instance_class=W_DirectoryIterator,
    extends=k_SplFileInfo,)


FI_CURRENT_AS_PATHNAME = 32
FI_CURRENT_AS_FILEINFO = 0
FI_CURRENT_AS_SELF = 16
FI_CURRENT_MODE_MASK = 240
FI_KEY_AS_PATHNAME = 0
FI_KEY_AS_FILENAME = 256
FI_FOLLOW_SYMLINKS = 512
FI_KEY_MODE_MASK = 3840
FI_NEW_CURRENT_AND_KEY = 256
FI_SKIP_DOTS = 4096
FI_UNIX_PATHS = 8192
FI_OTHER_MODE_MASK = 12288


class W_FilesystemIterator(W_DirectoryIterator):
    w_dir_res = None

    def clone(self, interp, contextclass):
        w_res = W_InstanceObject.clone(self, interp, contextclass)
        assert isinstance(w_res, W_FilesystemIterator)
        w_res.path_name = self.path_name
        w_res.w_dir_res = self.w_dir_res
        w_res.flags = self.flags
        w_res.path = self.path
        return w_res


@wrap_method(['interp', ThisUnwrapper(W_FilesystemIterator), str,
              Optional(int)], name='FilesystemIterator::__construct',
             error_handler=handle_as_exception)
def fi_construct(interp, this, path, flags=
        FI_KEY_AS_PATHNAME | FI_CURRENT_AS_FILEINFO | FI_SKIP_DOTS):
    if not os.path.isdir(path):
        raise PHPException(k_UnexpectedValueException.call_args(
            interp, [interp.space.wrap(
                "FilesystemIterator::__construct(%s): failed to open dir: No "
                "such file or directory" % path)]))
    this.flags = flags | FI_SKIP_DOTS       # PHP wants us to do this.
    this.path = path
    this.file_name = path
    this.index = 0
    try:
        w_dir = W_DirResource(interp.space, path, this.flags & FI_SKIP_DOTS)
        w_dir_res = w_dir.open()
        if not isinstance(w_dir_res, W_DirResource):
            raise OSError
        this.w_dir_res = w_dir_res
        this.path_name = _di_pathname(this)
    except OSError:
        raise PHPException(k_RuntimeException.call_args(
            interp, [interp.space.wrap(
                "FilesystemIterator::__construct(): error while opening stream"
                )]))


@wrap_method(['interp', ThisUnwrapper(W_FilesystemIterator)],
             name='FilesystemIterator::current')
def fi_current(interp, this):
    if this.flags & FI_CURRENT_AS_SELF:
        return this
    if this.flags & FI_CURRENT_AS_PATHNAME:
        pathname = _di_pathname(this)
        return interp.space.newstr(pathname)
    else:
        filename = _di_pathname(this)
        file_info = k_SplFileInfo.call_args(interp,
                [interp.space.wrap(filename)])
        return file_info


@wrap_method(['interp', ThisUnwrapper(W_FilesystemIterator)],
             name='FilesystemIterator::key')
def fi_key(interp, this):
    if this.flags & FI_KEY_AS_FILENAME:
        filename = this.w_dir_res.items[this.w_dir_res.index]
        return interp.space.wrap(filename)
    else:
        pathname = _di_pathname(this)
        return interp.space.newstr(pathname)


@wrap_method(['interp', ThisUnwrapper(W_FilesystemIterator)],
             name='FilesystemIterator::getFlags')
def fi_get_flags(interp, this):
    flags = this.flags & (FI_KEY_MODE_MASK | FI_CURRENT_MODE_MASK |
                          FI_OTHER_MODE_MASK)
    return interp.space.newint(flags)


@wrap_method(['interp', ThisUnwrapper(W_FilesystemIterator), int],
             name='FilesystemIterator::setFlags')
def fi_set_flags(interp, this, flags):
    this.flags &= ~(FI_KEY_MODE_MASK | FI_CURRENT_MODE_MASK |
                    FI_OTHER_MODE_MASK)
    this.flags |= ((FI_KEY_MODE_MASK | FI_CURRENT_MODE_MASK |
                    FI_OTHER_MODE_MASK) & flags)


k_FilesystemIterator = def_class(
    'FilesystemIterator',
    [fi_construct,
        fi_current,
        fi_key,
        fi_get_flags,
        fi_set_flags],
    constants=[
        ('CURRENT_AS_PATHNAME', W_IntObject(FI_CURRENT_AS_PATHNAME)),
        ('CURRENT_AS_FILEINFO', W_IntObject(FI_CURRENT_AS_FILEINFO)),
        ('CURRENT_AS_SELF', W_IntObject(FI_CURRENT_AS_SELF)),
        ('CURRENT_MODE_MASK', W_IntObject(FI_CURRENT_MODE_MASK)),
        ('KEY_AS_PATHNAME', W_IntObject(FI_KEY_AS_PATHNAME)),
        ('KEY_AS_FILENAME', W_IntObject(FI_KEY_AS_FILENAME)),
        ('FOLLOW_SYMLINKS', W_IntObject(FI_FOLLOW_SYMLINKS)),
        ('KEY_MODE_MASK', W_IntObject(FI_KEY_MODE_MASK)),
        ('NEW_CURRENT_AND_KEY', W_IntObject(FI_NEW_CURRENT_AND_KEY)),
        ('SKIP_DOTS', W_IntObject(FI_SKIP_DOTS)),
        ('UNIX_PATHS', W_IntObject(FI_UNIX_PATHS)),
        ('OTHER_MODE_MASK', W_IntObject(FI_OTHER_MODE_MASK))],
    implements=[k_SeekableIterator],
    instance_class=W_FilesystemIterator,
    extends=k_DirectoryIterator,)


class W_RecursiveDirectoryIterator(W_FilesystemIterator):
    w_dir_res = None

    def clone(self, interp, contextclass):
        w_res = W_InstanceObject.clone(self, interp, contextclass)
        assert isinstance(w_res, W_RecursiveDirectoryIterator)
        w_res.path_name = self.path_name
        w_res.w_dir_res = self.w_dir_res
        w_res.flags = self.flags
        w_res.path = self.path
        return w_res


@wrap_method(['interp', ThisUnwrapper(W_RecursiveDirectoryIterator), str,
              Optional(int)], name='RecursiveDirectoryIterator::__construct',
             error_handler=handle_as_exception)
def rdi_construct(interp, this, path, flags=
        FI_KEY_AS_PATHNAME | FI_CURRENT_AS_FILEINFO):
    if not os.path.isdir(path):
        raise PHPException(k_UnexpectedValueException.call_args(
            interp, [interp.space.wrap(
                "RecursiveDirectoryIterator::__construct(%s): failed to open dir: No "
                "such file or directory" % path)]))
    this.flags = flags
    this.path = path
    this.file_name = path
    this.index = 0
    try:
        w_dir = W_DirResource(interp.space, path, this.flags & FI_SKIP_DOTS)
        w_dir_res = w_dir.open()
        if not isinstance(w_dir_res, W_DirResource):
            raise OSError
        this.w_dir_res = w_dir_res
        this.path_name = _di_pathname(this)
    except OSError:
        raise PHPException(k_RuntimeException.call_args(
            interp, [interp.space.wrap(
                "RecursiveDirectoryIterator::__construct(): error while opening stream"
                )]))


@wrap_method(['interp', ThisUnwrapper(W_RecursiveDirectoryIterator)],
             name='RecursiveDirectoryIterator::hasChildren')
def rdi_has_children(interp, this):
    if this.w_dir_res.index < this.w_dir_res.no_of_items:
        if this.w_dir_res.items[this.w_dir_res.index] not in ('.', '..'):
            item = _di_pathname(this)
            assert item is not None
            return _is_dir(interp.space, item)
    return interp.space.w_False


@wrap_method(['interp', ThisUnwrapper(W_RecursiveDirectoryIterator)],
             name='RecursiveDirectoryIterator::getChildren')
def rdi_get_children(interp, this):
    if this.flags & FI_CURRENT_AS_PATHNAME:
        if this.w_dir_res.index < this.w_dir_res.no_of_items:
                pathname = _di_pathname(this)
                return interp.space.newstr(pathname)
        else:
            return interp.space.newstr(this.path + '/')
    else:
        if this.w_dir_res.index < this.w_dir_res.no_of_items:
            filename = _di_pathname(this)
            sub_dir_iter = k_RecursiveDirectoryIterator.call_args(interp,
                    [interp.space.wrap(filename)])
            return sub_dir_iter
        else:
            return this


@wrap_method(['interp', ThisUnwrapper(W_RecursiveDirectoryIterator)],
             name='RecursiveDirectoryIterator::getSubPath')
def rdi_get_subpath(interp, this):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_RecursiveDirectoryIterator)],
             name='RecursiveDirectoryIterator::getSubPathname')
def rdi_get_subpathname(interp, this):
    raise NotImplementedError


k_RecursiveDirectoryIterator = def_class(
    'RecursiveDirectoryIterator',
    [rdi_construct,
     rdi_has_children,
     rdi_get_children,
     rdi_get_subpath,
     rdi_get_subpathname, ],
    implements=[k_SeekableIterator, k_RecursiveIterator],
    instance_class=W_RecursiveDirectoryIterator,
    extends=k_FilesystemIterator,)
