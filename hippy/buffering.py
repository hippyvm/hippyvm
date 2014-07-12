from rpython.rlib.rstring import StringBuilder
from hippy.builtin import wrap, Optional
from hippy.objects.base import W_Root
from hippy.objects.strobject import W_StringObject
from hippy.error import InvalidCallback, ConvertError
from collections import OrderedDict


FLUSH = 4

CLEANABLE = 16
FLUSHABLE = 32
REMOVABLE = 64


class Buffer(object):
    def __init__(self, space, name, callback, chunk_size, flags, prev):
        self.space = space
        self.name = name
        self.callback = callback
        self.chunk_size = chunk_size
        self.buffer = StringBuilder(chunk_size)
        self.buffer_len = 0
        self.prev = prev
        self.flags = flags
        if self.prev:
            self.level = self.prev.level + 1
        else:
            self.level = 0

    def is_cleanable(self):
        return bool(self.flags & CLEANABLE)

    def is_flushable(self):
        return bool(self.flags & FLUSHABLE)

    def is_removable(self):
        return bool(self.flags & REMOVABLE)

    def get_callback_name(self):
        return self.callback.name

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
        interp = self.space.ec.interpreter
        if self.callback is not None:
            w_buffer = interp.call(self.callback,
                                   [self.space.wrap(val),
                                    self.space.wrap(self.flags)])
            val = self.space.str_w(w_buffer)
        if self.prev is None:
            interp.writestr(val, buffer=False)
        else:
            self.prev.write(val)
        self.reset()
        return True

    def clean(self):
        self.reset()

    def get_contents(self):
        return self.space.newstr(self.buffer.build())


@wrap(['interp', Optional(W_Root), Optional(int), Optional(int)])
def ob_start(interp, w_callback=None, chunk_size=4096, flags=112):
    callback = None
    name = 'default output handler'
    if chunk_size < 0:
        chunk_size = 0
    if w_callback:
        try:
            callback = interp.space._get_callback(w_callback)
            if isinstance(w_callback, W_StringObject):
                name = interp.space.str_w(w_callback)
            else:
                name = 'Closure::__invoke'
        except InvalidCallback as e:

            interp.warn("ob_start(): %s" % e.msg)
            interp.notice("ob_start(): failed to create buffer")
            return interp.space.w_False
    with interp.lock_ob('ob_start'):
        interp.start_buffering(interp.space, name, callback, chunk_size, flags)
    return interp.space.w_True


@wrap(['interp'])
def ob_flush(interp):
    if interp.output_buffer is None:
        interp.notice("ob_flush(): failed to flush buffer. No buffer to flush")
        return interp.space.w_False
    res = False
    with interp.lock_ob('ob_flush'):
        res = interp.output_buffer.flush()
    if res:
        return interp.space.w_True
    return interp.space.w_False


@wrap(['interp'])
def ob_clean(interp):
    buf = interp.output_buffer
    if buf is None:
        interp.notice("ob_clean(): failed to delete buffer. "
                      "No buffer to delete")
        return interp.space.w_False
    if not buf.is_cleanable():
        interp.notice("ob_clean(): failed to delete "
                      "buffer of %s (%d)"
                      % (buf.get_callback_name(), buf.level))
    buf.clean()
    return interp.space.w_True


@wrap(['interp'])
def ob_get_length(interp):
    if interp.output_buffer:
        l = interp.output_buffer.buffer_len
        return interp.space.newint(l)
    else:
        return interp.space.w_False


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
        return interp.space.wrap(interp.output_buffer.level)
    return interp.space.wrap(0)


@wrap(['interp', Optional(bool)])
def ob_get_status(interp, full=False):
    """
    level	Output nesting level
    type	PHP_OUTPUT_HANDLER_INTERNAL (0) or PHP_OUTPUT_HANDLER_USER (1)
    status	One of PHP_OUTPUT_HANDLER_START (0),
                PHP_OUTPUT_HANDLER_CONT (1) or PHP_OUTPUT_HANDLER_END (2)
    name	Name of active output handler
                or ' default output handler' if none is set
    del	Erase-flag as set by ob_start()
    """
    # XXXXX just mockup
    space = interp.space
    buffer = interp.output_buffer
    if not buffer:
        return space.new_array_from_list([])
    if not full:
        rdict_w = OrderedDict()
        stats = [
            ("level", space.newint(int(buffer.level))),
            ("type", space.newint(int(1))),
            ("status", space.newint(int(0))),
            ("name", space.newstr(buffer.name)),
            ("del", space.newint(int(1)))]
        for label, stat in stats:
            rdict_w[label] = stat

        return space.new_array_from_rdict(rdict_w)

    list = []
    while buffer:
        rdict_w = OrderedDict()
        stats = [
            ("chunk_size", space.newint(int(buffer.chunk_size))),
            ("size", space.newint(int(40960))),
            ("block_size", space.newint(int(10240))),
            ("type", space.newint(int(1))),
            ("buffer_size", space.newint(int(buffer.buffer_len))),
            ("status", space.newint(int(0))),
            ("name", space.newstr(buffer.name)),
            ("del", space.newint(int(1)))]
        for label, stat in stats:
            rdict_w[label] = stat
        list.append(space.new_array_from_rdict(rdict_w))
        buffer = buffer.prev
    list.reverse()
    return space.new_array_from_list(list)


@wrap(['interp'])
def ob_list_handlers(interp):
    space = interp.space
    buff = interp.output_buffer
    list = []
    while buff:
        list.append(space.newstr(buff.name))
        buff = buff.prev
    return space.new_array_from_list(list)


@wrap(['interp', 'args_w'])
def ob_implicit_flush(interp, args_w):
    if len(args_w) == 0:
        return
    space = interp.space
    if len(args_w) != 1:
        interp.warn("ob_implicit_flush() expects at most 1 parameter, 2 given")
        return space.w_Null
    w_implicit_flush = args_w[0]
    try:
        im = w_implicit_flush.as_int_arg(space)
    except ConvertError:
        interp.warn("ob_implicit_flush() expects "
                    "parameter 1 to be long, %s given"
                    % space.get_type_name(w_implicit_flush.tp))
        return space.w_Null
    interp.implicit_flush = im
