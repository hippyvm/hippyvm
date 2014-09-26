from rpython.rtyper.lltypesystem import rffi
from hippy.objects.resources import W_Resource
from hippy.module.hash.hash_klass import HashClass


class W_HashResource(W_Resource):

    resource_name = 'Hash'
    options = 0
    key = None
    hashinst = None

    def __init__(self, space, hashinst, options=0, key=None):
        W_Resource.__init__(self, space)
        self.options = options
        self.space = space
        self.key = key
        self.hashinst = hashinst

    def digest(self):
        assert isinstance(self.hashinst,  HashClass)
        return self.hashinst.digest()

    def hexdigest(self):
        assert isinstance(self.hashinst,  HashClass)
        return self.hashinst.hexdigest()

    def update(self, data):
        assert isinstance(self.hashinst,  HashClass)
        self.hashinst.update(data)

    def deepcopy(self):
        new_hash = self.hashinst.copy()
        w_new = W_HashResource(self.space,
                               new_hash, self.options, self.key)
        return w_new

    def is_valid(self):
        return True

    def get_resource_type(self):
        return "Hash Context"

    def var_dump(self, space, indent, recursion):
        return "%sresource(%d) of type (%s)\n" % (indent,
                                                  self.res_id,
                                                  self.get_resource_type())
