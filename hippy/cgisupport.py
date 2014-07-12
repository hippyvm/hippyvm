
from collections import OrderedDict
from rpython.rlib.rsre.rsre_re import search
import os
from rpython.rlib.rstring import assert_str0
from hippy.module.url import _urldecode
from rpython.rlib.rStringIO import RStringIO


class CGIConfig(object):
    def __init__(self, w_get, w_post, w_files, initial_server_dict, cookie):
        self.w_get = w_get
        self.w_post = w_post
        self.w_files = w_files
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


def get_param(params, s):
    if params is None:
        return os.environ.get(s)
    return params.get(s, None)


def all_keys_from(params):
    if params is None:
        return os.environ.keys()
    return params.keys()


def parse_header(fp):
    line = fp.readline().strip()
    d = {}
    while line != '':
        line = line.strip()
        parts = line.split(';')
        for p in parts:
            if ':' in p:
                k, v = p.split(':')
                d[k.strip()] = v.strip()
            if '=' in p:
                k, v = p.split('=')
                v = v.strip()
                d[k.strip()] = v.strip('"')
        line = fp.readline().strip()
        if line == '':
            return d
    return d


def read_until(fp, delimiter, sofar):
    sofar += fp.read(5)
    assert sofar is not None
    m = sofar.find(delimiter)
    if m > 0:
        act = fp.tell()
        fp.seek(act - (len(sofar) - m))
        assert m > 0
        data = sofar[:m]
        return data
    else:
        return read_until(fp, delimiter, sofar)


def parse_multipart(space, fp, boundary, data, files):
    line = fp.readline().strip()
    if line == '--' + boundary:
        pass
    elif line == '--' + boundary + '--':
        return data, files
    elif line == '':
        return parse_multipart(space, fp, boundary, data, files)
    else:
        print line
        raise ValueError()
    headers = parse_header(fp)
    content_disp = None
    content_type = None
    if 'Content-Type' in headers:
        content_type = headers['Content-Type']

    if 'Content-Disposition' in headers:
        content_disp = headers['Content-Disposition']
    else:
        raise ValueError('missing Content-Disposition')
    if content_disp == 'form-data' and not content_type:
        # simple filed
        name = headers['name']
        value = read_until(fp, '--' + boundary, "")
        data[name] = space.wrap(value.strip())
        parse_multipart(space, fp, boundary, data, files)
    if content_disp == 'form-data' and content_type:
        # file filed
        name = headers['name']
        filename = headers['filename']
        tmpname = os.tmpnam()
        fd = open(tmpname, 'w')
        fd.write(read_until(fp, '--' + boundary, ""))
        rdct = OrderedDict()
        rdct['name'] = space.wrap(filename)
        rdct['type'] = space.wrap(content_type)
        rdct['tmp_name'] = space.wrap(tmpname)
        rdct['error'] = space.wrap(0)
        rdct['size'] = space.wrap(fd.tell())
        files['name'] = space.new_array_from_rdict(rdct)
        fd.close()
        parse_multipart(space, fp, boundary, data, files)
    elif content_disp == 'file':
        raise NotImplementedError()
    return data, files


def setup_cgi(interp, params, argv, post_data=None):
    get = OrderedDict()
    post = OrderedDict()
    files = OrderedDict()
    space = interp.space
    query = get_param(params, 'QUERY_STRING')
    if query is not None:
        unpack_query(get, query, space)
    script_name = get_param(params, 'SCRIPT_NAME')
    initial_server_dict = OrderedDict()
    if script_name is not None:
        initial_server_dict['PHP_SELF'] = space.wrap(script_name)
    if argv:
        initial_server_dict['argc'] = space.wrap(len(argv))
        initial_server_dict['argv'] = space.new_array_from_list(
            [space.wrap(x) for x in argv])

    cookie = get_param(params, 'HTTP_COOKIE')
    content_length = get_param(params, 'CONTENT_LENGTH')
    content_type_set = get_param(params, 'CONTENT_TYPE')
    content_type = ""
    boundary = ""
    for k in all_keys_from(params):
        initial_server_dict[k] = space.wrap(get_param(params, k))
    if content_type_set is not None and content_length is not None:
        m = search("[; ,]", content_type_set)
        if m:
            start = m.start(0)
            assert start >= 0
            content_type = content_type_set[:start]
            content_type = content_type.lower()
        else:
            content_type = content_type_set.lower()

        if (content_type == 'x-www-form-urlencoded' or
            content_type == 'application/x-www-form-urlencoded'):
            content_length = int(content_length)
            if post_data is None:
                stdin = interp.open_stdin_stream()
                post_data = stdin.read(content_length)
            unpack_query(post, post_data, space)
        elif content_type == 'multipart/form-data':
            m = search("boundary", content_type_set)
            if m:
                end = m.end(0)
                assert end >= 0
                boundary = content_type_set[end + 1:]
            if not boundary:
                interp.warn("Missing boundary, ignoring post")
            fp = RStringIO()
            fp.write(post_data)
            fp.seek(0)
            post, files = parse_multipart(space, fp, boundary,
                                          OrderedDict(), OrderedDict())
            fp.close()
        else:
            interp.warn("Unknown content type: %s, ignoring post" %
                        content_type)
    return CGIConfig(space.new_array_from_rdict(get),
                     space.new_array_from_rdict(post),
                     space.new_array_from_rdict(files),
                     initial_server_dict, cookie)
