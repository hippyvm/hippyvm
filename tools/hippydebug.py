#!/usr/bin/env python
"""Hippy debugger.

Usage: hippydebug.py [debugger_options] ../hippy-c args...

(There are no debugger_options so far.)
"""

import sys, os, signal
import getopt
import subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hippy.debugger import Connection, Message

def run_interactive(read_fd, write_fd):
    import readline    # for raw_input() below
    con = Connection(read_fd, write_fd)
    last_command = ''
    while True:
        try:
            msg = con.read()
        except EOFError:
            break
        if msg.command == '>':
            line = raw_input('> ')
            if not line:   # Ctrl-D
                break
            line = line.strip()
            if not line:
                line = last_command
            else:
                last_command = line
            lst = line.split(" ", 1)
            if len(lst) == 1:
                con.write(Message(lst[0], None))
            else:
                con.write(Message(lst[0], [lst[1]]))
        else:
            print msg.command, " ".join(msg.args)
            con.write(Message(".", None))

def reopen_terminal():
    f = open("/dev/tty", "r+", 0)
    sys.stdin = sys.stdout = sys.stderr = f
    os.dup2(f.fileno(), 0)
    os.dup2(f.fileno(), 1)
    os.dup2(f.fileno(), 2)

def printable_process_status(status):
    if os.WIFEXITED(status):
        return 'exit code %s' % (os.WEXITSTATUS(status),)
    elif os.WIFSIGNALED(status):
        return 'terminated by signal %s' % (os.WTERMSIG(status),)
    else:
        return 'unknown exit status 0x%x' % (status,)

def main(hippy_command, *hippy_args):
    read_fd1, write_fd1 = os.pipe()
    read_fd2, write_fd2 = os.pipe()

    child_pid = os.fork()
    if child_pid == 0:     # in the child
        os.close(read_fd1)
        os.close(write_fd2)
        hippy_command_list = [
            hippy_command,
            '--debugger_pipes', str(read_fd2), str(write_fd1),
            ] + list(hippy_args)
        os.execvp(hippy_command, hippy_command_list)
        # this point never reached

    os.close(read_fd2)
    os.close(write_fd1)

    try:
        reopen_terminal()
        print >> sys.stderr, 'Hippy Debugger'
        run_interactive(read_fd1, write_fd2)
    finally:
        os.kill(child_pid, signal.SIGQUIT)

    print >> sys.stderr, 'Hippy finished:',
    _, status = os.waitpid(child_pid, 0)
    print >> sys.stderr, printable_process_status(status)

if __name__ == '__main__':
    options, args = getopt.getopt(sys.argv[1:], '', [])
    if not args:
        print >> sys.stderr, __doc__
        sys.exit(1)
    if not os.path.isfile(args[0]):
        print >> sys.stderr, '%s: No such file' % (args[0],)
        sys.exit(1)
    main(*args)
