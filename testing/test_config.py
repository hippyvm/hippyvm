
from hippy.config import load_ini
from hippy.constants import CONSTS
from hippy.objspace import ObjSpace
from hippy.interpreter import Interpreter

class TestConfig(object):
    def get_conf(self, input):
        space = ObjSpace()
        interp = Interpreter(space)
        self.space = space
        load_ini(interp, input)
        return interp.config

    def test_read_init(self):
        conf = self.get_conf("precision=18\n")
        assert self.space.int_w(conf.get_ini_w('precision')) == 18

    def test_const_reference(self):
        conf = self.get_conf("error_reporting = E_ALL")
        E_ALL = CONSTS['Core']['E_ALL']
        assert self.space.int_w(conf.ini['error_reporting']) == E_ALL

    def test_const_or(self):
        conf = self.get_conf("error_reporting = E_USER_ERROR | E_CORE_WARNING")
        exp = CONSTS['Core']['E_USER_ERROR'] | CONSTS['Core']['E_CORE_WARNING']
        assert self.space.int_w(conf.ini['error_reporting']) == exp

    def test_const_and(self):
        conf = self.get_conf("error_reporting = E_USER_ERROR & E_CORE_WARNING")
        exp = CONSTS['Core']['E_USER_ERROR'] & CONSTS['Core']['E_CORE_WARNING']
        assert self.space.int_w(conf.ini['error_reporting']) == exp

    def test_const_invert(self):
        conf = self.get_conf("error_reporting = E_ALL & ~E_CORE_WARNING")
        exp = CONSTS['Core']['E_ALL'] & ~CONSTS['Core']['E_CORE_WARNING']
        assert self.space.int_w(conf.ini['error_reporting']) == exp

    def test_timezone(self):
        conf = self.get_conf("date.timezone=Europe/Amsterdam\n")
        assert self.space.str_w(conf.ini['date.timezone']) == "Europe/Amsterdam"

    def test_memory_limit(self):
        conf = self.get_conf("memory_limit=128M")
        assert self.space.str_w(conf.ini['memory_limit']) == "128M"

    def test_error_reporting(self):
        conf = self.get_conf("error_reporting = E_ALL & ~E_STRICT & ~E_WARNING")
        E_ALL = CONSTS['Core']['E_ALL']
        E_STRICT = CONSTS['Core']['E_STRICT']
        E_WARNING = CONSTS['Core']['E_WARNING']
        assert self.space.int_w(conf.ini['error_reporting']) == E_ALL & ~E_STRICT & ~E_WARNING
