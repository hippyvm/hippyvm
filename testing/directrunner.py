
import py
import subprocess
import re
import tempfile

from hippy.objects.instanceobject import W_InstanceObject
from hippy.mapdict import Terminator
from testing.runner import MockEngine

class FakeClass(object):
    def __init__(self, name):
        self.name = name
        self.base_map = Terminator(self)


r = re.compile(r"\becho\s+(.+?);", re.DOTALL)


def source_replace(source):
    # replace all echos with var_dumps so we know what we're doing
    new = r.sub(r"var_dump(\1);", source)
    return "<?php\n" + new


def parse_array(space, i, lines, lgt):
    pairs = []
    for k in range(lgt):
        line = lines[i].strip()
        assert line.endswith('=>')
        if line[1] == '"':
            if line[-4] == '"':
                w_key = space.newstr(line[2:-4])
            elif line.endswith('":protected]=>'):
                w_key = space.newstr('\x00*\x00' + line[2:-14])
            elif line.endswith('":private]=>'):
                j = line.index('":"')
                w_key = space.newstr('\x00%s\x00%s' % (
                    line[j + 3:-12], line[2:j]))
            else:
                assert 0, line
        else:
            w_key = space.wrap(int(line[1:-3]))
        w_value, i = parse_single(space, i + 1, lines)
        pairs.append((w_key, w_value))
    return pairs, i + 1


def parse_single(space, i, lines):
    line = lines[i].strip()

    #ignore byref markers in arrays/objects
    if line.startswith('&'):
        line = line[1:]

    if line.startswith('int'):
        return space.wrap(int(line[len('int('):-1])), i + 1
    elif line.startswith('bool'):
        return space.wrap(line[len('bool('):-1] == 'true'), i + 1
    if line.startswith('float'):
        return space.wrap(float(line[len('float('):-1])), i + 1
    elif line == 'NULL':
        return space.w_Null, i + 1
    elif line.startswith('array'):
        lgt = int(line[len('array') + 1:line.find(')')])
        pairs, i = parse_array(space, i + 1, lines, lgt)
        return space.new_array_from_pairs(pairs), i
    elif line.startswith('string'):
        lgt = int(line[len('string') + 1:line.find(')')])
        return space.newstr(line[line.find('"') + 1:-1]), i + 1
    elif line.startswith('object('):
        lgt = int(line[line.rfind('(') + 1:line.rfind(')')])
        clsname = line[len('object('):line.index(')')]
        pairs, i = parse_array(space, i + 1, lines, lgt)
        obj = W_InstanceObject(FakeClass(clsname), [])
        for w_name, w_value in pairs:
            obj._create_attr(space.str_w(w_name), w_value)
        return obj, i
    else:
        raise Exception("unsupported line %s" % line)


def parse_error(space, i, lines):
    line = lines[i + 1]
    line = line[:line.rfind(' in /')]
    return line, i + 2


def parse_result(space, stdout):
    lines = []
    (NORMAL, QUOTE) = range(2)
    state = NORMAL
    sofar = ""
    ### cut output char by char
    for c in stdout:
        sofar += c
        if state == NORMAL and c == '"':
            state = QUOTE
            continue
        if state == QUOTE and c == '"':
            state = NORMAL
            continue
        if state == NORMAL and c == '\n':
            lines.append(sofar[:-1])
            sofar = ""
    output = []
    errors = []
    i = 0
    while i < len(lines):
        if lines[i] == '':
            # an empty line is printed before Notice / Fatal error / etc.
            err, i = parse_error(space, i, lines)
            errors.append(err)
        else:
            next, i = parse_single(space, i, lines)
            output.append(next)
    return output, errors


def run_source(space, source, expected_warnings=None):
    return DirectRunner(space)._run(source, expected_warnings=expected_warnings)


def run_php_source(php_source, expected_return_code=0):
    f = tempfile.NamedTemporaryFile()
    py.path.local(f.name).write(php_source, mode='wb')
    pipe = subprocess.Popen(['php', '-d', 'error_reporting=65535',
        '-d', 'display_errors=1', f.name],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    stdout, stderr = pipe.communicate()
    if pipe.returncode != expected_return_code:
        crash = "php exited with error code %s (expected %s)" % (
            pipe.returncode, expected_return_code)
    else:
        return stdout
    raise Exception("%s\nstdout:\n%s" % (crash, stdout))


class DirectRunner(MockEngine):
    def _run(self, source, extra_func=None, err_stream=None, inp_stream=None,
            expected_warnings=None, **kwds):
        php_source = source_replace(source)
        if (expected_warnings and
               (expected_warnings[-1].startswith('Fatal error: ') or
                expected_warnings[-1].startswith('Catchable fatal error: '))):
            expected_return_code = 255
        else:
            expected_return_code = 0
        stdout = run_php_source(php_source, expected_return_code)
        output, errors = parse_result(self.space, stdout)
        self.err_stream.extend(errors)
        return output

    def filter_warnings(self, warnings):
        return [msg for msg in warnings
                if not msg.startswith('Hippy warning: ')]
