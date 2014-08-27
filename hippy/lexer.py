import py

from rpython.rlib import rpath
from rpython.rlib.parsing.regexparse import parse_regex
from rpython.rlib.parsing import regex
from rpython.rlib.parsing.lexer import LexingDFARunner
from rpython.rlib.parsing.deterministic import LexerError as rpy_LexerError

from rply import ParsingError
from rply.token import BaseBox, SourcePosition
from rply import token


def _basebox_getsourcepos(self):
    return self.lineno

def _basebox_append_item(self, item):
    raise NotImplementedError(self)

BaseBox._attrs_ = ['lineno']
BaseBox.getsourcepos = _basebox_getsourcepos
BaseBox.append_item = _basebox_append_item

class Token(BaseBox):

    source_position_class = SourcePosition

    def __init__(self, name, source, source_pos=SourcePosition(0, 0, 0)):
        self.name = name
        self.source = source
        self.source_pos = source_pos

    def copy(self):
        return self.__class__(self.name, self.source, self.source_pos)

    def gettokentype(self):
        return self.name

    def getsourcepos(self):
        return self.source_pos.lineno

    def getstr(self):
        return self.source

    def __repr__(self):
        return "Token(%r, %r)" % (self.name, self.source)


token.Token=Token


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
        self.source_pos = source_pos.lineno

    def __str__(self):
        return 'LexerError("%s", %d)' % (self.message, self.source_pos)




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



def group(*choices):
    return '(' + '|'.join(choices) + ')'


_KEYWORDS = (
    ("print", 'T_PRINT'),
    ("echo", 'T_ECHO'),
    ("instanceof", 'T_INSTANCEOF'),
    ("new", 'T_NEW'),
    ("clone", 'T_CLONE'),
    ("exit", 'T_EXIT'),
    ("die", 'T_EXIT'),
    ("if", 'T_IF'),
    ("elseif", 'T_ELSEIF'),
    ("else", 'T_ELSE'),
    ("endif", 'T_ENDIF'),
    ("array", 'T_ARRAY'),
    ("Array", "T_ARRAY"),
    ("include", 'T_INCLUDE'),
    ("include_once", 'T_INCLUDE_ONCE'),
    ("eval", 'T_EVAL'),
    ("require", 'T_REQUIRE'),
    ("require_once", 'T_REQUIRE_ONCE'),
    ("or", 'T_LOGICAL_OR'),
    ("xor", 'T_LOGICAL_XOR'),
    ("and", 'T_LOGICAL_AND'),
    ("foreach", 'T_FOREACH'),
    ("endforeach", 'T_ENDFOREACH'),
    ("do", 'T_DO'),
    ("while", 'T_WHILE'),
    ("endwhile", 'T_ENDWHILE'),
    ("for", 'T_FOR'),
    ("endfor", 'T_ENDFOR'),
    ("declare", 'T_DECLARE'),
    ("enddeclare", 'T_ENDDECLARE'),
    ("as", 'T_AS'),
    ("switch", 'T_SWITCH'),
    ("endswitch", 'T_ENDSWITCH'),
    ("case", 'T_CASE'),
    ("default", 'T_DEFAULT'),
    ("break", 'T_BREAK'),
    ("continue", 'T_CONTINUE'),
    ("goto", 'T_GOTO'),
    ("function", 'T_FUNCTION'),
    ("const", 'T_CONST'),
    ("return", 'T_RETURN'),
    ("try", 'T_TRY'),
    ("catch", 'T_CATCH'),
    ("throw", 'T_THROW'),
    ("use", 'T_USE'),
    #"insteadof", 'T_INSTEADOF'),
    ("global", 'T_GLOBAL'),
    ("static", 'T_STATIC'),
    ("abstract", 'T_ABSTRACT'),
    ("final", 'T_FINAL'),
    ("private", 'T_PRIVATE'),
    ("protected", 'T_PROTECTED'),
    ("public", 'T_PUBLIC'),
    ("var", 'T_VAR'),
    ("unset", 'T_UNSET'),
    ("isset", 'T_ISSET'),
    ("empty", 'T_EMPTY'),
    ("class", 'T_CLASS'),
    #"trait", 'T_TRAIT'),
    ("interface", 'T_INTERFACE'),
    ("extends", 'T_EXTENDS'),
    ("implements", 'T_IMPLEMENTS'),
    ("list", 'T_LIST'),
    ("namespace", 'T_NAMESPACE'),
    ("__halt_compiler", 'T_HALT_COMPILER'),
    ("__FILE__", 'T_FILE'),
    ("__CLASS__", 'T_CLASS_C'),
    #"__TRAIT__", 'T_TRAIT_C'),
    ("__METHOD__", 'T_METHOD_C'),
    ("__FUNCTION__", 'T_FUNC_C'),
    ("__LINE__", 'T_LINE'),
    ("__NAMESPACE__", 'T_NS_C'),
    ("__DIR__", 'T_DIR')
)

