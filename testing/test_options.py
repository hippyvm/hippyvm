import py
import re
from testing.test_interpreter import BaseTestInterpreter
from testing.test_main import TestMain
from hippy.main import entry_point

class TestOptionsMain(TestMain):
    def test_version_compare(self, capfd):
        output = self.run('''<?php
        $versions = array(
        '1',
        '1.0',
        '1.01',
        '1.1',
        '1.10',
        '1.10b',
        '1.10.0',
        '-3.2.1',
        '1rc.0.2',
        'bullshit.rc.9.2beta',

         );

         foreach ($versions as $version) {
             if (isset($last)) {
                 $comp = version_compare($last, $version);
                 echo $comp;
             }
             $last = $version;
        }

        ?>''', capfd)
        assert output == "-1-10-11-11-11"

    def test_version_compare_with_cmp(self, capfd):
        output = self.run('''<?php
        $versions = array(
        '1',
        '1.0',
        '1.01',
        '1.1',
        '1.10',
        '1.10b',
        '1.10.0',
        '-3.2.1',
        '1rc.0.2',
        'bullshit.rc.9.2beta',

         );

        $co = array(
        '=',
        '==',
        'eq',
        '!=',
        '<>',
        'ne',
        '>',
        'gt',
        '<',
        'lt',
        '>=',
        'ge',
        '<=',
        'le',
        );

        foreach ($versions as $version) {
          if (isset($last)) {
            foreach ($co as $c) {
              $comp = version_compare($last, $version, $c);
              echo (int)$comp;
            }
          }
          $last = $version;
        }


        ?>''', capfd)

        assert output ==  "000111001100110001110011001111100000001111000111001100110001111100110000011100110011000111110011000001110011001100011111001100"


class TestOptionsFunc(BaseTestInterpreter):

    def test_get_cfg_var(self):
        php_version = "6.0"
        test_value = "test_value"

        space = self.space
        def setup_conf(interp):
            interp.config.ini.update({
                'php_version': space.wrap(php_version),
                'test_value': space.wrap(test_value),
            })

        output = self.run('''
        echo get_cfg_var('php_version');
        echo get_cfg_var('test_value');
        ''', extra_func=setup_conf)

        assert self.space.str_w(output[0]) == php_version
        assert self.space.str_w(output[1]) == test_value

    def test_get_cfg_var2(self):
        output = self.run('''
        echo get_cfg_var('');
        echo get_cfg_var(' ');
        echo get_cfg_var('non_existent_var');
        echo get_cfg_var(null);
        echo get_cfg_var(1);
        echo get_cfg_var(1.0);
        ''')

        assert all([o == self.space.w_False for o in output])

    def test_get_cfg_var3(self):

        with self.warnings() as w:
            output = self.run('''
            echo get_cfg_var(array(1));

            class Test {};
            echo get_cfg_var(new Test);
            ''')

        assert output[0] == self.space.w_Null
        assert output[1] == self.space.w_Null

        assert w[0] == 'Warning: get_cfg_var() ' +\
            'expects parameter 1 to be string, array given'

        assert w[1] == 'Warning: get_cfg_var() ' +\
        'expects parameter 1 to be string, object given'
