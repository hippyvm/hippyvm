
""" This is a remote debugging utility that you can connect to
using pipes
"""

import os
from rpython.rlib.rstring import StringBuilder

class Message(object):
    def __init__(self, command, args):
        self.command = command
        self.args = args

    def escape(self):
        if self.args is None:
            return self.command
        s = StringBuilder()
        s.append(self.command)
        for arg in self.args:
            s.append(" ")
            for c in arg:
                if c == '\\':
                    s.append('\\\\')
                elif c == ';':
                    s.append('\\;')
                elif c == "\n":
                    s.append("\\n")
                elif c == " ":
                    s.append("\\_")
                else:
                    s.append(c)
        return s.build()

    def __repr__(self):
        return "Message(%s, %r)" % (self.command, self.args)

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return NotImplemented
        return self.command == other.command and self.args == other.args

EXPECTED_ARGS = {
    'breakpoint': 1,
    'force_breakpoint': 1,
    'continue': 0,
    'eval': 1,
    'backtrace': 0,
    'echo': -1,
    'warn': 1,
    '>': 0,
    '.': 0,     # sent to hippy-c in reply to any command that prints something
    'traceback': -1,
    'next': -1,
    'step': -1,
    'linechange': 4,
}

msg_prompt = Message('>', None)


class InvalidMessage(Exception):
    def __init__(self, msg):
        self.msg = msg


def create_message(raw_msg):
    first_space = raw_msg.find(" ")
    if first_space < 0:
        if raw_msg not in EXPECTED_ARGS or EXPECTED_ARGS[raw_msg] > 0:
            raise InvalidMessage(raw_msg)
        return Message(raw_msg, None)
    command = raw_msg[:first_space]
    if command not in EXPECTED_ARGS:
        raise InvalidMessage(raw_msg)
    i = first_space + 1
    s = StringBuilder()
    args = []
    while i < len(raw_msg):
        c = raw_msg[i]
        if c == '\\':
            if i < len(raw_msg) - 1:
                if raw_msg[i + 1] == '\\':
                    s.append('\\')
                    i += 2
                    continue
                elif raw_msg[i + 1] == ';':
                    s.append(';')
                    i += 2
                    continue
                elif raw_msg[i + 1] == "n":
                    s.append("\n")
                    i += 2
                    continue
                elif raw_msg[i + 1] == "_":
                    s.append(" ")
                    i += 2
                    continue
        elif c == "\n":
            # ignore newlines
            i += 1
            continue
        elif c == " ":
            args.append(s.build())
            s = StringBuilder()
            i += 1
            continue
        s.append(c)
        i += 1
    args.append(s.build())
    if EXPECTED_ARGS[command] != -1 and len(args) != EXPECTED_ARGS[command]:
        raise InvalidMessage(raw_msg)
    return Message(command, args)

class Connection(object):

    def __init__(self, read_fd, write_fd):
        self.read_fd = read_fd
        self.write_fd = write_fd
        # 'buffer' is the reversed list of string messages pending reception.
        # If not empty, then 'buffer[0]' is the last message, which is
        # incomplete --- we're still waiting for its final semicolon.
        self.buffer = []

    def read(self):
        msg = None
        while msg is None:
            msg = self._read()
        return msg

    def _find_first_split(self, msg, start=0):
        backslash = False
        i = start
        while i < len(msg):
            c = msg[i]
            if c == '\\':
                backslash = True
            elif c == ';' and not backslash:
                return i
            else:
                backslash = False
            i += 1
        return -1

    def _split_by_semicolon(self, msg):
        l = []
        prev_pos = 0
        pos = self._find_first_split(msg)
        while pos >= 0:
            l.append(msg[prev_pos:pos])
            prev_pos = pos + 1
            pos = self._find_first_split(msg, pos + 1)
        l.append(msg[prev_pos:])
        return l

    def _read(self):
        if len(self.buffer) > 1:
            return create_message(self.buffer.pop())
        msg = os.read(self.read_fd, 1024)
        if not msg:
            raise EOFError
        semicolon = self._find_first_split(msg)
        if semicolon < 0:
            # no semicolon, just append it to the last item in the buffer
            if self.buffer:
                self.buffer[-1] += msg
            else:
                self.buffer.append(msg)
            return
        # we have the semicolon
        one_msg = msg[:semicolon]
        if semicolon == len(msg) - 1:
            if self.buffer:
                # fast path
                res = self.buffer[0] + one_msg
                self.buffer = []
                return create_message(res)
            else:
                return create_message(one_msg)
        # otherwise store the rest split by semicolons, reversed
        res = self._split_by_semicolon(msg[semicolon + 1:])
        res.reverse()
        if self.buffer:
            one_msg = self.buffer[0] + one_msg
        self.buffer = res
        return create_message(one_msg)

    def more_pending_messages(self):
        return (len(self.buffer) > 1 or
                (len(self.buffer) == 1 and self.buffer[0] != ''))

    def write(self, msg):
        s = msg.escape() + ';'
        while True:
            sent = os.write(self.write_fd, s)
            if sent == len(s):
                break
            if sent < 0:
                raise OSError
            s = s[sent:]