def normalize_keywords(keywords):
    ret = []
    for k, t in keywords:
        rule = "".join([
            group(a.lower(), a.upper()) if a.isalpha() else a for a in k
        ])

        ret.append((parse_regex(rule), t))

    return ret

KEYWORDS = normalize_keywords(_KEYWORDS)

_RULES = (
    ("b?\<\<\<[^\n]*\n", 'T_START_HEREDOC'),
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

    ("\( *(int) *\)",   'T_INT_CAST'),
    ("\( *(integer) *\)",   'T_INT_CAST'),
    ("\( *(real) *\)",   'T_DOUBLE_CAST'),
    ("\( *(double) *\)",   'T_DOUBLE_CAST'),
    ("\( *(float) *\)",   'T_DOUBLE_CAST'),
    ("\( *(string) *\)",   'T_STRING_CAST'),
    ("\( *(binary) *\)",   'T_STRING_CAST'),
    ("\( *(array) *\)",   'T_ARRAY_CAST'),
    ("\( *(object) *\)",   'T_OBJECT_CAST'),
    ("\( *(bool) *\)",   'T_BOOL_CAST'),
    ("\( *(boolean) *\)",   'T_BOOL_CAST'),
    ("\( *(unset) *\)",   'T_UNSET_CAST'),
    ("\( *(unicode) *\)",   'T_UNICODE_CAST'),


    (group("([0-9]*\.[0-9]*|[0-9][0-9]*)[eE](\+|\-)?[0-9][0-9]*",
           "[0-9]+\.[0-9]+",
           "\.[0-9]+",
           "[0-9]+\."), 'T_DNUMBER'),

    (group("0x([0-9a-fA-F])*", "0X([0-9a-fA-F])*", "[0-9]+"), 'T_LNUMBER'),

    ("\$[a-zA-Z_][0-9a-zA-Z_]*", 'T_VARIABLE'),
    #("\$\{[a-zA-Z]*\}", 'T_STRING_VARNAME'),

    # ("(/\*\*([^*]|[\n]|(\*+([^*/]|[\n])))*\*+/)", 'T_DOC_COMMENT'),
    ("(/\*([^*]|[\n]|(\*+([^*/]|[\n])))*\*+/)|(//[^\n]*)|(#[^\n]*)", 'T_COMMENT'),

    ("\-\>", 'T_OBJECT_OPERATOR'),
    ("\=\>", 'T_DOUBLE_ARROW'),

    #("open tag", 'T_OPEN_TAG'),
    #("open tag with echo", 'T_OPEN_TAG_WITH_ECHO'),
    #("close tag", 'T_CLOSE_TAG'),
    ("whitespace", 'T_WHITESPACE'),
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
    (" ", 'H_WHITESPACE')
)

RULES = [(parse_regex(rule), name) for rule, name in _RULES]

_RULES_FOR_DOUBLE_QUOTE = (
    ("\$[a-zA-Z_][0-9a-zA-Z_]*(->[a-zA-Z_][0-9a-zA-Z_]*)?", 'T_VARIABLE'),
    (r"\{\$|\$\{", "T_DOLLAR_OPEN_CURLY_BRACES"),
    (r"([^\"\$\{\\]|\\.|\$[^a-zA-Z\"\{]|{[^\$])+", "T_ENCAPSED_AND_WHITESPACE"),
    (r"\$", "T_DOLLAR"),
    ('"', '"'),
)

