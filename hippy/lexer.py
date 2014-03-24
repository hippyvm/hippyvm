
import sys
from rply.token import BaseBox, Token
from rply import ParsingError

# -hacking-


def _token_init(self, name, value, lineno=0):
    self.name = name
    self.value = value
    self.lineno = lineno


def _basebox_getsourcepos(self):
    return self.lineno


def _basebox_append_item(self, item):
    raise NotImplementedError(self)

BaseBox._attrs_ = ['lineno']
BaseBox.getsourcepos = _basebox_getsourcepos
BaseBox.append_item = _basebox_append_item
Token._attrs_ = ['name', 'value']
Token.__init__ = _token_init
del Token.getsourcepos
# -done-


KEYWORDS = {
    "print": 'T_PRINT',
    "echo": 'T_ECHO',
    "instanceof": 'T_INSTANCEOF',
    "new": 'T_NEW',
    "clone": 'T_CLONE',
    "exit": 'T_EXIT',
    "die": 'T_EXIT',
    "if": 'T_IF',
    "elseif": 'T_ELSEIF',
    "else": 'T_ELSE',
    "endif": 'T_ENDIF',
    "array": 'T_ARRAY',
    "Array": "T_ARRAY",
    "include": 'T_INCLUDE',
    "include_once": 'T_INCLUDE_ONCE',
    "eval": 'T_EVAL',
    "require": 'T_REQUIRE',
    "require_once": 'T_REQUIRE_ONCE',
    "or": 'T_LOGICAL_OR',
    "xor": 'T_LOGICAL_XOR',
    "and": 'T_LOGICAL_AND',
    "foreach": 'T_FOREACH',
    "endforeach": 'T_ENDFOREACH',
    "do": 'T_DO',
    "while": 'T_WHILE',
    "endwhile": 'T_ENDWHILE',
    "for": 'T_FOR',
    "endfor": 'T_ENDFOR',
    "declare": 'T_DECLARE',
    "enddeclare": 'T_ENDDECLARE',
    "as": 'T_AS',
    "switch": 'T_SWITCH',
    "endswitch": 'T_ENDSWITCH',
    "case": 'T_CASE',
    "default": 'T_DEFAULT',
    "break": 'T_BREAK',
    "continue": 'T_CONTINUE',
    "goto": 'T_GOTO',
    "function": 'T_FUNCTION',
    "const": 'T_CONST',
    "return": 'T_RETURN',
    "try": 'T_TRY',
    "catch": 'T_CATCH',
    "throw": 'T_THROW',
    "use": 'T_USE',
    #"insteadof": 'T_INSTEADOF',
    "global": 'T_GLOBAL',
    "static": 'T_STATIC',
    "abstract": 'T_ABSTRACT',
    "final": 'T_FINAL',
    "private": 'T_PRIVATE',
    "protected": 'T_PROTECTED',
    "public": 'T_PUBLIC',
    "var": 'T_VAR',
    "unset": 'T_UNSET',
    "isset": 'T_ISSET',
    "empty": 'T_EMPTY',
    "class": 'T_CLASS',
    #"trait": 'T_TRAIT',
    "interface": 'T_INTERFACE',
    "extends": 'T_EXTENDS',
    "implements": 'T_IMPLEMENTS',
    "list": 'T_LIST',
    "__halt_compiler": 'T_HALT_COMPILER',
    "__FILE__": 'T_FILE',
    "__CLASS__": 'T_CLASS_C',
    #"__TRAIT__": 'T_TRAIT_C',
    "__METHOD__": 'T_METHOD_C',
    "__FUNCTION__": 'T_FUNC_C',
    "__LINE__": 'T_LINE',
    "__NAMESPACE__": 'T_NS_C',
    "__DIR__": 'T_DIR',
}
RULES = [(r'\b%s\b' % keyword, name) for keyword, name in KEYWORDS.items()]
RULES += [
    ("b?\<\<\<.*?\n", 'T_START_HEREDOC'),
    ("\x00", 'T_END_HEREDOC'),  # generated artificially
    ("\x00", 'T_ENCAPSED_AND_WHITESPACE'),  # generated artificially
    ("\x00", 'T_IGNORE_THIS_TOKEN'),  # generated artificially

    (r'b?"([^"\\]|\\.)*"|' +
     r"b?'([^'\\]|\\.)*'", 'T_CONSTANT_ENCAPSED_STRING'),

    ("[a-zA-Z_][a-zA-Z_0-9]*", 'T_STRING'),

    ("\?\>", 'B_END_OF_CODE_BLOCK'),
    ("\x00", 'B_LITERAL_BLOCK'),

    ("\+\=", 'T_PLUS_EQUAL'),
    ("\-\=", 'T_MINUS_EQUAL'),
    ("\*\=", 'T_MUL_EQUAL'),
    ("\/\=", 'T_DIV_EQUAL'),
    ("\.\=", 'T_CONCAT_EQUAL'),
    ("\%\=", 'T_MOD_EQUAL'),
    ("\&\=", 'T_AND_EQUAL'),
    ("\|\=", 'T_OR_EQUAL'),
    ("\^\=", 'T_XOR_EQUAL'),
    ("\<\<\=", 'T_SL_EQUAL'),
    ("\>\>\=", 'T_SR_EQUAL'),
    ("\|\|", 'T_BOOLEAN_OR'),
    ("\&\&", 'T_BOOLEAN_AND'),
    ("\=\=\=", 'T_IS_IDENTICAL'),
    ("\!\=\=", 'T_IS_NOT_IDENTICAL'),
    ("\=\=", 'T_IS_EQUAL'),
    ("\!\=", 'T_IS_NOT_EQUAL'),
    ("\<\>", 'T_IS_NOT_EQUAL'),
    ("\<\=", 'T_IS_SMALLER_OR_EQUAL'),
    ("\>\=", 'T_IS_GREATER_OR_EQUAL'),
    ("\<\<", 'T_SL'),
    ("\>\>", 'T_SR'),
    ("\+\+", 'T_INC'),
    ("\-\-", 'T_DEC'),

    ("\((int|integer)\)", 'T_INT_CAST'),
    ("\((real|double|float)\)", 'T_DOUBLE_CAST'),
    ("\((string|binary)\)", 'T_STRING_CAST'),
    ("\(array\)", 'T_ARRAY_CAST'),
    ("\(object\)", 'T_OBJECT_CAST'),
    ("\((bool|boolean)\)", 'T_BOOL_CAST'),
    ("\(unset\)", 'T_UNSET_CAST'),
    ("\(unicode\)", 'T_UNICODE_CAST'),

    ("([0-9]*\.[0-9]*|[0-9][0-9]*)[eE](\+|\-)?[0-9][0-9]*", 'T_DNUMBER'),
    ("[0-9]+\.[0-9]+", 'T_DNUMBER'),
    ("\.[0-9]+", 'T_DNUMBER'),
    ("[0-9]+\.", 'T_DNUMBER'),
    ("0x([0-9a-fA-F])*", 'T_LNUMBER'),
    ("0X([0-9a-fA-F])*", 'T_LNUMBER'),
    ("[0-9]+", 'T_LNUMBER'),

    ("\$[a-zA-Z_][0-9a-zA-Z_]*", 'T_VARIABLE'),
    #("\$\{[a-zA-Z]*\}", 'T_STRING_VARNAME'),
    ("(//[^\n]*)|(#[^\n]*)|(/\*(.|\n)*?\*/)", 'T_COMMENT'),

    ("\-\>", 'T_OBJECT_OPERATOR'),
    ("\=\>", 'T_DOUBLE_ARROW'),
    ("comment", 'T_COMMENT'),
    ("doc comment", 'T_DOC_COMMENT'),
    #("open tag", 'T_OPEN_TAG'),
    #("open tag with echo", 'T_OPEN_TAG_WITH_ECHO'),
    #("close tag", 'T_CLOSE_TAG'),
    ("whitespace", 'T_WHITESPACE'),
    ("namespace", 'T_NAMESPACE'),
    ("\\\\", 'T_NS_SEPARATOR'),


    ("\:\:", 'T_PAAMAYIM_NEKUDOTAYIM'),
    ("\&", '&'),
    ("\,", ','),
    ("\;", ';'),
    ("\:", ':'),
    ("\=", '='),
    ("\?", '?'),
    ("\|", '|'),
    ("\^", '^'),
    ("\<", '<'),
    ("\>", '>'),

    ("\+", '+'),
    ("\-", '-'),
    ("\.", '.'),
    ("\*", '*'),
    ("\/", '/'),
    ("\%", '%'),
    ("\!", '!'),
    ("\[", '['),
    ("\]", ']'),
    ('\(', '('),
    ('\)', ')'),
    ("\{", '{'),
    ("\}", '}'),
    ("\~", '~'),
    ("\@", '@'),
    ("\$", '$'),
    ("\"", '"'),
    ("`", '`'),
    ("\\n", 'H_NEW_LINE'),
    (r"\r\n", 'H_NEW_LINE'),
    ("\\t", 'H_TABULATURE'),
    (" ", 'H_WHITESPACE')]

