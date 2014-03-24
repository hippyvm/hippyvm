from hippy.objects.nullobject import W_NullObject
from hippy.function import ArgDesc, Signature

def test_print_argdesc():
    desc = ArgDesc('x')
    assert desc.str() == '$x'
    desc = ArgDesc('x', typehint='array', isref=True, default=W_NullObject())
    assert desc.str() == 'array &$x = NULL'

def test_print_signature():
    signature = Signature([ArgDesc('x'),
        ArgDesc('y', typehint='array', isref=True, default=W_NullObject())])
    assert signature.str() == '($x, array &$y = NULL)'

def test_match_signature():
    sig1 = Signature([ArgDesc('x')])
    sig2 = Signature([ArgDesc('x'),
        ArgDesc('y', typehint='array', isref=True, default=W_NullObject())])
    assert sig2.matches(sig1)
    assert not sig1.matches(sig2)