STATE_NOTHING, STATE_NEXT, STATE_STEP = range(3)


class Debugger(object):
    state = STATE_NOTHING
    tracing_frame = None

    def __init__(self, read_fd, write_fd):
        self.breakpoints = {}
        self.conn = Connection(read_fd, write_fd)

    def _eval(self, interp, frame, source):
        # XXX add all kinds of exception handling
        interp.debug_eval(source, frame, allow_direct_class_access=True)

    def send_echo(self, string):
        self.send_and_wait("echo", [string])

    def send_and_wait(self, command, args):
        self.conn.write(Message(command, args))
        reply = self.conn.read()
        assert reply.command == '.'

    def _send_backtrace(self, interp, frame):
        if frame is None:
            self.send_and_wait("warn", ["empty backtrace"])
            return
        msg = []
        tb = interp.get_traceback()
        for filename, funcname, line, source in tb:
            msg += [filename, funcname, str(line), source]
        self.send_and_wait("traceback", msg)

    def run_debugger_loop(self, interp, frame=None):
        while True:
            self.conn.write(msg_prompt)
            self.state = STATE_NOTHING
            try:
                msg = self.conn.read()
            except InvalidMessage, e:
                self.send_and_wait("warn", ["Invalid message %s" % e.msg])
                continue
            if msg.command == "breakpoint":
                fname = msg.args[0].lower()
                try:
                    interp.lookup_function(fname)
                    self.breakpoints[fname] = True
                    self.send_and_wait("echo", ["Breakpoint set %s" % fname])
                except KeyError:
                    self.send_and_wait("warn",
                                     ["error function %s not found" % fname])
            elif msg.command == "force_breakpoint":
                fname = msg.args[0].lower()
                self.breakpoints[fname] = True
                self.send_and_wait("echo", ["Breakpoint set %s" % fname])
            elif msg.command == "eval":
                self._eval(interp, frame, msg.args[0])
            elif msg.command == "backtrace":
                self._send_backtrace(interp, frame)
            elif msg.command == 'continue':
                self.send_and_wait("echo",  ["Continuing"])
                return
            elif msg.command == "next":
                if frame is not None:
                    self.state = STATE_NEXT
                else:
                    self.state = STATE_STEP  # enter the outermost frame anyway
                self.tracing_frame = frame
                return
            elif msg.command == "step":
                self.state = STATE_STEP
                return
            else:
                self.send_and_wait("warn", ["Unknown message %s;" % msg])

    def enter_frame(self, interp, frame):
        frame._debugger_lineno = -1
        self._enter_frame(interp, frame)

    def leave_frame(self, interp, frame):
        if self.state == STATE_NOTHING:
            return
        self._leave_frame(interp, frame)

    def bytecode_trace(self, interp, frame, pc):
        if self.state == STATE_NOTHING:
            return
        self._bytecode_trace(interp, frame, pc)

    def _bytecode_trace(self, interp, frame, pc):
        bc = frame.bytecode
        lineno = frame.get_lineno()
        if self.state == STATE_NEXT and self.tracing_frame is not frame:
            return
        if lineno != frame._debugger_lineno:
            frame._debugger_lineno = lineno
            self.send_and_wait("linechange", [bc.filename,
                                     str(lineno), bc.name, bc.getline(lineno)])
            self.run_debugger_loop(interp, frame)

    def get_frame_name(self, frame):
        name = frame.bytecode.name
        if frame.thisclass is not None:
            name = frame.thisclass.name + "::" + name
        return name

    def _enter_frame(self, interp, frame):
        name = self.get_frame_name(frame)
        if self.state == STATE_STEP:
            self.send_and_wait("echo", ["enter " + name])
        elif name.lower() in self.breakpoints:
            self.send_and_wait("echo", ["stop breakpoint " + name])
            self.run_debugger_loop(interp, frame)
    _enter_frame._dont_inline_ = True

    def _leave_frame(self, interp, frame):
        if self.state == STATE_NEXT:
            if self.tracing_frame is frame:
                self.tracing_frame = frame.f_backref()
            else:
                return
        name = self.get_frame_name(frame)
        self.send_and_wait("echo", ["leave " + name])
    _leave_frame._dont_inline_ = True
