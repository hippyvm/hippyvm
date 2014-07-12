import tempfile
from testing.test_interpreter import BaseTestInterpreter


class TestDir(BaseTestInterpreter):

    def test_dir_create(self):
        output = self.run("""
            $d = dir('/tmp/');
            echo $d->path;
        """)

        assert self.space.str_w(output.pop(0)) == '/tmp/'

    def test_dir_incorrect_param(self):
        with self.warnings() as w:
            self.run("""
                dir(123);
            """)

        assert w[0] == \
            "Warning: dir(123): failed to open dir: No such file or directory"

    def test_dir_success(self):
        tmpdir = tempfile.mkdtemp()
        output = self.run("""
            $d = dir("%s");
            echo $d->path;
        """ % tmpdir)

        assert self.space.str_w(output.pop(0)) == tmpdir

    def test_dir_NULL(self):
        with self.warnings() as w:
            output = self.run("""
                $d = dir(NULL);
                echo $d;
            """)

        assert output[0] == self.space.w_False
        assert w == []

    def test_dir_null(self):
        with self.warnings() as w:
            output = self.run("""
                echo dir(null);
            """)

        assert output[0] == self.space.w_False
        assert w == []
