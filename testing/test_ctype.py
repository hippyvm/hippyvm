
from testing.test_interpreter import BaseTestInterpreter

class TestCtype(BaseTestInterpreter):
    def test_isdigit(self):
        output = self.run("""
        echo ctype_digit("0");
        echo ctype_digit("1a");
        echo ctype_digit("a");
        echo ctype_digit("");
        """)
        assert [self.unwrap(w_x) for w_x in output] == [True, False, False,
                                                        False]
