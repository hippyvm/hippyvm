from hippy.module.spl.spl import W_RecursiveDirectoryIterator
from hippy.builtin import (wrap_method, ThisUnwrapper, Optional,
                           handle_as_exception)
from hippy.builtin_klass import def_class


class W_Phar(W_RecursiveDirectoryIterator):
    pass


def _phar_detect_phar_fname_ext():
    """
    if executable is 1, only returns SUCCESS if the extension is one of the tar/zip .phar extensions
    if executable is 0, it returns SUCCESS only if the filename does *not* contain ".phar" anywhere, and treats
    the first extension as the filename extension

    if an extension is found, it sets ext_str to the location of the file extension in filename,
    and ext_len to the length of the extension.
    for urls like "phar://alias/oops" it instead sets ext_len to -1 and returns FAILURE, which tells
    the calling function to use "alias" as the phar alias

    the last parameter should be set to tell the thing to assume that filename is the full path, and only to check the
    extension rules, not to iterate.

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
              Optional(str)], name='Phar::__construct',                 # TODO: Perhaps use Nullable here
             error_handler=handle_as_exception)
def phar_construct(interp, this, filename, flags=None, alias=None):
    # Throw BadMethodCallException:"Cannot call constructor twice", if called
    # twice


PharClass = def_class(
    'Phar',
    [phar_construct,
     ],     # Methods
    implements=['Countable', 'ArrayAccess'],
    instance_class=W_Phar,
    extends='RecursiveDirectoryIterator',)
