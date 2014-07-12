
import py, tempfile
from hippy.objspace import getspace
from hippy.phpcompiler import compile_php
from hippy.bytecode import unserialize
from hippy.bytecode_cache import BytecodeCache
from hippy.interpreter import get_printable_location
from testing.test_interpreter import MockInterpreter, BaseTestInterpreter


class TestBytecode(object):
    def test_basic_serialize(self):
        source = "<? $a = 3; var_dump($a);?>"
        space = getspace()
        bc = compile_php('<input>', source, space)
        dump = bc.serialize(space)
        bc2 = unserialize(dump, space)
        assert bc.dump() == bc2.dump()
        assert space.int_w(bc2.consts[0]) == 3
        assert bc2.name == bc.name
        assert bc2.filename == bc.filename
        assert bc2.startlineno == bc.startlineno
        assert bc2.sourcelines == bc.sourcelines
        assert bc.names == bc2.names
        assert bc.varnames == bc2.varnames
        interp = MockInterpreter(space)
        interp.run_main(space, bc2)
        assert interp.output[0] == 'int(3)\n'

    def test_serialize_with_calls(self):
        source = """<?
        function f($a) {
            return $a + 4;
        }
        echo f(3);
        ?>"""
        space = getspace()
        bc = compile_php('<input>', source, space)
        dump = bc.serialize(space)
        bc2 = unserialize(dump, space)
        interp = MockInterpreter(space)
        interp.run_main(space, bc2)
        assert space.int_w(interp.output[0]) == 3 + 4

    def test_serialize_with_classes(self):
        source = """<?
        class X {
            function __construct() {
               $this->x = 3;
            }
        }
        $x = new X();
        echo $x->x;
        ?>"""
        space = getspace()
        bc = compile_php('<input>', source, space)
        dump = bc.serialize(space)
        bc2 = unserialize(dump, space)
        interp = MockInterpreter(space)
        interp.run_main(space, bc2)
        assert space.int_w(interp.output[0]) == 3

    def test_serialize_array_constants(self):
        source = """<?
        $a = array("a", "b");
        $b = array("a"=>"b");
        echo $a[1];
        echo $b["a"];
        ?>"""
        space = getspace()
        bc = compile_php('<input>', source, space)
        dump = bc.serialize(space)
        bc2 = unserialize(dump, space)
        interp = MockInterpreter(space)
        interp.run_main(space, bc2)
        assert space.str_w(interp.output[0]) == "b"
        assert space.str_w(interp.output[1]) == "b"

class TestBytecodeCache(BaseTestInterpreter):
    def test_caching_works(self):
        tmpdir = py.path.local(tempfile.mkdtemp())
        f = tmpdir.join('x.php')
        f.write("""<? $a = 3; ?>""")
        output = self.run("""
        include "%s";
        echo $a;
        """ % f)
        bc1 = self.space.bytecode_cache.cached_files[str(f)][0]
        assert self.space.int_w(output[0]) == 3
        output = self.run("""
        include "%s";
        echo $a;
        """ % f)
        bc2 = self.interp.cached_files[str(f)]
        assert bc2 is bc1

    def test_tstamp_invalidation(self):
        tmpdir = py.path.local(tempfile.mkdtemp())
        f = tmpdir.join('x.php')
        f.write("""<? $a = 3; ?>""")
        self.space.bytecode_cache = BytecodeCache(0)
        output = self.run("""
        include "%s";
        echo $a;
        """ % f)
        bc1 = self.space.bytecode_cache.cached_files[str(f)][0]
        f.write("""<? $a = 4; ?>""")
        assert self.space.int_w(output[0]) == 3
        output = self.run("""
        include "%s";
        echo $a;
        """ % f)
        assert self.space.int_w(output[0]) == 4
        bc2 = self.interp.cached_files[str(f)]
        assert bc2 is not bc1

    def test_get_printable_location(self):
        source = "<? $a = 3; ?>"
        space = getspace()
        bc = compile_php('<input>', source, space)
        assert get_printable_location(0, bc) == "<main> 1 VAR_PTR"
        # it may be called with pc = len(bc.code) during jitting
        assert get_printable_location(len(bc.code), bc) == "<main> END ?"
