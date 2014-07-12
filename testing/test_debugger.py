import pytest
import os, thread
from hippy.debugger import Connection, Message
from hippy.objspace import ObjSpace
from testing.test_interpreter import MockInterpreter, preparse


class TestDebugger(object):
    def setup_method(self, meth):
        self.read_fd1, self.write_fd1 = os.pipe()
        self.read_fd2, self.write_fd2 = os.pipe()

    def teardown_method(self, meth):
        os.close(self.read_fd1)
        os.close(self.write_fd1)
        os.close(self.read_fd2)
        os.close(self.write_fd2)

    def run(self, interp, source):
        source = preparse(source)
        bc = interp.compile(source)
        interp.run_bytecode(bc)

    def test_basic_pipe_communication(self):
        d = Connection(self.read_fd1, self.write_fd2)
        os.write(self.write_fd1, "breakpoint a;")
        assert d.read() == Message("breakpoint", ["a"])
        os.write(self.write_fd1, "echo a;echo")
        assert d.read() == Message("echo", ["a"])
        os.write(self.write_fd1, " b;echo a;echo b;echo c;")
        assert d.read() == Message("echo", ["b"])
        assert d.read() == Message("echo", ["a"])
        assert d.read() == Message("echo", ["b"])
        assert d.read() == Message("echo", ["c"])
        d.write(Message("foo", ["a", "b"]))
        s = os.read(self.read_fd2, 100)
        assert s == "foo a b;"

    def test_basic_debugger(self):
        space = ObjSpace()
        interp = MockInterpreter(space)
        interp.setup_debugger(self.read_fd1, self.write_fd2)
        c = Connection(self.read_fd2, self.write_fd1)
        c.write(Message("force_breakpoint", ["f"])); ok(c)
        c.write(Message("continue", None)); ok(c)
        interp.debugger.run_debugger_loop(interp)
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ["Breakpoint set f"])
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ["Continuing"])
        self.run(interp, """
        function f() {
        }
        """)

        def c1():
            assert c.read() == Message("echo", ["stop breakpoint f"])
            ok(c)
            assert c.read() == Message(">", None)
            c.write(Message("continue", None)); ok(c)

        thread.start_new_thread(c1, ())
        self.run(interp, "f();")
        assert not c.more_pending_messages()
        assert not interp.debugger.conn.more_pending_messages()
        assert not interp.msgs
        interp.shutdown()

    def test_eval(self):
        space = ObjSpace()
        interp = MockInterpreter(space)
        interp.setup_debugger(self.read_fd1, self.write_fd2)
        c = Connection(self.read_fd2, self.write_fd1)
        c.write(Message("force_breakpoint", ["f"])); ok(c)
        c.write(Message("continue", None)); ok(c)
        interp.debugger.run_debugger_loop(interp)
        self.run(interp, """
        function f($a, $b, $x) {
        }
        """)
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ["Breakpoint set f"])
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ["Continuing"])
        ok(c)
        c.write(Message("eval", ["$x"])); ok(c)
        c.write(Message("backtrace", None)); ok(c)
        c.write(Message("continue", None)); ok(c)
        self.run(interp, """
        f(1, 2, 3);
        """)
        assert c.read() == Message("echo", ["stop breakpoint f"])
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ["int(3)"])
        assert c.read() == Message(">", None)
        exp_traceback = ["<input>", "f", "2", "function f($a, $b, $x) {",
                         "<input>", "<main>", "2", "f(1, 2, 3);"]
        msg = c.read()
        assert msg == Message("traceback", exp_traceback)
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ['Continuing'])
        assert not c.more_pending_messages()
        assert not interp.debugger.conn.more_pending_messages()
        assert not interp.msgs
        interp.shutdown()

    def test_empty_backtrace(self):
        space = ObjSpace()
        interp = MockInterpreter(space)
        interp.setup_debugger(self.read_fd1, self.write_fd2)
        c = Connection(self.read_fd2, self.write_fd1)
        c.write(Message("backtrace", None)); ok(c)
        c.write(Message("continue", None)); ok(c)
        interp.debugger.run_debugger_loop(interp)
        self.run(interp, "")
        assert c.read() == Message(">", None)
        assert c.read() == Message("warn", ["empty backtrace"])
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ['Continuing'])
        assert not c.more_pending_messages()
        assert not interp.debugger.conn.more_pending_messages()
        assert not interp.msgs
        interp.shutdown()

    def test_class_breakpoint_and_traceback(self):
        space = ObjSpace()
        interp = MockInterpreter(space)
        interp.setup_debugger(self.read_fd1, self.write_fd2)
        c = Connection(self.read_fd2, self.write_fd1)
        c.write(Message("force_breakpoint", ["klass::method"])); ok(c)
        c.write(Message("continue", None)); ok(c)
        interp.debugger.run_debugger_loop(interp)

        def c1():
            assert c.read() == Message(">", None)
            assert c.read() == Message("echo", ["Breakpoint set klass::method"])
            assert c.read() == Message(">", None)
            assert c.read() == Message("echo", ["Continuing"])
            assert c.read() == Message("echo", ["stop breakpoint klass::method"])
            ok(c)
            assert c.read() == Message(">", None)
            c.write(Message("eval", ["$x"])); ok(c)
            c.write(Message("continue", None)); ok(c)

        thread.start_new_thread(c1, ())
        self.run(interp, """
        class klass {
            function method($x) {
            }
        }
        $x = new klass();
        $x->method(13);
        """)
        assert c.read() == Message("echo", ["int(13)"])
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ['Continuing'])
        assert not c.more_pending_messages()
        assert not interp.debugger.conn.more_pending_messages()
        assert not interp.msgs
        interp.shutdown()

    def test_next_step(self):
        pytest.xfail()
        space = ObjSpace()
        interp = MockInterpreter(space)
        interp.setup_debugger(self.read_fd1, self.write_fd2)
        c = Connection(self.read_fd2, self.write_fd1)
        c.write(Message("force_breakpoint", ["f"])); ok(c)
        c.write(Message("continue", None)); ok(c)
        interp.debugger.run_debugger_loop(interp)

        def c1():
            assert c.read() == Message(">", None)
            assert c.read() == Message("echo", ["Breakpoint set f"])
            assert c.read() == Message(">", None)
            assert c.read() == Message("echo", ["Continuing"])
            assert c.read() == Message("echo", ["stop breakpoint f"])
            ok(c)
            assert c.read() == Message(">", None)
            c.write(Message("eval", ["$a"]))
            assert c.read() == Message("echo", ["int(1)"])
            ok(c)
            assert c.read() == Message(">", None)
            c.write(Message("next", None))
            assert c.read() == Message("linechange", ["<input>", "3", "f",
                                                      "   $z = $a + $b + $c;"])
            ok(c)
            assert c.read() == Message(">", None)
            c.write(Message("next", None))
            assert c.read() == Message("linechange", ["<input>", "4", "f",
                                                      "   $a = $z - 3 + g();"])
            ok(c)
            assert c.read() == Message(">", None)
            c.write(Message("eval", ["$z"]))
            assert c.read() == Message("echo", ["int(6)"])
            ok(c)
            assert c.read() == Message(">", None)
            c.write(Message("step", None))
            assert c.read() == Message("echo", ["enter g"])
            ok(c)
            assert c.read() == Message("linechange", ["<input>", "8", "g",
                                                      "   return 13;"])
            ok(c)
            c.write(Message("continue", None))
            ok(c)

        thread.start_new_thread(c1, ())
        self.run(interp, """
        function f($a, $b, $c) {
           $z = $a + $b + $c;
           $a = $z - 3 + g();
           return $a;
        }

        function g() {
           return 13;
        }
        f(1, 2, 3);
        """)
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ['Continuing'])
        assert not c.more_pending_messages()
        assert not interp.debugger.conn.more_pending_messages()
        assert not interp.msgs
        interp.shutdown()

    def test_step_precise_position(self):
        space = ObjSpace()
        interp = MockInterpreter(space)
        interp.setup_debugger(self.read_fd1, self.write_fd2)
        c = Connection(self.read_fd2, self.write_fd1)
        c.write(Message("step", None)); ok(c); ok(c)
        c.write(Message("step", None)); ok(c)
        c.write(Message("step", None)); ok(c); ok(c)
        c.write(Message("continue", None)); ok(c); ok(c)
        interp.debugger.run_debugger_loop(interp)
        interp.echo = interp.print_expr    # <= hack

        self.run(interp, """
        $a = 5;
        echo 'foobar';
        echo 'baz';
        """)
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ["enter <main>"])
        assert c.read() == Message("linechange", ["<input>", "2", "<main>",
                                                  "$a = 5;"])
        assert c.read() == Message(">", None)
        assert c.read() == Message("linechange", ["<input>", "3", "<main>",
                                                  "echo 'foobar';"])
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ['string(6) "foobar"'])
        assert c.read() == Message("linechange", ["<input>", "4", "<main>",
                                                  "echo 'baz';"])
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ['Continuing'])
        assert c.read() == Message("echo", ['string(3) "baz"'])
        assert not c.more_pending_messages()
        assert not interp.debugger.conn.more_pending_messages()
        assert not interp.msgs
        interp.shutdown()

    def test_step_enter_leave(self):
        space = ObjSpace()
        interp = MockInterpreter(space)
        interp.setup_debugger(self.read_fd1, self.write_fd2)
        c = Connection(self.read_fd2, self.write_fd1)
        c.write(Message("step", None)); ok(c); ok(c)
        c.write(Message("step", None)); ok(c); ok(c)
        c.write(Message("backtrace", None)); ok(c)
        c.write(Message("step", None)); ok(c); ok(c); ok(c); ok(c)
        c.write(Message("step", None)); ok(c); ok(c); ok(c)
        c.write(Message("step", None)); ok(c); ok(c)
        c.write(Message("continue", None)); ok(c); ok(c)
        interp.debugger.run_debugger_loop(interp)
        interp.echo = interp.print_expr    # <= hack

        self.run(interp, """
        function F() {
            echo 'fff';
        }
        F(); F();
        F();
        """)
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ["enter <main>"])
        assert c.read() == Message("linechange", ["<input>", "5", "<main>",
                                                  "F(); F();"])
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ["enter F"])
        assert c.read() == Message("linechange", ["<input>", "3", "F",
                                                  "    echo 'fff';"])
        assert c.read() == Message(">", None)
        exp_traceback = ["<input>", "F", "3", "    echo 'fff';",
                         "<input>", "<main>", "5", "F(); F();"]
        assert c.read() == Message("traceback", exp_traceback)
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ['string(3) "fff"'])
        assert c.read() == Message("echo", ["leave F"])
        assert c.read() == Message("echo", ["enter F"])
        assert c.read() == Message("linechange", ["<input>", "3", "F",
                                                  "    echo 'fff';"])
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ['string(3) "fff"'])
        assert c.read() == Message("echo", ["leave F"])
        assert c.read() == Message("linechange", ["<input>", "6", "<main>",
                                                  "F();"])
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ["enter F"])
        assert c.read() == Message("linechange", ["<input>", "3", "F",
                                                  "    echo 'fff';"])
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ['Continuing'])
        assert c.read() == Message("echo", ['string(3) "fff"'])
        assert not c.more_pending_messages()
        assert not interp.debugger.conn.more_pending_messages()
        assert not interp.msgs
        interp.shutdown()

    def test_next_is_step_if_not_a_call(self):
        space = ObjSpace()
        interp = MockInterpreter(space)
        interp.setup_debugger(self.read_fd1, self.write_fd2)
        c = Connection(self.read_fd2, self.write_fd1)
        c.write(Message("next", None)); ok(c); ok(c)
        c.write(Message("next", None)); ok(c); ok(c)
        c.write(Message("continue", None)); ok(c)
        interp.debugger.run_debugger_loop(interp)
        interp.echo = interp.print_expr    # <= hack

        self.run(interp, """
        echo 'fff';
        $a = 5;
        """)
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ["enter <main>"])
        assert c.read() == Message("linechange", ["<input>", "2", "<main>",
                                                  "echo 'fff';"])
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ['string(3) "fff"'])
        assert c.read() == Message("linechange", ["<input>", "3", "<main>",
                                                  "$a = 5;"])
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ['Continuing'])
        assert not c.more_pending_messages()
        assert not interp.debugger.conn.more_pending_messages()
        assert not interp.msgs
        interp.shutdown()

    def test_next_skips_all_nested_calls(self):
        space = ObjSpace()
        interp = MockInterpreter(space)
        interp.setup_debugger(self.read_fd1, self.write_fd2)
        c = Connection(self.read_fd2, self.write_fd1)
        c.write(Message("next", None)); ok(c); ok(c)
        c.write(Message("next", None)); ok(c)
        c.write(Message("continue", None)); ok(c)
        interp.debugger.run_debugger_loop(interp)
        interp.echo = interp.print_expr    # <= hack

        self.run(interp, """
        function F() {
            return G();
        }
        function G() {
            return 42;
        }
        $a = F();
        $a++;
        """)
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ["enter <main>"])
        assert c.read() == Message("linechange", ["<input>", "8", "<main>",
                                                  "$a = F();"])
        assert c.read() == Message(">", None)
        assert c.read() == Message("linechange", ["<input>", "9", "<main>",
                                                  "$a++;"])
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ['Continuing'])
        assert not c.more_pending_messages()
        assert not interp.debugger.conn.more_pending_messages()
        assert not interp.msgs
        interp.shutdown()

    def test_next_passes_over_calls_on_the_same_line(self):
        space = ObjSpace()
        interp = MockInterpreter(space)
        interp.setup_debugger(self.read_fd1, self.write_fd2)
        c = Connection(self.read_fd2, self.write_fd1)
        c.write(Message("next", None)); ok(c); ok(c)
        c.write(Message("next", None)); ok(c); ok(c); ok(c)
        c.write(Message("continue", None)); ok(c)
        interp.debugger.run_debugger_loop(interp)
        interp.echo = interp.print_expr    # <= hack

        self.run(interp, """
        function F() {
            echo 'fff';
        }
        F(); F();
        $a = 5;
        """)
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ["enter <main>"])
        assert c.read() == Message("linechange", ["<input>", "5", "<main>",
                                                  "F(); F();"])
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ['string(3) "fff"'])
        assert c.read() == Message("echo", ['string(3) "fff"'])
        assert c.read() == Message("linechange", ["<input>", "6", "<main>",
                                                  "$a = 5;"])
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ['Continuing'])
        assert not c.more_pending_messages()
        assert not interp.debugger.conn.more_pending_messages()
        assert not interp.msgs
        interp.shutdown()

    def test_next_when_returning(self):
        space = ObjSpace()
        interp = MockInterpreter(space)
        interp.setup_debugger(self.read_fd1, self.write_fd2)
        c = Connection(self.read_fd2, self.write_fd1)
        c.write(Message("next", None)); ok(c); ok(c)
        c.write(Message("step", None)); ok(c); ok(c)
        c.write(Message("next", None)); ok(c); ok(c); ok(c)
        c.write(Message("continue", None)); ok(c)
        interp.debugger.run_debugger_loop(interp)
        interp.echo = interp.print_expr    # <= hack

        self.run(interp, """
        function F() {
            echo 'fff';
        }
        F();
        $a = 5;
        """)
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ["enter <main>"])
        assert c.read() == Message("linechange", ["<input>", "5", "<main>",
                                                  "F();"])
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ["enter F"])
        assert c.read() == Message("linechange", ["<input>", "3", "F",
                                                  "    echo 'fff';"])
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ['string(3) "fff"'])
        assert c.read() == Message("echo", ["leave F"])
        assert c.read() == Message("linechange", ["<input>", "6", "<main>",
                                                  "$a = 5;"])
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ['Continuing'])
        assert not c.more_pending_messages()
        assert not interp.debugger.conn.more_pending_messages()
        assert not interp.msgs
        interp.shutdown()

    def test_next_does_not_reenter_when_returning(self):
        space = ObjSpace()
        interp = MockInterpreter(space)
        interp.setup_debugger(self.read_fd1, self.write_fd2)
        c = Connection(self.read_fd2, self.write_fd1)
        c.write(Message("next", None)); ok(c); ok(c)
        c.write(Message("step", None)); ok(c); ok(c)
        c.write(Message("next", None)); ok(c); ok(c); ok(c); ok(c)
        c.write(Message("continue", None)); ok(c)
        interp.debugger.run_debugger_loop(interp)
        interp.echo = interp.print_expr    # <= hack

        self.run(interp, """
        function F() {
            echo 'fff';
        }
        F(); F();
        $a = 5;
        """)
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ["enter <main>"])
        assert c.read() == Message("linechange", ["<input>", "5", "<main>",
                                                  "F(); F();"])
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ["enter F"])
        assert c.read() == Message("linechange", ["<input>", "3", "F",
                                                  "    echo 'fff';"])
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ['string(3) "fff"'])
        assert c.read() == Message("echo", ["leave F"])
        assert c.read() == Message("echo", ['string(3) "fff"'])
        assert c.read() == Message("linechange", ["<input>", "6", "<main>",
                                                  "$a = 5;"])
        assert c.read() == Message(">", None)
        assert c.read() == Message("echo", ['Continuing'])
        assert not c.more_pending_messages()
        assert not interp.debugger.conn.more_pending_messages()
        assert not interp.msgs
        interp.shutdown()


def ok(c):
    c.write(Message(".", None))
