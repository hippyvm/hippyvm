from hippy.module.spl.spl import W_RecursiveDirectoryIterator
from hippy.builtin import (wrap_method, ThisUnwrapper, Optional,
                           handle_as_exception)
from hippy.builtin_klass import def_class
from hippy.objects.iterator import W_InstanceIterator


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
    raise NotImplementedError()


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


@wrap_method(['interp'], name='Phar::apiVersion')        # XXX: final public static -> no need for this(?)
def phar_api_version(interp):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_Phar), str, Optional(str)],
             name='Phar::buildFromDirectory',
             error_handler=handle_as_exception)
def phar_build_from_dir(interp, this, base_dir, regex=''):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_Phar), W_InstanceIterator,
              Optional(str)], name='Phar::buildFromIterator',
             error_handler=handle_as_exception)
def phar_build_from_iterator(interp, this, iter, base_dir=''):
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
    raise NotImplementedError()



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
     ],
    implements=['Countable', 'ArrayAccess'],
    instance_class=W_Phar,
    extends='RecursiveDirectoryIterator',)
