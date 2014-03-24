from testing.test_interpreter import BaseTestInterpreter


class TestDateFuncs(BaseTestInterpreter):

    def test_date_default_timezone_set(self):

        with self.warnings() as w:
            output = self.run("""
                echo date_default_timezone_get();
            """)

        assert self.space.str_w(output.pop(0)) == "UTC"

        assert w == ["Warning: date_default_timezone_get(): It is not safe to rely on the system's timezone settings. You are *required* to use the date.timezone setting or the date_default_timezone_set() function. In case you used any of those methods and you are still getting this warning, you most likely misspelled the timezone identifier. We selected the timezone 'UTC' for now, but please set date.timezone to select your timezone."]

        output = self.run("""
            date_default_timezone_set('America/New_York');
            echo date_default_timezone_get();
        """)

        assert self.space.str_w(output.pop(0)) == "America/New_York"

    def test_date(self):

        with self.warnings() as w:

            output = self.run("""
                echo date("M d Y H:i:s", 873612800);
            """)

        assert w == ["Warning: date(): It is not safe to rely on the system's timezone settings. You are *required* to use the date.timezone setting or the date_default_timezone_set() function. In case you used any of those methods and you are still getting this warning, you most likely misspelled the timezone identifier. We selected the timezone 'UTC' for now, but please set date.timezone to select your timezone."]

        output = self.run("""
            date_default_timezone_set('America/New_York');

            echo date("M d Y H:i:s", 883612800);
            echo date("M d Y H:i:s", 873612800);
        """)

        assert self.space.str_w(output.pop(0)) == "Dec 31 1997 19:00:00"
        assert self.space.str_w(output.pop(0)) == "Sep 07 1997 02:13:20"

    def test_idate(self):

        output = self.run("""
            date_default_timezone_set('America/New_York');

            echo idate("m", 883612800);
            echo idate("d", 873612800);
        """)

        assert self.space.int_w(output.pop(0)) == 12
        assert self.space.int_w(output.pop(0)) == 7

    def test_gmdate(self):

        output = self.run("""
            echo gmdate("M d Y H:i:s", 883612800);
            echo gmdate("M d Y H:i:s", 873612800);
        """)

        assert self.space.str_w(output.pop(0)) == "Jan 01 1998 00:00:00"
        assert self.space.str_w(output.pop(0)) == "Sep 07 1997 06:13:20"

    def test_time(self):

        output = self.run("""
            echo time();
        """)

        assert self.space.int_w(output.pop(0)) > 0

    def test_strtotime(self):

        output = self.run("""
            date_default_timezone_set('America/New_York');

            echo strtotime("10 September 2000 14:14:14");
            echo strtotime("2007-10-12 14:14:14");
        """)

        assert self.space.int_w(output.pop(0)) == 968609654
        assert self.space.int_w(output.pop(0)) == 1192212854

    def test_mktime(self):

        output = self.run("""
            date_default_timezone_set('America/New_York');

            echo mktime(0, 0, 0, 7, 1, 2000);
            echo mktime(1, 2, 3, 4, 5, 2006);
        """)

        assert self.space.int_w(output.pop(0)) == 962424000
        assert self.space.int_w(output.pop(0)) == 1144213323

    def test_gmmktime(self):

        output = self.run("""
            echo gmmktime(0, 0, 0, 7, 1, 2000);
            echo gmmktime(1, 2, 3, 4, 5, 2006);
        """)

        assert self.space.int_w(output.pop(0)) == 962409600
        assert self.space.int_w(output.pop(0)) == 1144198923

    def test_localtime(self):

        output = self.run("""
            date_default_timezone_set('UTC');

            $t = mktime(0,0,0, 6, 27, 2006);
            echo localtime($t);
        """)

        result = output.pop(0).as_rdict()

        assert self.space.int_w(result['0']) == 0
        assert self.space.int_w(result['1']) == 0
        assert self.space.int_w(result['2']) == 0
        assert self.space.int_w(result['3']) == 27
        assert self.space.int_w(result['4']) == 5
        assert self.space.int_w(result['5']) == 106
        assert self.space.int_w(result['6']) == 2
        assert self.space.int_w(result['7']) == 177
        assert self.space.int_w(result['8']) == 0

    def test_getdate(self):

        output = self.run("""
            date_default_timezone_set('UTC');

            $t = mktime(0,0,0, 6, 27, 2006);
            echo getdate($t);
        """)

        result = output.pop(0).as_rdict()

        assert self.space.int_w(result['0']) == 1151366400
        assert self.space.int_w(result['seconds']) == 0
        assert self.space.int_w(result['minutes']) == 0
        assert self.space.int_w(result['hours']) == 0
        assert self.space.int_w(result['mday']) == 27
        assert self.space.int_w(result['wday']) == 2
        assert self.space.int_w(result['mon']) == 6
        assert self.space.int_w(result['year']) == 2006
        assert self.space.int_w(result['yday']) == 177
        assert self.space.int_w(result['weekday']) == 0
        assert self.space.int_w(result['month']) == 0

    def test_timezone_open(self):

        output = self.run("""
            echo timezone_open('UTC')->getName();
            echo timezone_open('Europe/London')->getName();
        """)

        assert self.space.str_w(output.pop(0)) == "UTC"
        assert self.space.str_w(output.pop(0)) == "Europe/London"

        with self.warnings() as w:
            self.run("""
                timezone_open(1);
            """)

        assert w == ["Warning: timezone_open(): Unknown or bad timezone (1)"]

    def test_strftime(self):
        output = self.run("""
            date_default_timezone_set('UTC');
            echo strftime("%A %d %w %u", 0);
            echo strftime("%R %T %d %s", 0);
        """)

        assert self.space.str_w(output.pop(0)) == "Thursday 01 4 4"
        assert self.space.str_w(output.pop(0)) == "00:00 00:00:00 01 -3600"

    def test_gmstrftime(self):
        output = self.run("""
            echo gmstrftime("%A %d %w %u", 0);
            echo gmstrftime("%R %T %d %s", 0);
        """)

        assert self.space.str_w(output.pop(0)) == "Thursday 01 4 4"
        assert self.space.str_w(output.pop(0)) == "00:00 00:00:00 01 -3600"

    def test_gettimeofday(self):
        output = self.run("""
            date_default_timezone_set('UTC');
            echo gettimeofday();
        """)

        assert len(output[0].as_rdict()) == 4

    def test_timezone_name_get(self):
        output = self.run('''
            $tz = new DateTimeZone('Pacific/Nauru');
            echo timezone_name_get($tz);
        ''')

        assert self.space.str_w(output[0]) == 'Pacific/Nauru'


    def test_date_timezone_set(self):
        output = self.run('''
            $date = new DateTime('2000-01-01', new DateTimeZone('Pacific/Nauru'));
            echo $date->format('Y-m-d H:i:sP');

            date_timezone_set($date, new DateTimeZone('Pacific/Chatham'));
            echo $date->format('Y-m-d H:i:sP');

        ''')

        assert self.space.str_w(output.pop(0)) == '2000-01-01 00:00:00+12:00'
        assert self.space.str_w(output.pop(0)) == '2000-01-01 01:45:00+13:45'

    def test_data_diff(self):

        output = self.run('''
            date_default_timezone_set("Europe/London");

            $datetime1 = new DateTime('2009-10-11');
            $datetime2 = new DateTime('2009-10-13');

            $interval = date_diff($datetime1, $datetime2);

            echo $interval->format('%d days');
            echo $interval->d;
        ''')

        assert self.space.str_w(output.pop(0)) == '2 days'
        assert self.space.int_w(output.pop(0)) == 2

        output = self.run('''
            date_default_timezone_set("Europe/London");

            $datetime2 = new DateTime('2009-10-11');
            $datetime1 = new DateTime('2000-10-13');

            $interval = date_diff($datetime1, $datetime2);

            echo $interval->format('%y years');
            echo $interval->y;
        ''')

        assert self.space.str_w(output.pop(0)) == '8 years'
        assert self.space.int_w(output.pop(0)) == 8

    def test_date_sun_info(self):

        output = self.run('''
            date_default_timezone_set("Europe/London");
            $sun_info = date_sun_info(strtotime("2006-12-12"), 31.7667, 35.2333);

            foreach ($sun_info as $key => $val) {
                echo "$key: ". $val;
            }
        ''')

        assert self.space.str_w(output.pop(0)) == "sunrise: 1165897782"
        assert self.space.str_w(output.pop(0)) == "sunset: 1165934168"
        assert self.space.str_w(output.pop(0)) == "transit: 1165915975"
        assert self.space.str_w(output.pop(0)) == "civil_twilight_begin: 1165896176"
        assert self.space.str_w(output.pop(0)) == "civil_twilight_end: 1165935773"
        assert self.space.str_w(output.pop(0)) == "nautical_twilight_begin: 1165894353"
        assert self.space.str_w(output.pop(0)) == "nautical_twilight_end: 1165937597"
        assert self.space.str_w(output.pop(0)) == "astronomical_twilight_begin: 1165892570"
        assert self.space.str_w(output.pop(0)) == "astronomical_twilight_end: 1165939380"

    def test_date_sunrise(self):

        output = self.run('''
            date_default_timezone_set("Europe/London");

            echo date_sunrise(1390463446, SUNFUNCS_RET_TIMESTAMP, 38.4, -9, 90, 1);
            echo date_sunrise(1390463446, SUNFUNCS_RET_STRING, 38.4, -9, 90, 1);
            echo date_sunrise(1390463446, SUNFUNCS_RET_DOUBLE, 38.4, -9, 90, 1);
        ''')

        assert self.space.int_w(output.pop(0)) == 1390463446
        assert self.space.str_w(output.pop(0)) == "08:50"
        assert abs(self.space.float_w(output.pop(0)) - 8.846326666099895) < 0.000000000001

    def test_date_sunset(self):

        output = self.run('''
            date_default_timezone_set("Europe/London");

            echo date_sunset(1390463446, SUNFUNCS_RET_TIMESTAMP, 38.4, -9, 90, 1);
            echo date_sunset(1390463446, SUNFUNCS_RET_STRING, 38.4, -9, 90, 1);
            echo date_sunset(1390463446, SUNFUNCS_RET_DOUBLE, 38.4, -9, 90, 1);
        ''')

        assert self.space.int_w(output.pop(0)) == 1390499108
        assert self.space.str_w(output.pop(0)) == "18:45"
        assert abs(self.space.float_w(output.pop(0)) - 18.752409548077) < 0.000000000001

    def test_timezone_identifiers_list(self):

        output = self.run('''
            date_default_timezone_set("Europe/London");

            echo count(timezone_identifiers_list(128));
            echo count(timezone_identifiers_list(DateTimeZone::EUROPE));
        ''')

        assert self.space.int_w(output.pop(0)) == 56
        assert self.space.int_w(output.pop(0)) == 56

