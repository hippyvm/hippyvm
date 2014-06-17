from collections import OrderedDict

from hippy import consts
from hippy.module.spl.spl import W_RecursiveDirectoryIterator, W_SplFileInfo
from hippy.builtin import (wrap_method, ThisUnwrapper, Optional,
                           handle_as_exception)
from hippy.error import PHPException
from hippy.builtin_klass import def_class, k_ArrayAccess
from hippy.module.spl.exception import k_BadMethodCallException
from hippy.module.spl.interface import k_Countable
from hippy.module.spl.spl import k_RecursiveDirectoryIterator, k_SplFileInfo
from hippy.objects.base import W_Root
from hippy.module.phar import utils
from hippy.module.bzip2.funcs import _bzdecompress
from hippy.module.zlib.funcs import _decode, ZLIB_ENCODING_GZIP
from hippy.objects.intobject import W_IntObject
from hippy.objects.instanceobject import W_InstanceObject
from rpython.rlib import rpath
from hippy.rpath import exists
import time as pytime
from hippy.module.hash.funcs import _get_hash_algo
import py

PHAR_ENT_PERM_DEF_FILE = 0x000001B6
PHAR_ENT_PERM_DEF_DIR = 0x000001FF
PHAR_API_VERSION = 0x1110
PHAR_API_VERSION_NODIR = 0x1100


class PharManifest(object):
    length = 0
    files_count = 0
    api_version = PHAR_API_VERSION_NODIR
    flags = 65536  # ???
    metadata = ""
    metadata_length = 0
    alias_length = 0
    alias = ""
    signature_algo = "sha1"
    signature_length = 20
    files = OrderedDict()

    def __init__(self):
        pass

    def update(self, space):
        packed = utils.pack_manifest(space, self)
        self.length = len(packed)

    def __repr__(self):
        return """PharManifest(length:%d, files_count:%d,
        api:%d, flags:%d, meta:%s,
        meta_len:%d,
        alias:%s, alias_len:%d,
        signature_algo:%s, signature_len:%d)""" % (self.length,
                                                   self.files_count,
                                                   self.api_version,
                                                   self.flags,
                                                   self.metadata,
                                                   self.metadata_length,
                                                   self.alias,
                                                   self.alias_length,
                                                   self.signature_algo,
                                                   self.signature_length)


class PharFile(object):
    realname = None
    localname = None
    content = None
    name_length = 0
    size_uncompressed = 0
    size_compressed = 0
    timestamp = 0
    crc_uncompressed = 0
    flags = PHAR_ENT_PERM_DEF_FILE
    metadata = 0

    def __init__(self):
        pass

    def __repr__(self):
        return """PharFile(real:%s, local:%s, name_len:%d,
        size_u:%d, size_c:%d, timestamp:%d,
        crc:%d, flags:%d, metadata:%d,
        content:%s)""" % (self.realname,
                          self.localname,
                          self.name_length,
                          self.size_uncompressed,
                          self.size_compressed,
                          self.timestamp,
                          self.crc_uncompressed,
                          self.flags,
                          self.metadata,
                          self.content)


class W_Phar(W_RecursiveDirectoryIterator):

    def write_to_disc(self, space):
        content = open(self.filename, 'w+')
        content.write(self.stub)
        content.write(utils.write_phar(space, self.manifest, self.stub))

    def add_file(self, interp, realname, localname):
        if not exists(realname):
            msg = "phar error: unable to open "
            "file \"%s\" to add to phar archive" % realname
            raise PHPException(k_RuntimeException.call_args(
                interp, [interp.space.wrap(msg)]))

        pf = PharFile()
        pf.realname = realname
        pf.name_length = len(localname or realname)
        pf.localname = localname
        pf.content = open(realname, 'r').read()
        pf.timestamp = int(pytime.time())
        pf.size_uncompressed = len(pf.content)
        pf.size_compressed = pf.size_uncompressed
        h = _get_hash_algo('crc32b')
        h.update(pf.content)
        pf.crc_uncompressed = int(h.hexdigest(), 16)
        pf.metadata = 0
        self.manifest.files[localname or realname] = pf
        self.manifest.files_count += 1
        self.manifest.update(interp.space)
        self.write_to_disc(interp.space)

    def add_dir(self, interp, dirname):
        if not dirname[-1] == '/':
            dirname += '/'
        pf = PharFile()
        pf.realname = dirname
        pf.name_length = len(dirname)
        pf.localname = dirname
        pf.content = None
        pf.timestamp = int(pytime.time())
        pf.size_uncompressed = 0
        pf.size_compressed = 0
        pf.crc_uncompressed = 0
        pf.metadata = 0
        pf.flags = PHAR_ENT_PERM_DEF_DIR
        self.manifest.files[dirname] = pf
        self.manifest.files_count += 1
        self.manifest.api_version = PHAR_API_VERSION
        self.manifest.update(interp.space)
        self.write_to_disc(interp.space)


