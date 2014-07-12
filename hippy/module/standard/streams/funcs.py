from rpython.rlib import rpath

from hippy.objects.resources.file_resource import W_FileResource
from hippy.objects.base import W_Root
from hippy.builtin import (
    wrap, Optional, FileResourceArg, StreamContextArg)
from hippy.objects.resources.socket_resource import W_SocketResource
from hippy.module.url import urlsplit


def set_socket_blocking():
    """ Alias of stream_set_blocking"""
    raise NotImplementedError()


def stream_bucket_append():
    """ Append bucket to brigade"""
    raise NotImplementedError()


def stream_bucket_make_writeable():
    """ Return a bucket object from the brigade for operating on"""
    raise NotImplementedError()


def stream_bucket_new():
    """ Create a new bucket for use on the current stream"""
    raise NotImplementedError()


def stream_bucket_prepend():
    """ Prepend bucket to brigade"""
    raise NotImplementedError()


def stream_context_create():
    """ Creates a stream context"""
    raise NotImplementedError()


def stream_context_get_default():
    """ Retrieve the default stream context"""
    raise NotImplementedError()


def stream_context_get_options():
    """ Retrieve options for a stream/wrapper/context"""
    raise NotImplementedError()


def stream_context_get_params():
    """ Retrieves parameters from a context"""
    raise NotImplementedError()


def stream_context_set_default():
    """ Set the default stream context"""
    raise NotImplementedError()


def stream_context_set_option():
    """ Sets an option for a stream/wrapper/context"""
    raise NotImplementedError()


def stream_context_set_params():
    """ Set parameters for a stream/wrapper/context"""
    raise NotImplementedError()


def stream_copy_to_stream():
    """ Copies data from one stream to another"""
    raise NotImplementedError()


def stream_encoding():
    """ Set character set for stream encoding"""
    raise NotImplementedError()

FILTERS = ['string.rot13', 'string.toupper', 'string.tolower',
           'convert.base64-encode', 'convert.base64-decode',
           'zlib.deflate', 'zlib.inflate',
           'bzip2.compress', 'bzip2.decompress']


@wrap(['interp', FileResourceArg(False), str, Optional(int), Optional(W_Root)])
def stream_filter_append(interp, w_res, filtername, _type=1, w_params=None):
    """ Attach a filter to a stream"""
    assert isinstance(w_res, W_FileResource)
    if not filtername in FILTERS:
        interp.warn("stream_filter_append(): unable to "
                    "locate filter \"wrong_filter\"")
    if _type == 1:
        w_res.read_filters_append(filtername)
        w_res.read_filters_params_append(w_params)
    elif _type == 2:
        w_res.write_filters_append(filtername)
        w_res.write_filters_params_append(w_params)
    elif _type == 3:
        w_res.read_filters_append(filtername)
        w_res.read_filters_params_append(w_params)
        w_res.write_filters_append(filtername)
        w_res.write_filters_params_append(w_params)
    return w_res


def stream_filter_prepend():
    """ Attach a filter to a stream"""
    raise NotImplementedError()


def stream_filter_register():
    """ Register a user defined stream filter"""
    raise NotImplementedError()


def stream_filter_remove():
    """ Remove a filter from a stream"""
    raise NotImplementedError()


@wrap(['interp', FileResourceArg(False), Optional(int), Optional(int)])
def stream_get_contents(interp, w_res, max_length=-1, offset=-1):
    """ Reads remainder of a stream into a string"""
    assert isinstance(w_res, W_FileResource)
    res = w_res.read(-1)
    return interp.space.wrap(res)


def stream_get_filters():
    """ Retrieve list of registered filters"""
    raise NotImplementedError()


def stream_get_line():
    """ Gets line from stream resource up to a given delimiter"""
    raise NotImplementedError()


@wrap(['interp', FileResourceArg(False)])
def stream_get_meta_data(interp, w_res):
    """ Retrieves header/meta data from streams/file pointers"""
    return w_res.get_meta_data()


def stream_get_transports():
    """ Retrieve list of registered socket transports"""
    raise NotImplementedError()


def stream_get_wrappers():
    """ Retrieve list of registered streams"""
    raise NotImplementedError()


def stream_is_local():
    """ Checks if a stream is a local stream"""
    raise NotImplementedError()


