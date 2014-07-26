from hippy.builtin import wrap,   Optional


@wrap(['interp',   str,   str,   str,   Optional(str),   Optional(str)])
def mail(interp,   to,   topic,   content,
         extra_headers=None,   extra_params=None):
    # XXXX dummy
    return interp.space.w_True
