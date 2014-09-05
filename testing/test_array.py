# -*- coding: utf-8 -*-
import py
from hippy.objects.arrayiter import RDictArrayIteratorRef
from hippy.objects.intobject import W_IntObject as W_Int
from hippy.objects.strobject import W_ConstStringObject as W_Str
from hippy.objects.reference import W_Reference
from hippy.objspace import ObjSpace
from hippy.interpreter import Interpreter
from testing.test_interpreter import BaseTestInterpreter


def test_iter_ref():
    space = ObjSpace()
    w_arr = space.new_array_from_pairs([(W_Int(1), W_Int(1)),
                                        (W_Str("x"), W_Str("x")),
                                        (W_Int(2), W_Str("2"))])
    r_arr = W_Reference(w_arr)
    it = w_arr.create_iter_ref(space, r_arr)
    assert isinstance(it, RDictArrayIteratorRef)
    w_k, w_v = it.next_item(space)
    assert (w_k, w_v.deref()) == (W_Int(1), W_Int(1))
    w_k, w_v = it.next_item(space)
    assert (w_k, w_v.deref()) == (W_Str('x'), W_Str('x'))
    w_k, w_v = it.next_item(space)
    assert (w_k, w_v.deref()) == (W_Int(2), W_Str('2'))
    assert it.finished

class TestArrayDirect(object):
    def create_array_strats(self, space):
        # int, float, mix, empty, hash, copy
        # XXX for now we don't have all of them any more, so some of
        # XXX them are identical.
        int_arr = space.new_array_from_list([space.wrap(1), space.wrap(2)])
        return (int_arr,
                space.new_array_from_list([space.wrap(1.2), space.wrap(2.2)]),
                space.new_array_from_list([space.wrap(1.2),
                                           space.newstr("x")]),
                space.new_array_from_list([]),
                space.new_array_from_pairs([
                    (space.newstr("xyz"), space.wrap(1)),
                    (space.newstr("a"), space.wrap(2)),
                    (space.newstr("b"), space.wrap(3)),
                    (space.newstr("c"), space.wrap(4))]),
                int_arr)  # .copy(space))

    def test_value_iterators(self):
        space = ObjSpace()
        interp = Interpreter(space)
        int_arr, float_arr, mix_arr, empty, hash, cp_arr = \
            self.create_array_strats(space)
        w_iter = int_arr.create_iter(space)
        assert space.int_w(w_iter.next(space)) == 1
        assert space.int_w(w_iter.next(space)) == 2
        assert w_iter.done()
        w_iter = float_arr.create_iter(space)
        assert space.float_w(w_iter.next(space)) == 1.2
        assert not w_iter.done()
        assert space.float_w(w_iter.next(space)) == 2.2
        assert w_iter.done()
        w_iter = mix_arr.create_iter(space)
        assert space.float_w(w_iter.next(space)) == 1.2
        assert space.str_w(w_iter.next(space)) == "x"
        assert w_iter.done()
        assert empty.create_iter(space).done()
        w_iter = hash.create_iter(space)
        assert space.int_w(w_iter.next(space)) == 1
        assert space.int_w(w_iter.next(space)) == 2
        assert space.int_w(w_iter.next(space)) == 3
        assert space.int_w(w_iter.next(space)) == 4
        assert w_iter.done()
        w_iter = cp_arr.create_iter(space)
        assert space.int_w(w_iter.next(space)) == 1
        assert space.int_w(w_iter.next(space)) == 2
        assert w_iter.done()

    def test_item_iterators(self):
        space = ObjSpace()
        interp = Interpreter(space)
        unpack = self.unpack
        int_arr, float_arr, mix_arr, empty, hash, cp_arr = \
            self.create_array_strats(space)
        w_iter = int_arr.create_iter(space)
        assert unpack(space, w_iter.next_item(space)) == [0, 1]
        assert not w_iter.done()
        assert unpack(space, w_iter.next_item(space)) == [1, 2]
        assert w_iter.done()
        w_iter = float_arr.create_iter(space)
        assert unpack(space, w_iter.next_item(space)) == [0, 1.2]
        assert unpack(space, w_iter.next_item(space)) == [1, 2.2]
        assert w_iter.done()
        w_iter = mix_arr.create_iter(space)
        assert unpack(space, w_iter.next_item(space)) == [0, 1.2]
        assert unpack(space, w_iter.next_item(space)) == [1, "x"]
        assert w_iter.done()
        assert empty.create_iter(space).done()
        w_iter = hash.create_iter(space)
        assert unpack(space, w_iter.next_item(space)) == ['xyz', 1]
        assert unpack(space, w_iter.next_item(space)) == ['a', 2]
        assert unpack(space, w_iter.next_item(space)) == ['b', 3]
        assert unpack(space, w_iter.next_item(space)) == ['c', 4]
        assert w_iter.done()
        w_iter = cp_arr.create_iter(space)
        assert unpack(space, w_iter.next_item(space)) == [0, 1]
        assert unpack(space, w_iter.next_item(space)) == [1, 2]
        assert w_iter.done()

    def test_isset_index(self):
        space = ObjSpace()
        int_arr, float_arr, mix_arr, empty, hash, cp_arr = \
            self.create_array_strats(space)
        assert int_arr.isset_index(space, space.wrap(0))
        assert not int_arr.isset_index(space, space.wrap(13))
        assert float_arr.isset_index(space, space.wrap(0))
        assert not float_arr.isset_index(space, space.wrap(13))
        assert mix_arr.isset_index(space, space.wrap(0))
        assert not mix_arr.isset_index(space, space.wrap(13))
        assert not empty.isset_index(space, space.wrap(0))
        assert hash.isset_index(space, space.newstr("a"))
        assert hash.isset_index(space, space.newstr("xyz"))
        assert not hash.isset_index(space, space.wrap(3))
        assert cp_arr.isset_index(space, space.wrap(0))
        assert not cp_arr.isset_index(space, space.wrap(13))

    def test_hashes(self):
        space = ObjSpace()
        assert space.wrap(1).hash(space) == space.newstr("1").hash(space)
        assert space.wrap(123).hash(space) == space.newstr("123").hash(space)

    def test_map(self):
        space = ObjSpace()
        w_a = space.newstr("a")
        w_b = space.newstr("b")
        w_arr = space.new_map_from_pairs([(w_a, space.wrap(0)),
                                          (w_b, space.wrap(12))])
        assert space.int_w(space.getitem(w_arr, w_a)) == 0
        w_arr = space.setitem(w_arr, w_b, space.wrap(3))
        assert space.int_w(space.getitem(w_arr, w_b)) == 3
        assert w_arr.arraylen() == 2
        assert w_arr.isset_index(space, w_b)
        assert not w_arr.isset_index(space, space.wrap(0))
        assert not w_arr.isset_index(space, space.newstr("c"))
        w_arr2 = space.setitem(w_arr, space.wrap(0), space.wrap(15))
        assert w_arr2.strategy_name == 'hash'
        assert space.int_w(space.getitem(w_arr, w_a)) == 0
        assert space.int_w(space.getitem(w_arr, w_b)) == 3
        assert space.int_w(space.getitem(w_arr2, space.wrap(0))) == 15
        w_arr = space.setitem(w_arr, space.newstr("c"), space.wrap(38))
        assert w_arr.strategy_name == 'hash'

    def test_map_iter(self):
        space = ObjSpace()
        unpack = self.unpack
        w_a = space.newstr("a")
        w_b = space.newstr("b")
        w_arr = space.new_map_from_pairs([(w_a, space.wrap(0)),
                                          (w_b, space.wrap(12))])
        w_iter = w_arr.create_iter(space)
        assert space.int_w(w_iter.next(space)) == 0
        assert space.int_w(w_iter.next(space)) == 12
        assert w_iter.done()
        w_iter = w_arr.create_iter(space)
        assert unpack(space, w_iter.next_item(space)) == ["a", 0]
        assert unpack(space, w_iter.next_item(space)) == ["b", 12]
        assert w_iter.done()

    def unpack(self, space, (w_key, w_obj)):
        if w_key.tp == space.tp_int:
            key = space.int_w(w_key)
        elif w_key.tp == space.tp_str:
            key = space.str_w(w_key)
        else:
            raise AssertionError, w_key.tp
        if w_obj.tp == space.tp_str:
            value = space.str_w(w_obj)
        elif w_obj.tp == space.tp_float:
            value = space.float_w(w_obj)
        elif w_obj.tp == space.tp_int:
            value = space.int_w(w_obj)
        else:
            raise NotImplementedError
        return [key, value]


