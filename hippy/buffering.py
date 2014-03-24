from rpython.rlib.rstring import StringBuilder
from hippy.builtin import wrap, Optional
from hippy.objects.base import W_Root
from hippy.error import InvalidCallback


FLUSH = 4

class Buffer(object):
    def __init__(self, space, callback, chunk_size, prev):
        self.space = space
        self.callback = callback
        self.chunk_size = chunk_size
        self.buffer = StringBuilder(chunk_size)
        self.buffer_len = 0
        self.prev = prev

    def reset(self):
        self.buffer = StringBuilder(self.chunk_size)
        self.buffer_len = 0

    def getlength(self):
        if self.prev is None:
            return 1
        return self.prev.getlength() + 1

    def write(self, str):
        self.buffer.append(str)
        if self.chunk_size and len(str) + self.buffer_len >= self.chunk_size:
            self.flush()
            self.reset()
        else:
            self.buffer_len += len(str)

    def flush(self):
        val = self.buffer.build()
        if self.callback is not None:
            flags = FLUSH
            w_buffer = self.space.call_args(self.callback,
                                            [self.space.wrap(val),
                                             self.space.wrap(flags)])
            val = self.space.str_w(w_buffer)
        if self.prev is None:
            self.space.ec.interpreter.writestr(val, buffer=False)
        else:
            self.prev.write(val)
        self.reset()

    def clean(self):
        self.reset()

    def get_contents(self):
        return self.space.newstr(self.buffer.build())


@wrap(['interp', Optional(W_Root), Optional(int)])
def ob_start(interp, w_callback=None, chunk_size=4096):
    callback = None
    if chunk_size < 0:
        chunk_size = 0
    if w_callback:
        try:
            callback = interp.space._get_callback(w_callback)
        except InvalidCallback as e:
            interp.warn("ob_start(): %s" % e.msg)
            interp.notice("ob_start(): failed to create buffer")
            return interp.space.w_False
    with interp.lock_ob('ob_start'):
        interp.start_buffering(interp.space, callback, chunk_size)
    return interp.space.w_True


@wrap(['interp'])
def ob_flush(interp):
    if interp.output_buffer is None:
        interp.notice("ob_flush(): failed to flush buffer. No buffer to flush")
        return interp.space.w_False
    with interp.lock_ob('ob_flush'):
        interp.output_buffer.flush()
    return interp.space.w_True

@wrap(['interp'])
def ob_clean(interp):
    if interp.output_buffer is None:
        interp.notice("ob_clean(): failed to delete buffer. No buffer to delete")
        return interp.space.w_False
    interp.output_buffer.clean()
    return interp.space.w_True


@wrap(['interp'])
def ob_end_flush(interp):
    buf = interp.output_buffer
    if buf is None:
        interp.notice("ob_end_flush(): failed to delete and flush buffer. "
                      "No buffer to delete or flush")
        return interp.space.w_False
    with interp.lock_ob('ob_end_flush'):
        buf.flush()
    interp.output_buffer = buf.prev
    return interp.space.w_True


@wrap(['interp'])
def ob_get_contents(interp):
    buffer = interp.output_buffer
    if buffer is None:
        return interp.space.w_False
    return buffer.get_contents()


@wrap(['interp'])
def ob_get_flush(interp):
    buf = interp.output_buffer
    if buf is None:
        return interp.space.w_False
    w_str = buf.get_contents()
    with interp.lock_ob('ob_get_flush'):
        buf.flush()
    return w_str


@wrap(['interp'])
def ob_get_clean(interp):
    buf = interp.output_buffer
    if buf is None:
        return interp.space.w_False
    w_str = buf.get_contents()
    interp.output_buffer = buf.prev
    return w_str


@wrap(['interp'])
def ob_end_clean(interp):
    buffer = interp.output_buffer
    if buffer is None:
        interp.notice("ob_end_clean(): failed to delete buffer. "
                      "No buffer to delete")
        return interp.space.w_False
    interp.output_buffer = buffer.prev
    return interp.space.w_True

@wrap(['interp'])
def ob_get_level(interp):
    if interp.output_buffer:
        return interp.space.wrap(interp.output_buffer.getlength())
    return interp.space.wrap(0)
