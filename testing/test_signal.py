import pytest

from testing.test_interpreter import BaseTestInterpreter
from hippy.error import SignalReceived


class TestSignal(BaseTestInterpreter):
    @pytest.yield_fixture(autouse=True)
    def handle_signals(self, setup_interp):
        self.space.ec.init_signals()
        try:
            yield
        finally:
            self.space.ec.clear_signals()

    def test_signal(self):
        import thread, time, os, signal

        def f():
            time.sleep(.5)
            os.kill(os.getpid(), signal.SIGINT)

        thread.start_new_thread(f, ())

        code = """
        while (True) { }
        """
        with pytest.raises(SignalReceived):
            self.run(code)
