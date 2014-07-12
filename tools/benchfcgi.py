
""" fastcgi benchmarking tool

Usage: benchfcgi.py <port number>
"""

import py, tempfile
import sys, optparse, socket, struct

FCGI_BEGIN_REQUEST = 1
FCGI_ABORT_REQUEST = 2
FCGI_END_REQUEST = 3
FCGI_PARAMS = 4
FCGI_STDIN = 5
FCGI_STDOUT = 6
FCGI_STDERR = 7
FCGI_DATA = 8
FCGI_GET_VALUES = 9
FCGI_GET_VALUES_RESULT = 10
FCGI_UNKNOWN_TYPE = 11
FCGI_MAXTYPE = FCGI_UNKNOWN_TYPE

FCGI_HEADER_LEN = 8
     
FCGI_HEADER = '!BBHHBx'
FCGI_BEGIN_REQUEST_BODY = '!HB5x'
FCGI_END_REQUEST_BODY = '!LB3x'

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

def main(argv):
    if not argv:
        print __doc__
        sys.exit(1)
        
    port_no = int(argv[0])
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("localhost", port_no))
    tmpdir = py.path.local(tempfile.mkdtemp())
    tmpdir.join('index.php').write('<? echo 3; ?>')
    d = {'SCRIPT_FILENAME': str(tmpdir.join('index.php')),
         'DOCUMENT_ROOT': str(tmpdir)}
    hdr = pack_dict(d)
    packets = [
        struct.pack(FCGI_HEADER, 1, FCGI_BEGIN_REQUEST,
                    1, struct.calcsize(FCGI_BEGIN_REQUEST_BODY) , 0),
        struct.pack(FCGI_BEGIN_REQUEST_BODY, 0, 0),
        struct.pack(FCGI_HEADER, 1, FCGI_PARAMS, 1, len(hdr), 0),
        hdr,
        struct.pack(FCGI_HEADER, 1, FCGI_PARAMS, 1, 0, 0),
        struct.pack(FCGI_HEADER, 1, FCGI_STDIN, 1, 0, 0),
    ]
    for packet in packets:
        s.sendall(packet)

    XXX
    #print s.recv(1024)

if __name__ == '__main__':
    main(sys.argv[1:])
