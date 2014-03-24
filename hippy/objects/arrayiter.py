from hippy.objects.arrayobject import wrap_array_key
from hippy.objects.iterator import W_BaseIterator

class W_ListArrayIterator(W_BaseIterator):

    def __init__(self, storage_w):
        self.storage_w = storage_w
        self.index = 0
        self.finished = len(storage_w) == 0

    def next(self, space):
        index = self.index
        w_value = self.storage_w[index]
        self.index = index + 1
        self.finished = self.index == len(self.storage_w)
        return w_value

    def next_item(self, space):
        index = self.index
        w_value = self.storage_w[index]
        self.index = index + 1
        self.finished = self.index == len(self.storage_w)
        return space.wrap(index), w_value

class ListArrayIteratorRef(W_BaseIterator):
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

class W_RDictArrayIterator(W_BaseIterator):
    def __init__(self, rdct_w):
        self.rdct_w = rdct_w
        self.dctiter = rdct_w.iteritems()
        self.remaining = len(rdct_w)
        self.finished = self.remaining == 0

    def next(self, space):
        self.remaining -= 1
        self.finished = self.remaining == 0
        return self.dctiter.next()[1]

    def next_item(self, space):
        self.remaining -= 1
        self.finished = self.remaining == 0
        key, w_value = self.dctiter.next()
        return wrap_array_key(space, key), w_value

class RDictArrayIteratorRef(W_BaseIterator):
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


class W_FixedIterator(W_BaseIterator):
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
