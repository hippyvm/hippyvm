

from testing.test_interpreter import BaseTestInterpreter


class TestArray(BaseTestInterpreter):
    def test_max(self):
        output = self.run('''
        $max = array(6, 6, 4);
        $res = max(
	     array(0, 1, 2),
	     array(2, 3, 4),
	     array(6, 3, 4),
	     array(0, 0, 2),
	     array(6, 3, 4),
	     array(0, 0, 2),
	     $max,
	     array(0, 0, 2)
        );
        echo $res == $max;

        $res = max(
	     array(0, 1, 2),
	     array(2, 3, 4),
	     array(6, 3, 4),
	     array(0, 0, 2),
	     array(6, 3, 4),
	     array(0, 0, 2),
	     $max,
	     array(0, 0, 2)
        );
        echo $res == $max;

        $res = max(
	     array(0, 1, 2),
	     array(2, 3, 4),
	     $max,
	     array(6, 3, 4),
	     array(0, 0, 2),
	     array(6, 3, 4),
	     array(0, 0, 2),
	     array(0, 0, 2)
        );
        echo $res == $max;

        $res = max(
	     $max,
	     array(0, 1, 2),
	     array(2, 3, 4),
	     array(6, 3, 4),
	     array(0, 0, 2),
	     array(6, 3, 4),
	     array(0, 0, 2),
	     array(0, 0, 2)
        );
        echo $res == $max;

        $res = max(
	     array(0, 1, 2),
	     array(2, 3, 4),
	     array(6, 3, 4),
	     array(0, 0, 2),
	     array(6, 3, 4),
	     array(0, 0, 2),
	     array(0, 0, 2),
	     $max
        );
        echo $res == $max;

        echo max(1, 3, 5, 6, 7);  // 7
        echo max(array(2, 4, 5)); // 5

        echo max(0, 'hello');     // 0
        echo max('hello', 0);     // hello
        echo max(-1, 'hello');    // hello

        $a = max('string', array(2, 5, 7), 42);
        echo $a[2];

        echo max('7iuwmssuxue', 1); //returns 7iuwmssuxu
        echo max('-7suidha', -4); //returns -4
        echo max('sdihatewin7wduiw', 3); //returns 3

        $d1 = array(450,420,440,430,421);
        $d2 = array(460,410,410,430,413,375,256,411,656);
        $d3 = array(430,440,470,435,434,255,198);

        echo max(max($d1),max($d2),max($d3));

        echo max(array("", "t", "b"));
        echo max(array(1, true, false, true));

        echo max("", "t", "b");
        echo max(1, true, false, true);


        ''')
        space = self.space
        assert space.int_w(output[0]) == 1
        assert space.int_w(output[1]) == 1
        assert space.int_w(output[2]) == 1
        assert space.int_w(output[3]) == 1
        assert space.int_w(output[4]) == 1

        assert space.str_w(output[5]) == "7"
        assert space.str_w(output[6]) == "5"
        assert space.str_w(output[7]) == "0"
        assert space.str_w(output[8]) == "hello"
        assert space.str_w(output[9]) == "hello"

        assert space.int_w(output[10]) == 7

        assert space.str_w(output[11]) == "7iuwmssuxue"
        assert space.str_w(output[12]) == "-4"
        assert space.str_w(output[13]) == "3"
        assert space.str_w(output[14]) == "656"

        assert space.str_w(output[15]) == "t"
        assert space.str_w(output[16]) == "1"

        assert space.str_w(output[17]) == "t"
        assert space.str_w(output[18]) == "1"
