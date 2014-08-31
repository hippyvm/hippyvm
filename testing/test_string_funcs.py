import pytest, sys

from hippy.module.standard.strings.funcs import (unwrap_needle, intsign, rstrcmp, _split_word,
        _substr_window)
from hippy.objspace import ObjSpace

from testing.test_interpreter import BaseTestInterpreter


def _rec_unwrap(space, w_arr):
    dct = w_arr.as_dict()
    return dict((key, space.str_w(val) if not isinstance(val, str) else val)
        for key, val in dct.iteritems())


def _as_list(w_arr):
    space = ObjSpace()
    iter = space.create_iter(w_arr)
    result = []
    while not iter.done():
        _, w_val = iter.next_item(space)
        result.append(space.str_w(w_val))
    return result


@pytest.mark.parametrize(["input", "expected"],
        [(-5, -1), (0, 0), (1024, 1)])
def test_intsign(input, expected):
    assert intsign(input) == expected


@pytest.mark.parametrize(["args", "expected"], [
    [("a", "aaa"), -1],
    [("", "x"), -1],
    [("\x03", "\x00"), 1],
    [("abc", "xyz"), -1],
    [("abc", "abc"), 0],
    [("", ""), 0],
    ])
def test_rstrcmp(args, expected):
    assert rstrcmp(*args) == expected


@pytest.mark.parametrize(["n", "start", "length", "result"], [
        (3, 0, sys.maxint, (0, 3)),
        (3, -1, 1, (2, 3)),
        (3, -4, 1, (0, 1)),
        (3, 0, -1, (0, 2)),
        (3, 1, 3, (1, 3))])
def test_substr_window(n, start, length, result):
    (start, end) = _substr_window(n, start, length)
    assert 0 <= start <= end <= n
    assert (start, end) == result


