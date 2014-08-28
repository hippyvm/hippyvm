from rpython.rlib.rsre.rsre_re import compile, M, IGNORECASE

from rply import ParserGenerator
from rply.token import BaseBox, SourcePosition

from hippy.constants import E_ALL
from hippy.lexer import Token, BaseLexer
from hippy.sourceparser import BaseParser

EXTENSIONS = ['session', 'standard', 'mysql', 'pcre', 'posix', 'Core',
              'xml', 'ctype', 'hash', 'spl', 'mbstring', 'mcrypt']


class Config(object):

    def __init__(self, space):
        self.space = space
        self.precision = 14
        self.ini = {
            'php_version': space.wrap("5.4.17"),
            'zend_version': space.wrap("2.2.0"),
            'precision': space.wrap(14),
            'serialize_precision': space.wrap(17),
            'include_path': space.wrap('.'),
            'mysql.default_host': space.wrap('localhost'),
            'mysql.max_links': space.wrap(-1),
            'mysql.max_persistent': space.wrap(-1),
            'sql.safe_mode': space.wrap(0),
            'mysql.default_user': space.wrap('root'),
            'mysql.default_password': space.wrap('root'),
            'session.name': space.wrap('PHPSESSID'),
            'session.auto_start': space.wrap(0),
            'session.cookie_lifetime': space.wrap(0),
            'session.cookie_path': space.wrap("/"),
            'session.save_path': space.wrap("/tmp"),
            'session.cache_expire': space.wrap(180),
            'session.cache_limiter': space.wrap('nocache'),
            'session.cookie_domain': space.wrap(""),
            'session.cookie_secure': space.wrap(0),
            'session.cookie_httponly': space.wrap(0),
            'session.serialize_handler': space.wrap('php'),
            'session.hash_function': space.wrap(0),
            'session.save_handler': space.wrap("files"),
            'register_argc_argv': space.wrap(1),
            'error_reporting': space.wrap(E_ALL),
            'default_socket_timeout': space.wrap(60)
            }

    def set_precision(self, prec):
        self.precision = prec

    def get_precision(self):
        return self.precision

    def get_ini_w(self, key):
        if key == 'precision':
            return self.space.wrap(self.precision)
        return self.ini.get(key, None)

    def get_ini_str(self, key):
        w_v = self.get_ini_w(key)
        if w_v is not None:
            return self.space.str_w(w_v)
        return None

    def set_ini_w(self, key, w_value):
        if key == 'precision':
            self.set_precision(self.space.int_w(w_value))
            return
        if key == 'open_basedir':
            # we can set this only once
            if self.ini.get(key, None):
                return
        self.ini[key] = w_value

RULES = [
    ('\[.*', "T_SECTION"),
    ("^[^=\n\r\t;|&$~(){}!\"\[]+", "TC_LABEL"),
    ("[a-zA-Z_][a-zA-Z0-9_]*", "TC_CONSTANT"),
    ('"[^"]*"', "TC_CONSTANT_STRING"),
    ("=", "="),
    ("[-]?([0-9]+|([0-9]*[\.][0-9]+)|([0-9]+[\.][0-9]*))", "NUMBER"),
    ("[ \t]*(\r|\n|\r\n)", "END_OF_LINE"),
    ("\|", "|"),
    ("&", "&"),
    ('!|~', '~'),
    ("[ \t]+", "H_WHITESPACE"),
    ("[^\r\n\]]+", "TC_RAW"),
]

PRECEDENCES = [
]


class IniLexerError(Exception):
    def __init__(self, lineno):
        self.lineno = lineno


class IniLexer(BaseLexer):
    def __init__(self):
        self.rules = []
        for rule, token_name in RULES:
            self.rules.append((compile(rule, M | IGNORECASE),
                               token_name))

    def input(self, buf):
        self.buf = buf
        self.lineno = 1
        self.pos = 0

    def __iter__(self):
        return self

    def next(self):
        tok = self.token()
        return tok

    def token(self):
        if self.pos >= len(self.buf):
            return None
        for rule, token_type in self.rules:
            m = rule.match(self.buf, pos=self.pos)
            if m:
                end = m.end()
                assert end >= 0
                val = self.buf[self.pos:end]
                tok = Token(token_type, val, SourcePosition(self.pos, self.lineno, 0))
                if token_type == "END_OF_LINE":
                    self.lineno += 1
                self.pos = end
                return tok
        raise IniLexerError(self.lineno)


