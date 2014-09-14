import pytest

from hippy.lexer import Lexer, LexerError


class TestLexer(object):

    def setup_class(cls):
        cls.lexer = Lexer()

    def lex(self, buf):
        self.lexer.input(buf, 0, 0)
        return [i.name for i in self.lexer.token() if i]

    def lex_full(self, buf):
        self.lexer.input(buf, 0, 0)
        return [(i.name, i.source, i.source_pos.lineno)
                for i in self.lexer.token() if i]

    def lex_content(self, buf):
        self.lexer.input(buf, 0, 0)
        return [i.source for i in self.lexer.token() if i]

    def test_basic(self):
        assert self.lex("12 + 12") == ["T_LNUMBER", "+", "T_LNUMBER"]

    def test_variable(self):
        assert self.lex("$x 12") == ["T_VARIABLE", "T_LNUMBER"]

    def test_keyword_indetifier(self):
        assert self.lex("return $xyz") == ['T_RETURN', 'T_VARIABLE']

    def test_ctx_obj(self):
        assert self.lex("interface $x->interface") == ["T_INTERFACE",
                                                       "T_VARIABLE",
                                                       "T_OBJECT_OPERATOR",
                                                       "T_STRING"]

    def test_case_insensitive_keywords(self):
        assert self.lex("Interface") == self.lex("interface") == ["T_INTERFACE"]
        assert self.lex("InstanceOf") == self.lex("instanceof") == ["T_INSTANCEOF"]
        assert self.lex("Class") == self.lex("class") == ["T_CLASS"]



    def test_left_bracket(self):
        assert self.lex('"x $var y"') == ['"', "T_ENCAPSED_AND_WHITESPACE",
                                          "T_VARIABLE",
                                          "T_ENCAPSED_AND_WHITESPACE", '"']

        assert self.lex('"x{$var}y"') == ['"', "T_ENCAPSED_AND_WHITESPACE",
                                          "T_DOLLAR_OPEN_CURLY_BRACES",
                                          "T_VARIABLE", "}",
                                          "T_ENCAPSED_AND_WHITESPACE", '"']

    def test_brackets_expr(self):
        assert self.lex('"a{$x[1 + 2]}b"') == [
            '"',
            "T_ENCAPSED_AND_WHITESPACE",
            "T_DOLLAR_OPEN_CURLY_BRACES",
            "T_VARIABLE",
            "[",
            "T_LNUMBER", "+", "T_LNUMBER",
            "]",
            "}",
            "T_ENCAPSED_AND_WHITESPACE",
            '"'
        ]

    def test_simple_brackets(self):
        assert self.lex('"$a[13]"') == [
            '"', "T_VARIABLE", "[", "T_NUM_STRING", "]", '"'
        ]

    def test_dollar_brackets(self):
        assert self.lex('"${a}"') == [
            '"', "T_DOLLAR_OPEN_CURLY_BRACES", "T_VARIABLE", "}", '"'
        ]

    def test_escaped_quotes(self):
        assert self.lex('"x \\\"$a\\\""') == [
            '"', "T_ENCAPSED_AND_WHITESPACE",
            "T_VARIABLE",
            "T_ENCAPSED_AND_WHITESPACE",
            '"'
        ]

    def test_complex_case(self):
        exp = ['"', "T_ENCAPSED_AND_WHITESPACE", "T_VARIABLE",
               "[", "T_VARIABLE", "]", "T_VARIABLE",
               "T_ENCAPSED_AND_WHITESPACE", '"']
        assert self.lex('"\\${x$x[$y]$x}"') == exp

    def test_dollar_no_var(self):
        exp = ['"', "T_VARIABLE", "T_ENCAPSED_AND_WHITESPACE", '"']
        assert self.lex('"$a/$1"') == exp

    def test_heredoc_1(self):
        r = self.lex("<<< HERE\n sadsadasdas \nHERE;\n $var")
        assert r == [
            'T_START_HEREDOC',
            'T_ENCAPSED_AND_WHITESPACE',
            'T_END_HEREDOC', ';', 'T_VARIABLE'
        ]

        r = self.lex("<<< HERE\n sadsadasdas \nHERE\n $var")
        assert r == [
            'T_START_HEREDOC',
            'T_ENCAPSED_AND_WHITESPACE',
            'T_END_HEREDOC', 'T_VARIABLE'
        ]

        with pytest.raises(LexerError):
            self.lex("<<< HERE\n sadsadasdas \nHERE; $var")

    def test_heredoc_2(self):
        r = self.lex("<<< HERE\nHERE;")
        assert r == ['T_START_HEREDOC', 'T_END_HEREDOC', ';']

        with pytest.raises(LexerError):
            self.lex("<<< HERE\nHERE; $var")

    def test_heredoc_3(self):
        r = self.lex("""<<< HERE\n asd1 {$foo} asd2 \nHERE;\n""")

        assert r == [
            'T_START_HEREDOC', 'T_ENCAPSED_AND_WHITESPACE',
            'T_DOLLAR_OPEN_CURLY_BRACES', 'T_VARIABLE', '}',
            'T_ENCAPSED_AND_WHITESPACE',
            'T_END_HEREDOC', ';'
        ]

    def test_heredoc_4(self):
        r = self.lex("""<<< HERE\n sads $foo adasdas \nHERE;\n""")

        assert r == [
            'T_START_HEREDOC', 'T_ENCAPSED_AND_WHITESPACE',
            'T_VARIABLE',
            'T_ENCAPSED_AND_WHITESPACE',
            'T_END_HEREDOC', ';'
        ]

    def test_heredoc_5(self):
        r = self.lex("""<<< HERE\n sads\n "$foo" adasdas \nHERE;\n""")

        assert r == [
            'T_START_HEREDOC', 'T_ENCAPSED_AND_WHITESPACE',
            'T_VARIABLE',
            'T_ENCAPSED_AND_WHITESPACE',
            'T_END_HEREDOC', ';'
        ]

    def test_heredoc_6(self):
        r = self.lex("""<<< HERE\n sads\n "$foo" adasdas \nHERE;\n <<< HERE\n sads\n "$foo" adasdas \nHERE;\n""")

        assert r == [
            'T_START_HEREDOC', 'T_ENCAPSED_AND_WHITESPACE',
            'T_VARIABLE', 'T_ENCAPSED_AND_WHITESPACE',
            'T_END_HEREDOC', ';',

            'T_START_HEREDOC', 'T_ENCAPSED_AND_WHITESPACE',
            'T_VARIABLE', 'T_ENCAPSED_AND_WHITESPACE',
            'T_END_HEREDOC', ';'
        ]

    def test_heredoc_7(self):
        r = self.lex_full("""<<< HERE\n sads HERE adasdas \nHERE;\n""")

        assert r == [
            ('T_START_HEREDOC', '<<< HERE\n', 0),
            ('T_ENCAPSED_AND_WHITESPACE', ' sads HERE adasdas ', 1),
            ('T_END_HEREDOC', 'HERE', 2),
            (';', ';', 2)
        ]

    def test_heredoc_8(self):
        r = self.lex_full("<<<X\nXX\n X\nX;\n")
        assert r == [
            ('T_START_HEREDOC', '<<<X\n', 0),
            ('T_ENCAPSED_AND_WHITESPACE', 'XX\n X', 1),
            ('T_END_HEREDOC', 'X', 3),
            (';', ';', 3)]

    def test_heredoc_with_quoted_dollar(self):
        r = self.lex_full("<<<X\n\"$\"\nX;\n")
        assert r == [
            ('T_START_HEREDOC', '<<<X\n', 0),
            ('T_ENCAPSED_AND_WHITESPACE', '"$"', 1),
            ('T_END_HEREDOC', 'X', 2),
            (';', ';', 2)]

    def test_heredoc_error(self):
        with pytest.raises(LexerError) as excinfo:
            self.lex("<<< HERE\n sadsadasdas\n")

        assert excinfo.value.message == 'unfinished heredoc'

    def test_string_backslash(self):
        r = self.lex('$rp .= "+(\\\\$i)";')
        assert r == ['T_VARIABLE', 'T_CONCAT_EQUAL', '"',
                     'T_ENCAPSED_AND_WHITESPACE', 'T_VARIABLE',
                     'T_ENCAPSED_AND_WHITESPACE', '"', ";"]

    def test_b_quote(self):
        r = self.lex('b"xy$a z"')
        assert r == ['"', "T_ENCAPSED_AND_WHITESPACE", "T_VARIABLE",
                     "T_ENCAPSED_AND_WHITESPACE", '"']


    def test_var(self):
        r = self.lex('"sadsada {$class} sadads\n"')
        assert r == ['"', 'T_ENCAPSED_AND_WHITESPACE',
                     "T_DOLLAR_OPEN_CURLY_BRACES", "T_VARIABLE", "}",
                     "T_ENCAPSED_AND_WHITESPACE", '"']

    def test_backtick(self):
        r = self.lex('`ls "-1"`')
        assert r == ['`', 'T_ENCAPSED_AND_WHITESPACE', '`']

    def test_backtick_2(self):
        r = self.lex('`ls "-1" "-2"`')
        assert r == ['`', 'T_ENCAPSED_AND_WHITESPACE', '`']

    def test_backtick_3(self):
        r = self.lex('`ls "-1" -2 `')
        assert r == ['`', 'T_ENCAPSED_AND_WHITESPACE', '`']

    def test_backtick_4(self):
        r = self.lex('`ls "-1" \'-2\' `')
        assert r == ['`', 'T_ENCAPSED_AND_WHITESPACE', '`']

    def test_backtick_5(self):
        r = self.lex('`ls $php ls`')
        assert r == ['`', 'T_ENCAPSED_AND_WHITESPACE',
                     'T_VARIABLE', 'T_ENCAPSED_AND_WHITESPACE',  '`']

    def test_backtick_6(self):
        r = self.lex('`ls "$php" ls`')
        assert r == ['`', 'T_ENCAPSED_AND_WHITESPACE',
                     'T_VARIABLE', 'T_ENCAPSED_AND_WHITESPACE',  '`']

    def test_backtick_7(self):
        src = '`ls "$php" ls $sdf->fsdf`'
        r = self.lex(src)
        assert r == ['`', 'T_ENCAPSED_AND_WHITESPACE',
                     'T_VARIABLE', 'T_ENCAPSED_AND_WHITESPACE',
                     'T_VARIABLE', '`']
        assert self.lex_content(src) == ['`', 'ls "', '$php', '" ls ',
                                         '$sdf->fsdf', '`']

    def test_backtick_8(self):
        r = self.lex('`ls "$php" ls \'asdasd\' \'asdasd\'`')
        assert r == ['`', 'T_ENCAPSED_AND_WHITESPACE',
                     'T_VARIABLE', 'T_ENCAPSED_AND_WHITESPACE', '`']

    def test_backtick_9(self):
        r = self.lex('`$php $php $hph`')
        assert r == ['`', 'T_VARIABLE', 'T_ENCAPSED_AND_WHITESPACE',
                     'T_VARIABLE', 'T_ENCAPSED_AND_WHITESPACE',
                     'T_VARIABLE', '`']

    def test_backtick_10(self):
        r = self.lex('`echo "`')
        assert r == ['`', 'T_ENCAPSED_AND_WHITESPACE', '`']

    def test_dollar_at_the_end_1(self):
        r = self.lex('"xyz $a $" + 3')
        assert r == ['"', "T_ENCAPSED_AND_WHITESPACE", "T_VARIABLE",
                     "T_ENCAPSED_AND_WHITESPACE", "T_DOLLAR", '"', "+", "T_LNUMBER"]

    def test_dollar_at_the_end_2(self):
        r = self.lex('"%{$errors[1]}$"')
        assert r == ['"', 'T_ENCAPSED_AND_WHITESPACE',
             'T_DOLLAR_OPEN_CURLY_BRACES', 'T_VARIABLE',
             '[', 'T_LNUMBER', ']', '}', 'T_DOLLAR', '"'
        ]

    def test_namespace_statement(self):
        r = self.lex("namespace Foo\\Bar;")
        assert r == ["T_NAMESPACE",
                     "T_STRING", "T_NS_SEPARATOR", "T_STRING", ";"]