class TestArray(BaseTestInterpreter):
    def test_array_constructor(self):
        output = self.run('''
        $a = array(1, 2, 3);
        echo $a;
        ''')
        space = self.space
        assert space.int_w(space.getitem(output[0], space.wrap(0))) == 1
        assert space.int_w(space.getitem(output[0], space.wrap(1))) == 2

    def test_array_constructor_mix(self):
        output = self.run('''
        $a = array(1, "2", 3);
        echo $a;
        ''')
        space = self.space
        assert space.int_w(space.getitem(output[0], space.wrap(0))) == 1
        assert space.str_w(space.getitem(output[0], space.wrap(1))) == "2"

    def test_array_constructor_to_hash(self):
        output = self.run('''
        $a = array(1, "a" => 5, 3, "a" => 99);
        echo $a;
        echo $a["a"];
        ''')
        space = self.space
        assert space.int_w(space.getitem(output[0], space.wrap(0))) == 1
        assert space.str_w(space.getitem(output[0], space.wrap(1))) == "3"
        assert self.space.int_w(output[1]) == 99

    def test_array_constructor_to_hash_2(self):
        output = self.run('''
        $a = array("a", "0"=>"b", "c");
        echo $a[0];
        echo $a["0"];
        echo $a["1"];
        $a = array("0" => "1", "b" => null, 3);
        echo $a[0];
        echo $a["b"];
        echo $a[1];

        ''')
        assert self.space.str_w(output[0]) == "b"
        assert self.space.str_w(output[1]) == "b"
        assert self.space.str_w(output[2]) == "c"

        assert self.space.str_w(output[3]) == "1"
        assert self.space.int_w(output[4]) == 0
        assert self.space.int_w(output[5]) == 3

    def test_array_constructor_to_hash_3(self):
        output = self.run('''
        $a = array(0 => "1", "b" => null, 3, 0.52=>33);
        echo $a[0];
        echo $a["b"];
        echo $a[1];
        ''')
        assert self.space.int_w(output[0]) == 33
        assert self.space.is_true(output[1]) is False
        assert self.space.int_w(output[2]) == 3

    def test_array_constructor_to_hash_4_set_and_get(self):
        output = self.run('''
        $arr1 = array(4, '1234567898765432123456789' => 'dd', 11.11=>'last');
        $arr1[12313.222] = '233';
        echo $arr1[12313.222];
        echo $arr1[11.11];
        echo $arr1['1234567898765432123456789'];
        echo $arr1[1234567898765432123456789];
        $arr1 = array(4, 1234567898765432123456789 => 'dd', 11.11=>'last');
        echo $arr1[0];
        echo $arr1[11];
        ''')
        assert self.space.str_w(output[0]) == '233'
        assert self.space.str_w(output[1]) == 'last'
        assert self.space.str_w(output[2]) == 'dd'
        assert self.space.int_w(output[3]) == 4
        assert self.space.str_w(output[4]) == 'dd'
        assert self.space.str_w(output[5]) == 'last'

    def test_array_empty_strat_append(self):
        output = self.run('''
        $a = array();
        echo $a[] = 3;
        $a[] = 15;
        $a[] = "xyz";
        $a[] = 5;
        echo $a[0];
        echo $a[1];
        echo $a[2];
        echo $a[3];
        ''')
        assert self.space.int_w(output[0]) == 3
        assert self.space.int_w(output[1]) == 3
        assert self.space.int_w(output[2]) == 15
        assert self.space.str_w(output[3]) == "xyz"
        assert self.space.int_w(output[4]) == 5

    def test_array_append_1(self):
        output = self.run('''
        $a = array('a', 'b', 'c');
        $a[4] = 'e';
        $a[] = 'f';
        echo $a[5];
        ''')
        assert self.space.str_w(output[0]) == 'f'

    def test_array_append_2(self):
        output = self.run('''
        $a = array('a', 'b', 'c');
        $a[10] = 'e';
        $a[8] = 'f';
        $a[] = 'g';
        echo $a[11];
        ''')
        assert self.space.str_w(output[0]) == 'g'

    def test_array_append_3(self):
        output = self.run('''
        $a = array('a'=>'b', 0=>'c');
        $a[] = 'd';
        echo $a[1];
        ''')
        assert self.space.str_w(output[0]) == 'd'

    def test_array_append_4(self):
        output = self.run('''
        $a = array_count_values(array('a'=>5));
        $a[] = 'd';
        echo $a[6];
        ''')
        assert self.space.str_w(output[0]) == 'd'

    def test_array_setitem(self):
        output = self.run('''
        $a = array(1, 2, 3);
        echo $a[1] = 15;
        echo $a[1];
        $a[0] = "xyz";
        echo $a[0];
        echo $a[1];
        ''')
        assert [self.space.int_w(output[i]) for i in [0, 1, 3]] == [15, 15, 15]
        assert self.space.str_w(output[2]) == "xyz"

    def test_array_setitem_inplace(self):
        output = self.run('''
        $a = array(1);
        $a[0] += 3;
        echo $a[0];
        ''')
        assert self.space.int_w(output[0]) == 4

    def test_copy_on_write(self):
        output = self.run('''
        $a = array(1, 2, 3);
        $b = $a;
        $a[1] = 15;
        echo $b[1];
        ''')
        assert self.space.int_w(output[0]) == 2

    def test_float_strategy(self):
        py.test.skip("no special float strategy for now")
        output = self.run('''
        $a = array();
        $a[] = 3.0;
        $b = array(1.2, 3.2);
        echo $a, $b;
        $a[1] = 1.2;
        $b[0] = 1;
        echo $a, $b;
        ''')
        [i.force_write() for i in output]
        assert [i.strategy.name for i in output] == [
            'lfloat', 'lfloat', 'lfloat', 'lobject']
        assert output[0].strategy.unerase(output[0].storage) == [3.0]
        assert output[1].strategy.unerase(output[1].storage) == [1.2, 3.2]
        assert output[2].strategy.unerase(output[2].storage) == [3.0, 1.2]
        assert self.space.int_w(
            output[3].strategy.unerase(output[3].storage)[0]) == 1

    def test_append_empty(self):
        output = self.run('''
        $a = array();
        $a[0] = "abc";
        echo $a[0];
        ''')
        assert self.space.str_w(output[0]) == 'abc'

    def test_hash_constructor(self):
        output = self.run('''
        $z = "xy";
        $z[0] = "a";
        $a = array("x" => "y", "z" => 3, $z => 5);
        echo $a["x"], $a["z"], $a["ay"];
        ''')
        assert self.space.str_w(output[0]) == "y"
        assert self.space.int_w(output[1]) == 3
        assert self.space.int_w(output[2]) == 5

    def test_int_iterator(self):
        output = self.run('''
        $a = array(1, 2, 3, 4);
        foreach($a as $x) {
           echo $x;
        }
        ''')
        assert [self.space.int_w(i) for i in output] == [1, 2, 3, 4]

    def test_modifying_while_iterating(self):
        output = self.run('''
        $a = array(1, 2);
        foreach ($a as $x) {
          $a[1] = 13;
          echo $x;
        }
        ''')
        assert [self.space.int_w(i) for i in output] == [1, 2]

    def test_modifying_while_iterating_2(self):
        output = self.run('''
        $a = array("a" => 1, "b" => 2);
        foreach ($a as $x => $y) {
          $a[1] = 13;
          echo $x;
        }
        ''')
        assert [self.space.str_w(i) for i in output] == ["a", "b"]

    def test_reference_to_arrayitem(self):
        output = self.run('''
        function f(&$a) {
          $a = 3;
        }
        $a = array(1, 2);
        f($a[1]);
        echo $a[1];
        ''')
        assert self.space.int_w(output[0]) == 3

    def test_key_value_iterator(self):
        output = self.run('''
        $a = array("a" => 3, "b" => 4);
        foreach ($a as $x => $y) {
           echo $x, $y;
        }
        ''')
        assert self.space.str_w(output[0]) == "a"
        assert self.space.int_w(output[1]) == 3
        assert self.space.str_w(output[2]) == "b"
        assert self.space.int_w(output[3]) == 4

    def test_cast(self):
        output = self.run('''
        $a = (array)3;
        $b = (array)$a;
        echo $a[0], $b[0];
        ''')
        assert [self.space.int_w(i) for i in output] == [3, 3]

    def test_promotion_to_hash(self):
        output = self.run('''
        $a = array(1);
        $a["xyz"] = 3;
        echo $a["xyz"], $a[0];
        ''')
        assert [self.space.int_w(i) for i in output] == [3, 1]

    def test_copy_of_a_copy(self):
        output = self.run('''
        $a = array(1, 2, 3);
        $b = $a;
        $c = $b;
        $c[0] = 3;
        echo $c[0], $a[0], $b[0];
        ''')
        assert [self.space.int_w(i) for i in output] == [3, 1, 1]

    def test_copy_of_a_copy_2(self):
        output = self.run('''
        $a = array(1, 2, 3);
        $b = $a;
        $c = $b;
        $b[0] = 3;
        echo $c[0], $a[0], $b[0];
        ''')
        assert [self.space.int_w(i) for i in output] == [1, 1, 3]

    def test_hash_copy(self):
        output = self.run('''
        $a = array(1 => 2, 3 => 4);
        $a["x"] = 3;
        echo $a["x"];
        ''')
        assert self.space.int_w(output[0]) == 3

    def test_store_makes_copy(self):
        output = self.run('''
        $a = "x";
        $b = array();
        $b["y"] = $a;
        $b["y"][0] = "c";
        echo $a;
        ''')
        assert self.space.str_w(output[0]) == "x"

    def test_array_cast_null(self):
        output = self.run('''
        $a = (array)NULL;
        echo count($a);
        ''')
        assert self.space.int_w(output[0]) == 0

    def test_hashes_equal(self):
        output = self.run('''
        $a = array(123 => "xyz");
        echo $a["123"];
        ''')
        assert self.space.str_w(output[0]) == "xyz"

    def test_hashes_creation(self):
        output = self.run('''
        $a = array(123 => "xyz", "marry", 199=> "abc", "had");
        echo $a["123"];
        echo $a["124"];
        echo $a["200"];

        ''')
        assert self.space.str_w(output[0]) == "xyz"
        assert self.space.str_w(output[1]) == "marry"
        assert self.space.str_w(output[2]) == "had"

    def test_hashes_creation_2(self):
        output = self.run('''
        $a = array(true => 1, false => 0, TRUE => -1);
        echo $a[1];
        echo $a[0];
        ''')
        assert self.space.int_w(output[0]) == -1
        assert self.space.int_w(output[1]) == 0

    def test_array_elem(self):
        output = self.run('''
        $x = 3;
        $y = &$x;
        $a = array();
        $a[0] = $y;
        echo $a[0];
        $x = 8;
        echo $a[0];
        ''')
        assert [self.space.int_w(i) for i in output] == [3, 3]

    def test_array_key_exists(self):
        output = self.run('''
        $a = array(0, 1, 2);
        echo array_key_exists(0, $a);
        echo array_key_exists(3, $a);
        $a = array("0" => "1", "b" => null, 3);
        echo array_key_exists("0", $a);
        echo array_key_exists("b", $a);
        echo array_key_exists(0, $a);
        echo array_key_exists(1, $a);
        echo array_key_exists("1", $a);
        ''')
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 0

        assert self.space.int_w(output[2]) == 1
        assert self.space.int_w(output[3]) == 1
        assert self.space.int_w(output[4]) == 1
        assert self.space.int_w(output[5]) == 1
        assert self.space.int_w(output[6]) == 1

    def test_array_search(self):
        output = self.run('''
        $a = array(0, 1, 2, "C", "c", "5");
        echo array_search(0, $a);
        echo array_search(2, $a);
        echo array_search("C", $a);
        echo array_search("c", $a);
        echo array_search(5, $a);
        echo array_search(5, $a, true);

        $a = array(0, "str1", "str2");
        echo array_search("str1", $a);

        $a = array(0, 3, "null"=>NULL, "ab", 1);
        echo array_search(array(), $a);

        $a = array(0, 3, "null"=>NULL, "ab", 1);
        echo array_search(NULL, $a);

        $a = array(3, "null"=>NULL, "ab", 1);
        echo array_search(NULL, $a);

        $a = array("str1", "str2");
        echo array_search("str2", $a);


        ''')
        assert self.space.int_w(output[0]) == 0
        assert self.space.int_w(output[1]) == 2
        assert self.space.int_w(output[2]) == 0
        assert self.space.int_w(output[3]) == 0
        assert self.space.int_w(output[4]) == 5
        assert self.space.int_w(output[5]) == 0

        assert self.space.int_w(output[6]) == 0
        assert self.space.str_w(output[7]) == "null"
        assert self.space.int_w(output[8]) == 0
        assert self.space.str_w(output[9]) == "null"
        assert self.space.int_w(output[10]) == 1

    def test_array_in_array(self):
        output = self.run('''
        $a = array(0, 1, 2, "C", "c", "5");
        echo in_array(0, $a);
        echo in_array(2, $a);
        echo in_array("C", $a);
        echo in_array("c", $a);
        echo in_array(5, $a);
        echo in_array(5, $a, true);
        echo in_array("Test", $a, true);
        echo in_array("Test", $a);

        ''')
        assert self.space.is_true(output[0]) is True
        assert self.space.is_true(output[1]) is True
        assert self.space.is_true(output[2]) is True
        assert self.space.is_true(output[3]) is True
        assert self.space.is_true(output[4]) is True
        assert self.space.is_true(output[5]) is False
        assert self.space.is_true(output[6]) is False
        assert self.space.is_true(output[7]) is True

    def test_array_intersect(self):
        output = self.run('''
        $arr1 = array(1, 2, "hello", 'world');
        $arr2 = array("one" => 1, "two" => 2);
        $arr3 = array(1, 2, 'hello');
        $c = array_intersect($arr1, $arr2, $arr3);
        echo count($c);
        echo $c[0];
        echo $c[1];
        ''')
        assert [self.space.int_w(s) for s in output] == [2, 1, 2]

    def test_array_intersect_variation1(self):
        output = self.run('''
        $a = array('one', 'two', 'three', 'four', 'five',
                   'six', 'seven', 'height', 'nine', 'ten');
        $b = array('four', 'one', 'height', 'five');
        $c = array_intersect($a, $b);
        echo count($c);
        echo $c[0];
        echo $c[3];
        echo $c[4];
        echo $c[7];
        ''')
        assert [self.space.str_w(s) for s in output] == ['4', 'one', 'four',
                                                         'five', 'height']

    def test_array_intersect_variation2(self):
        output = self.run('''
        $a = array_intersect(array(1,2,2),array(1,"2",3));
        $b = array_intersect(array(1,2,3),array(1,2,2));
        echo count($a);
        echo $a[0];
        echo $a[1];
        echo $a[2];
        echo count($b);
        echo $b[0];
        echo $b[1];
        echo $b[2];

        ''', ["Notice: Undefined offset: 2"])
        assert [self.space.int_w(s) for s in output] == [3, 1, 2, 2,
                                                         2, 1, 2, 0]

    def test_array_intersect_error(self):
        self.run('''
        echo array_intersect();
        ''', ["Warning: array_intersect(): at least 2 parameters "
              "are required, 0 given"])

    def test_array_intersect_error2(self):
        self.run('''
        var_dump( array_intersect("34", "3434") );
        ''', ["Warning: array_intersect(): Argument #1 is not an array"])

    def test_array_prev(self):
        output = self.run('''
        $subarray = array(9,8,7);
        end($subarray);
        $array_arg = array($subarray, 'a' => 'z');
        end($array_arg);
        echo count(prev($array_arg));
        echo prev($array_arg);
        echo prev($array_arg[0]);
        ''')
        assert [self.space.str_w(s) for s in output] == ['3', '', '8']

    def test_array_next(self):
        output = self.run('''
        $array_arg = array ('a' => 'z', array(9, 8, 7));
        echo count(next($array_arg));
        echo next($array_arg);
        echo next($array_arg[0]);
        ''')
        assert [self.space.str_w(s) for s in output] == ['3', '', '8']

    def test_array_reset(self):
        output = self.run('''
        $array = array('a', 'b', 'c');
        echo current($array);
        echo key($array);
        unset($array[0]);
        echo reset($array);''')

        assert self.space.str_w(output[0]) == "a"
        assert self.space.str_w(output[1]) == "0"
        assert self.space.str_w(output[2]) == "b"

    def test_array_pop_resets_internal_pointer(self):
        output = self.run('''
        $array = array(1, 2, 3, 4, 5, 6, 7, 8);
        echo current($array);
        echo next($array);
        echo next($array);
        array_pop($array);
        echo current($array);

        $array = array(1=>1, 2=>2, 3=>3, 4=>4, 5=>5, 6=>6, 7=>7);
        echo current($array);
        echo next($array);
        echo next($array);
        array_pop($array);
        echo current($array);

        ''')

        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 2
        assert self.space.int_w(output[2]) == 3
        assert self.space.int_w(output[3]) == 1

        assert self.space.int_w(output[4]) == 1
        assert self.space.int_w(output[5]) == 2
        assert self.space.int_w(output[6]) == 3
        assert self.space.int_w(output[7]) == 1

    def test_array_each(self):
        output = self.run('''
        $array_arg = array ('a' => 'z');
        $a = each($array_arg);
        foreach($a as $k => $v) {
            echo $k;
            echo $v;
        }
        ''')
        assert [self.space.str_w(s) for s in output] == [
            '1', 'z', 'value', 'z', '0', 'a', 'key', 'a']

    def test_empty_array_each(self):
        output = self.run('''
        $array_arg = array();
        echo (each($array_arg) === FALSE);
        ''')
        assert output[0] == self.space.w_True

    def test_array_each_2(self):
        output = self.run('''
        $array_arg = array(5, 6);
        list($x, $y) = each($array_arg);
        echo $x;
        echo $y;
        list($x, $y) = each($array_arg);
        echo $x;
        echo $y;
        echo each($array_arg) === false;
        ''')
        assert [self.space.int_w(s) for s in output] == [
            0, 5, 1, 6, 1]

    def test_array_each_reassign(self):
        py.test.skip("corner case with different behavior")
        # this occurs because the refcount of $new is two at the time
        # where we call each($new).  This forces a copy of the array,
        # and the copy's current index starts at 0 instead of being
        # copied...  But we can't do the same, because we copy more
        # often, so it would be an important change of semantics.
        output = self.run('''
        $array_arg = array(5);
        list($x, $y) = each($array_arg);
        echo $x;
        echo $y;
        echo each($array_arg);
        $new = $array_arg;
        list($x, $y) = each($new);
        echo $x;
        echo $y;

        ''')
        assert self.space.str_w(output[0]) == '0'
        assert self.space.str_w(output[1]) == '5'
        assert output[2] == self.space.w_False
        assert self.space.str_w(output[3]) == '0'
        assert self.space.str_w(output[4]) == '5'

    def test_instance_end_prev(self):
        output = self.run('''
        $a = new StdClass;
        $a->x = 11;
        $a->y = 12;
        $a->z = 13;
        echo end($a);
        echo prev($a);
        echo prev($a);
        ''')
        assert self.space.int_w(output[0]) == 13
        assert self.space.int_w(output[1]) == 12
        assert self.space.int_w(output[2]) == 11

    def test_new_returns_a_reference_but_whyyyyy(self):
        self.run('''
        echo next(new stdClass);
        ''')

    def test_array_end_warning(self):
        output = self.run('''
        $a = 42;
        echo end($a);
        ''', ["Warning: end() expects parameter 1 to be array, integer given"])
        assert self.space.is_w(output[0], self.space.w_Null)

    def test_array_pop(self):
        output = self.run('''
        $a = array(9, 8, 7);
        echo array_pop($a);
        echo array_pop($a);
        $a[] = 11;
        echo $a[1];
        $b = array(0=>2, 'a'=>5, 1=>7);
        echo array_pop($b);
        $b[] = 15;
        echo $b[1];
        echo array_pop($b);
        echo array_pop($b);
        $b[] = 16;
        echo $b[1];
        echo array_pop($b);
        echo array_pop($b);
        $b[] = 17;
        echo $b[0];
        ''')
        assert [self.space.str_w(s) for s in output] == [
            '7', '8', '11',
            '7', '15', '15', '5', '16', '16', '2', '17']

    def test_array_iterate_with_unset(self):
        output = self.run('''
        $array = array('a', 'b', 'c');
        unset($array[0]);
        echo current($array);
        $array = array('a', 'b', 'c');
        unset($array[1]);
        echo current($array);
        $array = array('a', 'b', 'c');
        next($array);
        unset($array[0]);
        echo current($array);
        $array = array('a', 'b', 'c');
        next($array);
        unset($array[1]);
        echo current($array);
        $array = array('a', 'b', 'c');
        next($array);
        unset($array[2]);
        echo current($array);
        $array = array('a', 'b', 'c');
        next($array);
        next($array);
        unset($array[1]);
        echo current($array);
        $array = array('a', 'b', 'c');
        next($array);
        next($array);
        unset($array[2]);
        echo current($array);
        $array = array('a', 'b', 'c');
        next($array);
        next($array);
        next($array);
        unset($array[2]);
        echo current($array);
        ''')
        assert [self.space.str_w(s) for s in output] == [
            'b', 'a', 'b', 'c', 'b', 'c', '', '']

    def test_compact(self):
        output = self.run('''
        $city  = "San Francisco";
        $state = "CA";
        $event = "SIGGRAPH";
        $location_vars = array("city", "state");
        $result = compact("event", "nothing_here", $location_vars);
        echo $result["event"];
        echo $result["city"];
        echo $result["state"];
        echo count($result);

        ''')
        assert [self.space.str_w(s) for s in output] == ['SIGGRAPH',
                                                         'San Francisco',
                                                         'CA', '3']

    def test_compact_2(self):
        output = self.run('''
        $city = "San Francisco";
        $state = "CA";
        function f() {
        $event = "SIGGRAPH";

        $location_vars = array("city", "state");

        $result = compact("event", "nothing_here", $location_vars);
        echo $result["event"];
        echo count($result);

        }
        f();
        ''')
        assert [self.space.str_w(s) for s in output] == ['SIGGRAPH', '1']

    def test_array_merge(self):
        output = self.run('''
        $a = array("xyz" => 1);
        $b = array("a" => 2);
        $c = array_merge($a, $b);
        echo $c["a"], $c["xyz"];
        $a = array(1, 2, 3);
        $b = array(4, 5, 6);
        $c = array_merge($a, $b);
        echo $c[4];
        $array1 = array("color" => "red", 2, 4);
        $array2 = array("a", "b", "color" => "green",
                        "shape" => "trapezoid", 4);
        $result = array_merge($array1, $array2);
        echo $result[4];
        echo $result[1];
        echo $result['color'];
        echo $result['shape'];
        $arr1 = array('12345678987654321234567899999999999999999999999' => 'dd');
        $arr2 = array('12345678987654321234567' => 'ddd', '35' => 'xxx');
        $v = array_merge($arr1, $arr2);
        echo $v['12345678987654321234567899999999999999999999999'];
        ''')
        assert [self.space.str_w(i) for i in output] == ['2', '1', '5',
                                                         '4', '4',
                                                         'green',
                                                         'trapezoid', 'dd']

    def test_array_diff_key(self):
        output = self.run('''
        $array1 = array('blue'  => 1, 'red'  => 2,
                        'green'  => 3, 'purple' => 4);
        $array2 = array('green' => 5, 'blue' => 6,
                        'yellow' => 7, 'cyan'   => 8);
        $a = array_diff_key($array1, $array2);
        echo $a["red"];
        echo $a["purple"];
        echo count($a);
        ''')
        assert self.space.int_w(output[0]) == 2
        assert self.space.int_w(output[1]) == 4
        assert self.space.int_w(output[2]) == 2

    def test_array_diff_key2(self):
        output = self.run('''
        $a = array_diff_key(array("a" => 1, 1 => 2, "c" =>3),
                            array("c"=>18), array(0, 1));
        echo count($a), $a["a"];
        ''')
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 1

    def test_array_diff_assoc(self):
        output = self.run('''
        $array1 = array("a" => "green", "b" => "brown", "c" => "blue", "red");
        $array2 = array("a" => "green", "yellow", "red");
        $result = array_diff_assoc($array1, $array2);
        echo $result["b"];
        echo $result["c"];
        echo $result[0];
        ''')
        assert self.space.str_w(output[0]) == "brown"
        assert self.space.str_w(output[1]) == "blue"
        assert self.space.str_w(output[2]) == "red"

    def test_array_diff_assoc_2(self):
        output = self.run('''
        $arr_default_int = array(1, 2, 3, 'a');
        $arr_string_float = array('0' => '1.00', '1.00' => '2.00',
                                  '2.00' => '3.00', 'd');
        $a = array_diff_assoc($arr_default_int, $arr_string_float);
        $b = array_diff_assoc($arr_string_float, $arr_default_int);
        foreach($a as $k => $v) {
          echo $k, $v;
        }
        foreach($b as $k => $v) {
          echo $k, $v;
        }
        ''')
        res = ["0", "1", "1", "2", "2", "3", "3", "a",
               "0", "1.00", "1.00", "2.00", "2.00", "3.00", "1", "d"]
        assert [self.space.str_w(s) for s in output] == res

    def test_array_diff_assoc_error(self):
        self.run('''
        array_diff_assoc();
        array_diff_assoc(array());
        array_diff_assoc(133, 1333);
        ''', ["Warning: array_diff_assoc(): at least 2 "
              "parameters are required, 0 given",
              "Warning: array_diff_assoc(): at least 2 "
              "parameters are required, 1 given",
              "Warning: array_diff_assoc(): Argument #1 is not an array"])

    def test_array_diff(self):
        output = self.run('''
        $array1 = array("a" => "green", "red", "blue", "red");
        $array2 = array("b" => "green", "yellow", "red");
        $result = array_diff($array1, $array2);
        echo $result[1];
        echo count($result);

        ''')
        assert self.space.str_w(output[0]) == "blue"
        assert self.space.int_w(output[1]) == 1

    def test_array_diff_ukey(self):
        output = self.run('''
        function key_compare_func($key1, $key2)
        {
           if ($key1 == $key2)
               return 0;
           else if ($key1 > $key2)
               return 1;
           else
               return -1;
         }
        $array1 = array('blue'  => 1, 'red'  => 2,
                        'green'  => 3, 'purple' => 4);
        $array2 = array('green' => 5, 'blue' => 6,
                        'yellow' => 7, 'cyan'   => 8);
        $result = array_diff_ukey($array1, $array2, 'key_compare_func');
        echo $result["red"];
        echo $result["purple"];

        echo count($result);

        ''')
        assert self.space.int_w(output[0]) == 2
        assert self.space.int_w(output[1]) == 4
        assert self.space.int_w(output[2]) == 2

    def test_array_map(self):
        output = self.run('''
        function cube($n){
          $x = $n * $n * $n;
          return $x;
        }

        $a = array('a'=>1, 2, 3, 4, 'c'=>5);
        $b = array_map("cube", $a);
        echo $b["a"];
        echo $b["c"];
        echo $b[2];
        ''')
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 125
        assert self.space.int_w(output[2]) == 64

    def test_array_change_key_case(self):
        output = self.run('''
        $a = array("a" => 1, 1 => 2, "c" =>3);
        $a = array_change_key_case($a, 1);
        echo $a['A'];
        echo $a[1];
        $a = array("A" => 1, 1 => 2, "c" =>3);
        $a = array_change_key_case($a, 0);
        echo $a['a'];
        echo $a[1];
        echo $a['c'];

        ''')
        assert self.space.str_w(output[0]) == "1"
        assert self.space.str_w(output[1]) == '2'
        assert self.space.str_w(output[2]) == "1"
        assert self.space.str_w(output[3]) == '2'
        assert self.space.str_w(output[4]) == "3"

    def test_array_slice_1(self):
        output = self.run('''
        $a = array(0, 1, 2, 3, 4, 5, 6, 7, 8, 9);
        $a = array_slice($a, 2, true);
        echo count($a);
        echo $a[0];
        ''')
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 2

    def test_array_slice_2(self):
        output = self.run('''
        $a = array(0, 1, 2, 3, 4, 5, 6, 7, 8, 9);
        $a = array_slice($a, 2);
        echo $a[0];
        $a = array(0, 1, 2, 3, 4, 5, 6, 7, 8, 9);
        $a = array_slice($a, 1, 3);
        echo $a[0];
        echo $a[1];
        $a = array(0, 1, 2, 3, 4, 5, 6, 7, 8, 9);
        $a = array_slice($a, 5, 6);
        echo $a[0];
        $a = array(0, 1, 2, 3, 4, 5, 6, 7, 8, 9);
        $a = array_slice($a, -2, 6);
        echo $a[0];
        $a = array(0, 1, 2, 3, 4, 5, 6, 7, 8, 9);
        $a = array_slice($a, -5, -2);
        echo $a[0];
        echo $a[1];
        echo $a[2];

        $a = array(0, 1, 2, 3, 4, 5, 6, 7, 8, 9);
        $a = array_slice($a, 2, true);
        echo $a[0];

        $a = array(0, 1, 2, 3, 4, 5, 6, 7, 8, 9);
        $a = array_slice($a, 1, 3, true);
        echo $a[1];
        echo $a[2];
        $a = array(0, 1, 2, 3, 4, 5, 6, 7, 8, 9);
        $a = array_slice($a, 5, 6, true);
        echo $a[5];
        $a = array(0, 1, 2, 3, 4, 5, 6, 7, 8, 9);
        $a = array_slice($a, -2, 6, true);
        echo $a[8];
        $a = array(0, 1, 2, 3, 4, 5, 6, 7, 8, 9);
        $a = array_slice($a, "-5", "-2", true);
        echo $a[5];
        echo $a[6];
        echo $a[7];

        $a = array(0, 1, 2, 3, 4, 5, 6, 7, 8, 9);
        $a = array_slice($a, -2, 0, true);

        $a = array(0, 1, 2, 3, 4, 5, 6, 7, 8, 9);
        $a = array_slice($a, -2, -3, true);
        $a = array ('one' => 1, 2 => 'two', 'three', 9 => 'nine', 'ten' => 10);
        $a = array_slice($a, -7);
        echo count($a);
        echo $a["ten"];
        $a = array_slice(range(1, 3), 0, NULL, 1);
        echo count($a);
        echo $a[2];

        ''')

        assert self.space.int_w(output[0]) == 2

        assert self.space.int_w(output[1]) == 1
        assert self.space.int_w(output[2]) == 2

        assert self.space.int_w(output[3]) == 5

        assert self.space.int_w(output[4]) == 8

        assert self.space.int_w(output[5]) == 5
        assert self.space.int_w(output[6]) == 6
        assert self.space.int_w(output[7]) == 7

        assert self.space.int_w(output[8]) == 2

        assert self.space.int_w(output[9]) == 1
        assert self.space.int_w(output[10]) == 2

        assert self.space.int_w(output[11]) == 5

        assert self.space.int_w(output[12]) == 8

        assert self.space.int_w(output[13]) == 5
        assert self.space.int_w(output[14]) == 6
        assert self.space.int_w(output[15]) == 7

        assert self.space.int_w(output[16]) == 5
        assert self.space.int_w(output[17]) == 10

        assert self.space.int_w(output[18]) == 3
        assert self.space.int_w(output[19]) == 3

    def test_array_chunk(self):
        output = self.run('''
        $a = array(0, 1, 2, 3, 4, 5, 6, 7, 8, 9);
        $a = array_chunk($a, 3);
        echo $a[0][0];
        echo $a[1][0];
        echo $a[2][0];
        echo count($a);
        echo $a[3][0];
        echo count($a[0]);
        echo count($a[3]);

        $a = array(0, 1, 2, 3, 4, 5, 6, 7, 8, 9);
        $a = array_chunk($a, 3, true);
        echo $a[0][0];
        echo $a[1][3];
        echo $a[2][6];
        echo count($a);
        echo $a[3][9];
        echo count($a[0]);
        echo count($a[3]);

        $a = array(0, 1, 2, 3, 4, 5);
        $a = array_chunk($a, 2);
        echo count($a[0]);
        echo count($a[1]);
        echo count($a[2]);

        $a = array('key1' => 1, "key2" => 2, "key3" => 3);
        $a = array_chunk($a, 2);
        echo count($a);
        echo count($a[0]);
        echo $a[0][0];

        $a = array('key1' => 1, "key2" => 2, "key3" => 3);
        $a = array_chunk($a, 2, "hippy");
        echo count($a);
        echo count($a[0]);
        echo $a[0]["key1"];

        ''')
        assert self.space.int_w(output[0]) == 0
        assert self.space.int_w(output[1]) == 3
        assert self.space.int_w(output[2]) == 6
        assert self.space.int_w(output[3]) == 4
        assert self.space.int_w(output[4]) == 9
        assert self.space.int_w(output[5]) == 3
        assert self.space.int_w(output[6]) == 1

        assert self.space.int_w(output[7]) == 0
        assert self.space.int_w(output[8]) == 3
        assert self.space.int_w(output[9]) == 6
        assert self.space.int_w(output[10]) == 4
        assert self.space.int_w(output[11]) == 9
        assert self.space.int_w(output[12]) == 3
        assert self.space.int_w(output[13]) == 1

        assert self.space.int_w(output[14]) == 2
        assert self.space.int_w(output[15]) == 2
        assert self.space.int_w(output[16]) == 2

        assert self.space.int_w(output[17]) == 2
        assert self.space.int_w(output[18]) == 2
        assert self.space.int_w(output[19]) == 1

        assert self.space.int_w(output[20]) == 2
        assert self.space.int_w(output[21]) == 2
        assert self.space.int_w(output[22]) == 1

    def test_array_chunk_error(self):
        self.run('''
        array_chunk("fail", 2, "");
        ''',  ["Warning: array_chunk() expects "
               "parameter 1 to be array, string given"])

    def test_array_count_values(self):
        output = self.run('''
        $a = array(1, "hello", 1, "world", "hello");
        $a = array_count_values($a);
        echo $a[1];
        echo $a["hello"];
        echo $a["world"];
        ''')
        assert self.space.str_w(output[0]) == '2'
        assert self.space.str_w(output[1]) == '2'
        assert self.space.str_w(output[2]) == '1'

    def test_array_count_values_errors(self):
        self.run('''
        array_count_values();
        array_count_values(array(1,2), 10);
        array_count_values(10);

        ''', ["Warning: array_count_values() expects "
              "exactly 1 parameter, 0 given",
              "Warning: array_count_values() expects "
              "exactly 1 parameter, 2 given",
              "Warning: array_count_values() expects "
              "parameter 1 to be array, integer given"])

    def test_array_flip(self):
        output = self.run('''
        $a = array('a'=>0, 'b'=>2, 'c');
        $a = array_flip($a);
        echo $a[2];
        echo $a['c'];
        echo $a[0];
        $a =  array("a" => 1, "b" => 1, "c" => 2);
        $a = array_flip($a);
        echo $a[1];
        $a =  array("a" => 1, "b" => 1, "c" => 2, NULL, TRUE, FALSE);
        $a = array_flip($a);
        echo $a[1];
        ''', ["Warning: array_flip(): Can only flip STRING "
              "and INTEGER values!",
              "Warning: array_flip(): Can only flip STRING "
              "and INTEGER values!",
              "Warning: array_flip(): Can only flip STRING "
              "and INTEGER values!"])
        assert self.space.str_w(output[0]) == "b"
        assert self.space.str_w(output[1]) == "0"
        assert self.space.str_w(output[2]) == "a"
        assert self.space.str_w(output[3]) == "b"
        assert self.space.str_w(output[4]) == "b"

    def test_array_flip_2(self):
        output = self.run('''
        $input = array(true => 1, false => 0, TRUE => -1);
        $out = array_flip($input);
        echo $out[-1];
        echo $out[0];
        echo count($out);
        ''')
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 0
        assert self.space.int_w(output[2]) == 2

    def test_array_flip_error(self):
        self.run('''
        array_flip();
        array_flip(array(10,20), 3);
        ''', ["Warning: array_flip() expects exactly 1 parameter, 0 given",
              "Warning: array_flip() expects exactly 1 parameter, 2 given"])

    def test_array_sum(self):
        output = self.run('''
        $a = array('a'=>0, 'b'=>2, 'c', 1, 2, 3, '5');
        $a = array_sum($a);
        echo $a;
        ''')
        assert self.space.str_w(output[0]) == "13"

    def test_array_sum_float(self):
        output = self.run('''
        $a = array(1.0, 2.2, 3.4, 4.6);
        $a = array_sum($a);
        echo $a;

        $a = array(1, 2.3, 4, 0.6, 10);
        $a = array_sum($a);
        echo $a;

        ''')
        assert self.space.float_w(output[0]) == 11.2
        assert self.space.float_w(output[1]) == 17.9

    def test_array_pad(self):
        output = self.run('''
        $b = array(1229600459=>'large', 1229604787=>20, 9609459=>'red');
        $b = array_pad($b, 5, 'foo');
        echo $b[0], $b[1], $b[2], $b[3], $b[4], count($b);
        ''')
        assert self.space.str_w(output[0]) == "large"
        assert self.space.int_w(output[1]) == 20
        assert self.space.str_w(output[2]) == "red"
        assert self.space.str_w(output[3]) == "foo"
        assert self.space.str_w(output[4]) == "foo"
        assert self.space.int_w(output[5]) == 5
        #
        output = self.run('''
        $a = array('a'=> 'a', 'b'=>4, '0'=>'0');
        $a = array_pad($a, -6, "x");
        echo $a[0], $a[1], $a[2], $a['a'], $a['b'], $a[3], count($a);
        ''')
        assert self.space.str_w(output[0]) == "x"
        assert self.space.str_w(output[1]) == "x"
        assert self.space.str_w(output[2]) == "x"
        assert self.space.str_w(output[3]) == "a"
        assert self.space.int_w(output[4]) == 4
        assert self.space.str_w(output[5]) == "0"
        assert self.space.int_w(output[6]) == 6

    def test_array_product(self):
        output = self.run('''
        echo array_product(array('a'=>1, 'b'=>2, 'c', 1, 2, 3, '5'));
        echo array_product(array('a'=>1, 'b'=>2, 1, 1, 2, 3, '5'));
        echo array_product(array(1=>1, 'b'=>2, 1, 1, 2, 3, 5));
        echo array_product(array());
        ''')
        assert self.space.int_w(output[0]) == 0
        assert self.space.int_w(output[1]) == 60
        assert self.space.int_w(output[2]) == 60
        assert self.space.int_w(output[3]) == 1

    def test_array_reverse(self):
        output = self.run('''
        $a = array("php", 4.5, array ("green", "red"));
        $a = array_reverse($a);
        echo $a[2];
        echo $a[1];
        $a = array(0=>1, 2=>4, '3'=>'6');
        $b = array_reverse($a, true);
        $c = array_reverse($a, false);
        echo $b[0];
        echo $c[0];
        $a = array(0=>1, 2=>4, '3'=>'6');
        $b = array_reverse($a, 'x');
        $c = array_reverse($a, '');
        echo $b[0];
        echo $c[0];
        $a = array(0=>1, 2=>4, '3'=>'6');
        $b = array_reverse($a, 0.001);
        $c = array_reverse($a, 0);
        echo $b[0];
        echo $c[0];

        ''')
        assert self.space.str_w(output[0]) == "php"
        assert self.space.str_w(output[1]) == "4.5"
        assert self.space.str_w(output[2]) == "1"
        assert self.space.str_w(output[3]) == "6"
        assert self.space.str_w(output[4]) == "1"
        assert self.space.str_w(output[5]) == "6"
        assert self.space.str_w(output[6]) == "1"
        assert self.space.str_w(output[7]) == "6"

    def test_array_keys(self):
        output = self.run('''
        $a = array("php", 4.5, "test"=>"test");
        $a = array_keys($a);
        echo $a[0];
        echo $a[1];
        echo $a[2];
        $a = array("php", 4.5, "test"=>"test", "php");
        $a = array_keys($a, "php");
        echo $a[0];
        echo $a[1];
        $a = array(1, 2, 3, 4, 5, 6, 7);
        $a = array_keys($a, '2');
        echo $a[0];
        $a = array(1, 2, 3, 4, 5, 6, 7);
        $a = array_keys($a, '2', true);
        echo sizeof($a);

        ''')
        assert self.space.str_w(output[0]) == "0"
        assert self.space.str_w(output[1]) == "1"
        assert self.space.str_w(output[2]) == "test"
        assert self.space.str_w(output[3]) == "0"
        assert self.space.str_w(output[4]) == "2"
        assert self.space.str_w(output[5]) == "1"
        assert self.space.str_w(output[6]) == "0"

    def test_array_values(self):
        output = self.run('''
        $a = array("php", 4.5, "key"=>"test");
        $a = array_values($a);
        echo $a[0];
        echo $a[1];
        echo $a[2];

        ''')
        assert self.space.str_w(output[0]) == "php"
        assert self.space.str_w(output[1]) == "4.5"
        assert self.space.str_w(output[2]) == "test"

    def test_array_combine(self):
        output = self.run('''
        $a = array('god', 'save', 'the', 'queen');
        $b = array(1, 2, 3, 4);
        $c = array_combine($a, $b);
        echo $c['god'];
        echo $c['the'];
        $a = array(1, 2, 3, 4);
        $b = array('god', 'save', 'the', 'queen');
        $c = array_combine($a, $b);
        echo $c['1'];
        echo $c['4'];
        $a = array('a'=>1, 'b', 'c', 'd');
        $b = array('q', 'w', 'e', 'r'=>5);
        $c = array_combine($a, $b);
        echo $c['1'];
        echo $c['b'];
        echo $c['d'];
        $c = array_combine(array(), array());
        echo $c;
        ''')
        assert self.space.str_w(output[0]) == '1'
        assert self.space.str_w(output[1]) == "3"
        assert self.space.str_w(output[2]) == "god"
        assert self.space.str_w(output[3]) == "queen"
        assert self.space.str_w(output[4]) == "q"
        assert self.space.str_w(output[5]) == "w"
        assert self.space.str_w(output[6]) == "5"
        assert output[7].arraylen() == 0

    def test_array_combine_mix(self):
        output = self.run('''
        $a = array('a'=>1, 'b', 'c', 'd');
        $b = array('q', 'w', 'e', 'r'=>5);
        $c = array_combine($a, $b);
        echo $c[1];
        echo $c['b'];
        echo $c['c'];
        echo $c['d'];

        ''')
        assert self.space.str_w(output[0]) == "q"
        assert self.space.str_w(output[1]) == "w"
        assert self.space.str_w(output[2]) == "e"
        assert self.space.str_w(output[3]) == "5"

    def test_array_combine_mix_2(self):
        output = self.run('''
        $array2 = array('1', '2', '3');
        $array3 = array(0, 1, 2);
        $array4 = array(TRUE, FALSE, NULL);

        $c = array_combine($array4, $array2);
        echo count($c);
        echo $c[1];
        echo $c[""];

        $c = array_combine($array4, $array3);
        echo count($c);
        echo $c[1];
        echo $c[""];

        $c = array_combine($array4, $array4);
        echo count($c);
        echo $c[1];
        echo $c[""];

        ''')
        assert self.space.int_w(output[0]) == 2
        assert self.space.str_w(output[1]) == "1"
        assert self.space.str_w(output[2]) == "3"

        assert self.space.int_w(output[3]) == 2
        assert self.space.int_w(output[4]) == 0
        assert self.space.int_w(output[5]) == 2

        assert self.space.int_w(output[6]) == 2
        assert self.space.int_w(output[7]) == 1  # true
        assert self.space.int_w(output[8]) == 0  # NULL

    def test_array_combine_float(self):
        output = self.run('''
        $c = array_combine(array(1.1, 2.2), array(1.1, 2.2));
        echo count($c);
        echo $c["1.1"];
        echo $c["2.2"];

        ''')
        assert self.space.int_w(output[0]) == 2
        assert self.space.str_w(output[1]) == "1.1"
        assert self.space.str_w(output[2]) == "2.2"

    def test_array_combine_error(self):
        self.run('''
        array_combine("array(1.1, 2.2)", array(1.1, 2.2));
        array_combine(array(1.1, 2.2), "array(1.1, 2.2)");
        array_combine(1, array(1.1, 2.2));
        array_combine(array(1.1, 2.2), 1);
        ''', ["Warning: array_combine() expects parameter 1 "
              "to be array, string given",
              "Warning: array_combine() expects parameter 2 "
              "to be array, string given",
              "Warning: array_combine() expects parameter 1 "
              "to be array, integer given",
              "Warning: array_combine() expects parameter 2 "
              "to be array, integer given"])

    def test_array_fill_keys(self):
        output = self.run('''
        $a = array(1, 2, 3, 4);
        $b = array_fill_keys($a, "x");
        echo $b[3], $b[4];
        ''')
        assert [self.space.str_w(i) for i in output] == ["x", "x"]

    def test_array_fill(self):
        output = self.run('''
        $a = array_fill(0, 10, "x");
        echo $a[0];
        echo $a[8];
        $a = array_fill("0", "0010", "x");
        echo count($a);
        ''')
        assert self.space.str_w(output[0]) == 'x'
        assert self.space.str_w(output[1]) == 'x'
        assert self.space.int_w(output[2]) == 10

    def test_array_filter(self):
        output = self.run('''
        function odd($var) {
           return $var & 1;
        }
        $array1 = array(1, 2, 3, 4, 5, 6, 7, 8);
        $result = array_filter($array1, "odd");
        echo count($result);
        echo $result[2];
        echo $result[6];

        $array1 = array(-2, -1, 0, 0, 0, 0, 1, true, false, 0);
        $result = array_filter($array1);
        echo count($result);
        echo $result[0];
        echo $result[6];
        echo $result[7];

        ''')
        assert self.space.int_w(output[0]) == 4
        assert self.space.int_w(output[1]) == 3
        assert self.space.int_w(output[2]) == 7

        assert self.space.int_w(output[3]) == 4
        assert self.space.int_w(output[4]) == -2
        assert self.space.int_w(output[5]) == 1
        assert self.space.int_w(output[6]) == 1

    def test_array_reduce(self):

        output = self.run('''
        function rsum($v, $w)
        {
            $v += $w;
            return $v;
        }
        function rmul($v, $w)
        {
           $v *= $w;
           return $v;
        }

        $a = array('a'=>10, 0, 1, 2, 3, 'c'=>55);
        $a = array_reduce($a , 'rsum');

        echo $a;

        $a = array('a'=>10, 1, 1, 2, 3, 'c'=>55);
        $a = array_reduce($a , 'rmul', 1);

        echo $a;


        $a = array();
        $a = array_reduce($a , 'rsum', 'Empty Array');

        echo $a;

        ''')
        assert self.space.int_w(output[0]) == 71
        assert self.space.int_w(output[1]) == 3300
        assert self.space.str_w(output[2]) == "Empty Array"

    def test_range(self):
        output = self.run('''
        foreach(range(0, 10) as $k => $v){
           echo $v;
        }
        ''')
        res = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        assert [self.space.int_w(i) for i in output] == res

        output = self.run('''
        foreach(range(10, 0) as $k => $v){
           echo $v;
        }
        ''')
        res = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
        assert [self.space.int_w(i) for i in output] == res

        output = self.run('''
        foreach(range("10", "0") as $k => $v){
           echo $v;
        }
        ''')
        res = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
        assert [self.space.int_w(i) for i in output] == res

        output = self.run('''
        foreach(range("10", "d") as $k => $v){
           echo $v;
        }
        ''')
        res = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
        assert [self.space.int_w(i) for i in output] == res

        output = self.run('''
        foreach(range("a", "h") as $k => $v){
           echo $v;
        }
        ''')
        res = ["a", "b", "c", "d", "e", "f", "g", "h"]
        assert [self.space.str_w(i) for i in output] == res

        output = self.run('''
        foreach(range(1.1, 5.2) as $k => $v){
           echo $v;
        }
        ''')
        res = [1.1, 2.1, 3.1, 4.1, 5.1]
        assert [self.space.float_w(i) for i in output] == res

        output = self.run('''
        foreach(range(1, 2, 0.2) as $k => $v){
           echo $v;
        }
        ''')
        res = [1.0, 1.2, 1.4, 1.6, 1.8, 2.0]
        assert [self.space.float_w(i) for i in output] == res

        output = self.run('''
        foreach(range(1, 2, "0.2") as $k => $v){
           echo $v;
        }
        ''')
        res = [1.0, 1.2, 1.4, 1.6, 1.8, 2.0]
        assert [self.space.float_w(i) for i in output] == res

        output = self.run('''
        foreach(range("array", "hippy") as $k => $v){
           echo $v;
        }
        ''')
        res = ["a", "b", "c", "d", "e", "f", "g", "h"]
        assert [self.space.str_w(i) for i in output] == res

        output = self.run('''
        foreach(range("a", "h", 2) as $k => $v){
           echo $v;
        }
        ''')
        res = ["a", "c", "e", "g"]
        assert [self.space.str_w(i) for i in output] == res

        output = self.run('''
        foreach(range("a", "h", 2.5) as $k => $v){
           echo $v;
        }
        ''')
        res = [0]
        assert [self.space.int_w(i) for i in output] == res

        output = self.run('''
        foreach(range(5, 5) as $k => $v){
           echo $v;
        }
        ''')
        res = [5]
        assert [self.space.int_w(i) for i in output] == res

        output = self.run('''
        foreach(range(0.000000000001, 0.000000000004, 0.000000000001) as $k => $v){
           echo $v;
        }
        ''')
        res = [0.000000000001, 0.000000000002, 0.000000000003, 0.000000000004]
        assert [self.space.float_w(i) for i in output] == res

        output = self.run('''
        foreach(range(1, 5, array(1, 2)) as $k => $v){
           echo $v;
        }
        ''')
        res = [1, 2, 3, 4, 5]
        assert [self.space.int_w(i) for i in output] == res

        output = self.run('''
        foreach(range(1, 5, TRUE) as $k => $v){
           echo $v;
        }
        ''')
        res = [1, 2, 3, 4, 5]
        assert [self.space.int_w(i) for i in output] == res

    def test_range_errors(self):
        output = self.run('''
        echo range();
        echo range(1);
        echo range(1,2,3,4);
        echo range(-1, -2, 2);
        echo range("a", "j", "z");
        echo range("a", "j", FALSE);
        ''', ["Warning: range() expects at least 2 parameters, 0 given",
              "Warning: range() expects at least 2 parameters, 1 given",
              "Warning: range() expects at most 3 parameters, 4 given",
              "Warning: range(): step exceeds the specified range",
              "Warning: range(): step exceeds the specified range",
              "Warning: range(): step exceeds the specified range"])
        assert [self.space.is_true(i) for i in output] == [False, False, False,
                                                           False, False, False]

    def test_range_mem_error(self):
        py.test.skip("MemoryError")

        self.run('''
        foreach(range(1, 1000000000004, 1) as $k => $v){
           echo $v;
        }
        ''')

    def test_shuffle(self):
        output = self.run('''
        $a = array(0, 1, 2, 3, 4, 9);
        shuffle($a);
        echo $a[0];
        echo $a[1];
        echo $a[2];
        echo $a[3];
        echo $a[4];
        echo $a[5];
        echo count($a);
        ''')
        _count = output.pop()
        assert self.space.int_w(_count) == 6
        lst = [self.space.int_w(i) for i in output]
        assert lst != [0, 1, 2, 3, 4, 9]    # unless we're very unlucky
        assert sorted(lst) == [0, 1, 2, 3, 4, 9]

    def test_shuffle_hash(self):
        output = self.run('''
        $a = array("a"=>0, "b"=>1,"c"=> 2, "d"=>3, "e"=>4, "f"=>9);
        shuffle($a);
        echo $a[0];
        echo $a[1];
        echo $a[2];
        echo $a[3];
        echo $a[4];
        echo $a[5];
        echo count($a);
        ''')
        _count = output.pop()
        assert self.space.int_w(_count) == 6
        lst = [self.space.int_w(i) for i in output]
        assert lst != [0, 1, 2, 3, 4, 9]    # unless we're very unlucky
        assert sorted(lst) == [0, 1, 2, 3, 4, 9]

    def test_shuffle_error(self):
        self.run('''
        shuffle();
        $x = 10;
        shuffle($x);
        $x = "array";
        shuffle($x);
        shuffle($x, $x);
        $x = array(0,1);
        shuffle($x, 1);
        ''', ["Warning: shuffle() expects exactly 1 parameter, 0 given",
              "Warning: shuffle() expects parameter 1 to be array, integer given",
              "Warning: shuffle() expects parameter 1 to be array, string given",
              "Warning: shuffle() expects exactly 1 parameter, 2 given",
              "Warning: shuffle() expects exactly 1 parameter, 2 given",
              ])

    def test_array_rand(self):
        repeat = 100
        letters = ["a", "b", "c", "d"]
        must_see_0 = set(letters)
        must_see_1 = set(letters)
        must_see_2 = set(letters)
        while must_see_0 or must_see_1 or must_see_2:
            repeat -= 1
            assert repeat > 0
            output = self.run('''
            $a = array("a"=>0, "b"=>1,"c"=> 2, "d"=>3);
            $a = array_rand($a, 2);
            foreach($a as $v) {
                echo $v;
            }

            $a = array("a"=>0, "b"=>1,"c"=> 2, "d"=>3);
            $a = array_rand($a, 1);
            echo $a;

            ''')
            lst = [self.space.str_w(i) for i in output]
            assert len(lst) == 3
            assert lst[0] in letters
            assert lst[1] in letters and lst[1] != lst[0]
            assert lst[2] in letters
            must_see_0.discard(lst[0])
            must_see_1.discard(lst[1])
            must_see_2.discard(lst[2])
            print lst[0], lst[1], lst[2]

    def test_array_rand_error(self):
        output = self.run('''
        $a = array("a"=>0, "b"=>1,"c"=> 2, "d"=>3, "e"=>4, "f"=>5);
        echo array_rand($a, 7);
        echo array_rand($a, -1);
        echo array_rand("php");
        echo array_rand("php", 5);
        ''', ["Warning: array_rand(): Second argument has to be between 1"
              " and the number of elements in the array",
              "Warning: array_rand(): Second argument has to be between 1"
              " and the number of elements in the array",
              "Warning: array_rand() expects parameter 1 to be array, "
              "string given",
              "Warning: array_rand() expects parameter 1 to be array, "
              "string given"])
        assert [self.space.is_true(i) for i in output] == [False, False, False,
                                                           False]

    def test_array_uintersect_assoc(self):
        output = self.run('''
        $t1 = array("a" => "zielony", "b" => "brązowy",
                    "c" => "niebieski", "czerwony");
        $t2 = array("a" => "ZIELONY", "B" => "brązowy", "żółty", "czerwony");
        $r = array_uintersect_assoc($t1, $t2, "strcasecmp");
        echo count($r);
        echo $r["a"];
        ''')
        assert [self.space.str_w(i) for i in output] == ["1", "zielony"]

    def test_array_uintersect_uassoc(self):
        output = self.run('''
        $t1 = array("a" => "green", "b" => "brown", "c" => "blue", "red");
        $t2 = array("a" => "GREEN", "B" => "brown", "yellow", "red");
        $r = array_uintersect_uassoc($t1,
                                     $t2, "strcasecmp", "strcasecmp");
        echo count($r);
        echo $r["a"];
        echo $r["b"];
        ''')
        assert [self.space.str_w(i) for i in output] == ["2", "green", "brown"]

    def test_array_uintersect(self):
        output = self.run('''
        $t1 = array("a" => "green", "b" => "brown", "c" => "blue", "red");
        $t2 = array("a" => "GREEN", "B" => "brown", "yellow", "red");
        $r = array_uintersect($t1, $t2, "strcasecmp");
        echo count($r);
        echo $r["a"];
        echo $r["b"];
        echo $r[0];
        ''')
        assert [self.space.str_w(i) for i in output] == ["3", "green",
                                                         "brown", "red"]

    def test_array_arithmetics(self):
        output = self.run('''
        $x = array(1, 2) + array("x"=>3);
        echo $x[0], $x[1], $x["x"];
        ''')
        assert [self.space.int_w(w_v) for w_v in output] == [1, 2, 3]

    def test_count(self):
        output = self.run('''
        echo count(array());
        echo count(array(1));
        echo count(array(1, 2));

        echo count(array());
        echo count(array('1' => 1));
        echo count(array('1' => 1, '2' => 2));

        echo count(array(10, '0' => 20));
        ''')

        assert [self.space.int_w(o) for o in output] == [0, 1, 2, 0, 1, 2, 1]

    def test_count2(self):

        output = self.run('''
        $food = array('fruits' => array('orange', 'banana', 'apple'),
                      'veggie' => array('carrot', 'collard', 'pea'));

        echo count($food);
        echo count($food, COUNT_RECURSIVE);
        ''')

        assert self.space.int_w(output[0]) == 2
        assert self.space.int_w(output[1]) == 8

    def test_count3(self):

        with self.warnings() as w:
            output = self.run('''
            $a = array(1, 2, 3, 4);
            $a[5] = &$a;

            $b = array();
            $b[0] = &$b;

            echo count($a, COUNT_RECURSIVE);
            echo count($b, COUNT_RECURSIVE);
            ''')

        assert self.space.int_w(output[0]) == 15
        assert self.space.int_w(output[1]) == 3

        warning_msg = 'Warning: count(): recursion detected'
        assert w[0] == warning_msg
        assert w[1] == warning_msg

    def test_setitem_keylist_hash_old_instance(self):
        space = ObjSpace()
        w_a = space.newstr("a")
        w_b = space.newstr("b")
        w_arr = space.new_map_from_pairs([(w_a, space.wrap(0)),
                                          (w_b, space.wrap(12))])
        assert w_arr._getkeylist() == ['a', 'b']
        assert w_arr.arraylen() == 2
        assert len(w_arr.dct_w) == 2
        assert space.int_w(space.getitem(w_arr, w_a)) == 0
        w_arr2 = space.setitem(w_arr, space.wrap(0), space.wrap(15))
        assert w_arr._getkeylist() == ['a', 'b']
        assert w_arr2._getkeylist() == ['a', 'b', '0']

    def test_setitem_keylist_hash(self):
        space = ObjSpace()
        w_a = space.newstr("a")
        w_b = space.newstr("b")
        w_arr = space.new_map_from_pairs([(w_a, space.wrap(0)),
                                          (w_b, space.wrap(12))])
        assert w_arr._getkeylist() == ['a', 'b']
        assert w_arr.arraylen() == 2
        assert len(w_arr.dct_w) == 2
        assert space.int_w(space.getitem(w_arr, w_a)) == 0
        w_arr = space.setitem(w_arr, w_b, space.wrap(3))
        assert w_arr._getkeylist() == ['a', 'b']
        assert space.int_w(space.getitem(w_arr, w_b)) == 3
        assert w_arr.isset_index(space, w_b)

        assert not w_arr.isset_index(space, space.wrap(0))
        assert not w_arr.isset_index(space, space.newstr("c"))
        w_arr2 = space.setitem(w_arr, space.wrap(0), space.wrap(15))

        assert w_arr._getkeylist() == ['a', 'b']
        assert w_arr.arraylen() == len(w_arr.dct_w)

        assert w_arr2._getkeylist() == ['a', 'b', '0']
        assert w_arr2.arraylen() == len(w_arr2.dct_w)

        assert w_arr2.strategy_name == 'hash'
        assert space.int_w(space.getitem(w_arr, w_a)) == 0
        assert space.int_w(space.getitem(w_arr, w_b)) == 3
        assert space.int_w(space.getitem(w_arr2, space.wrap(0))) == 15

        w_arr3 = space.setitem(w_arr2, space.newstr("c"), space.wrap(38))
        assert w_arr3._getkeylist() == ['a', 'b', '0', 'c']
        assert w_arr3.arraylen() == len(w_arr3.dct_w)

        w_arr4 = w_arr3._unsetitem(space, space.newstr("c"))
        assert w_arr4._getkeylist() == ['a', 'b', '0']
        assert w_arr4.arraylen() == len(w_arr4.dct_w)

        w_arr5 = w_arr4._unsetitem(space, space.newstr("0"))
        assert w_arr5._getkeylist() == ['a', 'b']
        assert w_arr5.arraylen() == len(w_arr5.dct_w)

        w_arr6 = w_arr5._unsetitem(space, space.newstr("a"))
        assert w_arr6._getkeylist() == ['b']
        assert w_arr6.arraylen() == len(w_arr6.dct_w)

        w_arr7 = space.setitem(w_arr6, space.newstr("b"), space.wrap(38))
        assert w_arr7._getkeylist() == ['b']
        assert w_arr7.arraylen() == 1
        assert len(w_arr7.dct_w) == 1

        w_arr8 = w_arr7._unsetitem(space, space.newstr("b"))
        assert w_arr8._getkeylist() == []
        assert w_arr8.arraylen() == len(w_arr8.dct_w)

        w_arr9 = space.setitem(w_arr8, space.newstr("php"), space.wrap(38))
        assert w_arr9._getkeylist() == ['php']
        assert w_arr9.arraylen() == 1
        assert len(w_arr9.dct_w) == 1

        assert w_arr.strategy_name == 'hash'

    def test_setitem_keylist_list(self):
        space = ObjSpace()
        w_a = space.newstr("a")
        w_b = space.newstr("b")
        w_arr = space.new_array_from_list([w_a, w_b, w_a, w_b, w_a, w_b])
        assert w_arr.arraylen() == len(w_arr.lst_w)

        assert space.str_w(space.getitem(w_arr, space.wrap(0))) == 'a'
        assert space.str_w(space.getitem(w_arr, space.wrap(1))) == 'b'

        w_arr2 = space.setitem(w_arr, space.wrap(11), space.wrap(15))
        assert w_arr2.strategy_name == 'hash'
        assert w_arr2._getkeylist() == ['0', '1', '2', '3', '4', '5', '11']
        assert w_arr2.arraylen() == len(w_arr2.dct_w)

        w_arr3 = space.setitem(w_arr2, space.wrap(11), space.wrap(15))
        assert w_arr3._getkeylist() == ['0', '1', '2', '3', '4', '5', '11']
        assert w_arr3.arraylen() == len(w_arr3.dct_w)

        w_arr4 = w_arr3._unsetitem(space, space.wrap(0))
        assert w_arr4._getkeylist() == ['1', '2', '3', '4', '5', '11']
        assert w_arr4.arraylen() == len(w_arr4.dct_w)

        w_arr5 = space.setitem(w_arr4, space.wrap(0), space.wrap(15))
        assert w_arr5._getkeylist() == ['1', '2', '3', '4', '5', '11', '0']
        assert w_arr5.arraylen() == len(w_arr5.dct_w)

        w_arr6 = space.setitem(w_arr5, space.wrap(11), space.wrap(15))
        assert w_arr6._getkeylist() == ['1', '2', '3', '4', '5', '11', '0']
        assert w_arr6.arraylen() == len(w_arr2.dct_w)

        w_arr7 = space.setitem(w_arr6, space.newstr('11'), space.wrap(15))
        assert w_arr7._getkeylist() == ['1', '2', '3', '4', '5', '11', '0']
        assert w_arr7.arraylen() == len(w_arr2.dct_w)

    def test_array_intersect_key(self):
        output = self.run('''
        $a = array_intersect_key(array(7=>0, 3=>6, 5=>1, 4=>2),
                                 array(4=>0, 3=>8, 7>=0),
                                 array(4=>null, 3=>null, 5=>null, 9=>null));
        foreach($a as $k=>$v) {
            echo $k;
            echo $v;
        }
        ''')
        assert [self.space.int_w(i) for i in output] == [3, 6, 5, 1, 4, 2]

    def test_array_shift(self):
        output = self.run('''
        $a = array(55, 22, 33);
        echo array_shift($a);
        echo array_shift($a);
        echo array_shift($a);
        echo count($a);
        ''')
        assert [self.space.int_w(i) for i in output] == [55, 22, 33, 0]

    def test_array_unshift(self):
        output = self.run('''
        $a = array();
        echo array_unshift($a, 33, 55);
        echo array_unshift($a, 44);
        echo count($a);
        foreach($a as $v) {
            echo $v;
        }
        ''')
        assert [self.space.int_w(i) for i in output] == [2, 3, 3, 44, 33, 55]

    def test_array_unique(self):
        output = self.run('''
        $a = array(66, 22, 22, 44);
        $b = array_unique($a);
        echo count($a);
        foreach($b as $k=>$v) {
            echo $k;
            echo $v;
        }
        ''')
        assert [self.space.int_w(i) for i in output] == [
            4, 0, 66, 1, 22, 3, 44]

    def test_array_splice_1(self):
        output = self.run('''
        function test($a, $offset) {
            $b = array_splice($a, $offset);
            echo "a";
            foreach($a as $k=>$v) {
                echo $k;
                echo $v;
            }
            echo "b";
            foreach($b as $k=>$v) {
                echo $k;
                echo $v;
            }
        }
        test(array(55, 33, 77, 99), 0);
        test(array(55, 33, 77, 99), 2);
        test(array(55, 33, 77, 99), 4);
        test(array(55, 33, 77, 99), 6);
        test(array(55, 33, 77, 99), -1);
        test(array(55, 33, 77, 99), -9);
        test(array(55, 33, 'x'=>77, 99), 0);
        test(array(55, 33, 'x'=>77, 99), 2);
        test(array(55, 33, 'x'=>77, 99), 4);
        test(array(55, 33, 'x'=>77, 99), 6);
        test(array(55, 33, 'x'=>77, 99), -1);
        test(array(55, 33, 'x'=>77, 99), -9);
        test(array(55, 33, 9=>77, 99), 0);
        test(array(55, 33, 9=>77, 99), 2);
        test(array(55, 33, 9=>77, 99), 4);
        test(array(55, 33, 9=>77, 99), 6);
        test(array(55, 33, 9=>77, 99), -1);
        test(array(55, 33, 9=>77, 99), -9);
        ''')
        assert [self.space.str_w(i) for i in output] == [
            'a', 'b', '0', '55', '1', '33', '2', '77', '3', '99',
            'a', '0', '55', '1', '33', 'b', '0', '77', '1', '99',
            'a', '0', '55', '1', '33', '2', '77', '3', '99', 'b',
            'a', '0', '55', '1', '33', '2', '77', '3', '99', 'b',
            'a', '0', '55', '1', '33', '2', '77', 'b', '0', '99',
            'a', 'b', '0', '55', '1', '33', '2', '77', '3', '99',
            'a', 'b', '0', '55', '1', '33', 'x', '77', '2', '99',
            'a', '0', '55', '1', '33', 'b', 'x', '77', '0', '99',
            'a', '0', '55', '1', '33', 'x', '77', '2', '99', 'b',
            'a', '0', '55', '1', '33', 'x', '77', '2', '99', 'b',
            'a', '0', '55', '1', '33', 'x', '77', 'b', '0', '99',
            'a', 'b', '0', '55', '1', '33', 'x', '77', '2', '99',
            'a', 'b', '0', '55', '1', '33', '2', '77', '3', '99',
            'a', '0', '55', '1', '33', 'b', '0', '77', '1', '99',
            'a', '0', '55', '1', '33', '2', '77', '3', '99', 'b',
            'a', '0', '55', '1', '33', '2', '77', '3', '99', 'b',
            'a', '0', '55', '1', '33', '2', '77', 'b', '0', '99',
            'a', 'b', '0', '55', '1', '33', '2', '77', '3', '99',
            ]

    def test_array_splice_2(self):
        output = self.run('''
        function test($a, $offset, $length) {
            $b = array_splice($a, $offset, $length);
            echo "a";
            foreach($a as $k=>$v) {
                echo $k;
                echo $v;
            }
            echo "b";
            foreach($b as $k=>$v) {
                echo $k;
                echo $v;
            }
        }
        test(array(55, 33, 77, 99), 0, 3);
        test(array(55, 33, 77, 99), 2, 1);
        test(array(55, 33, 77, 99), 3, 3);
        test(array(55, 33, 77, 99), 6, 3);
        test(array(55, 33, 77, 99), -2, 1);
        test(array(55, 33, 77, 99), -9, 2);
        test(array(55, 33, 'x'=>77, 99), 0, 3);
        test(array(55, 33, 'x'=>77, 99), 2, 1);
        test(array(55, 33, 'x'=>77, 99), 4, 3);
        test(array(55, 33, 'x'=>77, 99), 6, 3);
        test(array(55, 33, 'x'=>77, 99), -1, 1);
        test(array(55, 33, 'x'=>77, 99), -9, 2);
        test(array(55, 33, 9=>77, 99), 0, 3);
        test(array(55, 33, 9=>77, 99), 2, 1);
        test(array(55, 33, 9=>77, 99), 4, 3);
        test(array(55, 33, 9=>77, 99), 6, 3);
        test(array(55, 33, 9=>77, 99), -1, 1);
        test(array(55, 33, 9=>77, 99), -9, 2);
        ''')
        assert [self.space.str_w(i) for i in output] == [
            'a', '0', '99', 'b', '0', '55', '1', '33', '2', '77',
            'a', '0', '55', '1', '33', '2', '99', 'b', '0', '77',
            'a', '0', '55', '1', '33', '2', '77', 'b', '0', '99',
            'a', '0', '55', '1', '33', '2', '77', '3', '99', 'b',
            'a', '0', '55', '1', '33', '2', '99', 'b', '0', '77',
            'a', '0', '77', '1', '99', 'b', '0', '55', '1', '33',
            'a', '0', '99', 'b', '0', '55', '1', '33', 'x', '77',
            'a', '0', '55', '1', '33', '2', '99', 'b', 'x', '77',
            'a', '0', '55', '1', '33', 'x', '77', '2', '99', 'b',
            'a', '0', '55', '1', '33', 'x', '77', '2', '99', 'b',
            'a', '0', '55', '1', '33', 'x', '77', 'b', '0', '99',
            'a', 'x', '77', '0', '99', 'b', '0', '55', '1', '33',
            'a', '0', '99', 'b', '0', '55', '1', '33', '2', '77',
            'a', '0', '55', '1', '33', '2', '99', 'b', '0', '77',
            'a', '0', '55', '1', '33', '2', '77', '3', '99', 'b',
            'a', '0', '55', '1', '33', '2', '77', '3', '99', 'b',
            'a', '0', '55', '1', '33', '2', '77', 'b', '0', '99',
            'a', '0', '77', '1', '99', 'b', '0', '55', '1', '33',
            ]

    def test_array_splice_3(self):
        output = self.run('''
        function test($a, $offset, $length) {
            $b = array_splice($a, $offset, $length, 'y');
            echo "a";
            foreach($a as $k=>$v) {
                echo $k;
                echo $v;
            }
            echo "b";
            foreach($b as $k=>$v) {
                echo $k;
                echo $v;
            }
        }
        test(array(55, 33, 77, 99), 0, 3);
        test(array(55, 33, 77, 99), 2, 1);
        test(array(55, 33, 77, 99), 3, 3);
        test(array(55, 33, 77, 99), 6, 3);
        test(array(55, 33, 77, 99), -2, 1);
        test(array(55, 33, 77, 99), -9, 2);
        test(array(55, 33, 'x'=>77, 99), 0, 3);
        test(array(55, 33, 'x'=>77, 99), 2, 1);
        test(array(55, 33, 'x'=>77, 99), 4, 3);
        test(array(55, 33, 'x'=>77, 99), 6, 3);
        test(array(55, 33, 'x'=>77, 99), -1, 1);
        test(array(55, 33, 'x'=>77, 99), -9, 2);
        test(array(55, 33, 9=>77, 99), 0, 3);
        test(array(55, 33, 9=>77, 99), 2, 1);
        test(array(55, 33, 9=>77, 99), 4, 3);
        test(array(55, 33, 9=>77, 99), 6, 3);
        test(array(55, 33, 9=>77, 99), -1, 1);
        test(array(55, 33, 9=>77, 99), -9, 2);
        ''')
        assert [self.space.str_w(i) for i in output] == [
            'a', '0', 'y', '1', '99', 'b', '0', '55', '1', '33', '2', '77',
            'a', '0', '55', '1', '33', '2', 'y', '3', '99', 'b', '0', '77',
            'a', '0', '55', '1', '33', '2', '77', '3', 'y', 'b', '0', '99',
            'a', '0', '55', '1', '33', '2', '77', '3', '99', '4', 'y', 'b',
            'a', '0', '55', '1', '33', '2', 'y', '3', '99', 'b', '0', '77',
            'a', '0', 'y', '1', '77', '2', '99', 'b', '0', '55', '1', '33',
            'a', '0', 'y', '1', '99', 'b', '0', '55', '1', '33', 'x', '77',
            'a', '0', '55', '1', '33', '2', 'y', '3', '99', 'b', 'x', '77',
            'a', '0', '55', '1', '33', 'x', '77', '2', '99', '3', 'y', 'b',
            'a', '0', '55', '1', '33', 'x', '77', '2', '99', '3', 'y', 'b',
            'a', '0', '55', '1', '33', 'x', '77', '2', 'y', 'b', '0', '99',
            'a', '0', 'y', 'x', '77', '1', '99', 'b', '0', '55', '1', '33',
            'a', '0', 'y', '1', '99', 'b', '0', '55', '1', '33', '2', '77',
            'a', '0', '55', '1', '33', '2', 'y', '3', '99', 'b', '0', '77',
            'a', '0', '55', '1', '33', '2', '77', '3', '99', '4', 'y', 'b',
            'a', '0', '55', '1', '33', '2', '77', '3', '99', '4', 'y', 'b',
            'a', '0', '55', '1', '33', '2', '77', '3', 'y', 'b', '0', '99',
            'a', '0', 'y', '1', '77', '2', '99', 'b', '0', '55', '1', '33',
            ]

    def test_array_splice_4(self):
        output = self.run('''
        function test($a, $offset, $length) {
            $b = array_splice($a, $offset, $length, array(66, 'y'=>44));
            echo "a";
            foreach($a as $k=>$v) {
                echo $k;
                echo $v;
            }
            echo "b";
            foreach($b as $k=>$v) {
                echo $k;
                echo $v;
            }
        }
        test(array(55, 33, 77, 99), 0, -3);
        test(array(55, 33, 77, 99), 2, -1);
        test(array(55, 33, 77, 99), 3, 0);
        test(array(55, 33, 77, 99), 6, -3);
        test(array(55, 33, 77, 99), -2, -1);
        test(array(55, 33, 77, 99), -9, -2);
        test(array(55, 33, 'x'=>77, 99), 0, -3);
        test(array(55, 33, 'x'=>77, 99), 2, -1);
        test(array(55, 33, 'x'=>77, 99), 4, 0);
        test(array(55, 33, 'x'=>77, 99), 6, -3);
        test(array(55, 33, 'x'=>77, 99), -1, -1);
        test(array(55, 33, 'x'=>77, 99), -9, -2);
        test(array(55, 33, 9=>77, 99), 0, -3);
        test(array(55, 33, 9=>77, 99), 2, -1);
        test(array(55, 33, 9=>77, 99), 4, 0);
        test(array(55, 33, 9=>77, 99), 6, -3);
        test(array(55, 33, 9=>77, 99), -1, -1);
        test(array(55, 33, 9=>77, 99), -9, -2);
        ''')
        assert [self.space.str_w(i) for i in output] == [
            'a','0','66','1','44','2','33','3','77','4','99','b','0','55',
            'a','0','55','1','33','2','66','3','44','4','99','b','0','77',
            'a','0','55','1','33','2','77','3','66','4','44','5','99','b',
            'a','0','55','1','33','2','77','3','99','4','66','5','44','b',
            'a','0','55','1','33','2','66','3','44','4','99','b','0','77',
            'a','0','66','1','44','2','77','3','99','b','0','55','1','33',
            'a','0','66','1','44','2','33','x','77','3','99','b','0','55',
            'a','0','55','1','33','2','66','3','44','4','99','b','x','77',
            'a','0','55','1','33','x','77','2','99','3','66','4','44','b',
            'a','0','55','1','33','x','77','2','99','3','66','4','44','b',
            'a','0','55','1','33','x','77','2','66','3','44','4','99','b',
            'a','0','66','1','44','x','77','2','99','b','0','55','1','33',
            'a','0','66','1','44','2','33','3','77','4','99','b','0','55',
            'a','0','55','1','33','2','66','3','44','4','99','b','0','77',
            'a','0','55','1','33','2','77','3','99','4','66','5','44','b',
            'a','0','55','1','33','2','77','3','99','4','66','5','44','b',
            'a','0','55','1','33','2','77','3','66','4','44','5','99','b',
            'a','0','66','1','44','2','77','3','99','b','0','55','1','33',
            ]

    def test_null2array(self):
        output = self.run('''
        $a = null;
        $a[] = 5;
        echo $a[0];
        ''', ['Hippy warning: Creating array from empty value'])
        assert self.space.int_w(output[0]) == 5

    def test_instance_getitem(self):
        self.run('''
        class A { }
        $a = new A;
        $a[0];
        ''', ['Fatal error: Cannot use object of type A as array'])

    def test_instance_setitem(self):
        self.run('''
        class A { }
        $a = new A;
        $a[0] = 5;
        ''', ['Fatal error: Cannot use object of type A as array'])

    def test_instance_setitem_ref(self):
        self.run('''
        class A { }
        $a = new A;
        $a[0] = &$a;
        ''', ['Fatal error: Cannot use object of type A as array'])

    def test_instance_appenditem(self):
        self.run('''
        class A { }
        $a = new A;
        $a[] = 5;
        ''', ['Fatal error: Cannot use object of type A as array'])

    def test_array_push(self):
        output = self.run('''
        $a = array();
        echo array_push($a, 5);
        echo array_push($a, 6);
        echo next($a);
        echo array_push($a, 7);
        echo next($a);
        ''')
        assert [self.space.int_w(s) for s in output] == [1, 2, 6, 3, 7]

    @py.test.mark.xfail(reason="$a=&$b doesn't return a reference")
    def test_array_push_byref(self):
        output = self.run('''
        $a = array();
        $b = array();
        $c = &$a;
        echo array_push($a=&$b, 5);
        echo $a;
        echo $b;
        echo $c;
        ''')
        assert self.space.int_w(output[0]) == 1
        assert self.unwrap(output[1]) == {'0': 5}
        assert self.unwrap(output[2]) == {'0': 5}
        assert self.unwrap(output[3]) == {}

    def test_array_pop_instance(self):
        output = self.run('''
        class P {
          public $var = 'oho';
          public $foo = 'ioi';
        }
        $inst = new P;
        echo array_pop($inst);
        ''', ['Warning: array_pop() expects parameter 1 to be array, object given'])
        assert output[0] == self.space.w_Null

    def test_natsort(self):
        output = self.run('''

        $array = array ('A01', 'a1', 'b10',  'a01', 'b01');
        natsort($array);
        foreach($array as $k=>$v) {
          echo $v;
        }
        ''')

        assert [self.space.str_w(s) for s in output] == [
            'A01', 'a01', 'a1', 'b01', 'b10']

    def test_array_plus(self):
        output = self.run('''
        echo array(1, 2) + array(3, 4);
        echo array("a" => 1, "b" => 2) + array("a" => null, "c" => 3);
        ''')

        assert self.unwrap(output[0]) == {'0': 1, '1': 2}
        assert self.unwrap(output[1]) == {"a": 1, "b": 2, "c": 3}

    def test_multisort_a(self):
        output = self.run('''
        $ar1 = array(10, 100, 100, 0);
        $ar2 = array(1, 3, 2, 4);
        array_multisort($ar1, SORT_ASC, SORT_REGULAR, $ar2);
        foreach($ar1 as $k=>$v) {
          echo $v;
        }
        foreach($ar2 as $k=>$v) {
          echo $v;
        }

        $ar1 = array(5, 5, 5, 5, 5,  4,  3,  2,  1);
        $ar2 = array(1, 2, 3, 4, 5, 2, 2, 2, 2);
        array_multisort($ar1, SORT_ASC, SORT_REGULAR, $ar2);
        foreach($ar1 as $k=>$v) {
          echo $v;
        }
        foreach($ar2 as $k=>$v) {
          echo $v;
        }

        ''')
        assert [self.space.str_w(s) for s in output] == [
            '0', '10', '100', '100',
            '4', '1', '2', '3',
            '1', '2', '3', '4', '5', '5', '5', '5', '5',
            '2', '2', '2', '2', '1', '2', '3', '4', '5'
        ]

    def test_multisort_b(self):
        output = self.run('''
        $ar1 = array(10, 100, 100, 0);
        $ar2 = array(1, 3, 2, 4);
        array_multisort($ar1, SORT_DESC, SORT_REGULAR, $ar2);
        foreach($ar1 as $k=>$v) {
          echo $v;
        }
        foreach($ar2 as $k=>$v) {
          echo $v;
        }

        $ar1 = array(5, 5, 5, 5, 5,  4,  3,  2,  1);
        $ar2 = array(1, 2, 3, 4, 5, 2, 2, 2, 2);
        array_multisort($ar1, SORT_DESC, SORT_REGULAR, $ar2);
        foreach($ar1 as $k=>$v) {
          echo $v;
        }
        foreach($ar2 as $k=>$v) {
          echo $v;
        }

        ''')
        assert [self.space.str_w(s) for s in output] == [
            '100', '100', '10', '0',
            '2', '3', '1', '4',

            '5', '5', '5', '5', '5', '4', '3', '2', '1',
            '1', '2', '3', '4', '5', '2', '2', '2', '2'
        ]

    def test_multisort_string(self):
        output = self.run('''
        class B {
            function __toString() {return 'B';}
        }
        $ar = array(
            'instance' => new B,
            'float' => -2.5,
            'int' => 4,
            'null' => null);
        array_multisort($ar, SORT_STRING);
        foreach($ar as $k=>$v) {
            echo $k;
        }
        ''')
        assert [self.space.str_w(s) for s in output] == \
            ['null', 'float', 'int', 'instance']
