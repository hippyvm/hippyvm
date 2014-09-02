
from hippy.mapdict import Terminator

class TestMapdictDirect(object):
    def test_simple(self):
        t = Terminator()
        assert t.lookup("name") is None
        new_attr = t.add_attribute("name")
        a1 = new_attr.lookup("name")
        assert a1 is new_attr
        a2 = t.add_attribute("name")
        assert a2 is a1
        a3 = a1.add_attribute("name2")
        assert a3.lookup("name") is a2
        assert a3.lookup("name2") is a3
        assert a3.lookup("xyz") is None
        assert a3.index == 1
        assert a2.index == 0

    def test_getallkeys(self):
        t = Terminator()
        a = t.add_attribute("a")
        a = a.add_attribute("b")
        a = a.add_attribute("c")
        assert a.get_all_keys() == ["a", "b", "c"]

    def test_delattr(self):
        t = Terminator()
        a = t.add_attribute("a")
        a1 = a.add_attribute("b")
        a2 = a1.add_attribute("c")
        assert a2.lookup("c").index == 2
        a3, _ = a2.del_attribute("b")
        assert a3.lookup("b") is None
        assert a3.lookup("a").index == 0
        assert a3.lookup("c").index == 1

    def test_delattr_2(self):
        t = Terminator()
        a = t.add_attribute("a")
        a1 = a.add_attribute("b")
        a2 = a1.add_attribute("c")
        assert a2.lookup("c").index == 2
        a3, _ = a2.del_attribute("a")
        assert a3.lookup("a") is None
        assert a3.lookup("b").index == 0
        assert a3.lookup("c").index == 1
