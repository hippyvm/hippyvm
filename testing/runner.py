import sys
import re
import py

from hippy.ast import CompilerError
from hippy.interpreter import Interpreter
from hippy.error import FatalError, ExplicitExitException
from hippy.objects.base import W_Root

# Check for the php executable -- this is a prerequisite.
# If we catch this now, then we can avoid obscure errors later on.
from distutils.spawn import find_executable
if find_executable("php") is None:
    raise RuntimeError("I could not find the 'php' executable!")

def preparse(source):
    """Preparse the source a bit so traceback starts with the
    correct number of whitespaces."""
    lines = source.splitlines(True)
    prefix = sys.maxint
    for line in lines:
        stripped = line.lstrip()
        if stripped:
            prefix = min(len(line) - len(stripped), prefix)
    for i, line in enumerate(lines):
        lines[i] = lines[i][prefix:]
    return "".join(lines)


class MockInterpreter(Interpreter):
    """ Like the interpreter, but captures stdout
    """
    def __init__(self, space, err_stream=None, inp_stream=None, pyspace=None):
        if err_stream is None:
            self.msgs = []
        else:
            self.msgs = err_stream
        Interpreter.__init__(self, space, pyspace)
        self.tb = []
        self.output = []
        self.inp_stream = inp_stream

    def open_stdin_stream(self):
        return self.inp_stream

    def writestr(self, msg, buffer=True):
        self.output.append(msg)

    def _log_traceback(self, filename, funcname, line, source):
        self.tb.append((filename, funcname, line, source))

    def _log(self, level, msg, filename='', line=-1):
        self.log_error(level, msg)

    def err_write(self, msg):
        self.msgs.append(msg.strip('\n'))

    def echo(self, space, w):
        assert isinstance(w, W_Root)
        self.output.append(w.deref())

    def send_headers(self):
        self.sent_headers = self.headers
        self.sent_extra_headers = self.extra_headers
        self.headers = None
        self.extra_headers = None

    def run_bytecode(self, bc, expected_warnings=None):
        try:
            self.run_main(self.space, bc, top_main=True)
        except (FatalError, ExplicitExitException):
            ok = False
            if expected_warnings:
                s = expected_warnings[-1]
                ok = (s.startswith('Fatal error: ') or
                    s.startswith('Catchable fatal error: '))
            if not ok:
                raise
        except CompilerError as e:
            s = ''
            if expected_warnings:
                s = expected_warnings[-1]
            if not s.startswith('Fatal error: '):
                raise
            self.msgs.append('Fatal error: ' + e.msg)
        return self.output

    def compile(self, source):
        return self.compile_bytecode('<input>', '<?\n' + source)


def matching_errors(got, expected):
    __tracebackhide__ = True
    for i in range(min(len(got), len(expected))):
        msg = expected[i]
        msg = re.escape(msg).replace(r'\.\.\.', '.*') + '$'
        if not re.match(msg, got[i]):
            py.test.fail("got the warning:\n%s\nbut expected:\n%s" % (
                got[i], expected[i]))
    if len(got) < len(expected):
        py.test.fail("missing an expected warning:\n%s" %
                '\n'.join(expected[len(got):]))
    elif len(got) > len(expected):
        py.test.fail("got an unexpected warning:\n%s" %
                '\n'.join(got[len(expected):]))


class WarningChecker(object):

    def __init__(self, engine, expected_warnings):
        self.engine = engine
        self.expected_warnings = expected_warnings

    def __enter__(self):
        self.engine.warn_ctx = self
        return self.engine.err_stream

    def __exit__(self, exc, *args):
        if exc is None and self.expected_warnings is not None:
            expected = self.engine.filter_warnings(self.expected_warnings)
            matching_errors(self.engine.err_stream, expected)
        self.engine.warn_ctx = None

class MockEngine(object):
    warn_ctx = None

    def __init__(self, space, pyspace=None):
        self.space = space
        self.pyspace = pyspace
        self.err_stream = []

    def warnings(self, expected_warnings=None):
        """ Context manager: allows self.run() to produce exactly the
        specified list of warnings. Pass [] for no warnings.

        Captures and returns the warnings as a list, for additional testing.
        If expected_warnings is not given, allows any warnings.
        """
        return WarningChecker(self, expected_warnings)

    def run(self, source, expected_warnings=[], extra_func=None,
            inp_stream=None, **kwds):
        del self.err_stream[:]
        if self.warn_ctx is None:
            with self.warnings(expected_warnings):
                return self._run(source, extra_func=extra_func,
                    inp_stream=inp_stream,
                    expected_warnings=self.warn_ctx.expected_warnings, **kwds)
        else:
            return self._run(source, extra_func=extra_func,
                inp_stream=inp_stream,
                expected_warnings=self.warn_ctx.expected_warnings, **kwds)

    def _run(self, source, extra_func=None, inp_stream=None,
            expected_warnings=None, **kwds):
        source = preparse(source)
        self.interp = self.new_interp(inp_stream=inp_stream,
                extra_func=extra_func, **kwds)
        bc = self.interp.compile(source)
        if bc is None:
            return self.interp.output
        bc.show()
        res = self.interp.run_bytecode(bc, expected_warnings)
        self.interp.shutdown()
        return res

    def new_interp(self, inp_stream, extra_func, **kwds):
        interp = self.Interpreter(self.space, self.err_stream,
                                  inp_stream=inp_stream, pyspace=self.pyspace)
        interp.setup(**kwds)
        if extra_func is not None:
            extra_func(interp)
        return interp

    def filter_warnings(self, warnings):
        return warnings
