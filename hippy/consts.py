
""" Various important consts
"""

ARGVAL = 0xffff
ARGVAL1 = 0xfffe
ARGVAL2 = 0xfffc

# name, num_args, effect on stack, # effect on the alternate ptr stack
BYTECODES = [
    ('ILLEGAL', 0, 0),
    ('DISCARD_TOP', 0, -1),
    ('DUP', 0, 1),
    ('SWAP', 0, 0),
    ('ROT', 1, 0),
    ('STORE', 0, 0), # -1
    ('STORE_UNIQUE', 0, 0), # -1
    ('RESOLVE_FOR_WRITING', 0, +1), # -1
    ('STORE_REF', 0, 0), # -1
    ('LOAD_CONST', 1, +1),
    ('LOAD_STATIC', 1, +1),
    ('INTERPOLATE', 1, ARGVAL),
    ('LOAD_NAMED_CONSTANT', 1, +1),
    ('GETCONSTANT_NS', 0, -1),
    ('LOAD_NAME', 1, +1),
    ('LOAD_VAR', 1, +1),
    ('LOAD_VAR_SWAP', 1, +1),
    ('LOAD_VAR_INDIRECT', 0, 0),
    ('LOAD_VAR_ITEM_PTR', 1, 0), # -1+1
    ('LOAD_NULL', 0, +1),
    ('LOAD_NONE', 0, +1),
    ('DUMMY_STACK_PUSH', 0, +1),
    ('BINARY_ADD', 0, -1),
    ('BINARY_OR_', 0, -1),
    ('BINARY_AND_', 0, -1),
    ('BINARY_XOR', 0, -1),
    ('LOGICAL_XOR', 0, -1),
    ('BINARY_SUB', 0, -1),
    ('BINARY_MUL', 0, -1),
    ('BINARY_DIV', 0, -1),
    ('BINARY_MOD', 0, -1),
    ('BINARY_CONCAT', 0, -1),
    ('BINARY_GT', 0, -1),
    ('BINARY_LT', 0, -1),
    ('BINARY_GE', 0, -1),
    ('BINARY_LE', 0, -1),
    ('BINARY_EQ', 0, -1),
    ('BINARY_IS', 0, -1),
    ('BINARY_ISNOT', 0, -1),
    ('BINARY_NE', 0, -1),
    ('BINARY_LSHIFT', 0, -1),
    ('BINARY_RSHIFT', 0, -1),
    ('BINARY_INSTANCEOF', 0, -1),
    ('SUFFIX_PLUSPLUS', 0, 1), # -1
    ('SUFFIX_MINUSMINUS', 0, 1), # -1
    ('PREFIX_PLUSPLUS', 0, 1), # -1
    ('PREFIX_MINUSMINUS', 0, 1), # -1
    ('UNARY_PLUS', 0, 0),
    ('UNARY_MINUS', 0, 0),
    ('LOGICAL_NOT', 0, 0),
    ('BITWISE_NOT', 0, 0),
    ('IS_TRUE', 0, 0),
    ('ECHO', 0, -1),
    ('JUMP_IF_FALSE', 1, -1),
    ('JUMP_IF_FALSE_NO_POP', 1, 0),
    ('JUMP_IF_TRUE_NO_POP', 1, 0),
    ('JUMP_FORWARD', 1, 0),
    ('JUMP_BACKWARD', 1, 0),
    ('JUMP_BACK_IF_TRUE', 1, -1),
    ('THROW', 0, -1),
    ('PUSH_CATCH_BLOCK', 1, -1),
    ('CASE_IF_EQ', 1, -1),
    ('RETURN', 0, -1),
    ('GETFUNC', 0, 0),
    ('GETFUNC_NS', 0, -1),
    ('GETCLASS', 1, 0),
    ('GETMETH', 0, 0), # -1
    ('GETSTATICMETH', 0, -1),
    ('ARG_BY_VALUE', 1, 0),
    ('ARG_BY_PTR', 1, +1), # -1
    ('CALL', 1, ARGVAL),
    ('DEREF', 0, 0),
    ('GETITEM', 0, -1),
    ('GETITEM_NOPOP', 0, 0),
    ('GETITEM_VAR', 1, 0),
    ('VAR_PTR', 1, 0), # +1
    ('THIS_PTR', 0, 0), # +1
    ('VAR_INDIRECT_PTR', 0, -1), # +1
    ('REF_PTR', 0, -1), # +1
    ('MAKE_REF_PTR', 0, -1), # +1
    ('ITEM_PTR', 0, -1), # -1+1
    ('APPEND_PTR', 0, 0), # -1+1
    ('PTR_DEREF', 0, 1), # 0
    ('SET_FAST', 1, 0),
    ('SET_REF_INDIRECT', 0, -1),
    ('PTR_UNSET', 0, 0), # -1
    ('UNSET_FAST', 1, 0),
    ('UNSET_VAR_INDIRECT', 0, -1),
    ('PTR_ISSET', 0, +1), # -1
    ('PTR_EMPTY', 0, +1), # -1
    ('MAKE_ARRAY', 1, ARGVAL1),
    ('MAKE_HASH', 1, ARGVAL2),
    ('CREATE_ITER', 0, 0),
    ('CREATE_ITER_REF', 0, 0),
    ('NEXT_VALUE_ITER', 1, +1),
    ('NEXT_ITEM_ITER', 1, +2),
    ('DECLARE_GLOBAL', 1, 0),
    ('DECLARE_GLOBAL_INDIRECT', 0, -1),
    ('DECLARE_FUNC', 1, 0),
    ('DECLARE_CLASS', 1, 0),
    ('LOAD_CLOSURE', 1, +1),
    ('LOAD_STATIC_CLOSURE', 1, +1),
    ('PUT_CLOSURE_VARS', 1, ARGVAL),
    ('CAST_ARRAY', 0, 0),
    ('CAST_INT', 0, 0),
    ('CAST_FLOAT', 0, 0),
    ('CAST_STRING', 0, 0),
    ('CAST_OBJECT', 0, 0),
    ('GETATTR', 0, -1),
    ('THIS_ATTR', 0, 0),
    ('ATTR_PTR', 0, -1), # -1+1
    ('STATICMEMBER', 0, -1),
    ('STATICMEMBER_PTR', 0, -2), # +1
    ('CLASSCONST', 1, 0),
    ('ABSTRACT_METHOD', 0, 0),
    ('CLONE', 0, 0),
    ('SILENCE', 0, 0),
    ('UNSILENCE', 0, 0),
    ('_CHECKSTACK', 1, 0), # debug: at places where 'break' or 'continue' go
    ('BREAK_CONTINUE_POP', 1, 0), # (*) see below
    ('TYPEHINT_CLASS', 1, -1),
    ('TYPEHINT_ARRAY', 1, 0),
    ('REQUIRE', 0, 0),
    ('REQUIRE_ONCE', 0, 0),
    ('INCLUDE', 0, 0),
    ('INCLUDE_ONCE', 0, 0),
    ('PRINT_EXPR', 0, -1),
    ('POPEN', 0, 0),
    ('EVAL', 1, 0),
]
# (*) the stack effect of BREAK_CONTINUE_POP is not really 0: it
# pops 'arg' items.  But for the simple bytecode.count_stack_depth()
# we need to say 0, as it appears in the middle of a loop, just
# before a JUMP_xx that implements 'break;' or 'continue;'

