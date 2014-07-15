
import py
from Queue import Queue
import thread, traceback, sys, tempfile
import struct

from rpython.rlib.rsocket import RSocket
from rpython.rtyper.lltypesystem import rffi, lltype

from ext_module.fastcgi.fcgi import run_fcgi_server, FCGI_DEBUG_QUIT,\
     FCGI_BEGIN_REQUEST, FCGI_PARAMS, FCGI_STDIN, FCGI_END_REQUEST,\
     FCGI_STDOUT, FCGIServer, Quit
from ext_module.fastcgi.transport import SocketTransport

FCGI_HEADER_LEN = 8

FCGI_HEADER = '!BBHHBx'
FCGI_BEGIN_REQUEST_BODY = '!HB5x'
FCGI_END_REQUEST_BODY = '!LB3x'

def start_new_thread(f, args):
    def wrapper():
        try:
            f(*args)
        except Exception, e:
            traceback.print_tb(sys.exc_info()[2])
            print e
    thread.start_new_thread(wrapper, ())

def run_server_and_writer(tmpdir, writer_part, files):
    for fname, content in files:
        tmpdir.join(fname).write(content)

    server = FCGIServer(debug=True)
    server.last_request = True
    transport = SocketTransport()
    addr = transport.start_server(("127.0.0.1", 0))

    def writer():
        sock = RSocket()
        sock.connect(addr)
        writer_part(sock)
        sock.close()
        q.get()

    start_new_thread(writer, ())
    q = Queue()
    try:
        while True:
            t = transport.poll_connection()
            server.process_connection(t)
    except Quit:
        pass
    q.put(None)


class FakeTransport(object):
    def __init__(self, queue):
        self.queue = list(reversed(queue))
        self.send_queue = []

    def send(self, addr_as_int, lgt):
        buf = rffi.cast(rffi.CCHARP, addr_as_int)
        self.send_queue.append("".join([buf[i] for i in range(lgt)]))

    def sendall(self, out):
        self.send_queue.append(out)

    def recv(self, addr_as_int, lgt):
        data = self.queue.pop()
        buf = rffi.cast(rffi.CCHARP, addr_as_int)
        assert lgt == len(data)
        for i, c in enumerate(data):
            buf[i] = c

    def poll_connection(self):
        return self

    def close(self):
        pass

def run_fake_server(tmpdir, queue, files):
    for fname, content in files:
        tmpdir.join(fname).write(content)

    server = FCGIServer(debug=True)
    transport = FakeTransport(queue)
    try:
        while True:
            t = transport.poll_connection()
            server.process_connection(t)
    except Quit:
        pass
    return transport

def pack_dict(d):
    def p(v):
        return v | (0x80 << 24)

    q = []
    for k, v in d.iteritems():
        if len(k) < 128 and len(v) < 128:
            q += [chr(len(k)), chr(len(v)), k, v]
        elif len(v) < 128:
            q += [struct.pack("!I", p(len(k))), chr(len(v)), k, v]
        elif len(k) < 128:
            q += [chr(len(k)), struct.pack("!I", p(len(v))), k, v]
        else:
            q += [struct.pack("!I", p(len(k))), struct.pack("!I", p(len(v))),
                  k, v]
    return "".join(q)

def test_fcgi_missing_document_root():
    import os, StringIO
    from ext_module.fastcgi.fcgi import Request
    req = Request("some_request_id")
    req.query_params['DOCUMENT_ROOT'] = '/foo/bar/nonexistent'
    old_os_wite = os.write
    try:
        s = StringIO.StringIO()
        os.write = lambda fd, msg: s.write(msg)
        req.perform_query("fake server")
    finally:
        os.write = old_os_wite
    assert s.getvalue() == "DOCUMENT_ROOT=/foo/bar/nonexistent, but cannot chdir to it\n"

def test_fcgi_bogus_script_filename():
    import os, StringIO
    from ext_module.fastcgi.fcgi import Request
    req = Request("some_request_id")
    req.query_params['DOCUMENT_ROOT'] = '/tmp'
    req.query_params['SCRIPT_FILENAME'] = '/somewhere/else'
    old_os_wite = os.write
    try:
        s = StringIO.StringIO()
        os.write = lambda fd, msg: s.write(msg)
        req.perform_query("fake server")
    finally:
        os.write = old_os_wite
    assert s.getvalue() == ("DOCUMENT_ROOT=/tmp, but SCRIPT_FILENAME=/somewhere/else: "
                            "does not contain DOCUMENT_ROOT anywhere\n")


