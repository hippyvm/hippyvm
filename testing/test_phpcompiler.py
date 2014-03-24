import py
from hippy.phpcompiler import compile_php, PHPLexerWrapper
from hippy.objspace import ObjSpace

from testing.directrunner import run_php_source, DirectInterpreter
from testing.test_interpreter import BaseTestInterpreter, MockInterpreter

class LiteralInterpreter(MockInterpreter):
    def run_source(self, source, expected_warnings=[]):
        output_w = MockInterpreter.run_source(self, source)
        space = self.space
        output = [space.str_w(v) for v in output_w]
        return ''.join(output)

    def compile(self, source):
        return compile_php('<input>', source, self.space, self)

class DirectLiteralInterpreter(DirectInterpreter):
    def run_source(self, source, expected_warnings=None):
        s = run_php_source(source)
        return s

class BaseTestPHP(BaseTestInterpreter):
    interpreter = LiteralInterpreter
    interpreter_direct = DirectLiteralInterpreter


def test_phplexerwrapper():
    phplexerwrapper = PHPLexerWrapper(
        'Foo\n<?php Echo 5 ?>\nBar\nBaz\n<? echo')
    for expected in [('B_LITERAL_BLOCK', 'Foo\n', 1),
                     ('T_ECHO', 'Echo', 2),
                     ('T_LNUMBER', '5', 2),
                     (';', ';', 2),
                     ('B_LITERAL_BLOCK', 'Bar\nBaz\n', 3),
                     ('T_ECHO', 'echo', 5)]:
        tok = phplexerwrapper.next()
        assert (tok.name, tok.value, tok.getsourcepos()) == expected
    tok = phplexerwrapper.next()
    assert tok is None


def test_line_start_offset():
    space = ObjSpace()
    MockInterpreter(space)
    bc = compile_php('<input>', 'Hi there\n', space)
    assert bc.startlineno == 1


