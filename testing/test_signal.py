import signal
import pytest

from testing.test_interpreter import BaseTestInterpreter
from hippy.error import SignalReceived


class TestSignal(BaseTestInterpreter):
    @pytest.yield_fixture(autouse=True)
    def handle_signals(self, setup_interp):
        handler = signal.getsignal(signal.SIGINT)
        assert handler is not None
        self.space.ec.init_signals()
        yield
        self.space.ec.clear_signals()
        signal.signal(signal.SIGINT, handler)

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