all_phars = OrderedDict()

PHAR_NONE = 0
PHAR_COMPRESSED = 61440
PHAR_GZ = 4096
PHAR_BZ2 = 8192

PHAR_SAME = 0
PHAR_PHAR = 1
PHAR_TAR = 2
PHAR_ZIP = 3

PHAR_MD5 = 1
PHAR_SHA1 = 2
PHAR_SHA256 = 3
PHAR_SHA512 = 4
PHAR_OPENSSL = 16

PHAR_PHP = 1
PHAR_PHPS = 2


@wrap_method(['interp', Optional(str), Optional(int)],
             name='Phar::mapPhar', error_handler=handle_as_exception,
             flags=consts.ACC_FINAL | consts.ACC_STATIC)
def phar_map_phar(interp, alias='', dataoffset=0):
    filename, _, _ = interp.get_frame().get_position()

    alias = alias or filename

    content = open(filename, 'r').read()
    _, phar_data = utils.fetch_phar_data(content)
    all_phars[alias] = utils.read_phar(phar_data)

    return interp.space.w_True


@wrap_method(['interp', ThisUnwrapper(W_Phar), str, Optional(int),
              Optional(str)], name='Phar::__construct',
             error_handler=handle_as_exception)
def phar_construct(interp, this, filename, flags=PHAR_NONE,
                   alias=None):

    this.filename = filename
    this.flags = flags
    if not exists(filename):
        this.manifest = PharManifest()
        this.stub = utils.generate_stub('index.php', 'index.php')
        this.basename = py.path.local(filename)
    else:
        filename = py.path.local(filename)
        content = open(this.filename, 'r').read()

        if filename.ext == ".bz2":
            this.flags = this.flags | PHAR_BZ2
            content = _bzdecompress(content)
        if filename.ext == ".gz":
            this.flags = this.flags | PHAR_GZ
            content = _decode(content, ZLIB_ENCODING_GZIP)

        this.basename = filename.purebasename
        this.stub, phar_data = utils.fetch_phar_data(content)
        this.manifest = utils.read_phar(phar_data)
        import pdb; pdb.set_trace()


@wrap_method(['interp', ThisUnwrapper(W_Phar), str], name='Phar::addEmptyDir',
             error_handler=handle_as_exception)
def phar_add_empty_dir(interp, this, dirname):
    this.add_dir(interp, dirname)


@wrap_method(['interp', ThisUnwrapper(W_Phar), str, Optional(str)],
             name='Phar::addFile', error_handler=handle_as_exception)
def phar_add_file(interp, this, filepath, localname=''):
    this.add_file(interp, filepath, localname)


@wrap_method(['interp', ThisUnwrapper(W_Phar), str, str],
             name='Phar::addFromString', error_handler=handle_as_exception)
def phar_add_from_str(interp, this, localname, contents):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_Phar)], name='Phar::apiVersion')
def phar_api_version(interp):
    # XXX: final public static -> no need for this(?)
    return interp.space.newstr("1.1.1")


@wrap_method(['interp', ThisUnwrapper(W_Phar), str, Optional(str)],
             name='Phar::buildFromDirectory',
             error_handler=handle_as_exception)
