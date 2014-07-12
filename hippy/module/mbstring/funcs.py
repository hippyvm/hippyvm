
from hippy.builtin import wrap, Optional


@wrap(['interp', str, Optional(str)], error=False)
def mb_strlen(interp, s, encoding='utf-8'):
    encoding = encoding.lower()
    if encoding != 'utf-8' and encoding != 'utf8':
        interp.warn('mb_strlen(): Unsupported encoding "%s"' % encoding)
        return interp.space.w_False
    #
    # special-case logic to handle UTF-8 the fast way
    length = end = len(s)
    i = 0
    while i < end:
        c = s[i]
        if ord(c) < 0xc0:
            i += 1
        elif ord(c) < 0xe0:
            length -= 1
            i += 2
        elif ord(c) < 0xf0:
            length -= 2
            i += 3
        else:
            length -= 3
            i += 4
    return interp.space.wrap(length)
