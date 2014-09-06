from hippy.objects.arrayobject import wrap_array_key
from hippy.objects.iterator import BaseIterator

class ListArrayIterator(BaseIterator):

    def __init__(self, storage_w):
        self.storage_w = storage_w
        self.index = 0

    def next(self, space):
        interp = space.ec.interpreter
        w_value = self.current(interp)
        self.index += 1
        return w_value

    def next_item(self, space):
        interp = space.ec.interpreter
        index = self.index
        w_value = self.current(interp)
        w_index = self.key(interp)
        self.index = index + 1
        return w_index, w_value

    def current(self, interp):
        try:
            return self.storage_w[self.index]
        except IndexError:
            return None

    def key(self, interp):
        return interp.space.wrap(self.index)

    def rewind(self, interp):
        self.index = 0

    def valid(self, interp):
        return self.index < len(self.storage_w)

    def done(self):
        return not self.valid(None)

class ListArrayIteratorRef(BaseIterator):
    def __init__(self, space, r_array):
        self.r_array = r_array
        self.index = 0
        self.finished = self.is_finished()

    def get_current_value(self):
        # NB: the array must be deref'd every time, in case it's been mutated
        # between two calls to next()/next_item().
        w_array = self.r_array.deref()
        return w_array._getitem_int(self.index)

    def is_finished(self):
        w_array = self.r_array.deref_temp()
        return self.index == w_array.arraylen()

    def next(self, space):
        r_value = self.get_current_value()
        self.index += 1
        self.finished = self.is_finished()
        return r_value

    def next_item(self, space):
        r_value = self.get_current_value()
        index = self.index
        self.index = index + 1
        self.finished = self.is_finished()
        return space.wrap(index), r_value

class RDictArrayIterator(BaseIterator):
    def __init__(self, w_array):
        self.w_array = w_array
        self.rewind(None)

    def _current_index(self):
        keylist = self.w_array._getkeylist()
        try:
            return keylist[self.index]
        except IndexError:
            return None

    def current(self, interp):
        key = self._current_index()
        if key is None:
            return None
        return self.w_array.dct_w.get(key)

    def key(self, interp):
        key = self._current_index()
        if key is None:
            return None
        return wrap_array_key(interp.space, key)

    def next(self, space):
        w_value = self.current(None)
        self.index += 1
        self.finished = not self.valid(None)
        return w_value

    def next_item(self, space):
        interp = space.ec.interpreter
        w_value = self.current(interp)
        w_key = self.key(interp)
        if w_key is None:
            return None, None
        self.index += 1
        self.finished = not self.valid(interp)
        return w_key, w_value

    def rewind(self, interp):
        self.index = 0
        self.finished = not self.valid(interp)

    def valid(self, interp):
        return self.index < self.w_array.arraylen()


class RDictArrayIteratorRef(BaseIterator):
    def __init__(self, space, r_array):
        self.r_array = r_array
        self.index = 0
        self.finished = self.is_finished()

    def get_current_value(self):
        key = self._current_index()
        w_array = self.r_array.deref()
        return w_array._getitem_str(key)

    def _current_index(self):
        # NB: the array must be deref'd every time, in case it's been mutated
        # between two calls to next()/next_item().
        w_array = self.r_array.deref_temp()
        keylist = w_array._getkeylist()
        try:
            return keylist[self.index]
        except IndexError:
            return None

    def is_finished(self):
        w_array = self.r_array.deref_temp()
        return self.index == w_array.arraylen()

    def next(self, space):
        r_value = self.get_current_value()
        self.index += 1
        self.finished = self.is_finished()
        return r_value

    def next_item(self, space):
        r_value = self.get_current_value()
        key = self._current_index()
        if key is None:
            return None, None
        self.index += 1
        self.finished = self.is_finished()
        return wrap_array_key(space, key), r_value


class W_FixedIterator(BaseIterator):
    def __init__(self, items_w):
        self.items_w = items_w
        self.index = 0
        self.finished = len(items_w) == 0

    def next(self, space):
        index = self.index
        key, w_value = self.items_w[index]
        self.index = index + 1
        self.finished = self.index == len(self.items_w)
        return w_value

    def next_item(self, space):
        index = self.index
        key, w_value = self.items_w[index]
        self.index = index + 1
        self.finished = self.index == len(self.items_w)
        return space.newstr(key), w_value