def phar_build_from_dir(interp, this, base_dir, regex=''):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_Phar)], name='Phar::buildFromIterator',
             error_handler=handle_as_exception)
def phar_build_from_iterator(interp, this):
    # XXX: Check inputs
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_Phar), Optional(int)],
             name='Phar::canCompress')
def phar_can_compress(interp, this, comp_type=0):
    # XXX: final public static
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_Phar)], name='Phar::canWrite')
def phar_can_write(interp, this):
    # XXX: final public static
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_Phar), int, Optional(str)],
             name='Phar::compress', error_handler=handle_as_exception)
def phar_compress(interp, this, compression, extension=''):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_Phar), int],
             name='Phar::compressFiles', error_handler=handle_as_exception)
def phar_compress_files(interp, this, compression):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_Phar), Optional(int), Optional(int),
              Optional(str)], name='Phar::convertToData',
             error_handler=handle_as_exception)
def phar_convert_to_data(interp, this, format=9021976, compression=9021976,
                         extension=''):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar), Optional(int), Optional(int),
              Optional(str)], name='Phar::convertToExecutable',
             error_handler=handle_as_exception)
def phar_convert_to_executable(interp, this, format=9021976,
                               compression=9021976, extension=''):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar), str, str],
             name='Phar::copy', error_handler=handle_as_exception)
def phar_copy(interp, this, oldfile, newfile):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_Phar)],
             name='Phar::count')
def phar_count(interp, this):
    return interp.space.newint(this.manifest.files_count)


@wrap_method(['interp', ThisUnwrapper(W_Phar), Optional(str), Optional(str)],
             name='Phar::createDefaultStub', error_handler=handle_as_exception)
def phar_create_default_stub(interp, this, indexfile='', webindexfile=''):
    # XXX: final public static
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar), Optional(str)],
             name='Phar::decompress', error_handler=handle_as_exception)
def phar_decompress(interp, this, extension=''):
    decompressed_filename = rpath.dirname(this.filename) + '/' + this.basename
    open(decompressed_filename, "wb").write(this.content)
    res = PharClass.call_args(interp, [interp.space.wrap(
        decompressed_filename)])
    return res


@wrap_method(['interp', ThisUnwrapper(W_Phar)], name='Phar::decompressFiles',
             error_handler=handle_as_exception)
def phar_decompress_files(interp, this):
    try:
        for k, v in this.manifest.files.items():
            if v.flags & PHAR_BZ2:
                v.content = _bzdecompress(v['content'])
                v.flags = v.flags - PHAR_BZ2
            elif v.flags & PHAR_GZ:
                v.content = _decode(v.content, ZLIB_ENCODING_GZIP)
                v.flags = v.flags - PHAR_GZ
        return interp.space.w_True
    except:
        return interp.space.w_False


@wrap_method(['interp', ThisUnwrapper(W_Phar)], name='Phar::delMetadata',
             error_handler=handle_as_exception)
def phar_del_metadata(interp, this):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar), str, Optional(str),
              Optional(bool)], name='Phar::delete',
             error_handler=handle_as_exception)
def phar_delete(interp, this, entry):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar), str], name='Phar::extractTo',
             error_handler=handle_as_exception)
def phar_extract_to(interp, this, entry):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar)], name='Phar::getMetadata')
def phar_get_metadata(interp, this):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar)], name='Phar::hasMetadata')
def phar_has_metadata(interp, this):
    if this.phar['global_metadata']:
        return interp.space.w_True
    else:
        return interp.space.w_False


@wrap_method(['interp', ThisUnwrapper(W_Phar)], name='Phar::getModified')
def phar_get_modified(interp, this):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar)], name='Phar::getSignature')
def phar_get_signature(interp, this):
    hash_type = {
        'sha1': 'SHA-1',
        'sha256': 'SHA-256',
        'sha512': 'SHA-512',
        'md5': 'MD5'
    }
    space = interp.space
    packed_manifest = utils.pack_manifest(space, this.manifest)
    algo = this.manifest.signature_algo
    sig = utils.get_signature(this.stub, packed_manifest, algo)
    rdict_w = OrderedDict()
    rdict_w['hash'] = space.newstr(sig.hexdigest().upper())
    rdict_w['hash_type'] = space.newstr(hash_type[algo])
    return space.new_array_from_rdict(rdict_w)