RULES_FOR_DOUBLE_QUOTE = [(parse_regex(rule), name) for rule, name in _RULES_FOR_DOUBLE_QUOTE]

_RULES_FOR_BACKTICK = (
    (r"\{\$|\$\{", "T_DOLLAR_OPEN_CURLY_BRACES"),
    ("`", '`'),
    ("\}", '}'),
    ("\{", '{'),
    ("\$[a-zA-Z_][0-9a-zA-Z_]*(->[a-zA-Z_][0-9a-zA-Z_]*)?", 'T_VARIABLE'),

    (r'([^\$\{\`\}\\]|\\.|\$[^a-zA-Z\"\{]|{[^$])+', "T_ENCAPSED_AND_WHITESPACE"),
)

RULES_FOR_BACKTICK = [(parse_regex(rule), name) for rule, name in _RULES_FOR_BACKTICK]

_RULES_FOR_HEREDOC = (
    ("\$[a-zA-Z_][0-9a-zA-Z_]*(->[a-zA-Z_][0-9a-zA-Z_]*)?", 'T_VARIABLE'),
    (r"\{\$|\$\{", "T_DOLLAR_OPEN_CURLY_BRACES"),
    (r"([^\$\{\\]|\\.|\$[^a-zA-Z_\{]|{[^\$])+", "T_ENCAPSED_AND_WHITESPACE"),
)

RULES_FOR_HEREDOC = [(parse_regex(rule), name) for rule, name in _RULES_FOR_HEREDOC]

_RULES_FOR_BRACKETS = (
    ("\]", "]"),
    ("\[", "["),
    ("\d+", "T_NUM_STRING"),
    ("\$[a-zA-Z_][0-9a-zA-Z_]*", 'T_VARIABLE'),
    ("[a-zA-Z_][0-9a-zA-Z_]*", 'T_STRING'),
    (" ", 'H_WHITESPACE')
)

RULES_FOR_BRACKETS = [(parse_regex(rule), name) for rule, name in _RULES_FOR_BRACKETS]

_RULES_FOR_CURLY_BRACES = (
    ("\$?[a-zA-Z_][0-9a-zA-Z_]*", 'T_VARIABLE'),
    ("\}", '}'),
    ("\[", "["),
)

RULES_FOR_CURLY_BRACES = [(parse_regex(rule), name) for rule, name in _RULES_FOR_CURLY_BRACES]

ALL_RULES = _KEYWORDS +\
            _RULES +\
            _RULES_FOR_DOUBLE_QUOTE +\
            _RULES_FOR_BACKTICK +\
            _RULES_FOR_HEREDOC +\
            _RULES_FOR_BRACKETS +\
            _RULES_FOR_CURLY_BRACES


(CONTEXT_NORMAL,
 CONTEXT_OBJECT_ACCESS,
 CONTEXT_DOUBLEQUOTE,
 CONTEXT_CURLY_BRACES,
 CONTEXT_BRACKETS,
 CONTEXT_HEREDOC,
 CONTEXT_BACKTICK) = range(7)


