

from testing.test_interpreter import BaseTestInterpreter


class TestArray(BaseTestInterpreter):
    def test_bzip2(self):
        output = self.run('''
        $in = "HippyVM";
        $out = bzdecompress(bzcompress($in));
        echo $out;

        ''')
        space = self.space
        assert space.str_w(output[0]) == "HippyVM"
