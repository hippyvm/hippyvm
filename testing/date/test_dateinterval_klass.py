import pytest
from testing.test_interpreter import BaseTestInterpreter


class TestDateInterval(BaseTestInterpreter):

    def test_construct(self):
        output = self.run('''
            $di = new DateInterval('PT1111S');
            echo $di->y;
            echo $di->m;
            echo $di->d;
            echo $di->h;
            echo $di->i;
            echo $di->s;
        ''')

        assert [self.space.int_w(o) for o in output] == \
            [0, 0, 0, 0, 0, 1111]

        output = self.run('''
            $di = new DateInterval('P1D');
            echo $di->y;
            echo $di->m;
            echo $di->d;
            echo $di->h;
            echo $di->i;
            echo $di->s;
        ''')

        assert [self.space.int_w(o) for o in output] == \
            [0, 0, 1, 0, 0, 0]

        output = self.run('''
            $di = new DateInterval('P3Y6M4DT12H30M5S');
            echo $di->y;
            echo $di->m;
            echo $di->d;
            echo $di->h;
            echo $di->i;
            echo $di->s;
        ''')

        assert [self.space.int_w(o) for o in output] == \
            [3, 6, 4, 12, 30, 5]

        output = self.run('''
            $di = new DateInterval('P0Y0M1DT0H0M0S');
            echo $di->y;
            echo $di->m;
            echo $di->d;
            echo $di->h;
            echo $di->i;
            echo $di->s;
        ''')

        assert [self.space.int_w(o) for o in output] == \
            [0, 0, 1, 0, 0, 0]


    def test_create_from_date_string(self):
        output = self.run('''
            $di = DateInterval::createFromDateString('1 day');
            echo $di->y;
            echo $di->m;
            echo $di->d;
            echo $di->h;
            echo $di->i;
            echo $di->s;
        ''')

        assert [self.space.int_w(o) for o in output] == \
            [0, 0, 1, 0, 0, 0]

        output = self.run('''
            $di = DateInterval::createFromDateString('1 year + 1 day');
            echo $di->y;
            echo $di->m;
            echo $di->d;
            echo $di->h;
            echo $di->i;
            echo $di->s;
        ''')

        assert [self.space.int_w(o) for o in output] == \
            [1, 0, 1, 0, 0, 0]

        output = self.run('''
            $di = DateInterval::createFromDateString('3600 seconds');
            echo $di->y;
            echo $di->m;
            echo $di->d;
            echo $di->h;
            echo $di->i;
            echo $di->s;
        ''')

        assert [self.space.int_w(o) for o in output] == \
            [0, 0, 0, 0, 0, 3600]

    def test_format(self):

        output = self.run('''
            echo (new DateInterval('P2Y4DT6H8M'))->format('%d days');
            echo (new DateInterval('P2Y4DT6H8M'))->format('%h:%i:%s');
            echo (new DateInterval('P2Y4DT6H8M'))->format('%y %y %M');
            echo (new DateInterval('P2Y4DT6H8M'))->format('%m %D %d');
            echo (new DateInterval('P2Y4DT6H8M'))->format('%H %h');
            echo (new DateInterval('P2Y4DT6H8M'))->format('%I %i %S');
            echo (new DateInterval('P2Y4DT6H8M'))->format('%%%%%=');
            echo (new DateInterval('P2Y4DT6H8M'))->format('%%%=');
            echo (new DateInterval('P2Y4DT6H8M'))->format('%%=');
            echo (new DateInterval('P2Y4DT6H8M'))->format('%%');
            # echo (new DateInterval('P2Y4DT6H8M'))->format('x=%x');
        ''')

        assert self.space.str_w(output.pop(0)) == '4 days'
        assert self.space.str_w(output.pop(0)) == '6:8:0'
        assert self.space.str_w(output.pop(0)) == '2 2 00'
        assert self.space.str_w(output.pop(0)) == '0 04 4'
        assert self.space.str_w(output.pop(0)) == '06 6'
        assert self.space.str_w(output.pop(0)) == '08 8 00'
        assert self.space.str_w(output.pop(0)) == '%%%='
        assert self.space.str_w(output.pop(0)) == '%%='
        assert self.space.str_w(output.pop(0)) == '%='
        assert self.space.str_w(output.pop(0)) == '%'