@wrap_method(['interp', ThisUnwrapper(W_Phar)], name='Phar::getStub',
             error_handler=handle_as_exception)
def phar_get_stub(interp, this):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar)],
             name='Phar::getSupportedCompression')
def phar_get_supported_compression(interp, this):
    # XXX: final public static
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar)], name='Phar::getVersion')
def phar_get_version(interp, this):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar)],
             name='Phar::getSupportedSignatures')
def phar_get_supported_signatures(interp, this):
    # XXX: final public static
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar)],
             name='Phar::interceptFileFuncs')
def phar_intercept_file_funcs(interp, this):
    # XXX: final public static
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar)], name='Phar::isBuffering')
def phar_is_buffering(interp, this):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar)], name='Phar::isCompressed',
             error_handler=handle_as_exception)
def phar_is_compressed(interp, this):
    comp_type = this.flags & PHAR_COMPRESSED
    if comp_type:
        return interp.space.newint(this.flags & PHAR_COMPRESSED)
    else:
        return interp.space.w_False


@wrap_method(['interp', ThisUnwrapper(W_Phar), int], name='Phar::isFileFormat',
             error_handler=handle_as_exception)
def phar_is_file_format(interp, this, format):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar), str, Optional(bool)],
             name='Phar::isValidPharFilename')
def phar_is_valid_phar_filename(interp, this, filename, executable=True):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar), str, Optional(str)],
             name='Phar::loadPhar', error_handler=handle_as_exception)
def phar_load_phar(interp, this, filename, alias=''):
    # XXX: final public static
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar)], name='Phar::isWritable')
def phar_is_writable(interp, this):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar), str, str], name='Phar::mount',
             error_handler=handle_as_exception)
def phar_mount(interp, this, pharpath, externalpath):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar)],
             name='Phar::mungServer', error_handler=handle_as_exception)
def phar_mung_server(interp, this):
    # XXX: final public static
    # XXX: Check input
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar), str], name='Phar::offsetExists')
def phar_offset_exists(interp, this, offset):
    if offset not in this.files:
        return interp.space.w_False
    else:
        return interp.space.w_True


@wrap_method(['interp', ThisUnwrapper(W_Phar), str], name='Phar::offsetGet',
             error_handler=handle_as_exception)
def phar_offset_get(interp, this, offset):
    entry = 'phar://' + this.filename + '/' + offset
    if offset not in this.files:
        raise PHPException(k_BadMethodCallException.call_args(
            interp, [interp.space.wrap(
                "Entry %s does not exist" % offset)]))

    w_pfi = PharFileInfoClass.call_args(interp, [interp.space.wrap(entry)])
    w_pfi.manifest_data = this.phar['files'][offset]
    return w_pfi


@wrap_method(['interp', ThisUnwrapper(W_Phar), str, str],
             name='Phar::offsetSet', error_handler=handle_as_exception)
def phar_offset_set(interp, this, offset, value):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar), str], name='Phar::offsetUnset',
             error_handler=handle_as_exception)
def phar_offset_unset(interp, this, offset):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar), Optional(bool)],
             name='Phar::running')
def phar_running(interp, this, retphar=True):
    # XXX: final public static
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar), str], name='Phar::setAlias',
             error_handler=handle_as_exception)
def phar_set_alias(interp, this, alias):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar), Optional(str), Optional(str)],
             name='Phar::setDefaultStub', error_handler=handle_as_exception)
def phar_set_default_stub(interp, this, index='', webindex=''):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar)], name='Phar::setMetadata',
             error_handler=handle_as_exception)
def phar_set_metadata(interp, this, metadata):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar), int],
             name='Phar::setSignatureAlgorithm',
             error_handler=handle_as_exception)
