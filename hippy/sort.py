from rpython.rlib.listsort import make_timsort_class
from rpython.rlib.objectmodel import specialize
from rpython.rlib.unroll import unrolling_iterable
from hippy.module.standard.strings.funcs import _strnatcmp
from hippy.localemodule import strcoll_u

NONE, KEY, VALUE = range(3)

(SORT_REGULAR, SORT_NUMERIC, SORT_STRING, SORT_DESC, SORT_ASC,
 SORT_LOCALE_STRING, SORT_NATURAL) = range(7)
SORT_FLAG_CASE = 8

def identity(space, w_obj):
    return w_obj

def to_double(space, w_obj):
    return space.newfloat(space.float_w(w_obj))

def to_string(space, w_obj):
    return space.as_string(w_obj)

def to_string_lower(space, w_obj):
    w_str = space.as_string(w_obj)
    return space.newstr(w_str.unwrap().lower())

key_funcs = {
    SORT_REGULAR: identity, SORT_REGULAR | SORT_FLAG_CASE: identity,
    SORT_NUMERIC: to_double, SORT_NUMERIC | SORT_FLAG_CASE: to_double,
    SORT_STRING: to_string, SORT_STRING | SORT_FLAG_CASE: to_string_lower,
    SORT_LOCALE_STRING: to_string, SORT_LOCALE_STRING | SORT_FLAG_CASE: to_string,
    SORT_NATURAL: to_string, SORT_NATURAL | SORT_FLAG_CASE: to_string_lower,
}
SUPPORTED_SORT_TYPES = tuple(key_funcs)

def _get_key_func(sort_type):
    return key_funcs[sort_type]

def default_cmp(space, w_a, w_b):
    return space._compare(w_a, w_b)

def natcmp(space, w_a, w_b):
    return _strnatcmp(space.str_w(w_a), space.str_w(w_b))

def locale_cmp(space, w_a, w_b):
    return strcoll_u(space.str_w(w_a), space.str_w(w_b))

cmp_funcs = {
    SORT_REGULAR: default_cmp, SORT_REGULAR | SORT_FLAG_CASE: default_cmp,
    SORT_NUMERIC: default_cmp, SORT_NUMERIC | SORT_FLAG_CASE: default_cmp,
    SORT_STRING: default_cmp, SORT_STRING | SORT_FLAG_CASE: default_cmp,
    SORT_LOCALE_STRING: locale_cmp, SORT_LOCALE_STRING | SORT_FLAG_CASE: locale_cmp,
    SORT_NATURAL: natcmp, SORT_NATURAL | SORT_FLAG_CASE: natcmp,
}
def _get_cmp_func(sort_type):
    return cmp_funcs[sort_type]

class CustomSortMixin(object):
    _mixin_ = True

    def cmp(self, a, b):
        return self.space.int_w(self.space.call_args(self.cmp_func, [a, b]))


def new_sort_class(elem=NONE, sort_type=0, has_cmp_func=False, reverse=False):
    TimSort = make_timsort_class()
    key_func = _get_key_func(sort_type)
    cmp_func = _get_cmp_func(sort_type)
    if has_cmp_func:
        SortMixin = CustomSortMixin
    else:
        class SortMixin(object):
            _mixin_ = True

            def cmp(self, a, b):
                return cmp_func(self.space, a, b)

    class Sort(TimSort, SortMixin):
        def __init__(self, list, listlength=None, cmp_func=None,
                     space=None, reverse=reverse):
            TimSort.__init__(self, list, listlength)
            self.cmp_func = cmp_func
            self.space = space
            self.reverse = reverse

        def get_cmp_elem(self, a, b):
            if elem == KEY:
                a, _ = a
                b, _ = b
            elif elem == VALUE:
                _, a = a
                _, b = b
            return key_func(self.space, a), key_func(self.space, b)

        def lt(self, a, b):
            a, b = self.get_cmp_elem(a, b)
            res = self.cmp(a, b)
            if self.reverse:
                return res > 0
            return res < 0

    if elem == NONE:
        Sort.__name__ = 'Sort_NONE'
    elif elem == KEY:
        Sort.__name__ = 'Sort_KEY'
    else:
        Sort.__name__ = 'Sort_VALUE'
    return Sort


SORT_CLASSES = {
}

for _elem in (NONE, KEY, VALUE):
    for _sort_type in SUPPORTED_SORT_TYPES:
        for _has_cmp_func in (True, False):
            for rev in (True, False):
                _cls = new_sort_class(elem=_elem, sort_type=_sort_type,
                                      has_cmp_func=_has_cmp_func,
                                      reverse=rev)
                SORT_CLASSES[(_elem, _sort_type, _has_cmp_func, rev)] = _cls

all_sort_types = unrolling_iterable(SUPPORTED_SORT_TYPES)


@specialize.memo()
def _get_sort_class(elem, type, has_cmp, reverse):
    return SORT_CLASSES[(elem, type, has_cmp, reverse)]


@specialize.arg(4, 5)
def _sort(space, values, cmp=None, sort_type=0, elem=NONE, reverse=False):
    if sort_type not in SUPPORTED_SORT_TYPES:
        space.ec.hippy_warn("unknown sort type")
        sort_type = 0
    for type in all_sort_types:
        if sort_type == type:
            if cmp is None:
                Sort = _get_sort_class(elem, type, False, reverse)
                Sort(values, space=space).sort()
                return
            else:
                Sort = _get_sort_class(elem, type, True, reverse)
                Sort(values, space=space, cmp_func=cmp).sort()
                return
    raise Exception("unreachable code")


_TimSort = make_timsort_class()
class MultiSort(_TimSort):
    def __init__(self, space, list, key_funcs, cmp_funcs, signs):
        self.space = space
        _TimSort.__init__(self, list)
        self._n = len(key_funcs)
        assert len(signs) == self._n
        self.key_funcs = key_funcs
        self.cmp_funcs = cmp_funcs
        self.signs = signs

    def get_cmp_elem(self, line):
        return [self.key_funcs[i](self.space, line[i][1])
                for i in range(self._n)]

    def cmp(self, a, b):
        result = 0  # for RPython
        for i, sign in enumerate(self.signs):
            result = sign * self.cmp_funcs[i](self.space, a[i], b[i])
            if result != 0:
                return result
        else:
            return result

    def lt(self, line1, line2):
        key1 = self.get_cmp_elem(line1)
        key2 = self.get_cmp_elem(line2)
        res = self.cmp(key1, key2)
        return res < 0

signs = {SORT_DESC: -1, SORT_ASC: 1}

def _multisort(space, table, sort_types, sort_orders):
    key_funcs = [_get_key_func(sort_type) for sort_type in sort_types]
    cmp_funcs = [_get_cmp_func(sort_type) for sort_type in sort_types]
    _signs = [signs[sort_order] for sort_order in sort_orders]
    MultiSort(space, table, key_funcs, cmp_funcs, _signs).sort()
