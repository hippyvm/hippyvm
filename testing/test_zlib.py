

from testing.test_interpreter import BaseTestInterpreter


class TestArray(BaseTestInterpreter):

    def test_inflate_deflate(self):
        output = self.run('''
        $in = "HippyVM";
        $out = gzinflate(gzdeflate($in));
        echo $out;

        ''')
        space = self.space
        assert space.str_w(output[0]) == "HippyVM"

    def test_gzencode_gzdecode(self):
        output = self.run('''
        $in = "HippyVM";
        $out = gzdecode(gzencode($in));
        echo $out;

        ''')
        space = self.space
        assert space.str_w(output[0]) == "HippyVM"

    def test_gzcompress_gzuncompress(self):
        output = self.run('''
        $in = "HippyVM";
        $out = gzuncompress(gzcompress($in));
        echo $out;

        ''')
        space = self.space
        assert space.str_w(output[0]) == "HippyVM"