RULES_FOR_DOUBLE_QUOTE = [
    ("\$[a-zA-Z_][0-9a-zA-Z_]*", 'T_VARIABLE'),
    ("->", "T_OBJECT_OPERATOR"),
    (r"\{\$|\$\{", "T_DOLLAR_OPEN_CURLY_BRACES"),
    (r"([^\\\"$\{]|\\.|\$[^a-zA-Z\"{]|\$(?=\")|{[^$])+", "T_ENCAPSED_AND_WHITESPACE"),
    ('"', '"'),
]

RULES_FOR_BACKTICK = [
    (r"\{\$|\$\{", "T_DOLLAR_OPEN_CURLY_BRACES"),
    ("`", '`'),
    ("\}", '}'),
    ("\{", '{'),
    ("\$[a-zA-Z_][0-9a-zA-Z_]*", 'T_VARIABLE'),
    ("->", "T_OBJECT_OPERATOR"),
    (r"([^\\$\{\`\}]|\\.|\$[^a-zA-Z\"{]|\$(?=\")|{[^$])+", "T_ENCAPSED_AND_WHITESPACE"),


]


RULES_FOR_HEREDOC = [
    ("\$[a-zA-Z_][0-9a-zA-Z_]*", 'T_VARIABLE'),
    (r"\{\$|\$\{", "T_DOLLAR_OPEN_CURLY_BRACES"),
    (r"([^\\$\{]|\\.|\$[^a-zA-Z\"{]|\$(?=\")|{[^$]|\\$)+", "T_ENCAPSED_AND_WHITESPACE"),
]