class Base(object):
    def basic_query(self, fname):
        return {'SCRIPT_FILENAME': str(self.tmpdir.join(fname)),
                'DOCUMENT_ROOT': str(self.tmpdir)}

    def setup_method(self, meth):
        self.tmpdir = py.path.local(tempfile.mkdtemp())

class TestFastCGIFakeTransport(Base):

    def test_basic(self):
        d = self.basic_query('index.php')
        hdr = pack_dict(d)
        q = [
            struct.pack(FCGI_HEADER, 1, FCGI_BEGIN_REQUEST,
                        1, struct.calcsize(FCGI_BEGIN_REQUEST_BODY) , 0),
            struct.pack(FCGI_BEGIN_REQUEST_BODY, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_PARAMS, 1, len(hdr), 0),
            hdr,
            struct.pack(FCGI_HEADER, 1, FCGI_PARAMS, 1, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_STDIN, 1, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_DEBUG_QUIT, 0, 0, 0)
        ]
        transport = run_fake_server(self.tmpdir, q, [('index.php', '<? echo 3; ?>')])
        exp = "Content-Type: text/html\r\n\r\n3"
        assert transport.send_queue == [
            struct.pack(FCGI_HEADER, 1, FCGI_STDOUT, 1, len(exp), 0),
            exp,
            struct.pack(FCGI_HEADER, 1, FCGI_END_REQUEST,
                        1, struct.calcsize(FCGI_END_REQUEST_BODY), 0),
            struct.pack(FCGI_END_REQUEST_BODY, 0, 0),
        ]

    def test_include_cached(self):
        d = self.basic_query('index.php')
        hdr = pack_dict(d)
        q = [
            struct.pack(FCGI_HEADER, 1, FCGI_BEGIN_REQUEST,
                        1, struct.calcsize(FCGI_BEGIN_REQUEST_BODY) , 0),
            struct.pack(FCGI_BEGIN_REQUEST_BODY, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_PARAMS, 1, len(hdr), 0),
            hdr,
            struct.pack(FCGI_HEADER, 1, FCGI_PARAMS, 1, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_STDIN, 1, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_BEGIN_REQUEST,
                        1, struct.calcsize(FCGI_BEGIN_REQUEST_BODY) , 0),
            struct.pack(FCGI_BEGIN_REQUEST_BODY, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_PARAMS, 1, len(hdr), 0),
            hdr,
            struct.pack(FCGI_HEADER, 1, FCGI_PARAMS, 1, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_STDIN, 1, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_DEBUG_QUIT, 0, 0, 0)
        ]
        transport = run_fake_server(self.tmpdir, q, [
            ('index.php', '<? include "x.php"; echo f();?>'),
            ('x.php', '<? function f() { return 3; }?>'),
        ])
        exp = "Content-Type: text/html\r\n\r\n3"
        assert transport.send_queue == [
            struct.pack(FCGI_HEADER, 1, FCGI_STDOUT, 1, len(exp), 0),
            exp,
            struct.pack(FCGI_HEADER, 1, FCGI_END_REQUEST,
                        1, struct.calcsize(FCGI_END_REQUEST_BODY), 0),
            struct.pack(FCGI_END_REQUEST_BODY, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_STDOUT, 1, len(exp), 0),
            exp,
            struct.pack(FCGI_HEADER, 1, FCGI_END_REQUEST,
                        1, struct.calcsize(FCGI_END_REQUEST_BODY), 0),
            struct.pack(FCGI_END_REQUEST_BODY, 0, 0),
        ]

    def test_basic_params(self):
        d = self.basic_query('main.php')
        d.update({'QUERY_STRING': 'xyz=3'})
        hdr = pack_dict(d)
        q = [
            struct.pack(FCGI_HEADER, 1, FCGI_BEGIN_REQUEST,
                        1, struct.calcsize(FCGI_BEGIN_REQUEST_BODY) , 0),
            struct.pack(FCGI_BEGIN_REQUEST_BODY, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_PARAMS, 1, len(hdr), 0),
            hdr,
            struct.pack(FCGI_HEADER, 1, FCGI_PARAMS, 1, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_STDIN, 1, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_DEBUG_QUIT, 0, 0, 0)
        ]
        transport = run_fake_server(self.tmpdir, q, [('main.php', '<? echo $_GET["xyz"]; ?>')])
        exp = "Content-Type: text/html\r\n\r\n3"
        assert transport.send_queue == [
            struct.pack(FCGI_HEADER, 1, FCGI_STDOUT, 1, len(exp), 0),
            exp,
            struct.pack(FCGI_HEADER, 1, FCGI_END_REQUEST,
                        1, struct.calcsize(FCGI_END_REQUEST_BODY), 0),
            struct.pack(FCGI_END_REQUEST_BODY, 0, 0),
        ]

    def test_two_requests(self):
        d = self.basic_query('main.php')
        hdr = pack_dict(d)
        d = self.basic_query('index.php')
        hdr2 = pack_dict(d)
        q = [
            struct.pack(FCGI_HEADER, 1, FCGI_BEGIN_REQUEST,
                        1, struct.calcsize(FCGI_BEGIN_REQUEST_BODY) , 0),
            struct.pack(FCGI_BEGIN_REQUEST_BODY, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_PARAMS, 1, len(hdr), 0),
            hdr,
            struct.pack(FCGI_HEADER, 1, FCGI_PARAMS, 1, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_STDIN, 1, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_BEGIN_REQUEST,
                        1, struct.calcsize(FCGI_BEGIN_REQUEST_BODY) , 0),
            struct.pack(FCGI_BEGIN_REQUEST_BODY, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_PARAMS, 1, len(hdr2), 0),
            hdr2,
            struct.pack(FCGI_HEADER, 1, FCGI_PARAMS, 1, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_STDIN, 1, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_DEBUG_QUIT, 0, 0, 0)
        ]
        transport = run_fake_server(self.tmpdir, q, [('main.php', '<? echo "a\n"; ?>'),
                                        ("index.php", '<? echo "b\n"; ?>')])
        exp = "Content-Type: text/html\r\n\r\na\n"
        exp2 = "Content-Type: text/html\r\n\r\nb\n"
        assert transport.send_queue == [
            struct.pack(FCGI_HEADER, 1, FCGI_STDOUT, 1, len(exp), 0),
            exp,
            struct.pack(FCGI_HEADER, 1, FCGI_END_REQUEST,
                        1, struct.calcsize(FCGI_END_REQUEST_BODY), 0),
            struct.pack(FCGI_END_REQUEST_BODY, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_STDOUT, 1, len(exp2), 0),
            exp2,
            struct.pack(FCGI_HEADER, 1, FCGI_END_REQUEST,
                        1, struct.calcsize(FCGI_END_REQUEST_BODY), 0),
            struct.pack(FCGI_END_REQUEST_BODY, 0, 0),
        ]

    def test_long_names(self):
        d1 = {"a" * 130: "b"}
        d1.update(self.basic_query('index.php'))
        hdr1 = pack_dict(d1)
        d2 = {"a": "b" * 130}
        d2.update(self.basic_query('index.php'))
        hdr2 = pack_dict(d2)
        d3 = {"a" * 131: "b" * 131}
        d3.update(self.basic_query('index.php'))
        hdr3 = pack_dict(d3)
        q = [
            struct.pack(FCGI_HEADER, 1, FCGI_BEGIN_REQUEST,
                        1, struct.calcsize(FCGI_BEGIN_REQUEST_BODY) , 0),
            struct.pack(FCGI_BEGIN_REQUEST_BODY, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_PARAMS, 1, len(hdr1), 0),
            hdr1,
            struct.pack(FCGI_HEADER, 1, FCGI_PARAMS, 1, len(hdr2), 0),
            hdr2,
            struct.pack(FCGI_HEADER, 1, FCGI_PARAMS, 1, len(hdr3), 0),
            hdr3,
            struct.pack(FCGI_HEADER, 1, FCGI_PARAMS, 1, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_STDIN, 1, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_DEBUG_QUIT, 0, 0, 0)
        ]
        transport = run_fake_server(self.tmpdir, q, [('index.php',
                '''<? echo $_SERVER["%s"] . "\n";
                echo $_SERVER["%s"] . "\n";
                echo $_SERVER["a"] . "\n";
                ?>''' % ("a" * 130, "a" * 131))])
        exp = "Content-Type: text/html\r\n\r\nb\n%s\n%s\n" % ("b" * 131, "b" * 130)
        assert transport.send_queue == [
            struct.pack(FCGI_HEADER, 1, FCGI_STDOUT, 1, len(exp), 0),
            exp,
            struct.pack(FCGI_HEADER, 1, FCGI_END_REQUEST,
                        1, struct.calcsize(FCGI_END_REQUEST_BODY), 0),
            struct.pack(FCGI_END_REQUEST_BODY, 0, 0),
        ]

    def test_post(self):
        d = self.basic_query('index.php')
        d.update({
            'CONTENT_LENGTH': '12',
            'CONTENT_TYPE': 'x-www-form-urlencoded',
        })
        content = 'abcd=1234567'
        hdr = pack_dict(d)
        q = [
            struct.pack(FCGI_HEADER, 1, FCGI_BEGIN_REQUEST,
                        1, struct.calcsize(FCGI_BEGIN_REQUEST_BODY) , 0),
            struct.pack(FCGI_BEGIN_REQUEST_BODY, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_PARAMS, 1, len(hdr), 0),
            hdr,
            struct.pack(FCGI_HEADER, 1, FCGI_PARAMS, 1, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_STDIN, 1, len(content), 0),
            content,
            struct.pack(FCGI_HEADER, 1, FCGI_STDIN, 1, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_DEBUG_QUIT, 0, 0, 0)
        ]
        transport = run_fake_server(self.tmpdir, q, [('index.php', '<? echo $_POST["abcd"]; ?>')])
        exp = "Content-Type: text/html\r\n\r\n1234567"
        assert transport.send_queue == [
            struct.pack(FCGI_HEADER, 1, FCGI_STDOUT, 1, len(exp), 0),
            exp,
            struct.pack(FCGI_HEADER, 1, FCGI_END_REQUEST,
                        1, struct.calcsize(FCGI_END_REQUEST_BODY), 0),
            struct.pack(FCGI_END_REQUEST_BODY, 0, 0),
        ]

    def test_file_does_not_exist(self):
        d = self.basic_query('index.php')
        hdr = pack_dict(d)
        q = [
            struct.pack(FCGI_HEADER, 1, FCGI_BEGIN_REQUEST,
                        1, struct.calcsize(FCGI_BEGIN_REQUEST_BODY) , 0),
            struct.pack(FCGI_BEGIN_REQUEST_BODY, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_PARAMS, 1, len(hdr), 0),
            hdr,
            struct.pack(FCGI_HEADER, 1, FCGI_PARAMS, 1, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_STDIN, 1, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_DEBUG_QUIT, 0, 0, 0)
        ]
        transport = run_fake_server(self.tmpdir, q, [])
        assert transport.send_queue == [
            struct.pack(FCGI_HEADER, 1, FCGI_STDOUT, 1, 0, 0),
            struct.pack(FCGI_HEADER, 1, FCGI_END_REQUEST,
                        1, struct.calcsize(FCGI_END_REQUEST_BODY), 0),
            struct.pack(FCGI_END_REQUEST_BODY, 0, 0),
        ]        
        