class Lexer(object):

    def get_runner(self, context, text):
        matcher, automaton = self.runners_context[context]

        # Do I need to care?
        ignore = []
        eof = False

        return LexingDFARunner(matcher, automaton, text, ignore, eof,
                               token_class=self.token_class)


    def __init__(self):
        self.token_class = Token

        RULES_FOR_CONTEXT_BRACKETS = [
            (parse_regex("[a-zA-Z_][a-zA-Z_0-9]*"), 'T_VARIABLE')
        ]

        self.rules = {
            CONTEXT_NORMAL: KEYWORDS + RULES,
            CONTEXT_OBJECT_ACCESS: RULES,
            CONTEXT_DOUBLEQUOTE: RULES_FOR_DOUBLE_QUOTE,
            CONTEXT_CURLY_BRACES: KEYWORDS + RULES_FOR_CONTEXT_BRACKETS + RULES,
            CONTEXT_BRACKETS: RULES_FOR_BRACKETS,
            CONTEXT_HEREDOC: RULES_FOR_HEREDOC,
            CONTEXT_BACKTICK: RULES_FOR_BACKTICK
         }

        self.runners_context = {}
        for context, rules in self.rules.items():

            base_dir = rpath.dirname(__file__)
            runner_name = 'runner_%s' % context

            try:
                lexer_runner = __import__(
                    'hippy.%s.%s' % ("lexer_cache", runner_name) , None, None,
                    ['recognize', 'automaton']
                )

                self.runners_context[context] = (
                    lexer_runner.recognize, lexer_runner.automaton)
            except ImportError:
                runner_file = rpath.join(base_dir,
                    ["lexer_cache", "%s.py" % runner_name])

                names, regexs = [], []
                for rule, name in rules:
                    names.append(name)
                    regexs.append(rule)

                rex = regex.LexingOrExpression(regexs, names)
                automaton = rex.make_automaton()
                automaton = automaton.make_deterministic(names)
                automaton.optimize()
                code = automaton.generate_lexing_code()
                open(runner_file, "w").write(code)

                exec py.code.Source(code).compile()
                self.runners_context[context] = (recognize, automaton)

    def input(self, buf, pos, lineno):

        self.buf = buf
        self.context_stack = [CONTEXT_NORMAL]
        self.pos = pos - 1
        self.lineno = lineno
        self.last_token = None

        self.here_doc_id = None
        self.here_doc_end = -1
        self.here_doc_end_line = -1
        self.here_doc_finish = False

        self.runners = {
            CONTEXT_NORMAL: self.get_runner(CONTEXT_NORMAL, self.buf),
            CONTEXT_OBJECT_ACCESS: self.get_runner(CONTEXT_OBJECT_ACCESS, self.buf),
            CONTEXT_DOUBLEQUOTE: self.get_runner(CONTEXT_DOUBLEQUOTE, self.buf),
            CONTEXT_CURLY_BRACES: self.get_runner(CONTEXT_CURLY_BRACES, self.buf),
            CONTEXT_BRACKETS: self.get_runner(CONTEXT_BRACKETS, self.buf),
            CONTEXT_HEREDOC: self.get_runner(CONTEXT_HEREDOC, self.buf),
            CONTEXT_BACKTICK: self.get_runner(CONTEXT_BACKTICK, self.buf),
        }

    def token(self):

        while 1:
            try:
                ctx = self.context_stack[-1]
                runner = self.runners[ctx]

                runner.last_matched_index = self.pos
                runner.lineno = self.lineno
                try:
                    tok = runner.find_next_token()
                except rpy_LexerError as e:
                    raise LexerError("Syntax error", e.source_pos)

                last_pos = self.pos
                self.pos = runner.last_matched_index
                self.lineno = runner.lineno

                if (tok.name == 'T_COMMENT' and
                    not tok.getstr().startswith('/*')):
                    s = tok.getstr()
                    pos = s.find('?>')
                    if pos >= 0:
                        self.pos = pos + last_pos

                if tok.name not in ('H_NEW_LINE', 'H_WHITESPACE',
                                    'T_COMMENT', 'H_TABULATURE'):

                    tok = self.maybe_change_context(ctx, tok, runner)

                    if tok:
                        self.last_token = tok
                        yield tok


            except StopIteration:
                break

    def maybe_change_context(self, ctx, tok, runner):
        if ctx == CONTEXT_OBJECT_ACCESS:
            self.context_stack.pop()

        elif ctx == CONTEXT_BACKTICK and tok.getstr()[0] == '`':
            self.context_stack.pop()

        elif ctx == CONTEXT_NORMAL and tok.name == '`':
            self.context_stack.append(CONTEXT_BACKTICK)

        elif tok.name == "T_OBJECT_OPERATOR":
            self.context_stack.append(CONTEXT_OBJECT_ACCESS)

        elif (ctx == CONTEXT_NORMAL and
              tok.name == "T_CONSTANT_ENCAPSED_STRING" and
              (tok.getstr()[0] == '"' or tok.getstr().startswith('b"'))):
            newtok = self._scan_double_quote(tok)
            if newtok.name == '"':
                ofs = 1
                if tok.getstr()[0] == 'b':
                    ofs += 1
                self.pos = runner.last_matched_index - len(tok.getstr()) + ofs
            return newtok

        elif ctx == CONTEXT_DOUBLEQUOTE and tok.name == '"':
            self.context_stack.pop()

        elif (ctx == CONTEXT_DOUBLEQUOTE and
              tok.name == "T_ENCAPSED_AND_WHITESPACE" and
              tok.getstr().endswith('$"')):
            self.pos -= 1
            tok.source = tok.source[:-1]

        elif ctx == CONTEXT_BACKTICK and tok.name == '"':
            self.context_stack.pop()

        elif ((ctx == CONTEXT_DOUBLEQUOTE or
               ctx == CONTEXT_HEREDOC or
               ctx == CONTEXT_BACKTICK) and tok.name == "T_DOLLAR_OPEN_CURLY_BRACES"):

            self.context_stack.append(CONTEXT_CURLY_BRACES)
            if tok.getstr() == "{$":
                self.pos -= 1
            return tok

        elif ctx == CONTEXT_NORMAL and tok.name == "T_START_HEREDOC":
            here_doc_id = tok.getstr().lstrip("b<<<").lstrip("<<<").strip()
            if here_doc_id.startswith('"'):
                if not here_doc_id.endswith('"'):
                    raise LexerError("wrong marker", tok.source_pos)
                end = len(here_doc_id) - 1
                assert end >= 0
                here_doc_id = here_doc_id[1:end]
            self.here_doc_id = here_doc_id
            token_end = tok.source_pos.idx + len(tok.source) - 1
            assert token_end >= 0
            search_string = '\n' + self.here_doc_id
            id_len = len(search_string)
            search_start = token_end
            while True:
                candidate = self.buf[search_start:].find(search_string)
                if candidate < 0:
                    raise LexerError("unfinished heredoc", tok.source_pos)
                try:
                    semicolon = 0
                    if self.buf[search_start + candidate + id_len] == ';':
                        semicolon = 1
                    if self.buf[search_start + candidate + id_len + semicolon] == '\n':
                        here_doc_end = search_start + candidate
                        break
                except IndexError:
                    here_doc_end = search_start + candidate
                    break
                search_start = search_start + candidate + id_len
            heredoc_content = self.buf[token_end:here_doc_end]
            self.here_doc_pos = token_end
            self.here_doc_end = here_doc_end
            self.here_doc_end_line = self.lineno + heredoc_content.count("\n")
            self.context_stack.append(CONTEXT_HEREDOC)

        elif ((ctx == CONTEXT_DOUBLEQUOTE or
               ctx == CONTEXT_HEREDOC) and tok.name == "T_VARIABLE"):
            if runner.text[tok.source_pos.idx + len(tok.getstr())] == "[":
                self.context_stack.append(CONTEXT_BRACKETS)

        elif ctx == CONTEXT_HEREDOC:

            if self.here_doc_finish:
                tok.source = self.here_doc_id
                tok.name = 'T_END_HEREDOC'
                tok.source_pos.lineno -= 1

                self.pos = self.here_doc_end + len(self.here_doc_id)
                self.lineno = self.here_doc_end_line

                self.context_stack.pop()

                self.here_doc_id = None
                self.here_doc_end = -1
                self.here_doc_end_line = -1
                self.here_doc_finish = False

            elif tok.source_pos.idx + len(tok.source) > self.here_doc_end:

                start = tok.source_pos.idx
                assert start >= 0
                stop = self.here_doc_end
                assert stop >= 0

                source = self.buf[start:stop]
                self.here_doc_finish = True
                self.pos = self.here_doc_end

                if not source:
                    return None
                else:
                    tok.source = source

        elif ctx == CONTEXT_BRACKETS and tok.name == "]":
            self.context_stack.pop()

        elif ctx == CONTEXT_CURLY_BRACES and tok.name == "}":
            # XXX this is incorrect but we don't care at the moment
            #     if someone inserts } inside ] we have to do something else
            #     like scan grammar until we hit it
            self.context_stack.pop()

        return tok

    def _scan_double_quote(self, tok):
        p = 1
        v = tok.getstr()
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
                    return Token('"', '"', tok.source_pos)
                elif c == '\\':
                    backslash = True
            else:
                backslash = False
            p += 1
        assert False