class TestPHPCompiler(BaseTestPHP):

    def test_simple(self):
        output = self.run('Foo <?php echo 5; ?> Bar')
        assert output == 'Foo 5 Bar'

    def test_simple_2(self):
        output = self.run('Foo <? echo 5; ?> Bar')
        assert output == 'Foo 5 Bar'
        output = self.run('Foo<?echo 5;?>Bar')
        assert output == 'Foo5Bar'

    def test_windows_line_ending(self):
        output = self.run("Foo<?php\r\necho 5;\r\n?>Bar")
        assert output == "Foo5Bar"

    def test_case_insensitive(self):
        output = self.run('Foo <?phP echo 5; ?> Bar')
        assert output == 'Foo 5 Bar'

    def test_no_php_code(self):
        output = self.run('Foo\n')
        assert output == 'Foo\n'
        output = self.run('\nFoo')
        assert output == '\nFoo'

    def test_eol_after_closing_tag(self):
        output = self.run('Foo <?phP echo 5; ?>\nBar')
        assert output == 'Foo 5Bar'
        output = self.run('Foo <?phP echo 5; ?> \nBar')
        assert output == 'Foo 5 \nBar'
        output = self.run('Foo <?phP echo 5; ?>\n')
        assert output == 'Foo 5'
        output = self.run('Foo <?phP echo 5; ?>\n\n')
        assert output == 'Foo 5\n'
        output = self.run('Foo <?phP echo 5; ?> \n')
        assert output == 'Foo 5 \n'

    def test_end_in_comment_ignored_1(self):
        output = self.run('Foo <? echo 5; /* ?> */ echo 6; ?> Bar')
        assert output == 'Foo 56 Bar'

    def test_end_in_comment_not_ignored_1(self):
        output = self.run('Foo <? echo 5; //?>\necho 6; ?> Bar')
        assert output == 'Foo 5echo 6; ?> Bar'

    def test_end_in_comment_not_ignored_2(self):
        output = self.run('Foo <? echo 5; #?>\necho 6; ?> Bar')
        assert output == 'Foo 5echo 6; ?> Bar'

    def test_double_end(self):
        output = self.run('<?php echo 5; ?> echo 6; ?>\n')
        assert output == '5 echo 6; ?>\n'

    def test_multiple_blocks(self):
        output = self.run('-<?echo 5;?>+<?echo 6;?>*')
        assert output == '-5+6*'

    def test_non_closing_last_block_of_code(self):
        output = self.run('-<?echo 5;?>+<?echo 6;')
        assert output == '-5+6'

    def test_missing_semicolon_before_end(self):
        output = self.run('-<?echo 5?>+')
        assert output == '-5+'

    def test_reuse_var(self):
        output = self.run('<?$x=5?>----<?echo $x;')
        assert output == '----5'

    def test_multiple_use_of_block_of_text(self):
        output = self.run('<?for($x=0; $x<5; $x++){?>-+-+-\n<?}')
        assert output == '-+-+-\n' * 5

    def test_automatic_echo_1(self):
        output = self.run('abc<?=2+3?>def')
        assert output == 'abc5def'

    def test_automatic_echo_2(self):
        output = self.run('abc<?=2+3,7-1?>def')
        assert output == 'abc56def'

    def test_automatic_echo_3(self):
        output = self.run('abc<?=2+3,7-1; echo 8+1;?>def')
        assert output == 'abc569def'

    def test_automatic_echo_4(self):
        output = self.run('abc<?=2+3?><?=6*7?>def')
        assert output == 'abc542def'

    def test_automatic_echo_5(self):
        py.test.raises(Exception, self.run, 'abc<? =2+3?>def')

    def test_automatic_echo_6(self):
        output = self.run('abc<?=2+3?>\ndef<?=6*7?> \nghi')
        assert output == 'abc5def42 \nghi'

    def test_automatic_echo_7(self):
        output = self.run('abc<?=2+3;')
        assert output == 'abc5'
        py.test.raises(Exception, self.run, 'abc<?=2+3')

    def test_halt_compiler(self):
        output = self.run('abc<?php echo 5;__halt_compiler();]]]]]]]]]]?>def')
        assert output == 'abc5'
        output = self.run('abc<?php echo 5;__halt_compiler()?>def')
        assert output == 'abc5'
        output = self.run('abc<?php echo __COMPILER_HALT_OFFSET__;\n'
                          '__halt_compiler() ;]]]]]]]]]]?>def')
        assert output == 'abc59'
        output = self.run('abc<?php echo __COMPILER_HALT_OFFSET__;\n'
                          '__halt_compiler()   ?>     def')
        assert output == 'abc62'
        output = self.run('abc<?php echo __COMPILER_HALT_OFFSET__;\n'
                          '__halt_compiler()   ?>\n     def')
        assert output == 'abc63'

    def test_heredoc(self):
        output = self.run('''<? $x = <<<  \tPHP
Hello World
PHP;
echo $x;
?>''')
        assert output == 'Hello World'

    def test_heredoc_2(self):
        output = self.run('''<? $x = <<<PHP
Hello World
12
;;
"hello"
19x333
class var
PHP;
echo $x;
?>''')
        assert output == 'Hello World\n12\n;;\n"hello"\n19x333\nclass var'

    def test_heredoc_error(self):
        input = '''<? $x = <<<PHP
Hello World
PH;
echo $x;
?>'''
        py.test.raises(Exception, self.run, input)

    def test_heredoc_escape(self):
        output = self.run(r'''<? $x = <<<EOS
\n
\$variable
\"quotes\
EOS;
        echo $x;
        ?>''')
        assert output == '\n\n$variable\n\\"quotes\\'

    def test_heredoc_NUL(self):
        output = self.run(r'''<? $x = <<<EOS
Hello\0world
EOS;
        echo $x;
        ?>''')
        assert output == "Hello\0world"
        output = self.run('''<? $x = <<<EOS
Hello\0world
EOS;
        echo $x;
        ?>''')
        assert output == "Hello\0world"

    def test_heredoc_unfinished(self):
        output = self.run(r'''<?

class T {
  public function test($var) {
    echo $var;
  }
}

$t = new T;
$t->test(<<<HTML
test

HTML
);
        ?>''')
        assert output == "test\n"