def phar_set_signature_algorithm(interp, this, sigtype):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar), str, Optional(int)],
             name='Phar::setStub', error_handler=handle_as_exception)
def phar_set_stub(interp, this, stub, len=-1):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar)], name='Phar::startBuffering')
def phar_start_buffering(interp, this):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar)], name='Phar::stopBuffering',
             error_handler=handle_as_exception)
def phar_stop_buffering(interp, this):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar), str],
             name='Phar::unlinkArchive', error_handler=handle_as_exception)
def phar_unlink_archive(interp, this, archive):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar), Optional(str), Optional(str),
              Optional(str)],
             name='Phar::webPhar', error_handler=handle_as_exception)
def phar_web_phar(interp, this, alias='', index='index.php', f404='',
                  mimetypes=[], rewrites=None):
    # XXX: Check inputs
    raise NotImplementedError


PharClass = def_class(
    'Phar',
    [phar_construct,
     phar_add_empty_dir,
     phar_add_file,
     phar_add_from_str,
     phar_api_version,
     phar_build_from_dir,
     phar_build_from_iterator,
     phar_can_compress,
     phar_can_write,
     phar_compress,
     phar_compress_files,
     phar_convert_to_data,
     phar_convert_to_executable,
     phar_copy,
     phar_count,
     phar_create_default_stub,
     phar_decompress,
     phar_decompress_files,
     phar_del_metadata,
     phar_delete,
     phar_extract_to,
     phar_get_metadata,
     phar_has_metadata,
     phar_get_modified,
     phar_get_signature,
     phar_get_stub,
     phar_get_supported_compression,
     phar_get_supported_signatures,
     phar_get_version,
     phar_intercept_file_funcs,
     phar_is_buffering,
     phar_is_compressed,
     phar_is_file_format,
     phar_is_valid_phar_filename,
     phar_load_phar,
     phar_map_phar,
     phar_is_writable,
     phar_mount,
     phar_mung_server,
     phar_offset_exists,
     phar_offset_get,
     phar_offset_set,
     phar_offset_unset,
     phar_running,
     phar_set_alias,
     phar_set_default_stub,
     phar_set_metadata,
     phar_set_signature_algorithm,
     phar_set_stub,
     phar_start_buffering,
     phar_stop_buffering,
     phar_unlink_archive,
     phar_web_phar,
     ],
    constants=[
        ('NONE', W_IntObject(PHAR_NONE)),
        ('COMPRESSED', W_IntObject(PHAR_COMPRESSED)),
        ('GZ', W_IntObject(PHAR_GZ)),
        ('BZ2', W_IntObject(PHAR_BZ2)),
        ('SAME', W_IntObject(PHAR_SAME)),
        ('PHAR', W_IntObject(PHAR_PHAR)),
        ('TAR', W_IntObject(PHAR_TAR)),
        ('ZIP', W_IntObject(PHAR_ZIP)),
        ('MD5', W_IntObject(PHAR_MD5)),
        ('SHA1', W_IntObject(PHAR_SHA1)),
        ('SHA256', W_IntObject(PHAR_SHA256)),
        ('SHA512', W_IntObject(PHAR_SHA512)),
        ('OPENSSL', W_IntObject(PHAR_OPENSSL)),
        ('PHP', W_IntObject(PHAR_PHP)),
        ('PHPS', W_IntObject(PHAR_PHPS)),],
    implements=[k_Countable, k_ArrayAccess],
    instance_class=W_Phar,
    extends=k_RecursiveDirectoryIterator,)


class W_PharFileInfo(W_SplFileInfo):

    def clone(self, interp, contextclass):
        w_res = W_InstanceObject.clone(self, interp, contextclass)
        assert isinstance(w_res, W_PharFileInfo)
        w_res.entry = self.entry
        w_res.manifest_data = self.manifest_data
        return w_res


@wrap_method(['interp', ThisUnwrapper(W_PharFileInfo), int],
             name='PharFileInfo::chmod')
def pfi_chmod(interp, this, permissions):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_PharFileInfo), int],
             name='PharFileInfo::compress', error_handler=handle_as_exception)