class TestFastCGIRealSocket(Base):

    def send_begin(self, sock, req_id=1):
        sock.sendall(struct.pack(FCGI_HEADER, 1, FCGI_BEGIN_REQUEST,
                     req_id, struct.calcsize(FCGI_BEGIN_REQUEST_BODY)
                    , 0))
        sock.sendall(struct.pack(FCGI_BEGIN_REQUEST_BODY, 0, 0))

    def test_basic_response(self):
        def writer_part(sock):
            self.send_begin(sock)
            d = self.basic_query('index.php')
            hdr = pack_dict(d)
            sock.sendall(struct.pack(FCGI_HEADER, 1, FCGI_PARAMS, 1, len(hdr), 0))
            sock.sendall(hdr)
            sock.sendall(struct.pack(FCGI_HEADER, 1, FCGI_PARAMS, 1, 0, 0))
            sock.sendall(struct.pack(FCGI_HEADER, 1, FCGI_STDIN, 1, 0, 0))
            res1 = sock.recv(FCGI_HEADER_LEN)
            packet = struct.unpack(FCGI_HEADER, res1)
            assert packet[:3] == (1, FCGI_STDOUT, 1)
            content_length = packet[3]
            res2 = sock.recv(content_length)
            exp = "Content-Type: text/html\r\n\r\nxyz"
            assert res2 == exp
            res3 = sock.recv(FCGI_HEADER_LEN)
            s = struct.calcsize(FCGI_END_REQUEST_BODY)
            assert struct.unpack(FCGI_HEADER, res3) == (1, FCGI_END_REQUEST,
                                                        1, s, 0)
            sock.recv(s)

        run_server_and_writer(self.tmpdir, writer_part,
                              [('index.php', '<? echo "xyz"; ?>')])
