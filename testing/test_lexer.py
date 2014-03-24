
from hippy.lexer import Lexer

class TestLexer(object):
    def setup_class(cls):
        cls.lexer = Lexer()

    def lex(self, input):
        self.lexer.input(input, 0, 0)
        return [i.name for i in self.lexer.tokens() if i]

    def test_basic(self):
        assert self.lex("12 + 12") == ["T_LNUMBER", "+", "T_LNUMBER"]

    def test_variable(self):
        assert self.lex("$x 12") == ["T_VARIABLE", "T_LNUMBER"]

    def test_ctx_obj(self):
        assert self.lex("interface $x->interface") == ["T_INTERFACE",
                                                       "T_VARIABLE",
                                                       "T_OBJECT_OPERATOR",
                                                       "T_STRING"]

    def test_left_bracket(self):
        assert self.lex('"x $var y"') == ['"', "T_ENCAPSED_AND_WHITESPACE",
                                          "T_VARIABLE",
                                          "T_ENCAPSED_AND_WHITESPACE", '"']
        assert self.lex('"x{$var}y"') == ['"', "T_ENCAPSED_AND_WHITESPACE",
                                          "T_DOLLAR_OPEN_CURLY_BRACES",
                                          "T_VARIABLE", "}",
                                          "T_ENCAPSED_AND_WHITESPACE", '"']

    def test_brackets_expr(self):
        exp = ['"', "T_ENCAPSED_AND_WHITESPACE", "T_DOLLAR_OPEN_CURLY_BRACES",
               "T_VARIABLE", "[", "T_LNUMBER", "+", "T_LNUMBER", "]",
               "}", "T_ENCAPSED_AND_WHITESPACE", '"']
        assert self.lex('"a{$x[1 + 2]}b"') == exp

    def test_simple_brackets(self):
        assert self.lex('"$a[13]"') == ['"', "T_VARIABLE", "[", "T_NUM_STRING",
                                        "]", '"']

    def test_dollar_brackets(self):
        assert self.lex('"${a}"') == ['"', "T_DOLLAR_OPEN_CURLY_BRACES",
                                      "T_VARIABLE", "}", '"']

    def test_escaped_quotes(self):
        assert self.lex('"x \\\"$a\\\""') == ['"', "T_ENCAPSED_AND_WHITESPACE",
                                              "T_VARIABLE",
                                              "T_ENCAPSED_AND_WHITESPACE",
                                              '"']

    def test_complex_case(self):
        exp = ['"', "T_ENCAPSED_AND_WHITESPACE", "T_VARIABLE",
               "[", "T_VARIABLE", "]", "T_VARIABLE",
               "T_ENCAPSED_AND_WHITESPACE", '"']
        assert self.lex('"\\${x$x[$y]$x}"') == exp

    def test_dollar_no_var(self):
        exp = ['"', "T_VARIABLE", "T_ENCAPSED_AND_WHITESPACE", '"']
        assert self.lex('"$a/$1"') == exp

    def test_heredoc(self):
        r = self.lex("<<< HERE\n sadsadasdas \nHERE;\n")
        exp = ["T_START_HEREDOC", "T_ENCAPSED_AND_WHITESPACE", "T_END_HEREDOC",
               ";"]
        assert r == exp

    def test_heredoc_variable(self):
        r = self.lex("<<< HERE\n sadsa$v dasdas \nHERE;\n")
        exp = ["T_START_HEREDOC", "T_ENCAPSED_AND_WHITESPACE", "T_VARIABLE",
               "T_ENCAPSED_AND_WHITESPACE", "T_END_HEREDOC", ";"]
        assert r == exp

    def test_b_quote(self):
        r = self.lex('b"xy$a z"')
        assert r == ['"', "T_ENCAPSED_AND_WHITESPACE", "T_VARIABLE",
                     "T_ENCAPSED_AND_WHITESPACE", '"']

    def test_string_backslash(self):
        r = self.lex('$rp .= "+(\\\\$i)";')
        assert r == ['T_VARIABLE', 'T_CONCAT_EQUAL', '"',
                     'T_ENCAPSED_AND_WHITESPACE', 'T_VARIABLE',
                     'T_ENCAPSED_AND_WHITESPACE', '"', ";"]

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
        r = self.lex('`ls "$php" ls $sdf->fsdf`')
        assert r == ['`', 'T_ENCAPSED_AND_WHITESPACE',
                     'T_VARIABLE', 'T_ENCAPSED_AND_WHITESPACE',
                     'T_VARIABLE', 'T_OBJECT_OPERATOR', 'T_STRING', '`']

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
