
from collections import OrderedDict
from rpython.rlib.rsre.rsre_re import search
import os

from hippy.module.url import _urldecode

class CGIConfig(object):
    def __init__(self, w_get, w_post, initial_server_dict, cookie):
        self.w_get = w_get
        self.w_post = w_post
        self.initial_server_dict = initial_server_dict
        self.cookie = cookie


def unpack_query(dct, query, space):
    vars = query.split("&")
    for var in vars:
        l = var.split("=", 1)
        if len(l) == 1:
            dct[_urldecode(l[0])] = space.wrap("")
        else:
            dct[_urldecode(l[0])] = space.wrap(_urldecode(l[1]))


def setup_cgi(interp, argv):
    get = OrderedDict()
    post = OrderedDict()
    space = interp.space
    query = os.environ.get('QUERY_STRING')
    if query is not None:
        unpack_query(get, query, space)
    script_name = os.environ.get('SCRIPT_NAME')
    initial_server_dict = OrderedDict()
    if script_name is not None:
        initial_server_dict['PHP_SELF'] = space.wrap(script_name)
    if argv:
        initial_server_dict['argc'] = space.wrap(len(argv))
        initial_server_dict['argv'] = space.new_array_from_list(
            [space.wrap(x) for x in argv])

    cookie = os.environ.get('HTTP_COOKIE')
    content_length = os.environ.get('CONTENT_LENGTH')
    content_type = os.environ.get('CONTENT_TYPE')
    if content_type is not None and content_length is not None:
        m = search("[; ,]", content_type)
        if m:
            start = m.start(0)
            assert start >= 0
            content_type = content_type[:start]
        content_type = content_type.lower()
        if (content_type == 'x-www-form-urlencoded' or
            content_type == 'application/x-www-form-urlencoded'):
            content_length = int(content_length)
            stdin = interp.open_stdin_stream()
            post_data = stdin.read(content_length)
            unpack_query(post, post_data, space)
        else:
            interp.warn("Unknown content type: %s, ignoring post" %
                        content_type)

    return CGIConfig(space.new_array_from_rdict(get),
                     space.new_array_from_rdict(post),
                     initial_server_dict, cookie)
