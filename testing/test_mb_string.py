
from testing.test_interpreter import BaseTestInterpreter

class TestMBString(BaseTestInterpreter):
    def test_mb_strlen(self):
        output = self.run(r'''
        echo mb_strlen('abc', 'utf-8');
        echo mb_strlen("a\x00bc", 'utf8');
        echo mb_strlen("a\xc4\x82bc", 'utf-8');
        echo mb_strlen("a\x84\x82bc", 'utf8');     // invalid
        echo mb_strlen("a\xc4bc", 'utf-8');        // invalid
        echo mb_strlen("a\xe7\x00\x00c", 'utf8');
        echo mb_strlen("a\xf2\x00\x00\x00c", 'utf-8');
        echo mb_strlen("a\xf2\xf3\xf4\xf5c", 'utf-8');   // invalid
        ''')
        assert [self.space.int_w(s) for s in output] == [
            3, 4, 4, 5, 3, 3, 3, 3]
