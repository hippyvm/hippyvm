# -*- coding: utf-8 -*

import py
from testing.test_interpreter import BaseTestInterpreter, hippy_fail


class TestRegex(BaseTestInterpreter):
    def test_basic(self):
        output = self.run('''
        echo preg_match("/xyz/", "xyz");
        echo preg_match("/xxx/", "xyz");
        ''')
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 0

    def test_match_object(self):
        output = self.run('''
        $a = null;
        preg_match("/xy(z)/", "xyz", $a);
        echo $a;
        ''')
        assert output[0].dump() == "array('xyz', 'z')"

    def test_named_pattern(self):
        output = self.run('''
        $a = null;
        preg_match("/a(?P<foo>b)c/", "xabcy", $a);
        echo $a;
        ''')
        assert output[0].dump() == "array('abc', foo=>'b', 'b')"

    def test_offset_capture(self):
        output = self.run('''
        $a = null;
        preg_match("/a(b)c/", "xxxxxxxxxxabcyyy", $a, PREG_OFFSET_CAPTURE);
        echo $a;
        ''')
        assert output[0].dump() == "array(array('abc', 10), array('b', 11))"

    def test_offset_capture_named(self):
        output = self.run('''
        $a = null;
        preg_match("/a(?P<foo>b)c/", "xxxxxxxabcyyy", $a, PREG_OFFSET_CAPTURE);
        echo $a;
        ''')
        assert output[0].dump() == \
               "array(array('abc', 7), foo=>array('b', 8), array('b', 8))"

    def test_utf8_match(self):
        output = self.run('''
        $a = null;
        preg_match("/a(.)b/u", "xxxxaZbyyyy", $a);
        echo $a;
        preg_match("/a(.)b/u", "xxxxa\xc3\xa9byyyyyaZbyy", $a);
        echo $a;
        preg_match("/a(.)b/", "xxxxa\xc3\xa9byyyyyaZbyy", $a);
        echo $a;
        ''')
        assert output[0].dump() == "array('aZb', 'Z')"
        assert output[1].dump() == "array('a\xc3\xa9b', '\xc3\xa9')"
        assert output[2].dump() == "array('aZb', 'Z')"

    def test_match_all(self):
        output = self.run('''
        $a = null;
        preg_match_all("/ab+c/", "xxxabcyyyyyabbbc", $a);
        echo $a;
        ''')
        assert output[0].dump() == "array(array('abc', 'abbbc'))"

    def test_match_all_group(self):
        output = self.run('''
        $a = null;
        preg_match_all("/a(b+)c/", "xxxabcyyyyyabbbc", $a);
        echo $a;
        ''')
        assert output[0].dump() == \
               "array(array('abc', 'abbbc'), array('b', 'bbb'))"

    def test_match_all_named_group(self):
        output = self.run('''
        $a = null;
        preg_match_all("/a(?P<foo>b+)c/", "xxxabcyyyyyabbbc", $a);
        echo $a;
        ''')
        assert output[0].dump() == (
            "array(array('abc', 'abbbc'),"
            " foo=>array('b', 'bbb'),"
            " array('b', 'bbb'))")

    def test_match_all_setorder(self):
        output = self.run('''
        $a = null;
        preg_match_all("/ab+c/", "xxxabcyyyyyabbbc", $a, PREG_SET_ORDER);
        echo $a;
        ''')
        assert output[0].dump() == "array(array('abc'), array('abbbc'))"

    def test_match_all_setorder_group(self):
        output = self.run('''
        $a = null;
        preg_match_all("/a(b+)c/", "xxxabcyyyyyabbbc", $a, PREG_SET_ORDER);
        echo $a;
        ''')
        assert output[0].dump() == \
               "array(array('abc', 'b'), array('abbbc', 'bbb'))"

    def test_match_all_setorder_named_group(self):
        output = self.run('''
        $a = null;
        preg_match_all("/a(?P<foo>b+)c/", "xxxabcyyyyyabbbc", $a,
                       PREG_SET_ORDER);
        echo $a;
        ''')
        assert output[0].dump() == (
            "array(array('abc', foo=>'b', 'b'),"
            " array('abbbc', foo=>'bbb', 'bbb'))")

    def test_re_replace(self):
        output = self.run('''
        echo preg_replace("/xyz/", "x", "xyzaaxyz");
        ''')
        assert self.space.str_w(output[0]) == "xaax"

    def test_re_replace_limit_count(self):
        output = self.run('''
        $count = 0;
        echo preg_replace("/x/", "xb", "xaxa", 1, $count);
        echo $count;
        ''')
        assert self.space.str_w(output[0]) == "xbaxa"
        assert self.space.int_w(output[1]) == 1

    def test_re_replace_reference(self):
        output = self.run("""
        echo preg_replace('/a(x+)b/', 'c$1d$0e', 'yyaxxxbz');
        """)
        assert self.space.str_w(output[0]) == "yycxxxdaxxxbez"

    def test_re_replace_callback(self):
        output = self.run('''
        function callback($a) {
           return $a[0] . "3";
        }

        echo preg_replace_callback("/xyz/", "callback", "xyzaaxyz");
        ''')
        assert self.space.str_w(output[0]) == "xyz3aaxyz3"

    def test_re_replace_callback_limit_count(self):
        output = self.run('''
        function callback($a) {
           return $a[0] . "3";
        }
        $count = 0;
        echo preg_replace_callback("/x/", "callback", "xaxax", 2, $count);
        echo $count;
        ''')
        assert self.space.str_w(output[0]) == "x3ax3ax"
        assert self.space.int_w(output[1]) == 2

    def test_re_flags(self):
        output = self.run('''
        echo preg_match("/xyz/i", "XyZ");
        ''')
        assert self.space.int_w(output[0]) == 1

    def test_preg_quote(self):
        output = self.run('''
        echo preg_quote("-=x+*");
        ''')
        assert self.space.str_w(output[0]) == "\-\=x\+\*"

    def test_x_flag(self):
        output = self.run('''
        echo preg_match("/ x /x", "x");
        echo preg_match("/a[ ]b/x", "a b");
        echo preg_match("/a[ x]b/x", "a b");
        echo preg_match("/a# some comment
        b/x", "ab");
        echo preg_match("/a\ bc/x", "a bc");
        ''')
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 1
        assert self.space.int_w(output[2]) == 1
        assert self.space.int_w(output[3]) == 1
        assert self.space.int_w(output[4]) == 1

    def test_re_bug(self):
        output = self.run('''
        $m = array();
        echo preg_match("!^(.*\?)!", "http://localhost/", $m);
        ''')
        assert self.space.int_w(output[0]) == 0

    def test_re_bug_2(self):
        output = self.run('''
        echo preg_match("/\d\d|[a-zA-Z]{3,4}/", "Aug");
        echo preg_match("/00|[a-zA-Z]{3,4}/", "Aug");
        ''')
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 1

    @py.test.mark.skipif('config.option.runappdirect',
                         reason="confusion with ; in the middle")
    def test_re_match_all(self):
        output = self.run("""
        echo preg_match_all('/((?:(?:unsigned|struct)\s+)\w+)/S', "unsigned int xpto = 124; short a, b;");
        echo preg_match_all('/zend_parse_parameters(?:_ex\s*|\s*\([^,]+)/S', 'zend_parse_parameters( 0, "addd|s/", a, b, &c);');
        """)
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 1

    def test_re_split(self):
        output = self.run('''
        echo preg_split("/x/", "xyx");
        echo preg_split("/a(x)/", "axyax", -1, PREG_SPLIT_DELIM_CAPTURE);
        echo preg_split("/x/", "xyxzx", 4);
        echo preg_split("/x/", "xyxzx", 3);
        echo preg_split("/x/", "xyxzx", 2);
        echo preg_split("/x/", "xyxzx", 1);
        echo preg_split("/x/", "xyxzx", 0);
        ''')
        assert [self.space.str_w(x) for x in output[0].as_list_w()] == [
            "", "y", ""]
        assert [self.space.str_w(x) for x in output[1].as_list_w()] == [
            "", "x", "y", "x", ""]
        assert [self.space.str_w(x) for x in output[2].as_list_w()] == [
            "", "y", "z", ""]
        assert [self.space.str_w(x) for x in output[3].as_list_w()] == [
            "", "y", "zx"]
        assert [self.space.str_w(x) for x in output[4].as_list_w()] == [
            "", "yxzx"]
        assert [self.space.str_w(x) for x in output[5].as_list_w()] == [
            "xyxzx"]
        assert [self.space.str_w(x) for x in output[6].as_list_w()] == [
            "", "y", "z", ""]

    def test_re_compile_bug(self):
        output = self.run("""
        echo preg_match('/[^]]/', 'x');
        """)
        assert self.space.int_w(output[0]) == 1

    def test_groups_reference(self):
        output = self.run("""
        echo preg_match('/(xxx)\\1/', "xxxxxx");
        echo preg_match('/(xxx)\\1/', "xxxxx");
        """)
        assert [self.space.int_w(w_x) for w_x in output] == [1, 0]

    def test_re_compile_numeric_ranges(self):
        output = self.run("""
        echo preg_match('/\\x78/', 'x');
        echo preg_match('/\\x/', "\\x00");
        echo preg_match('/\\x7y/', "\\x07" . "y");
        echo preg_match('/\\xay/', "\\x0a" . "y");
        echo preg_match('/\\xAAy/', "\\xAA" . "y");
        echo preg_match('/\\170y/', "x" . "y");
        echo preg_match('/\\17y/', "\\017" . "y");
        echo preg_match('/\\0170y/', "\\017" . "0" . "y");
        echo preg_match('/[^][<>"\\x00-\\x20\\x7F]+/', '\\n');
        """)
        assert all([self.space.int_w(w_x) for w_x in output])

    def test_anchor(self):
        output = self.run("""
        echo preg_match('/123/A', 'x123');
        echo preg_match('/123/', 'x123');
        """)
        assert [self.space.int_w(w_x) for w_x in output] == [0, 1]

    def test_gcc_bugs(self):
        output = self.run("""
        $x = '/^((.+): In function [`\\'](\w+)\\':\\s+)?((?(1)([^:\\n]+)|[^:\\n]+))/';
        $y = "/p2/var/php_gcov/PHP_4_4/ext/ming/ming.c: In function `zif_swfbitmap_init':";
        echo preg_match_all($x, $y);
        $x = '/^((.+)(\\(\\.text\\+0x[[:xdigit:]]+\\)))/';
        $y = '/ext/ming/ming.o(.text+0x851):/';
        echo preg_match_all($x, $y);
        $x = '/^((.+)(\\(\\.text\\+0x[[:xdigit:]]+\\))?: In function [`\\'](\\w+)\\':\\s+)?((?(1)(?(3)[^:\\n]+|\\2)|[^:\\n]+)):(\\d+): (?:(error|warning):\\s+)?(.+)(?:\\s+\\5:(\\d+): (?:(error|warning):\\s+)?(.+))?/';
        $y = '\\n\\next/ming/ming.o(.text+0x851): In function `zif_ming_setSWFCompression\\':
/p2/var/php_gcov/PHP_5_2/ext/ming/ming.c:154: undefined reference to `Ming_setSWFCompression\\'';
        $m = "";
        echo preg_match_all($x, $y, $m, PREG_SET_ORDER);
        """)
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 1
        assert self.space.int_w(output[2]) == 1

    def test_multiline(self):
        output = self.run("""
        echo preg_match_all('/^a/m', "a\\na\\na");
        echo preg_match_all('/^a/', "a\\na\\na");
        echo preg_match_all('/a$/m', "a\\na\\na");
        echo preg_match_all('/a$/', "a\\na\\na");
        echo preg_match_all('/\Aa/m', "a\\na\\na");
        echo preg_match_all('/\Aa/', "a\\na\\na");
        echo preg_match_all('/a\z/m', "a\\na\\na");
        echo preg_match_all('/a\z/', "a\\na\\na");
        """)
        assert [self.space.int_w(w_x) for w_x in output] == [3, 1, 3, 1, 1,
                                                             1, 1, 1]

    def test_multiple_matches(self):
        output = self.run("""
        $m = null;
        echo preg_match_all('/^(a(b)c())?(?:x())?/', 'ab', $m, PREG_SET_ORDER);
        echo count($m[0]);
        echo preg_match_all('/^(a(b)c())?(?:x())?/', 'ab', $m);
        echo count($m);
        echo preg_match_all('/^(a(b)(c)?)? x/m', "\\n\\nab x", $m, PREG_SET_ORDER);
        echo count($m[0]);
        echo preg_match_all('/^((.+)(\\(\\.text\\+0x[[:xdigit:]]+\\))?: In function)?/m', "\\n/p2/var/php_gcov/PHP_4_4/ext/ming/ming.c: In function `zif_swfbitmap_init'", $m, PREG_SET_ORDER);
        echo count($m[0]);
        """)
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 1
        assert self.space.int_w(output[2]) == 1
        assert self.space.int_w(output[3]) == 5
        assert self.space.int_w(output[4]) == 1
        assert self.space.int_w(output[5]) == 3
        assert self.space.int_w(output[6]) == 2
        assert self.space.int_w(output[7]) == 1

    def test_unicode_basic(self):
        output = self.run("""
        echo preg_replace("/ą+/u", "aa", "ąą");
        """)
        assert self.space.str_w(output[0]) == "aa"
        py.test.skip('need to fix rpython')
        self.run("""
        echo preg_replace("/1\x85/u", "", "");
        """, ["Warning: preg_replace(): Compilation failed: invalid UTF-8 string at offset 1"])

    def test_unicode_in_set(self):
        output = self.run("""
        echo preg_match_all("/[ąać]+/", "ąaćasdqą");
        """)
        assert self.space.int_w(output[0]) == 2

    def test_replacement_with_groups(self):
        output = self.run("""
        echo preg_replace("/a(b)/", '${}', "abxxxababab");
        echo preg_replace("/a(b)/", '${abc}', "abxxxababab");
        echo preg_replace("/a(b)/", '${1}', "abxxxababab");
        echo preg_replace("/a(?P<abc>b)/", '${abc}', "ab");
        echo preg_replace("/a(b)/", '${1234}', "ab");
        """)
        assert self.space.str_w(output[0]) == "${}xxx${}${}${}"
        assert self.space.str_w(output[1]) == "${abc}xxx${abc}${abc}${abc}"
        assert self.space.str_w(output[2]) == "bxxxbbb"
        assert self.space.str_w(output[3]) == "${abc}"
        assert self.space.str_w(output[4]) == "${1234}"

    def test_viagra(self):
        output = self.run("""
        echo preg_match('~((V(I|1)(4|A)GR(4|A)))~i', 'VIAGRA');
        echo preg_match('~((V(I|1)(4|A)GR(4|A)))~i', 'Viagra');
        echo preg_match('~((V(I|1)(4|A)GR(4|A)))~i', 'v1agra');
        """)
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 1
        assert self.space.int_w(output[2]) == 1

    def test_unicode_code_point(self):
        output = self.run("""
        echo preg_match('/\\x{105}/u', "ą");
        echo preg_match('/\\x{105}/u', "ć");
        """)
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 0
        self.run("""
        preg_match('/\\x{105}/', '');
        """, ["Warning: preg_match(): Compilation failed: character value...too large at offset 6"])

    # those are known problems in the simplistic unicode implementation,
    # we have to write those tests and fix it one day

    def test_unicode_groups(self):
        pass

    def test_unicode_ignore_case(self):
        pass

    def test_unicode_categories(self):
        pass

    def test_replace_error_1(self):
        output = self.run('''
        echo preg_replace(12.3, array(), "");
        ''', ["Warning: preg_replace(): Parameter mismatch, pattern is "
              "a string while replacement is an array"])
        assert output[0].dump() == "false"

    def test_replace_subject_array(self):
        output = self.run('''
        echo preg_replace("/x/", "y", array("abxd", "zuzuzuz", "xxxx"));
        ''')
        assert output[0].dump() == "array('abyd', 'zuzuzuz', 'yyyy')"

    def test_replace_subject_hash(self):
        output = self.run('''
        echo preg_replace("/x/", "y", array(1=>"abxd", 0=>"zuzuzuz", "foo"=>"xxxx"));
        ''')
        assert output[0].dump() == "array(1=>'abyd', 0=>'zuzuzuz', foo=>'yyyy')"

    def test_filter_simple(self):
        output = self.run('''
        echo preg_filter("/x/", "y", "abxd");
        echo preg_filter("/x/", "y", "abyd");
        ''')
        assert output[0].dump() == "'abyd'"
        assert output[1].dump() == "NULL"

    def test_filter_subject_array(self):
        output = self.run('''
        echo preg_filter("/x/", "y", array("abxd", "zuzuzuz", "xxxx"));
        ''')
        assert output[0].dump() == "array('abyd', 2=>'yyyy')"

    def test_replace_regex_array(self):
        output = self.run('''
        echo preg_replace(array("/x/", "/yy/"), "L$0R", "abxcdyyef");
        echo preg_replace(array("/x/", "/yy/"), "L$1R", "abxcdyyef");
        echo preg_replace(array(1=>"/x/", "foo"=>"/yy/"), "L$0R", "abxcdyyef");
        echo preg_replace(array(1=>"/x/", "foo"=>"/yy/"), "L$0R", "zzzzz");
        ''')
        assert output[0].dump() == "'abLxRcdLyyRef'"
        assert output[1].dump() == "'abLRcdLRef'"
        assert output[2].dump() == "'abLxRcdLyyRef'"
        assert output[3].dump() == "'zzzzz'"

    def test_replace_regex_replace_array(self):
        output = self.run('''
        echo preg_replace(array("/x/","/yy/"), array("L$0R","2"), "abxcdyyef");
        ''')
        assert output[0].dump() == "'abLxRcd2ef'"

    def test_split_empty(self):
        output = self.run('''
        echo preg_split('/\d*/', 'ab2c3u');
        echo preg_split('/\d*/', 'ab2c3u', -1, PREG_SPLIT_NO_EMPTY);
        ''')
        assert output[0].dump() == "array('', 'a', 'b', '', 'c', '', 'u', '')"
        assert output[1].dump() == "array('a', 'b', 'c', 'u')"

    def test_match_all_offset_capture(self):
        output = self.run(r'''
        $m = null;
        preg_match_all('/\b/', "aa", $m, PREG_OFFSET_CAPTURE);
        echo $m;
        ''')
        assert output[0].dump() == "array(array(array('', 0), array('', 2)))"