def stream_notification_callback():
    """ A callback function for the notification context paramater"""
    raise NotImplementedError()


def stream_register_wrapper():
    """ Alias of stream_wrapper_register"""
    raise NotImplementedError()


@wrap(['interp', str])
def stream_resolve_include_path(interp, filename):
    """ Resolve filename against the include path"""

    for path in interp.include_path:
        fullpath = rpath.join(path, [filename])
        if rpath.exists(fullpath):
            return interp.space.wrap(rpath.realpath(fullpath))

    return interp.space.w_False


def stream_select():
    """ Runs the equivalent of the select() system call
    on the given arrays of streams with a
    timeout specified by tv_sec and tv_usec"""
    raise NotImplementedError()


def stream_set_blocking():
    """ Set blocking/non-blocking mode on a stream"""
    raise NotImplementedError()


def stream_set_chunk_size():
    """ Set the stream chunk size"""
    raise NotImplementedError()


def stream_set_read_buffer():
    """ Set read file buffering on the given stream"""
    raise NotImplementedError()


@wrap(['interp', FileResourceArg(), int, Optional(int)],
      aliases=['socket_set_timeout'])
def stream_set_timeout(interp, w_res, sec, mili=0):
    """ Set timeout period on a stream"""
    if mili:
        sec += mili / 1000000.0
    w_res.settimeout(sec)
    return interp.space.w_True


@wrap(['interp', FileResourceArg(), int])
def stream_set_write_buffer(interp, w_res, buffer):
    """ Sets write file buffering on the given stream"""
    ### mockup only
    return interp.space.newint(0)


@wrap(['interp', FileResourceArg(), Optional(float), Optional('reference')])
def stream_socket_accept(interp, w_res, timeout=-1, w_ref_peer=None):
    """ Accept a connection on a socket created by stream_socket_server"""
    space = interp.space
    fd, addr = w_res.accept()
    w_res = W_SocketResource(space, None, -1, fd=fd)
    if timeout == -1:
        w_timeout = interp.config.get_ini_w('default_socket_timeout')
        timeout = interp.space.float_w(w_timeout)
    w_res.settimeout(timeout)
    return w_res


def stream_socket_client():
    """ Open Internet or Unix domain socket connection"""
    raise NotImplementedError()


def stream_socket_enable_crypto():
    """ Turns encryption on/off on an already connected socket"""
    raise NotImplementedError()


@wrap(['interp', FileResourceArg(), bool])
def stream_socket_get_name(interp, w_res, remote):
    """ Retrieve the name of the local or remote sockets"""
    return w_res.get_name(remote)


def stream_socket_pair():
    """ Creates a pair of connected, indistinguishable socket streams"""
    raise NotImplementedError()


def stream_socket_recvfrom():
    """ Receives data from a socket, connected or not"""
    raise NotImplementedError()


def stream_socket_sendto():
    """ Sends a message to a socket, whether it is connected or not"""
    raise NotImplementedError()


@wrap(['interp', str, Optional('reference'), Optional('reference'),
       Optional(int), Optional(StreamContextArg(None))])
def stream_socket_server(interp, local_socket, w_ref_errno=None,
                         w_ref_errstr=None, flags=12, w_ctx=None):
    """ Create an Internet or Unix domain server socket
        ('STREAM_SERVER_BIND', 4),
        ('STREAM_SERVER_LISTEN', 8),
    """
    r = urlsplit(local_socket)
    space = interp.space
    bind = flags & 4 != 0
    listen = flags & 8 != 0

    w_res = W_SocketResource(space, r.host, r.port, r.scheme)
    if bind:
        w_res.bind()
    if listen:
        w_res.listen()
    return w_res
    # import pdb; pdb.set_trace()


def stream_socket_shutdown():
    """ Shutdown a full-duplex connection"""
    raise NotImplementedError()


def stream_supports_lock():
    """ Tells whether the stream supports locking."""
    raise NotImplementedError()


def stream_wrapper_register():
    """ Register a URL wrapper implemented as a PHP class"""
    raise NotImplementedError()


def stream_wrapper_restore():
    """ Restores a previously unregistered built-in wrapper"""
    raise NotImplementedError()


def stream_wrapper_unregister():
    """ Unregister a URL wrapper"""
    raise NotImplementedError()