assert len(BYTECODES) < 256
BYTECODES.sort(key=lambda t: t[1])   # first the no-arg, then the one-arg

BYTECODE_HAS_ARG = 0
while BYTECODES[BYTECODE_HAS_ARG][1] == 0:
    BYTECODE_HAS_ARG += 1
BYTECODE_NAMES = []
BYTECODE_STACK_EFFECTS = []

BINOP_COMPARISON_LIST = ['le', 'ge', 'lt', 'gt', 'eq', 'ne']
BINOP_BITWISE = ['or_', 'and_', 'xor']
BINOP_LIST = ['add', 'mul', 'sub', 'mod', 'div'] + BINOP_COMPARISON_LIST

def _setup():
    for i, (bc, numargs, stack_effect) in enumerate(BYTECODES):
        globals()[bc] = i
        assert numargs == (i >= BYTECODE_HAS_ARG)
        BYTECODE_NAMES.append(bc)
        BYTECODE_STACK_EFFECTS.append(stack_effect)
_setup()

BIN_OP_TO_BC = {'+': BINARY_ADD, '*': BINARY_MUL, '-': BINARY_SUB,
                '|': BINARY_OR_, '&': BINARY_AND_, '^': BINARY_XOR,
                'xor': LOGICAL_XOR,
                '/': BINARY_DIV, '>': BINARY_GT, '<': BINARY_LT,
                '>=': BINARY_GE, '<=': BINARY_LE, '==': BINARY_EQ,
                '!=': BINARY_NE, '<>': BINARY_NE,
                '.': BINARY_CONCAT, '>>': BINARY_RSHIFT,
                '<<': BINARY_LSHIFT, '%': BINARY_MOD, '===': BINARY_IS,
                '!==': BINARY_ISNOT, 'instanceof': BINARY_INSTANCEOF}
SUFFIX_OP_TO_BC = {'++': SUFFIX_PLUSPLUS, '--': SUFFIX_MINUSMINUS}
PREFIX_OP_TO_BC = {'++': PREFIX_PLUSPLUS, '--': PREFIX_MINUSMINUS,
        '+': UNARY_PLUS, '-': UNARY_MINUS, '!': LOGICAL_NOT, '~': BITWISE_NOT}
CAST_TO_BC = {'array': CAST_ARRAY,
              'bool': IS_TRUE,
              'boolean': IS_TRUE,
              'int': CAST_INT,
              'integer': CAST_INT,
              'float': CAST_FLOAT,
              'double': CAST_FLOAT,
              'real': CAST_FLOAT,
              'binary': CAST_STRING,
              'string': CAST_STRING,
              'object': CAST_OBJECT}

ARG_ARGUMENT, ARG_REFERENCE = 'A', 'R'    # no relation to 'A'rmin 'R'igo :-)

ACC_STATIC     = 0x01
ACC_ABSTRACT   = 0x02
ACC_FINAL      = 0x04

ACC_INTERFACE  = 0x80

ACC_PUBLIC     = 0x0100
ACC_PROTECTED  = 0x0200
ACC_PRIVATE    = 0x0400
ACCMASK_VISIBILITY = ACC_PUBLIC | ACC_PROTECTED | ACC_PRIVATE

ACC_IMPLICIT_PUBLIC = 0x1000  # instance property (for ReflectionProperty)

if __name__ == '__main__':
    for i, (bc, _, _) in enumerate(BYTECODES):
        print i, bc
