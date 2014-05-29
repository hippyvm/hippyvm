from hippy.module.spl.spl import W_RecursiveDirectoryIterator
from hippy.builtin import (wrap_method, ThisUnwrapper, Optional,
                           handle_as_exception)
from hippy.builtin_klass import def_class
from hippy.objects.iterator import W_InstanceIterator
from hippy.objects.arrayobject import W_ArrayObject


class W_Phar(W_RecursiveDirectoryIterator):
    pass


def _phar_detect_phar_fname_ext():
    """
    if executable is 1, only returns SUCCESS if the extension is one of the
    tar/zip .phar extensions if executable is 0, it returns SUCCESS only if the
    filename does *not* contain ".phar" anywhere, and treats the first
    extension as the filename extension

    if an extension is found, it sets ext_str to the location of the file
    extension in filename, and ext_len to the length of the extension.
    for urls like "phar://alias/oops" it instead sets ext_len to -1 and returns
    FAILURE, which tells the calling function to use "alias" as the phar alias

    the last parameter should be set to tell the thing to assume that filename
    is the full path, and only to check the extension rules, not to iterate.

    see: https://github.com/php/php-src/blob/af6c11c5f060870d052a2b765dc634d9e47d0f18/ext/phar/phar.c#L1893
    """


def _phar_open_parsed_phar():
    """ Open an already loaded phar """


def _phar_open_or_create_zip():
    """ Create or open a zip-based phar for writing """


def _phar_open_or_create_tar():
    """ Create or open a tar-based phar for writing """


def _phar_create_or_parse_filename():
    pass


def _phar_open_or_create_filename():
    """ Create or open a phar for writing """


@wrap_method(['interp', ThisUnwrapper(W_Phar), str, Optional(int),
              Optional(str)], name='Phar::__construct',
             error_handler=handle_as_exception)
def phar_construct(interp, this, filename, flags=None, alias=None):
    """
    phar_file = os.path.join(os.path.dirname(__file__), 'phar_files/phar.phar')
    phar_content = open(phar_file, 'r').read()

    phar_data = utils.fetch_phar_data(phar_content)
    this.phar = utils.read_phar(phar_data)
    """


@wrap_method(['interp', ThisUnwrapper(W_Phar), str], name='Phar::addEmptyDir',
             error_handler=handle_as_exception)
def phar_add_empty_dir(interp, this, dirname):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_Phar), str, Optional(str)],
             name='Phar::addFile', error_handler=handle_as_exception)
def phar_add_file(interp, this, filepath, localname=''):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_Phar), str, str],
             name='Phar::addFromString', error_handler=handle_as_exception)
def phar_add_from_str(interp, this, localname, contents):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_Phar)], name='Phar::apiVersion')
def phar_api_version(interp):
    # XXX: final public static -> no need for this(?)
    raise NotImplementedError()


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
    return interp.space.newint(this.phar['files_count'])


@wrap_method(['interp', ThisUnwrapper(W_Phar), Optional(str), Optional(str)],
             name='Phar::createDefaultStub', error_handler=handle_as_exception)
def phar_create_default_stub(interp, this, indexfile='', webindexfile=''):
    # XXX: final public static
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar), Optional(str)],
             name='Phar::decompress', error_handler=handle_as_exception)
def phar_decompress(interp, this, extension):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar)], name='Phar::decompressFiles',
             error_handler=handle_as_exception)
def phar_decompress_files(interp, this):
    raise NotImplementedError


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
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar)], name='Phar::getModified')
def phar_get_modified(interp, this):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar)], name='Phar::getSignature')
def phar_get_signature(interp, this):
    raise NotImplementedError


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
    raise NotImplementedError


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


@wrap_method(['interp', ThisUnwrapper(W_Phar), Optional(str), Optional(int)],
             name='Phar::mapPhar', error_handler=handle_as_exception)
def phar_map_phar(interp, this, alias='', dataoffset=0):
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
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_Phar), str], name='Phar::offsetGet',
             error_handler=handle_as_exception)
def phar_offset_get(interp, this, offset):
    raise NotImplementedError


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
    implements=['Countable', 'ArrayAccess'],
    instance_class=W_Phar,
    extends='RecursiveDirectoryIterator',)
