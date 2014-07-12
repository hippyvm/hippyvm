import py, sys
from rpython.rlib.rfloat import INFINITY, NAN, isnan

from testing.test_interpreter import BaseTestInterpreter


def doset(space, w_array, w_index, w_newvalue):
    w_res, w_new2 = w_array.setitem2_maybe_inplace(space, w_index, w_newvalue)
    assert w_new2 is w_newvalue
    assert w_res is w_array    # worked in-place

def doset_not_inplace(space, w_array, w_index, w_newvalue):
    w_res, w_new2 = w_array.setitem2_maybe_inplace(space, w_index, w_newvalue)
    assert w_new2 is w_newvalue
    assert w_res is not w_array    # did not work in-place
    return w_res

def dounset(space, w_array, w_index):
    w_result = w_array._unsetitem(space, w_index)
    assert w_result is w_array    # worked in-place

def dounset_not_inplace(space, w_array, w_index):
    w_result = w_array._unsetitem(space, w_index)
    assert w_result is not w_array    # did not work in-place
    return w_result

def doappend(space, w_array, w_newvalue):
    w_new2 = w_array.appenditem_inplace(space, w_newvalue)
    assert w_new2 is w_newvalue


class TestArrayObject(BaseTestInterpreter):

    def test_is_true(self):
        space = self.space
        w_array = space.new_array_from_list([])
        assert space.is_true(w_array) is False
        w_array = space.new_array_from_list([space.newint(0)])
        assert space.is_true(w_array) is True

    def test_getitem(self):
        space = self.space
        w_array = space.new_array_from_list([space.newint(42)])
        w_item = space.getitem(w_array, space.newint(0))
        assert space.is_w(w_item, space.newint(42))
        assert w_array.as_dict() == {"0": w_item}

    def test_getitem_hash(self):
        space = self.space
        w_array = space.new_array_from_dict({"foo": space.newint(42),
                                             "-84": space.newint(43)})
        w_item = space.getitem(w_array, space.newstr("foo"))
        assert space.is_w(w_item, space.newint(42))
        w_item = space.getitem(w_array, space.newint(-84))
        assert space.is_w(w_item, space.newint(43))

    def test_setitem(self):
        space = self.space
        w_array = space.new_array_from_list([])
        w_item = space.newstr("bok")
        doset(space, w_array, space.newint(0), w_item)
        assert w_array.as_dict() == {"0": w_item}
        w_item2 = space.newstr("bok2")
        doset(space, w_array, space.newint(0), w_item2)
        assert w_array.as_dict() == {"0": w_item2}
        w_item3 = space.newstr("bok3")
        doset(space, w_array, space.newint(1), w_item3)
        assert w_array.as_dict() == {"0": w_item2, "1": w_item3}

    def test_setitem_hash(self):
        space = self.space
        w_array = space.new_array_from_dict({})
        w_item = space.newstr("bok")
        doset(space, w_array, space.newint(0), w_item)
        assert w_array.as_dict() == {"0": w_item}
        w_item2 = space.newstr("bok2")
        doset(space, w_array, space.newstr("0"), w_item2)
        assert w_array.as_dict() == {"0": w_item2}
        w_item3 = space.newstr("bok3")
        doset(space, w_array, space.newstr("aAa"), w_item3)
        assert w_array.as_dict() == {"0": w_item2, "aAa": w_item3}

    def test_getitem_str(self):
        space = self.space
        w_array = space.new_array_from_list([space.newint(42)])
        w_item = space.getitem(w_array, space.newstr("0"))
        assert space.is_w(w_item, space.newint(42))
        w_item = space.getitem(w_array, space.newstr(""))
        assert w_item is space.w_Null
        w_item = space.getitem(w_array, space.newstr("00"))
        assert w_item is space.w_Null
        w_item = space.getitem(w_array, space.newstr("foo"))
        assert w_item is space.w_Null
        w_item = space.getitem(w_array, space.newstr(str(1 << 128)))
        assert w_item is space.w_Null

    def test_list2hash_out_of_bound(self):
        space = self.space
        w_x = space.newstr("x")
        w_y = space.newstr("y")
        w_array = space.new_array_from_list([w_x])
        w_array = doset_not_inplace(space, w_array, space.newint(100), w_y)
        assert w_array.as_dict() == {"0": w_x, "100": w_y}

    def test_list2hash_str(self):
        space = self.space
        w_x = space.newstr("x")
        w_y = space.newstr("y")
        w_array = space.new_array_from_list([w_x])
        w_array = doset_not_inplace(space, w_array, space.newstr("z"), w_y)
        assert w_array.as_dict() == {"0": w_x, "z": w_y}
        assert w_array._has_string_keys

    def test_setitem_numeric_str(self):
        space = self.space
        w_x = space.newstr("x")
        w_y = space.newstr("y")
        w_array = space.new_array_from_list([w_x])
        doset(space, w_array, space.newstr("0"), w_y)
        assert w_array.as_dict() == {"0": w_y}
        assert not w_array._has_string_keys

    def test_unsetitem(self):
        space = self.space
        for w_0, w_2 in [(space.newint(0), space.newint(2)),
                         (space.newstr("0"), space.newstr("2"))]:
            w_x = space.newstr("x")
            w_y = space.newstr("y")
            w_z = space.newstr("z")
            w_array = space.new_array_from_list([w_x, w_y, w_z])
            dounset(space, w_array, w_2)
            assert w_array.as_dict() == {"0": w_x, "1": w_y}
            assert not w_array._has_string_keys
            dounset(space, w_array, w_2)
            assert w_array.as_dict() == {"0": w_x, "1": w_y}
            assert not w_array._has_string_keys
            w_array = dounset_not_inplace(space, w_array, w_0)
            assert w_array.as_dict() == {"1": w_y}
            assert w_array._has_string_keys   # for now

    def test_unsetitem_hash(self):
        space = self.space
        w_x = space.newstr("x")
        w_y = space.newstr("y")
        w_array = space.new_array_from_dict({"foo": w_x, "42": w_y})
        dounset(space, w_array, space.newint(42))
        assert w_array.as_dict() == {"foo": w_x}
        dounset(space, w_array, space.newstr("bar"))
        assert w_array.as_dict() == {"foo": w_x}
        dounset(space, w_array, space.newstr("foo"))
        assert w_array.as_dict() == {}

    def test_append_item(self):
        space = self.space
        w_x = space.newstr("x")
        w_y = space.newstr("y")
        w_int = space.newint(330)
        w_array = space.new_array_from_list([w_x])
        doappend(space, w_array, w_x)
        doappend(space, w_array, w_x)
        w_array = doset_not_inplace(space, w_array, space.newint(99), w_y)
        doappend(space, w_array, w_y)
        assert w_array.as_dict() == {"0": w_x,
                                     "1": w_x,
                                     "2": w_x,
                                     "99": w_y,
                                     "100": w_y}
        doappend(space, w_array, w_y)
        assert w_array.as_dict() == {"0": w_x,
                                     "1": w_x,
                                     "2": w_x,
                                     "99": w_y,
                                     "100": w_y,
                                     "101": w_y}
        dounset(space, w_array, space.newint(101))
        assert w_array.as_dict() == {"0": w_x,
                                     "1": w_x,
                                     "2": w_x,
                                     "99": w_y,
                                     "100": w_y}
        doappend(space, w_array, w_y)
        assert w_array.as_dict() == {"0": w_x,
                                     "1": w_x,
                                     "2": w_x,
                                     "99": w_y,
                                     "100": w_y,
                                     "102": w_y}
        doset(space, w_array, space.newstr("255"), w_y)
        dounset(space, w_array, space.newint(255))
        assert w_array.as_dict() == {"0": w_x,
                                     "1": w_x,
                                     "2": w_x,
                                     "99": w_y,
                                     "100": w_y,
                                     "102": w_y}
        doappend(space, w_array, w_y)
        assert w_array.as_dict() == {"0": w_x,
                                     "1": w_x,
                                     "2": w_x,
                                     "99": w_y,
                                     "100": w_y,
                                     "102": w_y,
                                     '256': w_y}
        assert w_array.as_dict() == {"0": w_x,
                                     "1": w_x,
                                     "2": w_x,
                                     "99": w_y,
                                     "100": w_y,
                                     "102": w_y,
                                     '256': w_y}
        doset(space, w_array, space.newstr("monday"), w_y)
        doappend(space, w_array, w_y)
        assert w_array.as_dict() == {"0": w_x, "1": w_x, "2": w_x, "99": w_y,
                                     "100": w_y, "102": w_y, '256': w_y,
                                     "monday": w_y, '257': w_y}

        w_array = space.new_array_from_dict({"one": w_x,
                                             "-84": w_int})
        assert w_array.as_dict() == {'-84': w_int, 'one': w_x}
        doappend(space, w_array, w_x)
        assert w_array.as_dict() == {'-84': w_int, '0': w_x, 'one': w_x}
        doappend(space, w_array, w_x)
        assert w_array.as_dict() == {'-84': w_int,
                                     '0': w_x,
                                     'one': w_x,
                                     '1': w_x}
        doset(space, w_array, space.newint(100), w_y)
        assert w_array.as_dict() == {'-84': w_int,
                                     '0': w_x,
                                     'one': w_x,
                                     '1': w_x,
                                     '100': w_y}
        dounset(space, w_array, space.newint(100))
        doappend(space, w_array, w_x)
        assert w_array.as_dict() == {'-84': w_int,
                                     '0': w_x,
                                     'one': w_x,
                                     '1': w_x,
                                     '101': w_x}

        doset(space, w_array, space.newstr("255"), w_y)
        dounset(space, w_array, space.newint(255))
        doappend(space, w_array, w_x)
        assert w_array.as_dict() == {'-84': w_int,
                                     '0': w_x,
                                     'one': w_x,
                                     '1': w_x,
                                     '101': w_x,
                                     '256': w_x}
        doset(space, w_array, space.newstr("monday"), w_y)
        doappend(space, w_array, w_y)
        assert w_array.as_dict() == {'-84': w_int, '0': w_x, 'one': w_x,
                                     '1': w_x, '101': w_x, '256': w_x,
                                     "monday": w_y, '257': w_y}

    @py.test.mark.xfail(
        "not config.option.runappdirect and sys.maxint > 2**32",
        reason="parsing of floats doesn't get a 1-1 exact result")
    def test_index_overflow(self):
        def check(inputfloat, outputint):
            if isnan(inputfloat):
                inputfloat = 'NAN'
            elif inputfloat == INFINITY:
                inputfloat = 'INF'
            elif inputfloat == -INFINITY:
                inputfloat = '-INF'
            else:
                inputfloat = repr(inputfloat)
            output = self.run("""
                $arr1 = array(%d=>4);
                echo $arr1[%s];
            """ % (outputint, inputfloat))
            assert self.space.is_w(output[0], self.space.newint(4))

        check(123.95, 123)
        check(-123.95, -123)
        check(2147483647.1, 2147483647)
        check(-1234567898765432123456789.0, 0)
        check(1234567898765432123456789.0, 0)
        check(INFINITY, 0)
        check(-INFINITY, 0)
        check(NAN, -sys.maxint-1)
        check(-9.223372036855e+18, 0)
        check(9.223372036855e+18, 0)
        check(9.223372036854767e+18, -9216)
        check(9.223372036854766e+18, -10240)
        check(9.223372036854786e+18, 0)
        check(9.214148664817921e+18, 1511828480)

    def test_reference_update_does_not_change_array(self):
        space = self.space
        w_array = space.new_array_from_list([])
        w_itemref = space.empty_ref()
        w_new = w_array._setitem_ref(space, space.newint(0), w_itemref)
        assert w_new is w_array    # worked in-place
        doset(space, w_array, space.newint(0), space.newint(42))
        assert space.int_w(w_itemref.deref_temp()) == 42
        #
        w_new = w_array._setitem_ref(space, space.newstr('XY'), w_itemref)
        assert w_new is not w_array   # did not work in-place
        w_array = w_new
        doset(space, w_array, space.newstr('XY'), space.newint(42))
        assert space.int_w(w_itemref.deref_temp()) == 42

    def test_setitem_appenditem(self):
        space = self.space
        w_array = space.new_array_from_list([])
        w_item = space.newstr("bok")
        doset(space, w_array, space.newint(0), w_item)
        assert w_array.as_dict() == {"0": w_item}
        w_item2 = space.newstr("bok2")
        doappend(space, w_array, w_item2)
        assert w_array.as_dict() == {"0": w_item, "1": w_item2}

    def test_setitem_negative_integer_append(self):
        space = self.space
        w_array = space.new_array_from_list([])
        w_item = space.newstr("bok")
        w_array = doset_not_inplace(space, w_array, space.newint(-5), w_item)
        assert w_array.as_dict() == {"-5": w_item}
        w_item2 = space.newstr("bok2")
        doappend(space, w_array, w_item2)
        assert w_array.as_dict() == {"-5": w_item, "0": w_item2}
