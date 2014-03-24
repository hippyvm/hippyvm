
from hippy.objspace import getspace
from hippy.phpcompiler import compile_php
from hippy.bytecode import unserialize
from testing.test_interpreter import MockInterpreter

class TestBytecode(object):
    def test_basic_serialize(self):
        source = "<? $a = 3; var_dump($a);?>"
        space = getspace()
        bc = compile_php('<input>', source, space)
        dump = bc.serialize()
        interp = MockInterpreter(space)
        bc2 = unserialize(dump, interp)
        assert bc.dump() == bc2.dump()
        assert space.int_w(bc2.consts[0]) == 3
        assert bc2.name == bc.name
        assert bc2.filename == bc.filename
        assert bc2.startlineno == bc.startlineno
        assert bc2.sourcelines == bc.sourcelines
        assert bc.names == bc2.names
        assert bc.varnames == bc2.varnames
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
        dump = bc.serialize()
        interp = MockInterpreter(space)
        bc2 = unserialize(dump, interp)
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
        dump = bc.serialize()
        interp = MockInterpreter(space)
        bc2 = unserialize(dump, interp)
        interp.run_main(space, bc2)
        assert space.int_w(interp.output[0]) == 3
        
