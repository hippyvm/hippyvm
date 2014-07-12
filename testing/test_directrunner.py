
from hippy.objspace import ObjSpace
from hippy.objects.instanceobject import W_InstanceObject

from testing.directrunner import source_replace, run_source, run_php_source

def test_source_replace():
    res = source_replace('''
    echo 1;
    echo "echo"; echo 5, 2;
    123;
''')
    assert res == '''<?php

    var_dump(1);
    var_dump("echo"); var_dump(5, 2);
    123;
'''


def test_source_run():
    space = ObjSpace()
    output = run_source(space, '''
    echo 1;
    ''')
    assert len(output) == 1
    assert space.int_w(output[0]) == 1


def test_parse_array_output():
    space = ObjSpace()
    output = run_source(space, '''
    $a = array(1, 2, 3);
    echo $a;
    $a = array("c" => 2);
    echo $a;
    ''')
    assert len(output) == 2
    assert space.arraylen(output[0]) == 3
    assert space.arraylen(output[1]) == 1
    assert space.int_w(space.getitem(output[0], space.wrap(2))) == 3
    assert space.int_w(space.getitem(output[1], space.newstr('c'))) == 2


def test_parse_str():
    space = ObjSpace()
    output = run_source(space, '''
    echo "dupa";
    ''')
    assert space.str_w(output[0]) == 'dupa'


def test_parse_misc():
    space = ObjSpace()
    output = run_source(space, '''
    echo NULL, 3.5, TRUE;
    ''')
    assert output[0] is space.w_Null
    assert space.float_w(output[1]) == 3.5
    assert space.is_true(output[2])


def test_parse_builtin_instance():
    space = ObjSpace()
    output = run_source(space, '''
    $a = new stdClass;
    echo $a;
    ''')
    result, = output
    assert isinstance(result, W_InstanceObject)


def test_run_php_source():
    stdout = run_php_source("<?php echo 'hello' ?>_world")
    assert stdout == 'hello_world'