def pfi_compress(interp, this, compression):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_PharFileInfo), str],
             name='PharFileInfo::__construct',
             error_handler=handle_as_exception)
def pfi_construct(interp, this, entry):
    this.entry = entry
    this.manifest_data = None


@wrap_method(['interp', ThisUnwrapper(W_PharFileInfo)],
             name='PharFileInfo::decompress',
             error_handler=handle_as_exception)
def pfi_decompress(interp, this):
    try:
        if this.manifest_data['flags'] & PHAR_BZ2:
            this.manifest_data['content'] = _bzdecompress(this.manifest_data['content'])
            this.manifest_data['flags'] = this.manifest_data['flags'] - PHAR_BZ2
        elif this.manifest_data['flags'] & PHAR_GZ:
            this.manifest_data['content'] = _decode(this.manifest_data['content'], ZLIB_ENCODING_GZIP)
            this.manifest_data['flags'] = this.manifest_data['flags'] - PHAR_GZ
        return interp.space.w_True
    except:
        return interp.space.w_False


@wrap_method(['interp', ThisUnwrapper(W_PharFileInfo)],
             name='PharFileInfo::delMetadata',
             error_handler=handle_as_exception)
def pfi_del_metadata(interp, this):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_PharFileInfo)],
             name='PharFileInfo::getContent')
def pfi_get_content(interp, this):
    return interp.space.wrap(this.manifest_data['content'])


@wrap_method(['interp', ThisUnwrapper(W_PharFileInfo)],
             name='PharFileInfo::getCRC32',
             error_handler=handle_as_exception)
def pfi_get_crc32(interp, this):
    return interp.space.newint(this.manifest_data['size_crc_uncompressed'])


@wrap_method(['interp', ThisUnwrapper(W_PharFileInfo)],
             name='PharFileInfo::getCompressedSize')
def pfi_get_compressed_size(interp, this):
    return interp.space.newint(this.manifest_data['size_uncompressed'])


@wrap_method(['interp', ThisUnwrapper(W_PharFileInfo)],
             name='PharFileInfo::getMetadata')
def pfi_get_metadata(interp, this):
    return interp.space.newint(this.manifest_data['metadata'])


@wrap_method(['interp', ThisUnwrapper(W_PharFileInfo)],
             name='PharFileInfo::getPharFlags')
def pfi_get_phar_flags(interp, this):
    return interp.space.newint(0)


@wrap_method(['interp', ThisUnwrapper(W_PharFileInfo)],
             name='PharFileInfo::hasMetadata')
def pfi_has_metadata(interp, this):
    if this.manifest_data['metadata'] == 0:
        return interp.space.w_False
    else:
        return interp.space.w_True


@wrap_method(['interp', ThisUnwrapper(W_PharFileInfo)],
             name='PharFileInfo::isCRCChecked')
def pfi_is_crc(interp, this):
    # will always be crc verified in the current implementation
    # or so say php docs.
    return interp.space.w_True


@wrap_method(['interp', ThisUnwrapper(W_PharFileInfo), Optional(int)],
             name='PharFileInfo::isCompressed')
def pfi_is_compressed(interp, this, compression_type=9021976):
    if this.manifest_data['size_uncompressed'] == this.manifest_data['size_compressed']:
        return interp.space.w_False
    else:
        return (this.manifest_data['flags'] & compression_type)


@wrap_method(['interp', ThisUnwrapper(W_PharFileInfo)],
             name='PharFileInfo::setMetadata')
def pfi_set_metadata(interp, this):
    raise NotImplementedError


PharFileInfoClass = def_class(
    'PharFileInfo',
    [pfi_chmod,
     pfi_compress,
     pfi_construct,
     pfi_decompress,
     pfi_del_metadata,
     pfi_get_crc32,
     pfi_get_compressed_size,
     pfi_get_content,
     pfi_get_metadata,
     pfi_get_phar_flags,
     pfi_has_metadata,
     pfi_is_crc,
     pfi_is_compressed,
     pfi_set_metadata,
     ],
    instance_class=W_PharFileInfo,
    extends=k_SplFileInfo,)
