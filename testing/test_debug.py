from hippy.objspace import ObjSpace
from hippy.debug import make_space, builtin_impl

def test_make_space():
    space = make_space()
    assert isinstance(space, ObjSpace)
    assert space.ec.interpreter is not None

def test_builtin_impl():
    strlen = builtin_impl('strlen')
    assert strlen.func_name == 'strlen'