class Value(BaseBox):
    def __init__(self, w_v):
        self.w_value = w_v

    def getval(self):
        return self.w_value


class IniReader(BaseParser):
    pg = ParserGenerator([d for _, d in RULES],
                         cache_id='hippy_ini_parser',
                         precedence=PRECEDENCES)

    def __init__(self, interp):
        self.config = interp.config
        self.interp = interp
        self.space = interp.space

    @pg.production("statement_list : statement_list statement")
    def statement_list_more(self, p):
        pass

    @pg.production("statement_list :")
    def statement_list_empty(self, p):
        pass

    @pg.production("statement : TC_LABEL ws = ws string_or_value")
    def statement_label(self, p):
        label = p[0].getstr().strip()
        w_val = p[4].getval()
        self.config.set_ini_w(label, w_val)

    @pg.production("statement : END_OF_LINE")
    def statement_end_of_line(self, p):
        pass

    @pg.production("string_or_value : expr")
    def string_or_value_expr(self, p):
        return p[0]

    @pg.production("string_or_value : END_OF_LINE")
    def string_or_value_empty(self, p):
        return Value(self.space.wrap(""))

    @pg.production("expr : expr or expr")
    def expr_expr_or_expr(self, p):
        v_1 = self.space.int_w(p[0].getval())
        v_2 = self.space.int_w(p[2].getval())
        return Value(self.space.wrap(v_1 | v_2))

    @pg.production("expr : expr and expr")
    def expr_expr_and_expr(self, p):
        v_1 = self.space.int_w(p[0].getval())
        v_2 = self.space.int_w(p[2].getval())
        return Value(self.space.wrap(v_1 & v_2))

    @pg.production("expr : subexpr")
    def expr_subexpr(self, p):
        return p[0]

    @pg.production("subexpr : invert var_string_list")
    def subexpr_invert(self, p):
        v_1 = self.space.int_w(p[1].getval())
        return Value(self.space.wrap(~v_1))

    @pg.production("subexpr : var_string_list")
    def expr_var_string_list(self, p):
        return p[0]

    @pg.production("or : ws | ws")
    def or_operator(self, p):
        return p[1]

    @pg.production("and : ws & ws")
    def and_operator(self, p):
        return p[1]

    @pg.production("invert : ~ ws")
    def and_operator(self, p):
        return p[0]

    @pg.production("var_string_list : constant_string")
    def var_string_list_constant_string(self, p):
        return p[0]

    @pg.production('var_string_list : TC_CONSTANT_STRING')
    def var_string_list_encapsed_string(self, p):
        end = len(p[0].getstr()) - 1
        assert end >= 0
        return Value(self.space.wrap(p[0].getstr()[1:end]))

    @pg.production('var_string_list : raw')
    def var_string_list_raw(self, p):
        return p[0]

    @pg.production("var_string_list : TC_CONSTANT")
    def var_string_list_tc_constant(self, p):
        w_const = self.interp.locate_constant(p[0].getstr(), False)
        if w_const is None:
            return Value(self.space.wrap(p[0].getstr()))
        return Value(w_const)

    @pg.production("constant_string : NUMBER")
    def constant_string_number(self, p):
        try:
            return Value(self.space.wrap(int(p[0].getstr())))
        except ValueError:
            return Value(self.space.wrap(float(p[0].getstr())))

    @pg.production('raw : TC_RAW')
    def raw_basic(self, p):
        return Value(self.space.wrap(p[0].getstr()))

    @pg.production('raw : TC_CONSTANT TC_RAW')
    def raw_compound(self, p):
        s0, s1 = p[0].getstr(), p[1].getstr()
        return Value(self.space.wrap(s0 + s1))

    @pg.production('raw : NUMBER TC_CONSTANT')
    def number_raw(self, p):
        s0 = p[0].getstr()
        s1 = p[1].getstr()
        return Value(self.space.wrap(s0 + s1))

    @pg.production("ws : ")
    def whitespace_empty(self, p):
        return Token('H_WHITESPACE', '', SourcePosition(0, 0, 0))

    @pg.production("ws : H_WHITESPACE")
    def ws(self, p):
        return p[0]

    parser = pg.build()

ini_lexer = IniLexer()


def load_ini(interp, buf):
    ini_reader = IniReader(interp)
    ini_lexer.input(buf)
    ini_reader.parser.parse(ini_lexer, ini_reader)