class TestBuiltin(BaseTestInterpreter):

    @pytest.mark.parametrize(["input", "expected"], [
        ("97", "97"),
        (97, "a"),
        ("", ""),
        (False, "\x00"),
        (True, "\x01"),
        ])
    def test_unwrap_needle(self, input, expected):
        w_needle = self.space.wrap(input)
        assert unwrap_needle(self.space, w_needle) == expected

    def test_charmask(self):
        # test through addcslashes to get appdirect tests
        output = self.run('''
        echo addcslashes("abcd.", "a..acdc..d");
        ''')
        assert map(self.space.str_w, output) == [r"\ab\c\d."]

    def test_charmask_warn(self):
        with self.warnings() as w:
            output = self.run('''
            echo addcslashes("abcde.", "..acdc..d..e..");
            ''')
        assert map(self.space.str_w, output) == [r"\ab\c\d\e\."]
        assert w == [
                "Warning: addcslashes(): Invalid '..'-range, "
                        "no character to the left of '..'",
                "Warning: addcslashes(): Invalid '..'-range",
                "Warning: addcslashes(): Invalid '..'-range, "
                        "no character to the right of '..'",]
        with self.warnings() as w:
            output = self.run('''
            echo addcslashes("abcd.", "c..a");
            ''')
        assert map(self.space.str_w, output) == [r"\ab\cd\."]
        assert w == ["Warning: addcslashes(): Invalid '..'-range, "
                "'..'-range needs to be incrementing"]


    def test_addcslashes(self):
        output = self.run('''
        echo addcslashes("Abcd1\0\x7f\v", "\0..".chr(-1));
        echo addcslashes("Abcd1\0\x7f\v", "a..z");
        ''')
        assert map(self.space.str_w, output) == [r"\A\b\c\d\1\000\177\v",
                r"A\b\c\d1" + "\0\x7f\v"]

    def test_stripcslashes(self):
        source = (r'''
        echo stripcslashes('a\\a\\t\\c\\');
        echo stripcslashes('\\123\\x54');
        ''')
        output = self.run(source)
        assert map(self.space.str_w, output) == ["a\a\tc\\", "ST"]

    def test_addslashes(self):
        output = self.run("""
        echo addslashes('0ab');
        echo addslashes('\\\' " \\ \0');
        """)
        assert map(self.space.str_w, output) == ["0ab", r"""\' \" \\ \0"""]

    def test_stripslashes(self):
        # the strings PHP sees are `0ab`, `\a\x\`, `\' \" \\ \0`
        output = self.run(r'''
        echo stripslashes("0ab");
        echo stripslashes('\\a\\x\\');
        echo stripslashes('\\\' \" \\\\ \0');
        ''')
        assert map(self.space.str_w, output) == ["0ab", "ax", "' \" \ \0"]

    def test_bin2hex(self):
        output = self.run("echo bin2hex('A b-1');")
        assert self.space.str_w(output[0]) == "4120622d31"

    def test_hex2bin(self):
        output = self.run('''
        echo hex2bin('4120622d31');
        echo hex2bin('6578616d706c65206865782064617461');
        ''')
        assert self.space.str_w(output[0]) == "A b-1"
        assert self.space.str_w(output[1]) == "example hex data"

    def test_chr(self):
        output = self.run('''
        echo chr(97);
        echo chr("97");
        echo chr(97.8);
        echo chr(0);
        echo chr(1024);
        ''')
        assert [self.space.str_w(n) for n in output] == list("aaa\x00\x00")

    def test_chunk_split(self):
        output = self.run('''
        echo chunk_split("", 76, "xx");
        echo chunk_split("a", 2, "xx");
        echo chunk_split("aaa", 2, "xx");
        ''')
        assert map(self.space.str_w, output) == ['xx', 'axx', 'aaxxaxx']
        with self.warnings(["Warning: chunk_split(): "
            "Chunk length should be greater than zero"]):
            out, = self.run('''echo chunk_split("abc", 0);''')
        assert self.space.is_w(out, self.space.w_False)

    @pytest.mark.parametrize(['data', 'result'], [
        ('#86)C\n`\n', 'abc'),
('M86%A86%A86%A86%A86%A86%A86%A86%A86%A86%A86%A86%A86%A86%A86%A\n!80``\n`\n',
    "a"*46),
('M86%A86%A86%A86%A86%A86%A86%A86%A86%A86%A86%A86%A86%A86%A86%A\n`\n',
    "a"*45),
        ('#86)CX`X#86)C', 'abc'),  # bogus!
        ('#86)CX#86)C', 'abc'),  # bogus!
        (''.join(chr(ord(c) + 128) for c in '"86(`\n`\n'), 'ab'),  # bogus!
        ])
    def test_convert_uudecode(self, data, result):
        out, = self.run('echo convert_uudecode("%s");' % data)
        assert self.space.str_w(out) == result

    def test_convert_uudecode_warnings(self):
        out, = self.run('echo convert_uudecode("");')
        assert out == self.space.w_False
        with self.warnings(["Warning: convert_uudecode(): "
                "The given parameter is not a valid uuencoded string"]):
            out, = self.run('echo convert_uudecode("xbc");')
        assert out == self.space.w_False

    def test_convert_uuencode(self):
        output = self.run('''
        echo convert_uuencode("");
        echo convert_uuencode(str_repeat("a", 45));
        echo convert_uuencode(str_repeat("a", 46));
        echo convert_uuencode("ab");
        echo convert_uuencode("abc");
        ''')
        assert self.space.is_w(output[0], self.space.w_False)
        for out, res in zip(map(self.space.str_w, output[1:]), [
'M86%A86%A86%A86%A86%A86%A86%A86%A86%A86%A86%A86%A86%A86%A86%A\n`\n',
'M86%A86%A86%A86%A86%A86%A86%A86%A86%A86%A86%A86%A86%A86%A86%A\n!80``\n`\n',
                '"86(`\n`\n',
                '#86)C\n`\n']):
            assert out == res


    def test_explode(self):
        output = self.run('''
        echo explode("/", "//");
        echo explode("/", "//", 1);
        echo explode("/", "//", 0);
        echo explode("/", "a/b/c", -2);
        echo explode("//", "abc//b", 2);
        ''')
        assert [_rec_unwrap(self.space, out) for out in output] == [{'0':'', '1':'', '2':''},
                {'0':'//'}, {'0':'//'}, {'0':'a'}, {"0": "abc", "1": "b"}]
        with self.warnings() as w:
            output = self.run('echo explode("", "aaa");')
        assert self.space.is_w(output[0], self.space.w_False)
        assert w == ["Warning: explode(): Empty delimiter"]

    def test_implode(self):
        output = self.run('''
        echo implode(array(1, 2));
        echo implode(array(1, 2), " ");
        echo implode(" ", array(1, 2));
        echo join(" ", array(1, 2));
        echo implode(" ", array("x", 3, false, true, null, 1.3));
        ''')
        assert map(self.space.str_w, output) == ["12", "1 2", "1 2", "1 2",
                "x 3  1  1.3"]
        with self.warnings() as w:
            output = self.run('echo implode("foo");')
        assert self.space.is_w(output[0], self.space.w_Null)
        assert w == ["Warning: implode(): Argument must be an array"]
        with self.warnings() as w:
            output = self.run('echo implode("foo", "bar");')
        assert self.space.is_w(output[0], self.space.w_Null)
        assert w == ["Warning: implode(): Invalid arguments passed"]

    def test_lcfirst(self):
        output = self.run('''
        echo lcfirst('- Abc');
        echo lcfirst('ABC');
        echo lcfirst("");
        ''')
        assert [self.space.str_w(s) for s in output] == ['- Abc', 'aBC', '']

    def test_ord(self):
        output = self.run('''
        echo ord("a");
        echo ord("");
        echo ord(123);
        echo ord(False);
        ''')
        assert [self.space.int_w(i) for i in output] == [97, 0, 49, 0]

    @pytest.mark.skipif('config.option.runappdirect', reason='prints to stdout')
    def test_printf_1(self):
        pytest.skip("unsure about this test")
        output = self.run('''
        echo printf("%%a %d b\\n", 12);
        ''')
        assert self.space.str_w(output[0]) == '%a 12 b\n'
        assert self.space.int_w(output[1]) == len('%a 12 b\n')
        #
        output = self.run('echo printf();', [
            'Warning: printf() expects at least 1 parameter, 0 given'])
        assert self.space.is_w(output[0], self.space.w_False)
        #
        output = self.run('echo printf("foo %d bar");', [
            'Warning: printf(): Too few arguments'])
        assert self.space.is_w(output[0], self.space.w_False)
        #
        output = self.run('echo printf("foo %y bar %d baz", 42, 43);', [
            'Hippy warning: printf(): Unknown format char %y,'
            ' ignoring corresponding argument'])
        assert self.space.is_w(output[0], self.space.newstr("foo  bar 43 baz"))
        #
        output = self.run('echo printf("foo%");', [
            "Hippy warning: printf(): Trailing '%' character",
            'Warning: printf(): Too few arguments'])
        assert self.space.is_w(output[0], self.space.w_False)
        #
        output = self.run('echo printf("foo%", 42);', [
            "Hippy warning: printf(): Trailing '%' character, "
            "the next argument is going to be ignored"])
        assert self.space.is_w(output[0], self.space.newstr("foo"))
        #
        output = self.run('echo printf("foo", 1, 2, 3);', [
            'Hippy warning: printf(): Too many arguments passed, '
            'ignoring the 3 extra'])
        assert self.space.is_w(output[0], self.space.newstr("foo"))

    @pytest.mark.skipif('config.option.runappdirect', reason='prints to stdout')
    def test_sprintf(self):
        output = self.run('''
        echo sprintf("%%a %d b\\n", 12);
        echo sprintf("%x %X", 12, 13);
        echo sprintf("%03x %2X", 12, 13);
        ''')
        assert map(self.space.str_w, output) == ['%a 12 b\n', "c D",
                                                 "00c  D"]
        with self.warnings(['Warning: sprintf(): Too few arguments']):
            output = self.run('echo sprintf("foo %d bar");')
        assert self.space.is_w(output[0], self.space.w_False)

    @pytest.mark.skipif('config.option.runappdirect', reason='prints to stdout')
    def test_vprintf(self):
        output = self.run('''
        echo vprintf("%%a %d b\\n", array(12));
        echo vprintf("%%a %d b\\n", 12);
        ''')
        assert self.space.str_w(output[0]) == '%a 12 b\n'
        assert self.space.int_w(output[1]) == len('%a 12 b\n')
        assert self.space.str_w(output[2]) == '%a 12 b\n'
        assert self.space.int_w(output[3]) == len('%a 12 b\n')
        with self.warnings(['Warning: vprintf(): Too few arguments']):
            output = self.run('echo vprintf("foo %d bar", array());')
        assert self.space.is_w(output[0], self.space.w_False)

    @pytest.mark.skipif('config.option.runappdirect', reason='prints to stdout')
    def test_vsprintf(self):
        output = self.run('''
        echo vsprintf("%%a %d b\\n", array(12));
        ''')
        assert map(self.space.str_w, output) == ['%a 12 b\n']
        with self.warnings(['Warning: vsprintf(): Too few arguments']):
            output = self.run('echo vsprintf("foo %d bar", array());')
        assert self.space.is_w(output[0], self.space.w_False)

    def test_quotemeta(self):
        output = self.run('''
        echo quotemeta(".\\\\+123");
        ''')
        assert map(self.space.str_w, output) == [r'\.\\\+123']
        out, = self.run('echo quotemeta("");')
        assert self.space.is_w(out, self.space.w_False)

    def test_str_pad(self):
        output = self.run('''
        echo str_pad("xyz", 6);
        echo str_pad("xyz", 6, "01");
        echo str_pad("xyz", 6, "01", STR_PAD_LEFT);
        echo str_pad("xyz", 6, "01", STR_PAD_BOTH);
        echo str_pad("xyz", 3, "", 42);
        ''')
        assert map(self.space.str_w, output) == ['xyz   ',
                'xyz010', '010xyz', '0xyz01', 'xyz']
        with self.warnings() as w:
            output = self.run("echo str_pad('xyz', 6, '', 42);")
        assert self.space.is_w(output[0], self.space.w_Null)
        assert w == ["Warning: str_pad(): Padding string cannot be empty"]
        with self.warnings() as w:
            output = self.run("echo str_pad('xyz', 6, ' ', 42);")
        assert self.space.is_w(output[0], self.space.w_Null)
        assert w[0] == ("Warning: str_pad(): Padding type has to be "
                "STR_PAD_LEFT, STR_PAD_RIGHT, or STR_PAD_BOTH")

    def test_str_repeat(self):
        output = self.run('''
        $a = str_repeat("xyz", 2);
        echo $a;
        ''')
        assert self.space.str_w(output[0]) == 'xyzxyz'
        assert self.echo("str_repeat('a', 5)") == "aaaaa"
        assert self.echo("str_repeat('a', 5.9)") == "aaaaa"
        assert self.echo("str_repeat('a', '5')") == "aaaaa"
        assert self.echo("str_repeat('a', '+5')") == "aaaaa"
        assert self.echo("str_repeat('a', '5.1')") == "aaaaa"
        assert self.echo("str_repeat('a', '5.1')") == "aaaaa"
        assert self.echo("str_repeat('a', TRUE)") == "a"
        assert self.echo("str_repeat('a', FALSE)") == ""
        assert self.echo("str_repeat('a', NULL)") == ""

    def test_str_ireplace_simple(self):
        output = self.run('''
        echo str_ireplace("abA", "X", "ABabAb");
        echo str_ireplace("", "X", "aBa\x00ab");
        echo str_ireplace("abA", "X", "ABabAb", $count);
        echo $count;
        ''')
        assert map(self.space.str_w, output) == ["XbAb", "aBa\x00ab",
                "XbAb", "1"]

    def test_str_replace_simple(self):
        output = self.run('''
        echo str_replace("aba", "X", "ababab");
        echo str_replace("ab", "X", "aab");
        echo str_replace("", "X", "aba\x00ab");
        echo str_replace("aba", "X", "ababab", $count);
        echo $count;
        ''')
        assert map(self.space.str_w, output) == ["Xbab", "aX", "aba\x00ab",
                "Xbab", "1"]

    def test_str_replace_warn1(self):
        with self.warnings():
            output = self.run('''
            echo str_replace("aba", array("X"), "ababab");
            ''')
        assert self.space.str_w(output[0]) == "Arraybab"
        # XXX: missing Notice

    def test_str_replace_array1(self):
        output = self.run('''
        echo str_replace(array("aba", "Xb"), "X", "ababab", $count);
        echo $count;
        ''')
        assert self.space.str_w(output[0]) == "Xab"
        assert self.space.int_w(output[1]) == 2
        output = self.run('''
        echo str_replace(array("aba", "ab"), array("X"), "ababab", $count);
        echo $count;
        ''')
        assert self.space.str_w(output[0]) == "Xb"
        assert self.space.int_w(output[1]) == 2

    def test_str_replace_array2(self):
        output = self.run('''
        echo str_replace("aba", "X", array("ababab", "aXbaba"), $count);
        echo $count;
        ''')
        assert _as_list(output[0]) == ["Xbab", "aXbX"]
        assert self.space.int_w(output[1]) == 2

        output = self.run('''
        echo str_replace(array("aba", "Xb"), "X", array("ababab", "aXbaba"), $count);
        echo $count;
        ''')
        assert _as_list(output[0]) == ["Xab", "aXX"]
        assert self.space.int_w(output[1]) == 4

    def test_str_rot13(self):
        output = self.run('''
        echo str_rot13("PHp 5");
        echo str_rot13("CUc 5");
        ''')
        assert map(self.space.str_w, output) == ["CUc 5", "PHp 5"]

    def test_stripos(self):
        output = self.run('''
        echo stripos("Abcda", "a");
        echo stripos("AbcdA", "a", 1);
        echo stripos("abcdA", "a", "1");
        echo stripos("abcda", "A", TRUE);
        echo stripos("AbcdA", 97);
        echo stripos("Abcda", 97, 1);
        echo stripos("AbcdA", 256+97);
        echo stripos(123, "3");
        ''')
        assert [self.space.int_w(i) for i in output] == [0, 4, 4, 4, 0, 4, 0, 2]
        output = self.run('''
        echo stripos("abcda", "ae");
        echo stripos("abcda", "");''')
        assert all(self.space.is_w(out, self.space.w_False) for out in output)

    def test_stripos_warn(self):
        output = self.run("echo stripos('a', 'a', -1);", [
            "Warning: stripos(): Offset not contained in string"])
        assert self.space.is_w(output[0], self.space.w_False)

        output = self.run("echo stripos('a', 'a', 3);", [
            "Warning: stripos(): Offset not contained in string"])
        assert self.space.is_w(output[0], self.space.w_False)

        output = self.run("echo stripos('a', '', 1, 2);", [
            "Warning: stripos() expects at most 3 parameters, 4 given"])
        assert self.space.is_w(output[0], self.space.w_Null)

    def test_strcasecmp(self):
        output = self.run('''
        echo strcasecmp("AA", "aaaa");
        echo strcasecmp("AA", "abA");
        echo strcasecmp("Aba", "aA");
        echo strcasecmp("Aba", "Aba");
        echo strcasecmp(3, 25);
        echo strcasecmp("_", "A");
        ''')  # NB: 'A' < '_' < 'a'
        assert [intsign(self.space.int_w(i)) for i in output] == [
                -1, -1, 1, 0, 1, -1]

    def test_strcmp(self):
        output = self.run('''
        echo strcmp("aa", "aaaa");
        echo strcmp("aa", "aba");
        echo strcmp("aba", "aa");
        echo strcmp("aba", "aba");
        echo strcmp(3, 25);
        ''')
        assert [intsign(self.space.int_w(i)) for i in output] == [
                -1, -1, 1, 0, 1]

    def test_stristr(self):
        output = self.run('''
        echo stristr('one, two, THREE', 'th');
        echo stristr('one, two, THREE', 'th', true);
        echo stristr('AbC', 97);
        ''')
        assert [self.space.str_w(s) for s in output] == ['THREE',
                'one, two, ', 'AbC']
        output = self.run("echo stristr('abc', 'd');")
        assert self.space.is_w(output[0], self.space.w_False)
        output = self.run("echo stristr('a', '');", [
            "Warning: stristr(): Empty needle"])
        assert self.space.is_w(output[0], self.space.w_False)

    def test_strlen(self):
        output = self.run('''
        $a = "abc" . "def";
        echo strlen($a), strlen(12);
        ''')
        assert [self.space.int_w(i) for i in output] == [6, 2]

    def test_strncasecmp(self):
        output = self.run('''
        echo strncasecmp(123, 12, 2);
        echo strncasecmp("Abc", "Xyz", 1);
        echo strncasecmp("Abc", "", 0);
        echo strncasecmp("Abc", "ab", 10);
        ''')
        assert [intsign(self.space.int_w(i)) for i in output] == [0, -1, 0, 1]
        output = self.run('echo strncasecmp("abc", "xyz", -1);', [
            "Warning: Length must be greater than or equal to 0"])
        assert self.space.is_w(output[0], self.space.w_False)

    def test_strncmp(self):
        output = self.run('''
        echo strncmp(123, 12, 2);
        echo strncmp("abc", "xyz", 1);
        echo strncmp("abc", "", 0);
        echo strncmp("abc", "", 10);
        ''')
        assert [intsign(self.space.int_w(i)) for i in output] == [0, -1, 0, 1]
        output = self.run('echo strncmp("abc", "xyz", -1);', [
            "Warning: Length must be greater than or equal to 0"])
        assert self.space.is_w(output[0], self.space.w_False)

    def test_strpbrk(self):
        output = self.run('''
        echo strpbrk("Mummy", "mu");
        echo strpbrk("Mummy", "mmm");
        echo strpbrk("Mummy", "M");
        ''')
        assert [self.space.str_w(s) for s in output] == ['ummy', 'mmy', 'Mummy']
        output = self.run('''
        echo strpbrk("Mummy", "a");
        ''')
        assert all(self.space.is_w(out, self.space.w_False) for out in output)
        with self.warnings(
                ['Warning: strpbrk(): The character list cannot be empty']):
            output = self.run('echo strpbrk("Mummy", "");')
        assert self.space.is_w(output[0], self.space.w_False)

    @pytest.mark.skipif('config.option.runappdirect', reason='bug in PHP')
    def test_strpbrk_bug(self):
        output = self.run('''
        echo strpbrk("Mummy", "\x00M");
        echo strpbrk("Mummy", "M\x00");
        ''')
        assert [self.space.str_w(s) for s in output] == ['Mummy', 'Mummy']

    def test_strpos(self):
        output = self.run('''
        echo strpos("abcda", "a");
        echo strpos("abcda", "a", 1);
        echo strpos("abcda", "a", "1");
        echo strpos("abcda", "a", TRUE);
        echo strpos("abcda", 97);
        echo strpos("abcda", 97, 1);
        echo strpos("abcda", 256+97);
        echo strpos(123, "3");
        ''')
        assert [self.space.int_w(i) for i in output] == [0, 4, 4, 4, 0, 4, 0, 2]
        output = self.run('echo strpos("abcda", "ae");')
        assert self.space.is_w(output[0], self.space.w_False)

    def test_strpos_warn(self):
        output = self.run("echo strpos('a', 'a', -1);", [
            "Warning: strpos(): Offset not contained in string"])
        assert self.space.is_w(output[0], self.space.w_False)

        output = self.run("echo strpos('a', 'a', 3);", [
            "Warning: strpos(): Offset not contained in string"])
        assert self.space.is_w(output[0], self.space.w_False)

        output = self.run("echo strpos('a', '');", [
            "Warning: strpos(): Empty needle"])
        assert self.space.is_w(output[0], self.space.w_False)

        output = self.run("echo strpos('a', '', 1, 2);", [
            "Warning: strpos() expects at most 3 parameters, 4 given"])
        assert self.space.is_w(output[0], self.space.w_Null)

    def test_strrchr(self):
        output = self.run('''
        echo strrchr('one, two, three', ', four');
        echo strrchr('abcabc', 97);
        ''')
        assert [self.space.str_w(s) for s in output] == [', three', 'abc']
        output = self.run("echo strrchr('abc', 'd');")
        assert self.space.is_w(output[0], self.space.w_False)
        with self.warnings(["Hippy warning: strrchr(): "
                "Empty delimiter converted to NUL"]):
            output = self.run("echo strrchr('a\0b', '');")
        assert self.space.str_w(output[0]) == '\0b'


    def test_strrev(self):
        output = self.run('''
        echo strrev("abc");
        echo strrev(123);
        ''')
        assert [self.space.str_w(s) for s in output] == ["cba", "321"]

    def test_strripos(self):
        output = self.run('''
        echo strripos("AABCA", "a");
        echo strripos("AABCA", "a", 1);
        echo strripos("AABCA", "a", -1);
        echo strripos("AABCA", "a", "2");
        echo strripos("AABCA", "a", TRUE);
        echo strripos("AABCA", 97);
        echo strripos("AABCA", 256+97, -4);
        echo strripos(323, "3");
        ''')
        assert [self.space.int_w(i) for i in output] == [4, 4, 4, 4, 4, 4, 1, 2]
        output = self.run('''
        echo strripos("abcda", "ae");
        echo strripos("abcda", "");
        echo strripos("abcda", "b", 2);
        ''')
        assert all([self.space.is_w(out, self.space.w_False) for out in output])

    def test_strripos_warn(self):
        output = self.run("echo strripos('a', 'a', -2);", [
            "Warning: strripos(): Offset is greater than the length of haystack string"])
        assert self.space.is_w(output[0], self.space.w_False)

        output = self.run("echo strripos('a', 'a', 3);", [
            "Warning: strripos(): Offset is greater than the length of haystack string"])
        assert self.space.is_w(output[0], self.space.w_False)

        output = self.run("echo strripos('a', '', 1, 2);", [
            "Warning: strripos() expects at most 3 parameters, 4 given"])
        assert self.space.is_w(output[0], self.space.w_False)

    def test_strrpos(self):
        output = self.run('''
        echo strrpos("aabca", "a");
        echo strrpos("aabca", "a", 1);
        echo strrpos("aabca", "a", -1);
        echo strrpos("aabca", "a", "2");
        echo strrpos("aabca", "a", TRUE);
        echo strrpos("aabca", 97);
        echo strrpos("aabca", 256+97, -4);
        echo strrpos(323, "3");
        ''')
        assert [self.space.int_w(i) for i in output] == [4, 4, 4, 4, 4, 4, 1, 2]
        output = self.run('''
        echo strrpos("abcda", "ae");
        echo strrpos("abcda", "");
        echo strrpos("abcda", "b", 2);
        ''')
        assert all([self.space.is_w(out, self.space.w_False) for out in output])

    def test_strrpos_warn(self):
        output = self.run("echo strrpos('a', 'a', -2);", [
            "Warning: strrpos(): Offset is greater than the length of haystack string"])
        assert self.space.is_w(output[0], self.space.w_False)

        output = self.run("echo strrpos('a', 'a', 3);", [
            "Warning: strrpos(): Offset is greater than the length of haystack string"])
        assert self.space.is_w(output[0], self.space.w_False)

        output = self.run("echo strrpos('a', '', 1, 2);", [
            "Warning: strrpos() expects at most 3 parameters, 4 given"])
        assert self.space.is_w(output[0], self.space.w_False)

    def test_strspn(self):
        output = self.run('''
        echo strspn("abc", "cba");
        echo strspn("abc", "bcd");
        echo strspn("abc", "cba", -3, 2);
        echo strspn("abc", "cba", -2, -1);
        echo strspn("", "");
        ''')
        assert map(self.space.int_w, output) == [3, 0, 2, 1, 0]
        output = self.run('''
        echo strspn("abc", "cba", 4);
        ''')
        assert self.space.is_w(output[0], self.space.w_False)

    def test_strcspn(self):
        output = self.run('''
        echo strcspn("abc", "def");
        echo strcspn("abc", "xya");
        echo strcspn("abc", "def", -3, 2);
        echo strcspn("abc", "def", -2, -1);
        echo strcspn("", "");
        echo strcspn("abc\\0def\\0", "");
        ''')
        assert map(self.space.int_w, output) == [3, 0, 2, 1, 0, 3]
        output = self.run('''
        echo strcspn("abc", "def", 4);
        ''')
        assert self.space.is_w(output[0], self.space.w_False)

    def test_strstr(self):
        output = self.run('''
        echo strstr('name@ex.com', '@');
        echo strstr('name@ex.com', '@', false);
        echo strstr('name@ex.com', '@', true);
        echo strstr('name@ex.com', 'n', true);
        echo strstr('abc123', 97);
        echo strchr('name@ex.com', '@');
        ''')
        assert [self.space.str_w(s) for s in output] == [
                '@ex.com', '@ex.com', 'name', '', 'abc123', '@ex.com']

        output = self.run('''
        echo strstr("abcda", "ae");
        ''')
        assert all([self.space.is_w(out, self.space.w_False) for out in output])

        output = self.run('''echo strstr('abc', '');''', [
            "Warning: strstr(): Empty needle"])
        assert self.space.is_w(output[0], self.space.w_False)

    def test_strtr(self):
        output = self.run('''
        echo strtr('', 'abc', 'def');
        echo strtr('xyba', 'abc', 'def');
        ''')
        assert map(self.space.str_w, output) == ['', 'xyed']

    def test_strtr_array(self):
        output = self.run('''
        echo strtr("hello hi", array("h" => "x", "hello" => "y", "hi" => "z"));
        ''')
        assert map(self.space.str_w, output) == ["y z"]
        output = self.run('''
        echo strtr("hello hi", array("h" => "x", "hello" => "y", "" => "z"));
        ''')
        assert self.space.is_w(output[0], self.space.w_False)
        with self.warnings() as w:
            output = self.run("echo strtr('abc', 'def');")
        assert self.space.is_w(output[0], self.space.w_False)
        assert w == ["Warning: strtr(): The second argument is not an array"]

    def test_substr_compare(self):
        output = self.run('''
        echo substr_compare("abcde", "bc", 1);
        echo substr_compare("abcde", "bc", 1, 2);
        echo substr_compare("abcde", "de", -2, 2);
        echo substr_compare("abcde", "bcg", 1, 2);
        echo substr_compare("abcde", "BC", 1, 2, true);
        echo substr_compare("abcde", "bc", 1, 3);
        echo substr_compare("abcde", "cd", 1, 2);
        echo substr_compare("abcde", "abcdef", -10, 10);
        ''')
        assert [intsign(self.space.int_w(i)) for i in output] == [
                1, 0, 0, 0, 0, 1, -1, -1]

    def test_substr_compare_warn(self):
        with self.warnings(3 * ["Warning: substr_compare(): "
                "The start position cannot exceed initial string length"]):
            output = self.run('''
            echo substr_compare('', '', 0);
            echo substr_compare('', '', -1);
            echo substr_compare('abc', 'abc', 3);
            ''')
        assert all(self.space.is_w(o, self.space.w_False) for o in output)

        with self.warnings(["Warning: substr_compare(): "
                "The length must be greater than zero"]):
            output = self.run("echo substr_compare('abc', 'abc', 0, 0);")
        assert self.space.is_w(output[0], self.space.w_False)

        with self.warnings(["Warning: substr_compare() "
                "expects parameter 1 to be string, array given"]):
            output = self.run("echo substr_compare(array(), 'abc', 0);")
        assert self.space.is_w(output[0], self.space.w_False)

    def test_substr_count(self):
        output = self.run('''
        echo substr_count('', 'a');
        echo substr_count("ababc", "ab");
        echo substr_count("ababc", "ab", 1);
        echo substr_count("ababc", "ab", 5);
        echo substr_count("ababc", "ab", 1, 2);
        echo substr_count("ababababa", "aba");
        ''')
        assert [self.space.int_w(i) for i in output] == [0, 2, 1, 0, 0, 2]

    def test_substr_count_warn(self):
        output = self.run("echo substr_count('', '');", [
            "Warning: substr_count(): Empty substring"])
        assert self.space.is_w(output[0], self.space.w_False)

        output = self.run("echo substr_count('ababc', 'ab', -1);", [
            "Warning: substr_count(): Offset should be greater than or equal to 0"])
        assert self.space.is_w(output[0], self.space.w_False)

        output = self.run("echo substr_count('ababc', 'ab', 6);", [
            "Warning: substr_count(): Offset value 6 exceeds string length"])
        assert self.space.is_w(output[0], self.space.w_False)

        output = self.run("echo substr_count('ababc', 'ab', 0, 0);", [
            "Warning: substr_count(): Length should be greater than 0"])
        assert self.space.is_w(output[0], self.space.w_False)

        output = self.run("echo substr_count('ababc', 'ab', 0, 6);", [
            "Warning: substr_count(): Length value 6 exceeds string length"])
        assert self.space.is_w(output[0], self.space.w_False)

    def test_substr_replace_simple(self):
        output = self.run('''
        echo substr_replace("abcde", "123", 0);
        echo substr_replace("abcde", "123", 3);
        echo substr_replace("abcde", "123", 5);
        echo substr_replace("abcde", "123", -3);
        echo substr_replace("abcde", "123", -5);
        echo substr_replace("abcde", "123", 3, 1);
        echo substr_replace("abcde", "123", 3, -1);
        echo substr_replace("abcde", "123", 3, -3);
        echo substr_replace("abcde", array("123", "x"), 3, -3);
        echo substr_replace("abcde", array(), 3, -3);
        ''')
        assert map(self.space.str_w, output) == ['123', 'abc123', 'abcde123',
                'ab123', '123', 'abc123e', 'abc123e', 'abc123de', 'abc123de',
                'abcde']

    def test_substr_replace_array(self):
        output = self.run('''
        echo substr_replace(array("abc", "de", "fg"), "x", 1);
        echo substr_replace(array("abc", "de", "fg"), array("x", "y"), 1);
        echo substr_replace(array("abc", "de", "fg"), "x", array(0, 1));
        echo substr_replace(array("abc", "de", "fg"), array("x", "y"), 1, 1);
        echo substr_replace(array("abc", "de", "fg"), array("x", "y"), 1, array(0, 1));
        ''')
        assert map(_as_list, output) == [["ax", "dx", "fx"],
                ["ax", "dy", "f"],
                ["x", "dx", "x"],
                ["axc", "dy", "f"],
                ["axbc", "dy", "f"]]


    def test_substr_replace_warn(self):
        with self.warnings(["Warning: substr_replace(): "
                "'from' and 'len' should have the same number of elements"]):
            output = self.run('''
            echo substr_replace("abcde", "123", array(0), array(1, 2));
            ''')
        assert self.space.str_w(output[0]) == "abcde"

        with self.warnings(["Warning: substr_replace(): "
                "Functionality of 'from' and 'len' as arrays is not implemented"]):
            output = self.run('''
            echo substr_replace("abcde", "123", array(0), array(2));
            ''')
        assert self.space.str_w(output[0]) == "abcde"

        with self.warnings(["Warning: substr_replace(): "
                "'from' and 'len' should be of same type - numerical or array "]):
            output = self.run('''
            echo substr_replace("abcde", "123", array(0), 1);
            ''')
        assert self.space.str_w(output[0]) == "abcde"


    @pytest.mark.parametrize(['args', 'result'], [
        ['$a, -99', 'foobar'], ['$a, -3', 'bar'], ['$a, -2', 'ar'],
        ['$a, -1', 'r'], ['$a, 0', 'foobar'], ['$a, 1', 'oobar'],
        ['$a, 2', 'obar'], ['$a, 3', 'bar'], ['$a, 4', 'ar'],
        ['$a, 99', False],
        ['$a, 2.9', 'obar'], ['$a, -2.9', 'ar'],
        ['$a, "4"', 'ar'], ['$a, "-2"', 'ar'],
        ['$a, 2, 1', 'o'], ['$a, 2, 3', 'oba'], ['$a, 2, 9', 'obar'],
        ['$a, -2, 1', 'a'], ['$a, -2, 3', 'ar'],
        ['$a, -99, 2', 'fo'],
        ['$a, 2, 0', ''],
        ['$a, 2, -1', 'oba'],
        ['$a, 2, -4', ''], ['$a, 2, -5', False],
        ['$a, 5, -1', ''], ['$a, 5, -2', False],
        ['$a, 6, 0', False], ['$a, 6, -1', False], ['$a, 6, 1', False],
        ['$a, -55, 54', 'foobar'], ['$a, -55, 56', 'foobar'],
        ['$a, -55, NULL', ''], ['$a, 2, NULL', ''],
        ['$a, 6, NULL', False],])
    def test_substr(self, args, result):
        output = self.run('''
        $a = "foobar";
        echo substr(%s);
        ''' % args)[0]
        assert output.tp == getattr(self.space, 'tp_' + type(result).__name__)
        assert self.space.str_w(output) == self.space.str_w(
                                                    self.space.wrap(result))

    @pytest.mark.parametrize(['args', 'result', 'warning'], [
        ['$a, INF', 'foobar', 'value INF overflows and is returned as 0'],
        ['$a, -INF', 'foobar', 'value -INF overflows and is returned as 0'],
        ['$a, NAN', 'foobar', 'NaN is returned as %d' % (-sys.maxint - 1)],
        ['$a, 2, INF', '', 'value INF overflows and is returned as 0'],
        ['$a, 2, NAN', False, 'NaN is returned as %d' % (-sys.maxint - 1)],])
    def test_substr_warnings(self, args, result, warning):
        with self.warnings(['Hippy warning: cast float to integer: ' + warning]):
            output = self.run('''
            $a = "foobar";
            echo substr(%s);
            ''' % args)[0]
        assert output.tp == getattr(self.space, 'tp_' + type(result).__name__)
        assert self.space.str_w(output) == self.space.str_w(
                                                    self.space.wrap(result))


    def test_trim(self):
        output = self.run('''
        echo trim('\0 \t');
        echo trim('');
        echo trim('abcd', 'bad');
        echo trim(3152, 123);
        echo trim("xAyXb", "a..z");
        ''')
        assert map(self.space.str_w, output) == ['', '', 'c', '5', 'AyX']

    def test_ltrim(self):
        output = self.run('''
        echo ltrim(" abc ");
        echo ltrim("xAyXb", "a..z");
        ''')
        assert map(self.space.str_w, output) == ['abc ', 'AyXb']

    def test_rtrim(self):
        output = self.run('''
        echo rtrim(" abc ");
        echo chop(" abc ");
        echo rtrim("xAyXb", "a..z");
        ''')
        assert map(self.space.str_w, output) == [' abc', ' abc', 'xAyX']

    def test_ucfirst(self):
        output = self.run('''
        echo ucfirst('abc');
        echo ucfirst('- abc');
        echo ucfirst('ABC');
        echo ucfirst("");
        ''')
        assert [self.space.str_w(s) for s in output] == [
                'Abc', '- abc', 'ABC', '']

    def test_ucwords(self):
        output = self.run('''
        echo ucwords('abc d-e_f');
        echo ucwords('- abc');
        echo ucwords('abc  def');
        ''')
        assert [self.space.str_w(s) for s in output] == ['Abc D-e_f', '- Abc',
                'Abc  Def']

    def test_split_word(self):
        assert _split_word('abab', 2) == ['ab', 'ab']
        assert _split_word('ababa', 2) == ['ab', 'ab', 'a']

    @pytest.mark.skipif('config.option.runappdirect',
            reason='linebreaks in result')
    def test_wordwrap(self):
        output = self.run('''
        $text = "The quick brown fox jumped over the lazy dog.";
        $newtext = wordwrap($text, 20, "<br />\n");
        echo $newtext;
        ''')
        assert map(self.space.str_w, output) == ['''\
The quick brown fox<br />
jumped over the lazy<br />
dog.''']

        output = self.run('''
        $text = "A very loooooong woooooooooooord.";
        $newtext = wordwrap($text, 8, "\n", true);
        echo $newtext;
        ''')
        assert map(self.space.str_w, output) == ['''\
A very
loooooon
g
wooooooo
ooooord.''']
        output = self.run('echo wordwrap("", 0, "", true);')
        assert self.space.str_w(output[0]) == ''
        output = self.run('''
        $text = "A very loooooong woooooooooooord.";
        $newtext = wordwrap($text, 8, "\n");
        echo $newtext;
        ''')
        assert self.space.str_w(output[0]) == (
                "A very\nloooooong\nwoooooooooooord.")

        with self.warnings() as w:
            output = self.run("echo wordwrap('abcd', 8, '');")
        assert self.space.is_w(output[0], self.space.w_False)
        assert w == [('Warning: wordwrap(): Break string cannot be empty')]

        with self.warnings() as w:
            output = self.run("echo wordwrap('abcd', 0, '\n', true);")
        assert self.space.is_w(output[0], self.space.w_False)
        assert w == ["Warning: wordwrap(): Can't force cut when width is zero"]

    def test_htmlreplace(self):
        output = self.run('''
        echo htmlspecialchars("<xyz>");
        echo htmlspecialchars("3&");
        echo htmlspecialchars("3&", 2, "UTF-8", false);
        ''')
        assert [self.space.str_w(w_v) for w_v in output] == [
            '&lt;xyz&gt;', '3&amp;', '3&',
        ]

    def test_strnatcmp1(self):
        output = self.run('''
        echo strnatcmp("aBc", "abc");
        echo strnatcmp("img12.png", "img10.png");
        echo strnatcmp("img12.png", "iMg10.png");
        echo strnatcmp("a    5", "a              5");
        echo strnatcmp("A01", "A01");
        echo strnatcmp("A01", "a1");
        echo strnatcmp("A01", "b10");
        echo strnatcmp("A01", "a01");
        echo strnatcmp("A01", "b01");

        echo strnatcmp("a1", "A01");
        echo strnatcmp("a1", "a1");
        echo strnatcmp("a1", "b10");
        echo strnatcmp("a1", "a01");
        echo strnatcmp("a1", "b01");

        echo strnatcmp("b10", "A01");
        echo strnatcmp("b10", "a1");
        echo strnatcmp("b10", "b10");
        echo strnatcmp("b10", "a01");
        echo strnatcmp("b10", "b01");

        echo strnatcmp("a01", "A01");
        echo strnatcmp("a01", "a1");
        echo strnatcmp("a01", "b10");
        echo strnatcmp("a01", "a01");
        echo strnatcmp("a01", "b01");

        echo strnatcmp("b01", "A01");
        echo strnatcmp("b01", "a1");
        echo strnatcmp("b01", "b10");
        echo strnatcmp("b01", "a01");
        echo strnatcmp("b01", "b01");

        echo strnatcmp("a5", "a            5");
        ''')

        assert [self.space.int_w(w_v) for w_v in output] == [
            -1, 1, 1, 0, 0, -1, -1, -1, -1,
            1, 0, -1, 1, -1, 1, 1, 0, 1, 1,
            1, -1, -1, 0, -1, 1, 1, -1, 1, 0, 0
        ]

    def test_strnatcasecmp1(self):
        output = self.run('''
        echo strnatcasecmp("aBc", "abc");
        echo strnatcasecmp("img12.png", "img10.png");
        echo strnatcasecmp("img12.png", "iMg10.png");
        echo strnatcasecmp("a    5", "a              5");

        echo strnatcasecmp("A01", "A01");
        echo strnatcasecmp("A01", "a1");
        echo strnatcasecmp("A01", "b10");
        echo strnatcasecmp("A01", "a01");
        echo strnatcasecmp("A01", "b01");

        echo strnatcasecmp("a1", "A01");
        echo strnatcasecmp("a1", "a1");
        echo strnatcasecmp("a1", "b10");
        echo strnatcasecmp("a1", "a01");
        echo strnatcasecmp("a1", "b01");

        echo strnatcasecmp("b10", "A01");
        echo strnatcasecmp("b10", "a1");
        echo strnatcasecmp("b10", "b10");
        echo strnatcasecmp("b10", "a01");
        echo strnatcasecmp("b10", "b01");

        echo strnatcasecmp("a01", "A01");
        echo strnatcasecmp("a01", "a1");
        echo strnatcasecmp("a01", "b10");
        echo strnatcasecmp("a01", "a01");
        echo strnatcasecmp("a01", "b01");

        echo strnatcasecmp("b01", "A01");
        echo strnatcasecmp("b01", "a1");
        echo strnatcasecmp("b01", "b10");
        echo strnatcasecmp("b01", "a01");
        echo strnatcasecmp("b01", "b01");

        ''')
        assert [self.space.int_w(w_v) for w_v in output] == [
            0, 1, 1, 0, 0, -1, -1, 0, -1, 1, 0, -1,
            1, -1, 1, 1, 0, 1, 1, 0, -1, -1, 0, -1,
            1, 1, -1, 1, 0
        ]

    def test_strnatcasecmp_white(self):
        output = self.run('''
        echo strnatcasecmp(" ", "       ");
        echo strnatcasecmp("\t", " \t");
        echo strnatcasecmp("\n", "\t");
        echo strnatcasecmp("\n ", "\t");
        echo strnatcasecmp(NULL, "");
        echo strnatcasecmp("", NULL);

        echo strnatcasecmp(" ", "\f");
        echo strnatcasecmp(" ", "\n");
        echo strnatcasecmp(" ", "\t");
        echo strnatcasecmp(" ", "\v");


        ''')
        assert [self.space.int_w(w_v) for w_v in output] == [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        ]

    def test_strnatcasecmp_zero(self):
        output = self.run('''
        echo strnatcasecmp("0", "00");
        echo strnatcasecmp("000011", "0011");
        echo strnatcasecmp("0001", "03");
        echo strnatcasecmp("01", "00011");
        echo strnatcasecmp("05", "00008");


        ''')
        assert [self.space.int_w(w_v) for w_v in output] == [
            0, 0, -1, -1, -1
        ]

    def test_strnatcmp_zero(self):
        output = self.run('''
        echo strnatcmp("0", "00");
        echo strnatcmp("000011", "0011");
        echo strnatcmp("0001", "03");
        echo strnatcmp("01", "00011");
        echo strnatcmp("05", "00008");
        echo strnatcmp("008", "000014");


        ''')
        assert [self.space.int_w(w_v) for w_v in output] == [
            0, 0, -1, -1, -1, -1
        ]

    def test_strnatcasecmp_numbers(self):
        output = self.run('''
        echo strnatcasecmp(0, false);
        echo strnatcasecmp(0, -12);

        ''')
        assert [self.space.int_w(w_v) for w_v in output] == [
            1, 1
        ]

    def test_strnatcmp_mixed(self):
        output = self.run('''
        echo strnatcmp("0-0", "-123");
        echo strnatcmp(0, "Test1");
        echo strnatcmp("test2", "Test1");

        ''')
        assert [self.space.int_w(w_v) for w_v in output] == [
            1, -1, 1
        ]

    def test_count_chars(self):
        output = self.run('''
        echo count_chars("abc")[97];
        echo count_chars("abc")[100];
        echo count_chars("abc", 1);
        ''')
        assert self.unwrap(output[0]) == 1
        assert self.unwrap(output[1]) == 0
        assert self.unwrap(output[2]) == {'97': 1, '98': 1, '99': 1}

    def test_strtok(self):
        output = self.run('''
        echo strtok("xyazazazza", "zy");
        echo strtok("zy");
        echo strtok("zy");
        echo strtok("zy");
        echo strtok("zy");
        echo strtok("zy");
        ''')
        assert self.unwrap(output[0]) == 'x'
        assert self.unwrap(output[1]) == 'a'
        assert self.unwrap(output[2]) == 'a'
        assert self.unwrap(output[3]) == 'a'
        assert self.unwrap(output[4]) == 'a'
        assert self.unwrap(output[5]) == False

    def test_printf_formating(self, capfd):
        output = self.run('''
        echo sprintf("%c, ", 67);
        echo sprintf("%%, ", "");
        echo sprintf("% %%c c%", 38, -1234, 2345);
        ''')
        assert [self.space.str_w(w_v) for w_v in output] == [
            'C, ', '%, ', '%. c'
        ]

    def test_printf_formating_oct(self):
        output = self.run('''
        echo sprintf("%04.4o", 01234567);
        ''')
        assert [self.space.str_w(w_v) for w_v in output] == [
            '0000'
        ]

    def test_printf_formating_oct2(self):
        output = self.run('''
        echo sprintf("%o", 012);
        echo sprintf("%0.4o", 012);
        echo sprintf("%3.4o", 012);
        echo sprintf("%4.4o", 0123456);
        echo sprintf("%10.4o %-10.4o %04o %04.4o", 0123456, 012345678, -01234567, 01234567);
        ''')
        assert [self.space.str_w(w_v) for w_v in output] == [
            '12', '', '   ', '    ',
            '                      1777777777777776543211 0000'
        ]

    def test_printf_formating_oct3(self):
        output = self.run('''
        echo sprintf("%4o", 0);
        ''')
        assert [self.space.str_w(w_v) for w_v in output] == [
            '   0'
        ]

    def test_printf_formating_withL(self):
        output = self.run('''
        echo sprintf("%Lf", 1);
        echo sprintf("%Ls", 1);
        echo sprintf("%Lc", 1);
        echo sprintf("%LF", 1);
        echo sprintf("%Lg", 1);
        echo sprintf("%LG", 1);
        echo sprintf("%Lo", 1);
        ''')
        assert [self.space.str_w(w_v) for w_v in output] == [
            'f', 's', 'c', 'F', 'g', 'G', 'o'
        ]

    def test_printf_formating_string(self):
        output = self.run('''
        echo sprintf("%-10.4s", -2.7654321e10);
        ''')
        assert [self.space.str_w(w_v) for w_v in output] == [
            '-276      '
        ]

    def test_printf_formating_scientific(self):
        output = self.run('''
        echo sprintf("%10.4e", -22e12);
        echo sprintf("%-10.4e", 10e20);
        echo sprintf("%.4e", 1.2e2);
        ''')
        assert [self.space.str_w(w_v) for w_v in output] == [
            '-2.2000e+13', '1.0000e+21',  '1.2000e+2'
        ]

    def test_printf_formating_integer(self):
        output = self.run('''
        echo sprintf("%10.4d", 123456);
        echo sprintf("%-10.4d", 12345678);
        echo sprintf("%04d", -1234567);
        echo sprintf("%04.4d", 1234567);
        ''')
        assert [self.space.str_w(w_v) for w_v in output] == [
            '    123456', '12345678  ', '-1234567', '1234567'
        ]

    def test_printf_formating_hex(self):
        output = self.run('''
        echo sprintf("%10.4x", 123456);
        echo sprintf("%-10.4x", 12345678);
        echo sprintf("%04x", -1234567);
        echo sprintf("%04.4x", 1234567);
        echo sprintf("%x", "0xaxz");

        ''')
        assert [self.space.str_w(w_v) for w_v in output] == [
            '          ', '          ',
            'ffffffffffed2979', '0000',
            '0'
        ]

    def test_printf_formating_unsigned(self):
        output = self.run('''
        echo sprintf("%10.4u", "1234000");
        echo sprintf("%-10.4u", 10e20);
        echo sprintf("%.4u", 1.2e2);

        ''')
        assert [self.space.str_w(w_v) for w_v in output] == [
            '   1234000', '0         ', '120'
        ]

    def test_printf_formating_mix(self):
        with self.warnings() as w:
            output = self.run('''
            echo sprintf("%g", 10);
            echo sprintf("%#x", 255);
            echo sprintf("%*x", 255);
            echo sprintf("%g", 10.234234234);
            echo sprintf("%#g", 10.234234234);
            echo sprintf('%2$s %1$s', 10, 123);
            echo sprintf('%5$s %1$s', 10, 123);

        ''')
        assert w == ['Warning: sprintf(): Too few arguments']
        assert [self.space.str_w(w_v) for w_v in output] == [
            '10', 'x', 'x', '10.2342', 'g', '123 10', ''

        ]

    def test_printf_formating_mix2(self):
        output = self.run('''
        echo sprintf('%1$s %1$s', 10);

        ''')
        assert [self.space.str_w(w_v) for w_v in output] == [
            '10 10',

        ]

    def test_printf_formating_not_defined_mod(self):
        output = self.run('''
        echo sprintf('%r', 10);
        echo sprintf('%rrrr', 10);

        ''')
        assert [self.space.str_w(w_v) for w_v in output] == [
            '', 'rrr'

        ]

    def test_quoted_printable_decode(self):
        output = self.run(r'''
        echo quoted_printable_decode("=   \r\na");
        echo quoted_printable_decode("=   \na");
        echo quoted_printable_decode("=   xa");
        echo quoted_printable_decode("=f foo");
        echo quoted_printable_decode("=f");

        ''')
        assert [self.space.str_w(w_v) for w_v in output] == [
            'a', 'a', '=   xa', '=f foo', '=f'
        ]

    def test_crc32_basic(self):
        output = self.run('''
        $a = crc32('string_val1234');
        echo is_int($a);
        echo $a;

        ''')
        assert [output[0].boolval, self.space.int_w(output[1])] == [
            True, 256895812
        ]

    def test_crc32_variation1(self):
        output = self.run('''
        // declaring class
        class sample  {
          public function __toString() {
            return "object";
          }
        }

        //array of values to iterate over
        $values = array(

              // int data
              0,
              1,
              12345,
              -2345,

              // float data
              10.5,
              -10.5,
              10.1234567e10,
              10.7654321E-10,
              .5,

              // null data
              NULL,
              null,

              // boolean data
              true,
              false,
              TRUE,
              FALSE,

              // empty data
              "",
              '',

              // object data
              new sample(),
        );
        foreach($values as $value) {
            echo (crc32($value));
        };

        ''')
        expected = [-186917087, -2082672713, -873121252, 1860518047,
                    269248583, -834950157, -965354630, 1376932222,
                    -2036403827, 0, 0, -2082672713, 0, -2082672713, 0, 0, 0,
                    -1465013268]
        if sys.maxint >= 2**31:
            expected = [e & 0xFFFFFFFF for e in expected]

        assert [self.space.int_w(w_v) for w_v in output] == expected

        output = self.run('''
        $unset_var = 10;
        unset ($unset_var);
        echo crc32($undefined_var);
        echo crc32($unset_var);
        ''',
        [
            'Notice: Undefined variable: undefined_var',
            'Notice: Undefined variable: unset_var'
        ])
        assert [self.space.int_w(w_v) for w_v in output] == [0, 0]

        output = self.run('''
        // declaring class
        class sample  {
          public function __toString() {
            return "object";
          }
        }

        //array of values to iterate over
        $values = array(

              // array data
              array(),
              array(0),
              array(1),
              array(1, 2),
              array('color' => 'red', 'item' => 'pen'),
        );
        foreach($values as $value) {
            echo (crc32($value));
        };

        ''',
        ['Warning: crc32() expects parameter 1 to be string, array given'] * 5)
        assert [self.space.is_w(o, self.space.w_Null) for o in output] == [True] * 5

    def test_crc32_variation2(self):
        output = self.run('''
        $string_array = array(
          '',
          ' ',
          'hello world',
          'HELLO WORLD',
          ' helloworld ',

          '(hello world)',
          'hello(world)',
          'helloworld()',
          'hello()(world',

          '"hello" world',
          'hello "world"',
          'hello""world',

          'hello\\tworld',
          'hellowor\\\\tld',
          '\\thello world\\t',
          'hello\\nworld',
          'hellowor\\\\nld',
          '\\nhello world\\n',
          '\\n\\thelloworld',
          'hel\\tlo\\n world',

          '!@#$%&',
          '#hello@world.com',
          '$hello$world',
        );

        // looping to check the behaviour of the function for each string in the array

        foreach($string_array as $str) {
          echo crc32($str);
        }

        ''')

        # Note: some of the values are different to what is expected in
        # test_phpt/ext/standard/strings/crc32_variation2.phpt. However, that
        # test seems to be wrong as PHP in Appengine report the values below.
        expected = [0, -378745019, 222957957, -2015000997, 1234261835,
                    -1867296214, 1048577080, 2129739710, -1633247628, 135755572,
                    27384015, -497244052, -2065897232, 243585859, -856440615,
                    647088397, 523630053, -2062229676, 1169918910, -618551732,
                    -1828940657, -1654468652, -1648442217]
        if sys.maxint >= 2**31:
            expected = [e & 0xFFFFFFFF for e in expected]

        assert [self.space.int_w(w_v) for w_v in output] == expected

    def test_crc32_error(self):
        output = self.run('''
        echo crc32();

        //Test crc32 with one more than the expected number of arguments
        $str = 'string_val';
        $extra_arg = 10;
        echo crc32($str, $extra_arg);

        ''',
        [
            'Warning: crc32() expects exactly 1 parameter, 0 given',
            'Warning: crc32() expects exactly 1 parameter, 2 given'
        ])

        assert [self.space.is_w(o, self.space.w_Null) for o in output] == [True] * 2

    def test_hex2bin_invalid_data(self):
        output = self.run('''
        echo hex2bin('xx');
        echo hex2bin('0123456789abcdefxx');

        ''')

        assert [output[0].boolval, output[1].boolval] == [False] * 2