RULES_FOR_BRACKETS = [
    ("\]", "]"),
    ("\[", "["),
    ("\d+", "T_NUM_STRING"),
    ("\$[a-zA-Z_][0-9a-zA-Z_]*", 'T_VARIABLE'),
    ("[a-zA-Z_][0-9a-zA-Z_]*", 'T_STRING'),
]

ALL_RULES = RULES + RULES_FOR_DOUBLE_QUOTE + RULES_FOR_BRACKETS

PRECEDENCES = [
    ("left", ["T_INCLUDE", "T_INCLUDE_ONCE", "T_EVAL",
              "T_REQUIRE", "T_REQUIRE_ONCE"]),
    ("left", [","]),
    ("left", ["T_LOGICAL_OR", ]),
    ("left", ["T_LOGICAL_XOR", ]),
    ("left", ["T_LOGICAL_AND", ]),
    ("right", ["T_PRINT", ]),
    #("right", ["T_YIELD",]),
    ("left", ['=', "T_PLUS_EQUAL", "T_MINUS_EQUAL", "T_MUL_EQUAL",
              "T_DIV_EQUAL", "T_CONCAT_EQUAL", "T_MOD_EQUAL",
              "T_AND_EQUAL", "T_OR_EQUAL", "T_XOR_EQUAL",
              "T_SL_EQUAL", "T_SR_EQUAL"]),
    ("left", ["?", ":"]),
    ("left", ["T_BOOLEAN_OR"]),
    ("left", ["T_BOOLEAN_AND"]),
    ("left", ["!"]),
    ("left", ["|"]),
    ("left", ["^"]),
    ("left", ["&"]),
    ("nonassoc", ["T_IS_EQUAL", "T_IS_NOT_EQUAL",
                  "T_IS_IDENTICAL", "T_IS_NOT_IDENTICAL"]),
    ("nonassoc", ['<', "T_IS_SMALLER_OR_EQUAL", '>', "T_IS_GREATER_OR_EQUAL"]),
    ("left", ["T_SL", "T_SR"]),
    ("left", ["+", "-", "."]),
    ("left", ["*", "/", "%"]),
    ("nonassoc", ["T_INSTANCEOF"]),
    ("right", ['~', 'T_INC', 'T_DEC', 'T_INT_CAST',
               'T_DOUBLE_CAST', 'T_STRING_CAST',
               'T_UNICODE_CAST', 'T_BINARY_CAST', 'T_ARRAY_CAST',
               'T_OBJECT_CAST', 'T_BOOL_CAST', 'T_UNSET_CAST', '@']),
    ("right", ["["]),
    ("nonassoc", ["T_NEW", "T_CLONE"]),
    # XXX TODO: find out why this doesnt work
    # ("left", ["T_ELSEIF"]),
    # ("left", ["T_ELSE"]),
    # ("left", ["T_ENDIF"]),
    ("right", ["T_STATIC", "T_ABSTRACT", "T_FINAL",
               "T_PRIVATE", "T_PROTECTED", "T_PUBLIC"]),

]


