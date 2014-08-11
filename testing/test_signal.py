
from testing.test_interpreter import BaseTestInterpreter
from hippy.error import SignalReceived

class TestSignal(BaseTestInterpreter):
    def test_signal(self):
        import thread, time, os, signal

        def f():
            time.sleep(.5)
            os.kill(os.getpid(), signal.SIGINT)

        thread.start_new_thread(f, ())
        
        code = """
        while (True) { }
        """
        try:
            self.run(code)
        except SignalReceived:
            pass
        else:
            raise Exception("did not raise")
