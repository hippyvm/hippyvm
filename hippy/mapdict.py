
from rpython.rlib import jit

class AbstractAttribute(object):
    _immutable_fields_ = ['klass']
    _attrs_ = ['klass', 'transition_cache']

    def __init__(self):
        self.transition_cache = {}

    @jit.elidable
    def add_attribute(self, name):
        try:
            return self.transition_cache[name]
        except KeyError:
            a = Attribute(name, self.get_next_index(), self)
            self.transition_cache[name] = a
            return a

    def del_attribute(self, name):
        l = []
        current = self
        while isinstance(current, Attribute):
            if current.name == name:
                deleted_i = current.index
                prev_index = current.index
                current = current.next
                for i in range(len(l) - 1, -1, -1):
                    current = Attribute(l[i], prev_index, current)
                    prev_index += 1
                return current, deleted_i
            l.append(current.name)
            current = current.next
        assert False, "deleting attribute that's not there"

    def get_all_keys(self):
        l = [None] * self.get_next_index()
        i = 0
        while isinstance(self, Attribute):
            l[self.index] = self.name
            self = self.next
            i += 1
        return l

    def get_all_attrs(self):
        lgt = self.get_next_index()
        l = [None] * lgt
        i = 0
        while isinstance(self, Attribute):
            l[self.index] = self
            self = self.next
            i += 1
        return l

    def get_storage(self, old_storage):
        res = [None] * self.get_next_index()
        res[:len(old_storage)] = old_storage
        return res

class Attribute(AbstractAttribute):
    _immutable_fields_ = ['index', 'name']

    def __init__(self, name, index, next):
        AbstractAttribute.__init__(self)
        self.name = name
        self.index = index
        self.klass = next.klass
        self.next = next

    def __repr__(self):
        return "<attr %s %d>" % (self.name, self.index)

    def lookup(self, name):
        return self._lookup(name)

    @jit.elidable_promote()
    def _lookup(self, name):
        while isinstance(self, Attribute):
            if self.name == name:
                return self
            self = self.next
        return None

    def getsize(self):
        return self.index

    def get_next_index(self):
        return self.index + 1

class Terminator(AbstractAttribute):
    _attrs_ = ()

    index = 0

    def __init__(self, klass):
        AbstractAttribute.__init__(self)
        self.klass = klass

    def get_next_index(self):
        return 0

    def getsize(self):
        return 0

    def lookup(self, name):
        return None
