import pytest
from testing.test_interpreter import BaseTestInterpreter


class TestDateTime(BaseTestInterpreter):

    def test_constants(self):
        output = self.run('''
            echo DateTime::ATOM;
            echo DateTime::COOKIE;
            echo DateTime::ISO8601;
            echo DateTime::RFC822;
            echo DateTime::RFC850;
            echo DateTime::RFC1036;
            echo DateTime::RFC1123;
            echo DateTime::RFC2822;
            echo DateTime::RFC3339;
            echo DateTime::RSS;
            echo DateTime::W3C;
        ''')

        self.space.str_w(output.pop(0)) == "Y-m-d\TH:i:sP"
        self.space.str_w(output.pop(0)) == "l, d-M-y H:i:s T"
        self.space.str_w(output.pop(0)) == "Y-m-d\TH:i:sO"
        self.space.str_w(output.pop(0)) == "D, d M y H:i:s O"
        self.space.str_w(output.pop(0)) == "l, d-M-y H:i:s T"
        self.space.str_w(output.pop(0)) == "D, d M y H:i:s O"
        self.space.str_w(output.pop(0)) == "D, d M Y H:i:s O"
        self.space.str_w(output.pop(0)) == "D, d M Y H:i:s O"
        self.space.str_w(output.pop(0)) == "Y-m-d\TH:i:sP"
        self.space.str_w(output.pop(0)) == "D, d M Y H:i:s O"
        self.space.str_w(output.pop(0)) == "Y-m-d\TH:i:sP"

    def test_construct_1(self):
        output = self.run('''
            $tz = new DateTimeZone('Pacific/Nauru');

            echo (new DateTime('2000-01-01', $tz))->format('Y-m-d');
        ''')

        assert self.space.str_w(output.pop(0)) == '2000-01-01'

    def test_construct_2(self):
        output = self.run('''
            $tz = new DateTimeZone('Pacific/Nauru');
            try {
                new DateTime(array(), $tz);
            } catch (Exception $e) {
                echo $e->getMessage();
            }
        ''')

        assert self.space.str_w(output.pop(0)) == \
            'DateTime::__construct() expects parameter 1 to be string, array given'

    def test_construct_3(self):
        self.run('''
            $tz = new DateTimeZone('Pacific/Nauru');
            new DateTime(NULL, $tz);
            new DateTime(null, $tz);
            new DateTime('', $tz);
        ''')

    def test_construct_4(self):

        self.run('''
            date_default_timezone_set('Europe/London');

            new DateTime("2005-07-14 22:30:41", NULL);
            new DateTime("2005-07-14 22:30:41", null);
        ''')

    def test_construct_5(self):

        pytest.xfail("broken implementation")

        output = self.run('''

            date_default_timezone_set('Pacific/Nauru');

            $date = new DateTime("2005-07-14 22:30:41 Europe/London");
            echo $date->getTimezone()->getName();

            $date = new DateTime("2005-07-14 22:30:41 GMT");
            echo $date->getTimezone()->getName();

            $date = new DateTime("2005-07-14 22:30:41");
            echo $date->getTimezone()->getName();
        ''')

        assert self.space.str_w(output.pop(0)) == 'Europe/London'
        assert self.space.str_w(output.pop(0)) == 'GMT'
        assert self.space.str_w(output.pop(0)) == 'Pacific/Nauru'

    def test_format(self):
        output = self.run('''
            date_default_timezone_set("Europe/London");

            echo (new DateTime("2005-07-14 22:30:41"))->format("r");
            echo (new DateTime("2005-07-14 22:30:41"))->format("D-d");
            echo (new DateTime("2005-07-4 22:30:41"))->format("j-l");
            echo (new DateTime("2005-07-4 22:30:41"))->format("S-w");
            echo (new DateTime("2005-07-4 22:30:41"))->format("N-z");
            echo (new DateTime("2005-07-4 22:30:41"))->format("F-m");
            echo (new DateTime("2005-07-4 22:30:41"))->format("n-t");
            echo (new DateTime("2005-07-4 22:30:41"))->format("L-Y-y");
            echo (new DateTime("2005-07-4 22:30:41"))->format("G-L-Y-y");
            echo (new DateTime("2005-07-4 22:30:41"))->format("hello world");
            echo (new DateTime("2005-07-4 22:30:41"))->format("classWithoutToString");

        ''')

        assert self.space.str_w(output.pop(0)) == 'Thu, 14 Jul 2005 22:30:41 +0100'
        assert self.space.str_w(output.pop(0)) == 'Thu-14'
        assert self.space.str_w(output.pop(0)) == '4-Monday'
        assert self.space.str_w(output.pop(0)) == 'th-1'
        assert self.space.str_w(output.pop(0)) == '1-184'
        assert self.space.str_w(output.pop(0)) == 'July-07'
        assert self.space.str_w(output.pop(0)) == '7-31'
        assert self.space.str_w(output.pop(0)) == '0-2005-05'
        assert self.space.str_w(output.pop(0)) == '22-0-2005-05'
        assert self.space.str_w(output.pop(0)) == '10Europe/LondonMondayMonday2005 12005Mon, 04 Jul 2005 22:30:41 +0100Monday04'

    def test_create_from_format(self):

        pytest.xfail("check static function implementation")

        output = self.run('''
            $tz = new DateTimeZone('America/New_York');
            $format = 'Y-m-d H:i:s';
            $date = DateTime::createFromFormat($format, '2009-02-15 15:16:17', $tz);
            echo $date->format('Y-m-d H:i:s');
        ''')

        assert self.space.str_w(output.pop(0)) == '2009-02-15 15:16:17'

        output = self.run('''
            $tz = new DateTimeZone('America/New_York');
            $format = 'Y-m-!d H:i:s';
            $date = DateTime::createFromFormat($format, '2009-02-15 15:16:17', $tz);
            echo $date->format('Y-m-d H:i:s');
        ''')

        assert self.space.str_w(output.pop(0)) == '1970-01-15 15:16:17'

        output = self.run('''
            $tz = new DateTimeZone('America/New_York');
            $format = '!d';
            $date = DateTime::createFromFormat($format, '15', $tz);
            echo $date->format('Y-m-d H:i:s');
        ''')

        assert self.space.str_w(output.pop(0)) == '1970-01-15 00:00:00'

    def test_modify(self):

        output = self.run('''
            $tz = new DateTimeZone('Europe/London');
            $date = new DateTime('2006-12-12', $tz);

            $date->modify('+1 day');
            echo $date->format('Y-m-d');

            $date->modify('-1 day');
            echo $date->format('Y-m-d');

            $date->modify('+1 month');
            echo $date->format('Y-m-d');
        ''')

        assert self.space.str_w(output.pop(0)) == '2006-12-13'
        assert self.space.str_w(output.pop(0)) == '2006-12-12'
        assert self.space.str_w(output.pop(0)) == '2007-01-12'

    def test_get_timestamp(self):
        output = self.run('''
            $tz = new DateTimeZone('America/New_York');

            $date = new DateTime('2009-02-15 15:16:17', $tz);
            echo $date->getTimestamp();
        ''')

        assert self.space.str_w(output.pop(0)) == '1234728977'

    def test_set_timestamp(self):
        output = self.run('''
            $tz = new DateTimeZone('America/New_York');

            $date = new DateTime('2009-02-15 15:16:17', $tz);
            echo $date->format('U = Y-m-d');

            $date->setTimestamp(1171502725);
            echo $date->format('U = Y-m-d');
        ''')

        assert self.space.str_w(output.pop(0)) == '1234728977 = 2009-02-15'
        assert self.space.str_w(output.pop(0)) == '1171502725 = 2007-02-14'

    def test_set_timezone(self):

        output = self.run('''

            $date = new DateTime('2000-01-01', new DateTimeZone('Pacific/Nauru'));
            echo $date->format('Y-m-d H:i:sP');

            $date->setTimezone(new DateTimeZone('Pacific/Chatham'));
            echo $date->format('Y-m-d H:i:sP');

        ''')

        assert self.space.str_w(output.pop(0)) == '2000-01-01 00:00:00+12:00'
        assert self.space.str_w(output.pop(0)) == '2000-01-01 01:45:00+13:45'

    def test_get_timezone(self):

        output = self.run('''
            $date = new DateTime('2000-01-01', new DateTimeZone('Pacific/Nauru'));
            echo $date->getTimezone()->getName();

            $date->setTimezone(new DateTimeZone('UTC'));
            echo $date->getTimezone()->getName();
        ''')

        assert self.space.str_w(output.pop(0)) == 'Pacific/Nauru'
        assert self.space.str_w(output.pop(0)) == 'UTC'

    def test_set_date(self):
        output = self.run('''
            date_default_timezone_set("Europe/London");
            $date = new DateTime();
            $date->setDate(2001, 2, 3);
            echo $date->format('Y-m-d');
        ''')

        assert self.space.str_w(output.pop(0)) == '2001-02-03'

    def test_set_time(self):
        output = self.run('''
            date_default_timezone_set("Europe/London");
            $date = new DateTime('2001-01-01');

            $date->setTime(14, 55);
            echo $date->format('Y-m-d H:i:s');

            $date->setTime(14, 55, 24);
            echo $date->format('Y-m-d H:i:s');
        ''')

        assert self.space.str_w(output.pop(0)) == '2001-01-01 14:55:00'
        assert self.space.str_w(output.pop(0)) == '2001-01-01 14:55:24'

    def test_add_1(self):

        output = self.run('''
            $date = new DateTime('2000-01-01', new DateTimeZone('Pacific/Nauru'));
            $date->add(new DateInterval('P400D'));
            echo $date->format('Y-m-d');

            $date = new DateTime('2000-01-01', new DateTimeZone('Pacific/Nauru'));
            $date->add(new DateInterval('PT10H30S'));
            echo $date->format('Y-m-d H:i:s');

            $date = new DateTime('2000-01-01', new DateTimeZone('Pacific/Nauru'));
            $date->add(new DateInterval('P7Y5M4DT4H3M2S'));
            echo $date->format('Y-m-d H:i:s');
        ''')

        assert self.space.str_w(output.pop(0)) == '2001-02-04'
        assert self.space.str_w(output.pop(0)) == '2000-01-01 10:00:30'
        assert self.space.str_w(output.pop(0)) == '2007-06-05 04:03:02'

    def test_add_2(self):

        output = self.run('''
            date_default_timezone_set('America/New_York');

            $date = new DateTime('2010-11-06 18:38:28 EDT');
            $date->add(new DateInterval('P0Y0M0DT7H36M16S'));
            echo $date->format('Y-m-d H:i:s T');
        ''')

        assert self.space.str_w(output.pop(0)) == '2010-11-07 02:14:44 EDT'

        output = self.run('''
            date_default_timezone_set('America/New_York');

            $date = new DateTime('2010-11-07 01:59:59 EDT');
            $date->add(new DateInterval('P0Y0M0DT0H0M1S'));
            echo $date->format('Y-m-d H:i:s T');
        ''')

        assert self.space.str_w(output.pop(0)) == '2010-11-07 02:00:00 EDT'

    def test_add_3(self):

        output = self.run('''
            date_default_timezone_set('America/New_York');

            $interval = new DateInterval('P0Y0M0DT7H36M16S');
            $start = new DateTime('2010-11-06 18:38:28 EDT');
            $start->add($interval);

            echo $start->format('Y-m-d H:i:s T');
        ''')

        assert self.space.str_w(output.pop(0)) == '2010-11-07 02:14:44 EDT'

    def test_sub(self):

        output = self.run('''
            $date = new DateTime('2000-01-01', new DateTimeZone('Pacific/Nauru'));
            $date->sub(new DateInterval('P400D'));
            echo $date->format('Y-m-d');

            $date = new DateTime('2000-01-01', new DateTimeZone('Pacific/Nauru'));
            $date->sub(new DateInterval('PT10H30S'));
            echo $date->format('Y-m-d H:i:s');

            $date = new DateTime('2000-01-01', new DateTimeZone('Pacific/Nauru'));
            $date->sub(new DateInterval('P7Y5M4DT4H3M2S'));
            echo $date->format('Y-m-d H:i:s');
        ''')

        assert self.space.str_w(output.pop(0)) == '1998-11-27'
        assert self.space.str_w(output.pop(0)) == '1999-12-31 13:59:30'
        assert self.space.str_w(output.pop(0)) == '1992-07-27 19:56:58'

    def test_diff_1(self):

        output = self.run('''
            date_default_timezone_set("Europe/London");

            $datetime1 = new DateTime('2009-10-11');
            $datetime2 = new DateTime('2009-10-13');

            $interval = $datetime1->diff($datetime2);

            echo $interval->format('%d days');
            echo $interval->d;
        ''')

        assert self.space.str_w(output.pop(0)) == '2 days'
        assert self.space.int_w(output.pop(0)) == 2

        output = self.run('''
            date_default_timezone_set("Europe/London");

            $datetime2 = new DateTime('2009-10-11');
            $datetime1 = new DateTime('2000-10-13');

            $interval = $datetime1->diff($datetime2);

            echo $interval->format('%y years');
            echo $interval->y;
        ''')

        assert self.space.str_w(output.pop(0)) == '8 years'
        assert self.space.int_w(output.pop(0)) == 8

    def test_diff_2(self):
        output = self.run(
            '''
            date_default_timezone_set('America/New_York');

            $end = new DateTime;
            $end->setDate(333333, 1, 1);
            $end->setTime(16, 18, 02);

            $start = new DateTime;
            $start->setDate(-333333, 1, 1);
            $start->setTime(16, 18, 02);

            $interval = $end->diff($start);

            echo $interval->y;
        ''')

        assert self.space.int_w(output.pop(0)) == 666666

    def test_get_offset(self):

        pytest.xfail("in progress")

        output = self.run(
            '''
            $winter = new DateTime('2010-12-21', new DateTimeZone('America/New_York'));
            $summer = new DateTime('2008-06-21', new DateTimeZone('America/New_York'));

            echo $winter->getOffset();
            echo $summer->getOffset();
        ''')

        assert self.space.str_w(output.pop(0)) == '-18000'
        assert self.space.str_w(output.pop(0)) == '-14400'

        output = self.run(
            '''
            date_default_timezone_set('America/New_York');

            $summer = new DateTime('2008-06-21 EST');
            $winter = new DateTime('2010-12-21 EDT');

            echo $winter->getOffset();
            echo $summer->getOffset();
        ''')

        assert self.space.str_w(output.pop(0)) == '-14400'
        assert self.space.str_w(output.pop(0)) == '-18000'

        output = self.run(
            '''
            date_default_timezone_set('America/New_York');

            $winter = new DateTime('2010-12-21 -200');
            $summer = new DateTime('2008-06-21 +200');

            echo $winter->getOffset();
            echo $summer->getOffset();

        ''')

        assert self.space.str_w(output.pop(0)) == '-7200'
        assert self.space.str_w(output.pop(0)) == '7200'

    @pytest.mark.skipif("config.option.runappdirect")
    def test_var_dump(self):
        output = self.run("""
        date_default_timezone_set('America/New_York');
        var_dump(new DateTime('2010-12-21'));

        class X extends DateTime {}

        var_dump(new X('2010-12-21'));
        """)
        assert '(3)' in output[0]
        assert 'date' in output[0]
        assert 'timezone' in output[0]
        assert '(3)' in output[1]
        assert 'date' in output[1]
        assert 'timezone' in output[1]

    def test_set_iso_date(self):
        output = self.run("""
            date_default_timezone_set('America/New_York');
            $date = new DateTime();

            $date->setISODate(2008, 2);
            echo $date->format('Y-m-d');

            $date->setISODate(2008, 2, 7);
            echo $date->format('Y-m-d');
        """)

        assert self.space.str_w(output.pop(0)) == '2008-01-07'
        assert self.space.str_w(output.pop(0)) == '2008-01-13'
