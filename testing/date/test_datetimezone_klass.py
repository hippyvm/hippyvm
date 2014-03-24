import pytest
from testing.test_interpreter import BaseTestInterpreter


class TestDateTimeZone(BaseTestInterpreter):

    def test_constructor(self):

        output = self.run('''
            $tz = new DateTimeZone('Pacific/Nauru');
            echo get_class($tz);
        ''')

        assert self.space.str_w(output[0]) == 'DateTimeZone'

    def test_get_name(self):
        output = self.run('''
            $tz = new DateTimeZone('Pacific/Nauru');
            echo $tz->getName();
        ''')
        assert self.space.str_w(output[0]) == 'Pacific/Nauru'

    def test_get_offset(self):
        output = self.run('''

            $dateTimeZoneTaipei = new DateTimeZone("Asia/Taipei");
            $dateTimeZoneJapan = new DateTimeZone("Asia/Tokyo");

            $dateTimeTaipei = new DateTime("now", $dateTimeZoneTaipei);
            $dateTimeJapan = new DateTime("now", $dateTimeZoneJapan);

            echo $dateTimeZoneJapan->getOffset($dateTimeTaipei);
            echo $dateTimeZoneJapan->getOffset($dateTimeJapan);
        ''')

        assert self.space.int_w(output.pop(0)) == 32400
        assert self.space.int_w(output.pop(0)) == 32400

    def test_list_abbreviations(self):
        output = self.run('''
            $tz = new DateTimeZone('Pacific/Nauru');
            echo count($tz->listAbbreviations());
        ''')
        assert self.space.int_w(output[0]) == 373

    def test_list_identifiers(self):
        output = self.run('''
            $tz = new DateTimeZone('Pacific/Nauru');
            echo count($tz->listIdentifiers(128));
            echo count($tz->listIdentifiers(DateTimeZone::EUROPE));
        ''')

        assert self.space.int_w(output.pop(0)) == 56
        assert self.space.int_w(output.pop(0)) == 56

    def test_consts(self):
        output = self.run('''
            echo DateTimeZone::ASIA;
        ''')
        assert self.space.int_w(output[0]) == 16

    def test_listI_ientifiers_constants(self):
        output = self.run('''
            $tz = new DateTimeZone('Pacific/Nauru');
            echo count($tz->listIdentifiers(DateTimeZone::PER_COUNTRY, 'PL'));
            echo count($tz->listIdentifiers(DateTimeZone::PER_COUNTRY, 'RU'));
        ''')
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 18

    def test_get_transition_1(self):

        pytest.xfail("broken implementation")

        output = self.run('''
            $timezone = new DateTimeZone("Europe/London");

            echo $timezone->getTransitions();
            echo $timezone->getTransitions(2120015000);

            echo $timezone->getTransitions(0);
            echo $timezone->getTransitions(0, 2140045200);
            echo $timezone->getTransitions(0, 2140045300);

            echo $timezone->getTransitions(2140045200);
            echo $timezone->getTransitions(2121901200);
        ''')

        assert len(output.pop(0).as_pair_list(self.space)) == 243
        assert len(output.pop(0).as_pair_list(self.space)) == 3

        assert len(output.pop(0).as_pair_list(self.space)) == 135
        assert len(output.pop(0).as_pair_list(self.space)) == 134
        assert len(output.pop(0).as_pair_list(self.space)) == 135

        assert len(output.pop(0).as_pair_list(self.space)) == 1
        assert len(output.pop(0).as_pair_list(self.space)) == 2


    def test_get_transition_2(self):
        pytest.xfail("broken implementation")

        output = self.run('''
            $timezone = new DateTimeZone("Europe/Prague");
            echo $timezone->getTransitions();
        ''')

        first = output[0].as_list_w()[0].as_dict()
        last = output[0].as_list_w()[-1].as_dict()

        assert self.space.int_w(first['ts']) == -9223372036854775808
        assert self.space.str_w(first['time']) == '-292277022657-01-27T08:29:52+0000'
        assert self.space.int_w(first['offset']) == 7200
        assert first['isdst'] == self.space.w_True
        assert self.space.str_w(first['abbr']) == 'CEST'

        assert self.space.int_w(last['ts']) == 2140045200
        assert self.space.str_w(last['time']) == '2037-10-25T01:00:00+0000'
        assert self.space.int_w(first['offset']) == 7200
        assert last['isdst'] == self.space.w_False
        assert self.space.str_w(last['abbr']) == 'CET'