class BaseLexer(object):
    lineno = 0
    buf = None
    pos = 0
    last_token = None


class LexerError(ParsingError):
    """ Lexer error exception.

        pos:
            Position in the input line where the error occurred.
    """
    def __init__(self, message, source_pos):
        self.message = message
        self.source_pos = source_pos

    def __str__(self):
        return 'LexerError("%s", %d)' % (self.message, self.source_pos)

(CONTEXT_NORMAL, CONTEXT_OBJECT_ACCESS,
 CONTEXT_DOUBLEQUOTE, CONTEXT_CURLY_BRACES, CONTEXT_BRACKETS,
 CONTEXT_HEREDOC, CONTEXT_BACKTICK) = range(7)

""" How this goes: we start with a normal context (CONTEXT_NORMAL) and some
tokens change the context. If we change the context to a new one, we push
the old one on the stack. Some tokens will pop stuff from the stack.
"""


class Lexer(BaseLexer):
    """ A simple regex-based lexer/tokenizer.

        See below for an example of usage.
    """
    def __init__(self, use_rsre=False):
        """ Create a lexer.

            rules:
                A list of rules. Each rule is a `regex, type`
                pair, where `regex` is the regular expression used
                to recognize the token and `type` is the type
                of the token to return when it's recognized.

        """
        self.use_rsre = use_rsre
        # initialize rules for all the possible contextes
        self.rules = [None for _ in range(7)]

        self.rules[CONTEXT_NORMAL] = self._compile_rules(RULES)
        rules_no_kwds = self.rules[CONTEXT_NORMAL][len(KEYWORDS):]
        self.rules[CONTEXT_OBJECT_ACCESS] = rules_no_kwds

        rules = self._compile_rules(RULES_FOR_DOUBLE_QUOTE)
        self.rules[CONTEXT_DOUBLEQUOTE] = rules
        self.rules[CONTEXT_BACKTICK] = self._compile_rules(RULES_FOR_BACKTICK)

        self.rules[CONTEXT_CURLY_BRACES] = self.rules[CONTEXT_NORMAL]
        self.rules[CONTEXT_BRACKETS] = self._compile_rules(RULES_FOR_BRACKETS)
        self.rules[CONTEXT_HEREDOC] = self._compile_rules(RULES_FOR_HEREDOC)
        self.context_stack = [CONTEXT_NORMAL]
        self.var_re = self._compile("\{[a-zA-Z_][a-zA-Z_0-9]*")

        self.heredoc_finish = -1
        self.heredoc_lgt = 0

    def _compile(self, re):
        if self.use_rsre:
            from rpython.rlib.rsre.rsre_re import compile, M, DOTALL, IGNORECASE
        else:
            from re import compile, M, DOTALL, IGNORECASE
        return compile(re, IGNORECASE | M | DOTALL)

    def _compile_rules(self, rules):
        compiled = []
        for regex, type in rules:
            compiled.append((self._compile(regex), type))
        return compiled

    def input(self, buf, pos, lineno):
        """ Initialize the lexer with a buffer as input.
        """
        self.buf = buf
        self.pos = pos
        self.lineno = lineno
        self.last_token = None

    def _scan_double_quote(self, tok):
        p = 1
        v = tok.value
        if v[0] == "b":
            p += 1
        backslash = False
        while p < len(v):
            c = v[p]
            if not backslash:
                if c == '"':
                    # not encountered anything funny, this is just T_STRING
                    return tok
                if (((c == '$' and p < len(v) - 1 and v[p + 1].isalpha()) or
                    (c == "{" and p < len(v) - 1 and v[p + 1] == "$") or
                    (c == "$" and p < len(v) - 1 and v[p + 1] == "{"))):
                    p += 1
                    self.context_stack.append(CONTEXT_DOUBLEQUOTE)
                    return Token('"', '"', self.lineno)
                elif c == '\\':
                    backslash = True
            else:
                backslash = False
            p += 1
        assert False

    def _gettmpbuf(self, pos):
        if self.use_rsre:
            return None
        if self.heredoc_finish >= 0:
            return self.buf[pos:self.heredoc_finish]
        else:
            return self.buf[pos:]

    def match(self, token_regex, tmp_buf, pos):
        if self.use_rsre:
            if self.heredoc_finish >= 0:
                endpos = self.heredoc_finish
            else:
                endpos = sys.maxint
            m = token_regex.match(self.buf, pos=pos, endpos=endpos)
        else:
            m = token_regex.match(tmp_buf)
        return m

    def _getstartend(self, m):
        if self.use_rsre:
            start = m.start()
            end = m.end()
        else:
            start = self.pos + m.start()
            end = self.pos + m.end()
        assert start >= 0
        assert end >= 0
        return start, end

    def token(self):
        """ Return the next token (a Token object) found in the
            input buffer. None is returned if the end of the
            buffer was reached.
            In case of a lexing error (the current chunk of the
            buffer matches no rule), a LexerError is raised with
            the position of the error.
        """
        if self.pos >= len(self.buf):
            if len(self.context_stack) != 1:
                raise LexerError("contexts are not closed", -1)
            return None
        else:
            if self.pos >= self.heredoc_finish and self.heredoc_finish != -1:
                start = self.pos
                end = self.pos + self.heredoc_lgt
                assert start >= 0
                assert end >= 0
                tok = Token('T_END_HEREDOC', self.buf[start:end], self.lineno)
                self.pos = self.heredoc_finish + self.heredoc_lgt
                self.heredoc_finish = -1
                self.heredoc_lgt = 0
                self.context_stack.pop()
                return tok
            tmp_buf = self._gettmpbuf(self.pos)
            ctx = self.context_stack[-1]
            rules = self.rules[ctx]
            for token_regex, token_type in rules:
                pos = self.pos
                assert pos >= 0
                m = self.match(token_regex, tmp_buf, pos)
                if m:
                    start, end = self._getstartend(m)
                    value = self.buf[start:end]
                    if token_type == 'H_NEW_LINE':
                        self.lineno += 1
                    elif token_type == 'T_COMMENT':
                        self.lineno += value.count('\n')
                    elif token_type == 'T_CONSTANT_ENCAPSED_STRING':
                        self.lineno += value.count("\n")
                    # tokens changing the context
                    tok = Token(token_type, value, self.lineno)
                    tok = self.maybe_change_context(ctx, tok, token_type,
                                                    end)
                    self.last_token = token_type
                    return tok

            # if we're here, no rule matched
            raise LexerError("unknown token", self.lineno)

    def maybe_change_context(self, ctx, tok, token_type, endpos):
        # print self.context_stack, tok.name, tok.value
        if ctx == CONTEXT_OBJECT_ACCESS:
            self.context_stack.pop()
        elif (ctx == CONTEXT_NORMAL and
              token_type == "T_CONSTANT_ENCAPSED_STRING" and
              (tok.value[0] == '"' or tok.value[:2] == 'b"')):
            newtok = self._scan_double_quote(tok)
            if newtok.name == '"':
                # we have to rewind a little
                ofs = 1
                if tok.value[0] == 'b':
                    ofs += 1
                self.pos = endpos - len(tok.value) + ofs
            else:
                self.pos = endpos
            return newtok

        elif ctx == CONTEXT_BACKTICK and tok.value[0] == '`':
            self.context_stack.pop()
        elif ctx == CONTEXT_NORMAL and token_type == '`':
            self.context_stack.append(CONTEXT_BACKTICK)
        elif ctx == CONTEXT_BACKTICK and token_type == '"':
            self.context_stack.append(CONTEXT_DOUBLEQUOTE)
        elif ctx == CONTEXT_BACKTICK and token_type == '`':
            self.context_stack.pop()
        elif ctx == CONTEXT_NORMAL and token_type == "T_START_HEREDOC":
            lgt = 3
            if tok.value.startswith("b"):
                lgt += 1
            start = lgt
            end = len(tok.value) - 1
            while tok.value[start] in (' ', '\t'):
                start += 1
            while tok.value[end] in (' ', '\t'):
                end -= 1
            assert end >= 0
            marker = tok.value[start:end]
            if marker.startswith('"'):
                if not marker.endswith('"'):
                    raise LexerError("wrong marker", self.lineno)
                end = len(marker) - 1
                assert end >= 0
                marker = marker[1:end]
            heredoc_marker = "\n" + marker + ";"
            start = self.pos + len(tok.value) - 1
            assert start >= 0
            self.heredoc_finish = self.buf.find(heredoc_marker, start)
            self.heredoc_lgt = len(heredoc_marker) - 1
            if self.heredoc_finish == -1:
                # XXX case where heredoc does not end with [;]
                # its then heredoc is an argument and end like ... HEND );
                heredoc_marker = "\n" + marker
                self.heredoc_finish = self.buf.find(heredoc_marker, start)
                if self.heredoc_finish == -1:
                    raise LexerError("unfinished heredoc", self.lineno)
                self.heredoc_lgt = len(heredoc_marker)

            self.context_stack.append(CONTEXT_HEREDOC)
        elif ctx == CONTEXT_DOUBLEQUOTE and token_type == '"':
            self.context_stack.pop()
        elif ctx == CONTEXT_BACKTICK and token_type == '"':
            self.context_stack.pop()
        elif ((ctx == CONTEXT_DOUBLEQUOTE or ctx == CONTEXT_HEREDOC
               or ctx == CONTEXT_BACKTICK) and
              token_type == "T_DOLLAR_OPEN_CURLY_BRACES"):
            self.pos = endpos - 1
            self.context_stack.append(CONTEXT_CURLY_BRACES)
            return tok
        elif (ctx == CONTEXT_CURLY_BRACES and token_type == "{"
              and self.last_token == "T_DOLLAR_OPEN_CURLY_BRACES"):
            # instead, we recognize it as a variable
            tmp_buf = self._gettmpbuf(self.pos)
            m = self.match(self.var_re, tmp_buf, self.pos)
            assert m is not None
            start, end = self._getstartend(m)
            tok = Token("T_VARIABLE", self.buf[start:end], tok.lineno)
            self.pos = end
            return tok
        elif ((ctx == CONTEXT_DOUBLEQUOTE or ctx == CONTEXT_HEREDOC)
              and token_type == "T_VARIABLE"):
            # only if the next one is [
            if self.buf[endpos] == "[":
                self.context_stack.append(CONTEXT_BRACKETS)
        elif ((ctx == CONTEXT_DOUBLEQUOTE or ctx == CONTEXT_HEREDOC) and
              token_type == "T_OBJECT_OPERATOR"):
            if (self.last_token != "T_VARIABLE" or
                not self.buf[self.pos + 2].isalpha()):
                tok = Token("T_ENCAPSED_AND_WHITESPACE", tok.value,
                            tok.lineno)
            else:
                self.context_stack.append(CONTEXT_OBJECT_ACCESS)
        elif token_type == "T_OBJECT_OPERATOR":
            self.context_stack.append(CONTEXT_OBJECT_ACCESS)
        elif ctx == CONTEXT_BRACKETS and token_type == "]":
            self.context_stack.pop()
        elif ctx == CONTEXT_CURLY_BRACES and token_type == "}":
            # XXX this is incorrect but we don't care at the moment
            #     if someone inserts } inside ] we have to do something else
            #     like scan grammar until we hit it
            self.context_stack.pop()
        self.pos = endpos
        return tok

    def tokens(self):
        """ Returns an iterator to the tokens found in the buffer.
        """
        while 1:
            tok = self.token()
            # print tok.name, tok.value
            if tok is None:
                break
            while tok.name in ('H_NEW_LINE', 'H_WHITESPACE',
                               'T_COMMENT', 'H_TABULATURE'):
                tok = self.token()
                if tok is None:
                    break
            yield tok
