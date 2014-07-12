from rpython.rlib.rarithmetic import ovfcheck
from rpython.rlib import jit

from hippy.objects.base import W_Root
from hippy.objects.reference import W_Reference
from hippy.objects.arrayobject import new_rdict, W_ArrayObject
from hippy.objects.instanceobject import W_InstanceObject
from hippy.objects.nullobject import W_NullObject
from hippy.builtin import (
    wrap, Optional, ArrayArg, UniqueArray, register_builtin_function,
    BuiltinFunction, ExitFunctionWithError)
from hippy.objects.intobject import W_IntObject
from rpython.rlib.rrandom import Random
from rpython.rlib.objectmodel import newlist_hint
from hippy.sort import (
    KEY, VALUE, _sort, SUPPORTED_SORT_TYPES, SORT_REGULAR,
    SORT_DESC, SORT_ASC, _multisort)
import sys
from collections import OrderedDict
from hippy.objects.arrayobject import try_convert_str_to_int
_random = Random()


def force_ref(w_obj):
    """Convert a reference-or-object into a reference"""
    if not isinstance(w_obj, W_Reference):
        return W_Reference(w_obj)
    else:
        return w_obj


def _not_an_array(arg_no):
    raise ExitFunctionWithError("Argument #%d is not an array" % (arg_no))


@wrap(['space', ArrayArg(None), Optional(int)])
def array_change_key_case(space, w_arr, case=0):
    """ Changes all keys in an array """
    with space.iter(w_arr) as itr:
        d = new_rdict()
        while not itr.done():
            w_key, w_value = itr.next_item(space)
            if w_key.tp == space.tp_str:
                k_str = w_key.unwrap()
                if case != 0:
                    k_str = k_str.upper()
                else:
                    k_str = k_str.lower()
            else:
                k_str = space.str_w(w_key)
            d[k_str] = w_value
    return space.new_array_from_rdict(d)


@wrap(['space', ArrayArg(None), int, Optional(bool)])
def array_chunk(space, w_arr, chunk_size, keep_keys=False):
    """ Split an array into chunks """
    if chunk_size <= 0:
        space.ec.warn("array_chunk(): Size parameter "
                      "expected to be greater than 0")
        return space.w_Null

    last_idx = 0
    r = range(chunk_size, space.arraylen(w_arr) + chunk_size, chunk_size)
    res_arr = newlist_hint(len(r))
    for i in r:
        res_arr.append(space.slice(w_arr, last_idx, chunk_size, keep_keys))
        last_idx = i
    return space.new_array_from_list(res_arr)


@wrap(['space', ArrayArg(None), ArrayArg(None)])
def array_combine(space, w_arr_a, w_arr_b):
    """ Creates an array by using one array for keys
    and another for its values """
    if space.arraylen(w_arr_a) != space.arraylen(w_arr_b):
        space.ec.warn("array_combine(): Both parameters "
                      "should have an equal number of elements")
        return space.w_False

    d = new_rdict()
    with space.iter(w_arr_a) as a_iter:
        with space.iter(w_arr_b) as b_iter:
            while not a_iter.done():
                w_key = a_iter.next(space)
                w_val = b_iter.next(space)
                d[space.str_w(w_key)] = w_val
    return space.new_array_from_rdict(d)


@wrap(['space', ArrayArg(None)])
def array_count_values(space, w_arr):
    """ Counts all the values of an array """
    dct_w = new_rdict()
    with space.iter(w_arr) as itr:
        while not itr.done():
            w_val = itr.next(space).deref()
            if not (w_val.tp == space.tp_int or w_val.tp == space.tp_str):
                space.ec.warn("array_count_values(): Can only count "
                              "STRING and INTEGER values!")
                continue
            key = space.str_w(w_val)
            try:
                w_val = dct_w[key]
            except KeyError:
                nextval = 1
            else:
                nextval = space.int_w(w_val) + 1
            dct_w[key] = space.newint(nextval)
    return space.new_array_from_rdict(dct_w)


@wrap(['space', 'args_w'])
def array_diff_assoc(space, args_w):
    """ Computes the difference of arrays with additional index check """
    if len(args_w) < 2:
        space.ec.warn("array_diff_assoc(): at least 2 "
                      "parameters are required, %d given"
                      % len(args_w))
        return space.w_Null
    for i, w_arg in enumerate(args_w):
        if w_arg.tp != space.tp_array:
            space.ec.warn("array_diff_assoc(): Argument #%d "
                          "is not an array" % (i + 1))
            return space.w_Null
    w_arr = args_w[0]
    rdict = space.get_rdict_from_array(w_arr)
    args_w = args_w[1:]
    with space.iter(w_arr) as w_iter:
        while not w_iter.done():
            w_key, w_val = w_iter.next_item(space)
            for w_arg in args_w:
                with space.iter(w_arg) as w_arg_iter:
                    while not w_arg_iter.done():
                        w_arg_key, w_arg_val = w_arg_iter.next_item(space)
                        if space.is_w(space.as_string(w_key), space.as_string(w_arg_key)) and \
                                space.is_w(space.as_string(w_val), space.as_string(w_arg_val)):
                            space.rdict_remove(rdict, w_arg_key)
    return space.new_array_from_rdict(rdict)


@wrap(['space', 'args_w'])
def array_diff_key(space, args_w):
    """ Computes the difference of arrays using keys for comparison """
    if len(args_w) < 2:
        space.ec.warn("array_diff_key(): at least 2 "
                      "parameters are required, %d given"
                      % len(args_w))
        return space.w_Null
    for i, w_arg in enumerate(args_w):
        if w_arg.tp != space.tp_array:
            raise _not_an_array(i + 1)
    w_arr = args_w[0]
    args_w = args_w[1:]
    rdict = space.get_rdict_from_array(w_arr)
    for w_arg in args_w:
        with space.iter(w_arg) as w_iter:
            while not w_iter.done():
                w_key, w_val = w_iter.next_item(space)
                if w_arr.isset_index(space, w_key):
                    space.rdict_remove(rdict, w_key)
    return space.new_array_from_rdict(rdict)


@wrap(['space', 'args_w'])
def array_diff_uassoc(space, args_w):
    """ Computes the difference of arrays with additional
    index check which is performed by a user supplied
    callback function """
    if len(args_w) < 3:
        space.ec.warn("array_diff_uassoc(): at least 3 "
                      "parameters are required, %d given"
                      % len(args_w))
        return space.w_Null
    w_callback = args_w.pop()
    callback_func = None
    callback_func = space.get_callback('array_diff_uassoc',
                                       len(args_w) + 1, w_callback)
    if callback_func is None:
        return space.w_Null
    for i, w_arg in enumerate(args_w):
        if w_arg.tp != space.tp_array:
            raise _not_an_array(i + 1)

    w_arr = args_w[0]
    args_w = args_w[1:]
    d = new_rdict()
    with space.iter(w_arr) as w_iter:
        while not w_iter.done():
            w_key, w_val = w_iter.next_item(space)
            for w_arg in args_w:
                if w_arg.isset_index(space, w_key):
                    #try:
                        other_w_val = space.getitem(w_arg, w_key)
                        w_cb_res = space.call_args(callback_func,
                                                   [other_w_val.deref(),
                                                    w_val.deref()])
                        if space.int_w(w_cb_res) == 0:
                            break
                    #except InterpreterError:     -- XXX????
                    #    res_arr.append(w_key, w_val)
            else:
                d[space.str_w(w_key)] = w_val
    return space.new_array_from_rdict(d)


@wrap(['space', 'args_w'])
def array_diff_ukey(space, args_w):
    # XXX: soda, works but its not well done yet
    """ Computes the difference of arrays using a callback
    function on the keys for comparison """
    if len(args_w) < 3:
        space.ec.warn("array_diff_ukey(): at least 3 parameters "
                      "are required, %d given" % len(args_w))
        return space.w_Null
    w_callback = args_w[-1]
    callback_func = None
    callback_func = space.get_callback('array_diff_ukey',
                                       len(args_w), w_callback)
    if callback_func is None:
        return space.w_Null
    extra_args_w = []
    for i in range(len(args_w) - 1):
        w_arg = args_w[i]
        if w_arg.tp != space.tp_array:
            raise _not_an_array(i + 1)
        if i > 0:
            extra_args_w.append(space.as_array(w_arg))

    w_arr = args_w[0]
    rdict = space.get_rdict_from_array(w_arr)
    with space.iter(w_arr) as w_iter:
        while not w_iter.done():
            w_key, _ = w_iter.next_item(space)
            for w_arg in extra_args_w:
                with space.iter(w_arg) as w_arg_iter:
                    while not w_arg_iter.done():
                        w_arg_key, _ = w_arg_iter.next_item(space)
                        w_cb_res = space.call_args(
                            callback_func, [w_key, w_arg_key])
                        if space.int_w(w_cb_res) != 0:
                            space.rdict_remove(rdict, w_arg_key)
    return space.new_array_from_rdict(rdict)


@wrap(['space', 'args_w'])
def array_diff(space, args_w):
    """ Computes the difference of arrays """
    if len(args_w) < 2:
        space.ec.warn("array_diff(): at least 2 parameters "
                      "are required, %d given" % len(args_w))
        return space.w_Null
    for i, w_arg in enumerate(args_w):
        if w_arg.tp != space.tp_array:
            raise _not_an_array(i + 1)
    w_arr = args_w[0]
    rdict = space.get_rdict_from_array(w_arr)
    args_w = [space.as_array(w_arg) for w_arg in args_w[1:]]
    with space.iter(w_arr) as w_df_iter:
        while not w_df_iter.done():
            w_df_key, w_df_val = w_df_iter.next_item(space)
            for w_arg in args_w:
                with space.iter(w_arg) as w_iter:
                    while not w_iter.done():
                        _, w_val = w_iter.next_item(space)
                        if space.str_eq(w_df_val, w_val):
                            space.rdict_remove(rdict, w_df_key)
    return space.new_array_from_rdict(rdict)


@wrap(['space', ArrayArg(None), W_Root])
def array_fill_keys(space, w_arr, w_value):
    """ Fill an array with values, specifying keys """
    d = new_rdict()
    with space.iter(w_arr) as w_arrayiter:
        while not w_arrayiter.done():
            w_item = w_arrayiter.next(space).deref()
            d[space.str_w(w_item)] = w_value
    return space.new_array_from_rdict(d)


@wrap(['space', int, int, W_Root])
def array_fill(space, sidx, num, w_value):
    """ Fill an array with values """
    if num < 1:
        space.ec.warn("array_fill(): Number of elements must be positive")
        return space.w_False

    if sidx == 0:
        return space.new_array_from_list([w_value] * num)

    d = new_rdict()
    if sidx < 0:
        d[str(sidx)] = w_value
        num -= 1
        sidx = 0

    try:
        end = ovfcheck(sidx + num)
    except OverflowError:
        # XXX: PHP's error message is rather misleading
        space.ec.warn("array_fill(): Cannot add element to the array "
                     "as the next element is already occupied")
        return space.w_False

    for i in xrange(sidx, end):
        d[str(i)] = w_value
    return space.new_array_from_rdict(d)


@wrap(['space', ArrayArg(None), Optional(W_Root)])
def array_filter(space, w_arr, w_callback=None):
    """ Filters elements of an array using a callback function """
    callback_func = None
    if w_callback:
        callback_func = space.get_callback('array_filter',
                                           2, w_callback)
        if callback_func is None:
            return space.w_Null
    d = new_rdict()
    with space.iter(w_arr) as itr:
        while not itr.done():
            w_key, w_val = itr.next_item(space)
            if callback_func:
                w_cb_res = space.call_args(callback_func, [w_val])
                if space.is_true(w_cb_res):
                    d[space.str_w(w_key)] = w_val
            else:
                if space.is_true(w_val):
                    d[space.str_w(w_key)] = w_val
    return space.new_array_from_rdict(d)


@wrap(['space', ArrayArg(None)])
def array_flip(space, w_arr):
    """ Exchanges all keys with their associated values in an array """
    d = new_rdict()
    with space.iter(w_arr) as itr:
        while not itr.done():
            w_key, w_val = itr.next_item(space)
            if w_key.tp not in (space.tp_int, space.tp_str) or\
                    w_val.tp not in(space.tp_int, space.tp_str):
                space.ec.warn("array_flip(): Can only flip "
                              "STRING and INTEGER values!")
            else:
                d[space.str_w(w_val)] = w_key
    return space.new_array_from_rdict(d)


@wrap(['space', 'args_w'])
def array_intersect_assoc(space, args_w):
    """ Computes the intersection of arrays with additional index check """
    if len(args_w) < 2:
        space.ec.warn("array_intersect_assoc(): at least 2 "
                      "parameters are required, %d given"
                      % len(args_w))
        return space.w_Null
    for i, w_arg in enumerate(args_w):
        if w_arg.tp != space.tp_array:
            raise _not_an_array(i + 1)
    w_arr = args_w[0]
    rdict = space.get_rdict_from_array(w_arr)
    args_w = args_w[1:]

    with space.iter(w_arr) as w_arr_iter:
        while not w_arr_iter.done():
            w_arr_key, w_arr_val = w_arr_iter.next_item(space)
            exists = 0
            for w_arg in args_w:
                if w_arg.isset_index(space, w_arr_key):
                    w_one = space.as_string(w_arr_val)
                    w_two = space.as_string(space.getitem(w_arg, w_arr_key))
                    if space.str_eq(w_one, w_two):
                        exists += 1
            if exists < len(args_w):
                space.rdict_remove(rdict, w_arr_key)
    return space.new_array_from_rdict(rdict)


@wrap(['space', 'args_w'])
def array_intersect_key(space, args_w):
    """ Computes the intersection of arrays using keys for comparison """
    if len(args_w) < 2:
        space.ec.warn("array_intersect_key(): at least 2 "
                      "parameters are required, %d given"
                      % len(args_w))
        return space.w_Null
    for i, w_arg in enumerate(args_w):
        if w_arg.tp != space.tp_array:
            raise _not_an_array(i + 1)
    w_arr = args_w[0]
    args_w = args_w[1:]
    d = new_rdict()
    with space.iter(w_arr) as w_iter:
        while not w_iter.done():
            w_key, w_val = w_iter.next_item(space)
            for w_arg in args_w:
                if not w_arg.isset_index(space, w_key):
                    break
            else:
                d[space.str_w(w_key)] = w_val
    return space.new_array_from_rdict(d)


@wrap(['space', 'args_w'])
def array_intersect_uassoc(space, args_w):
    """ Computes the intersection of arrays with additional index check,
    compares indexes by a callback function """
    if len(args_w) < 3:
        space.ec.warn("array_intersect_uassoc(): at least 3 "
                      "parameters are required, %d given"
                      % len(args_w))
        return space.w_Null

    w_callback = args_w[-1]
    callback_func = space.get_callback('array_intersect_uassoc',
                                       len(args_w), w_callback)
    if callback_func is None:
        return space.w_Null

    stop = len(args_w) - 1
    assert stop >= 0
    for i, w_arg in enumerate(args_w[:stop]):
        if w_arg.tp != space.tp_array:
            raise _not_an_array(i + 1)

    w_arr = args_w[0]
    args_w = args_w[1:stop]
    rdict = space.get_rdict_from_array(w_arr)
    with space.iter(w_arr) as w_arr_iter:
        while not w_arr_iter.done():
            w_arr_key, w_arr_val = w_arr_iter.next_item(space)
            exists = 0
            for w_arg in args_w:
                with space.iter(w_arg) as w_arg_iter:
                    while not w_arg_iter.done():
                        w_arg_key, w_arg_val = w_arg_iter.next_item(space)
                        w_cb_res = space.call_args(
                            callback_func, [w_arr_key,
                                            w_arg_key])
                        if space.int_w(w_cb_res) == 0:
                            w_one = space.as_string(w_arr_val)
                            w_two = space.as_string(w_arg_val)
                            if space.is_w(w_one, w_two):
                                exists += 1
            if exists < len(args_w):
                space.rdict_remove(rdict, w_arr_key)
    return space.new_array_from_rdict(rdict)


@wrap(['space', 'args_w'])
def array_intersect_ukey(space, args_w):
    """ # Computes the intersection of arrays using a
    callback function on the keys for comparison """
    if len(args_w) < 3:
        space.ec.warn("array_intersect_ukey(): at least 3 parameters "
                      "are required, %d given" % len(args_w))
        return space.w_Null
    w_callback = args_w[-1]
    callback_func = space.get_callback('array_intersect_ukey',
                                       len(args_w), w_callback)
    if callback_func is None:
        return space.w_Null

    extra_args_w = []
    for i in range(len(args_w) - 1):
        w_arg = args_w[i]
        if w_arg.tp != space.tp_array:
            raise _not_an_array(i + 1)
        if i > 0:
            extra_args_w.append(space.as_array(w_arg))

    w_arr = args_w[0]
    rdict = space.get_rdict_from_array(w_arr)

    with space.iter(w_arr) as w_iter:
        while not w_iter.done():
            w_key, _ = w_iter.next_item(space)
            exists = 0
            for w_arg in extra_args_w:
                with space.iter(w_arg) as w_arg_iter:
                    while not w_arg_iter.done():
                        w_arg_key, _ = w_arg_iter.next_item(space)
                        w_cb_res = space.call_args(
                            callback_func, [w_key, w_arg_key])
                        if space.int_w(w_cb_res) == 0:
                            exists += 1
            if exists < len(extra_args_w):
                space.rdict_remove(rdict, w_key)
    return space.new_array_from_rdict(rdict)


@wrap(['space', 'args_w'])
def array_intersect(space, args_w):
    """ Computes the intersection of arrays """
    if len(args_w) < 2:
        space.ec.warn("array_intersect(): at least 2 parameters "
                      "are required, %d given" % len(args_w))
        return space.w_Null
    for i, w_arg in enumerate(args_w):
        if w_arg.tp != space.tp_array:
            raise _not_an_array(i + 1)
    w_arr = args_w[0]
    rdict = space.get_rdict_from_array(w_arr)
    args_w = args_w[1:]

    with space.iter(w_arr) as w_arr_iter:
        while not w_arr_iter.done():
            w_arr_key, w_arr_val = w_arr_iter.next_item(space)
            exists = 0
            for i, w_arg in enumerate(args_w):
                with space.iter(w_arg) as w_iter:
                    while not w_iter.done():
                        _, w_val = w_iter.next_item(space)
                        if space.str_eq(w_arr_val, w_val):
                            exists += 1
            if exists < len(args_w):
                space.rdict_remove(rdict, w_arr_key)
    return space.new_array_from_rdict(rdict)


@wrap(['interp', 'space', W_Root, W_Root], aliases=["key_exists"])
def array_key_exists(interp, space, w_key, w_obj):
    """ Checks if the given key or index exists in the array """
    if w_obj.tp not in (space.tp_object, space.tp_array):
        space.ec.warn("array_key_exists() expects parameter "
                      "2 to be array, %s given" %
                      space.get_type_name(w_obj.tp))
        return space.w_Null

    if w_key.tp not in (space.tp_int, space.tp_str, space.tp_null):
        space.ec.warn("array_key_exists(): The first argument "
                      "should be either a string or an integer")
        return space.w_False
    if w_obj.tp == space.tp_array:
        return space.newbool(w_obj.isset_index(space, w_key))
    if w_obj.tp == space.tp_object:
        return space.newbool(w_obj.hasattr(interp, space.str_w(w_key), None))


@wrap(['space', ArrayArg(None), Optional(W_Root), Optional(bool)])
def array_keys(space, w_arr, w_search=None, strict=False):
    """ Return all the keys or a subset of the keys of an array """
    lst = []
    with space.iter(w_arr) as itr:
        while not itr.done():
            w_key, w_val = itr.next_item(space)
            if w_search:
                if space.str_eq(w_val, w_search):
                    if not strict or w_val.tp == w_search.tp:
                        lst.append(w_key)
            else:
                lst.append(w_key)
    return space.new_array_from_list(lst)


@wrap(['space', 'args_w'])
def array_map(space, args_w):
    """ Applies the callback to the elements of the given arrays """
    """ Computes the difference of arrays using a callback
    function on the keys for comparison """
    if len(args_w) < 2:
        space.ec.warn("array_map() expects at least 2"
                      " parameters, %d given" % len(args_w))
        return space.w_Null

    w_callback = args_w[0]
    if isinstance(w_callback, W_NullObject):
        callback_func = None
    else:
        callback_func = space.get_callback('array_map', 1, w_callback)
        if callback_func is None:
            return space.w_Null
    w_arr_list = [w_arg for w_arg in args_w[1:]]
    max_arr_len = 0
    for i, w_arr in enumerate(w_arr_list):
        if w_arr.tp != space.tp_array:
            space.ec.warn("array_map(): Argument #%d "
                          "should be an array" % (i + 2))
            return space.w_Null
        else:
            _len = space.arraylen(w_arr)
            if _len > max_arr_len:
                max_arr_len = _len

    if len(w_arr_list) == 1:
        w_arr = w_arr_list[0]
        res_list = newlist_hint(max_arr_len)
        with space.iter(w_arr) as w_arr_iter:
            while not w_arr_iter.done():
                w_key, w_val = w_arr_iter.next_item(space)
                if callback_func:
                    res_list.append((w_key,
                                    space.call_args(callback_func, [w_val])))
                else:
                    res_list.append((w_key, w_val))
        return space.new_array_from_pairs(res_list)

    cb_call_w_args_list = [[] for i in range(len(w_arr_list))]
    res_list = newlist_hint(len(w_arr_list))
    for idx, w_arr in enumerate(w_arr_list):
        with space.iter(w_arr) as w_arr_iter:
            while not w_arr_iter.done():
                _, w_val = w_arr_iter.next_item(space)
                cb_call_w_args_list[idx].append(w_val)

    for i in range(max_arr_len):
        args_arr_w = []
        for items_w in cb_call_w_args_list:
            if len(items_w) > i:
                args_arr_w.append(items_w[i])
            else:
                args_arr_w.append(space.w_Null)
        if callback_func:
            res_list.append(space.call_args(callback_func, args_arr_w))
        else:
            res_list.append(space.new_array_from_list(args_arr_w))
    return space.new_array_from_list(res_list)


@wrap(['space', 'args_w'])
def array_merge_recursive(space, args_w):
    """ Merge two or more arrays recursively """
    """ Merge one or more arrays """
    if len(args_w) < 1:
        space.ec.warn("array_merge_recursive() expects at least 1 parameter"
                      ", %d given" % len(args_w))
        return space.w_Null
    for i, w_arg in enumerate(args_w):
        if w_arg.tp != space.tp_array:
            raise _not_an_array(i + 1)

    # concatenate the arrays while reindexing them
    return _merge_arrays(space, args_w)


def _merge_arrays(space, args_w):
    d = new_rdict()
    idx = 0

    for w_arg in args_w:
        if not space.is_array(w_arg):
            d[str(idx)] = w_arg
            idx += 1
            continue
        with space.iter(w_arg) as w_iter:
            while not w_iter.done():
                w_key, w_value = w_iter.next_item(space)
                if space.is_really_int(w_key):
                    d[str(idx)] = w_value
                    idx += 1
                else:
                    key = space.str_w(w_key)
                    if key in d:
                        d[key] = _merge_arrays(space, [d[key], w_value])
                    else:
                        d[space.str_w(w_key)] = w_value
    return space.new_array_from_rdict(d)


@wrap(['space', 'args_w'])
def array_merge(space, args_w):
    """ Merge one or more arrays """
    if len(args_w) < 1:
        space.ec.warn("array_merge() expects at least 1 parameter"
                      ", %d given" % len(args_w))
        return space.w_Null
    for i, w_arg in enumerate(args_w):
        if w_arg.tp != space.tp_array:
            raise _not_an_array(i + 1)

    # concatenate the arrays while reindexing them
    d = new_rdict()
    idx = 0
    for w_arg in args_w:
        with space.iter(w_arg) as w_iter:
            while not w_iter.done():
                w_key, w_value = w_iter.next_item(space)
                if space.is_really_int(w_key):
                    d[str(idx)] = w_value
                    idx += 1
                else:
                    d[space.str_w(w_key)] = w_value
    return space.new_array_from_rdict(d)

SORT_DEFAULTS = SORT_ASC, SORT_REGULAR

class ArrayMultisortFunction(BuiltinFunction):
    name = _fullname = 'array_multisort'
    runner = None

    def __init__(self):
        pass

    def needs_value(self, i):
        return False

    def needs_ref(self, i):
        return False

    def call_args(self, interp, args_w, w_this=None, thisclass=None,
            closureargs=None):
        if len(args_w) == 0:
            interp.warn("array_multisort() expects at least 1 parameter, "
                        "0 given")
            return interp.space.w_Null
        return _array_multisort(interp, args_w)

def _renumber_keys(pairs):
    result = []
    i = 0
    for key, value in pairs:
        if isinstance(key, W_IntObject):
            result.append((W_IntObject(i), value))
            i += 1
        else:
            result.append((key, value))
    return result

def _array_multisort(interp, args_w):
    """ Sort multiple or multi-dimensional arrays
    ('SORT_ASC', 4),
    ('SORT_DESC', 3),

    ('SORT_REGULAR', 0),
    ('SORT_NUMERIC', 1),
    ('SORT_STRING', 2),
    ('SORT_LOCALE_STRING', 5),
    ('SORT_NATURAL', 6),
    ('SORT_FLAG_CASE', 8),

    """
    space = interp.space
    arrays = []
    r_array = None
    sort_order, sort_type = SORT_DEFAULTS
    order_allowed = type_allowed = array_seen = False
    for i, rw_arg in enumerate(args_w):  # rw_arg is a ref or a W_*
        w_arg = rw_arg.deref()  # definitely an object
        if isinstance(w_arg, W_ArrayObject):
            if r_array is not None:
                arrays.append((r_array, sort_order, sort_type))
                order_allowed = type_allowed = array_seen = False
                sort_order, sort_type = SORT_DEFAULTS
            r_array = force_ref(rw_arg)
            order_allowed = type_allowed = array_seen = True
        elif isinstance(w_arg, W_IntObject):
            flag = w_arg.intval
            if flag in (SORT_ASC, SORT_DESC):
                if order_allowed:
                    sort_order = flag
                    order_allowed = False
                else:
                    interp.warn("array_multisort(): Argument #%d is expected "
                                "to be an array or sorting flag that has not "
                                "already been specified" % (i + 1))
                    return space.w_False
            elif flag in SUPPORTED_SORT_TYPES:
                if type_allowed:
                    sort_type = flag
                    type_allowed = False
                else:
                    interp.warn("array_multisort(): Argument #%d is expected "
                                "to be an array or sorting flag that has not "
                                "already been specified" % (i + 1))
                    return space.w_False
            else:
                interp.warn("array_multisort(): Argument #%d is an unknown "
                            "sort flag" % (i + 1))
                return space.w_False
        else:
            interp.warn("array_multisort(): Argument #%d is expected to be an "
                        "array or a sort flag" % (i + 1))
            return space.w_False
    if array_seen:
        arrays.append((r_array, sort_order, sort_type))

    array_len = arrays[0][0].deref().arraylen()
    for i in range(1, len(arrays)):
        if arrays[i][0].deref().arraylen() != array_len:
            interp.warn('array_multisort(): Array sizes are inconsistent')
            return space.w_False

    zipped = [[] for _ in range(array_len)]
    for i in range(len(arrays)):
        r_array = arrays[i][0]
        pair_column = r_array.deref().as_pair_list(space)
        for j in range(array_len):
            zipped[j].append(pair_column[j])
    sort_orders = [sort_order for _, sort_order, _ in arrays]
    sort_types = [sort_type for _, _, sort_type in arrays]
    _multisort(space, zipped, sort_types, sort_orders)

    for i in range(len(arrays)):
        r_array = arrays[i][0]
        pairs = [zipped[j][i] for j in range(array_len)]
        pairs = _renumber_keys(pairs)
        r_array.store(space.new_array_from_pairs(pairs), unique=True)
    return space.w_True

register_builtin_function('array_multisort', ArrayMultisortFunction())


def _pad_array(space, w_arr, pairs, idx):
    with space.iter(w_arr) as itr:
        while not itr.done():
            w_key, w_val = itr.next_item(space)
            if w_key.tp != space.tp_int:
                pairs.append((w_key, w_val))
            else:
                pairs.append((space.newint(idx), w_val))
                idx += 1
    return idx


@wrap(['space',  ArrayArg(None), W_Root, W_Root])
def array_pad(space, w_arr, w_size, w_value):
    """ Pad array to the specified length with a value """
    w_int_size = space.is_really_int(w_size)
    if w_int_size is None:
        space.ec.warn("array_pad() expects parameter "
                      "2 to be long, %s given"
                      % (space.get_type_name(w_size.tp)))
        return space.w_Null
    size = space.int_w(w_int_size)
    if size > 1048576:
        space.ec.warn("array_pad(): You may only pad up to "
                      "1048576 elements at a time")
        return space.w_False

    pairs = []
    arr_len = space.arraylen(w_arr)
    pad_size = abs(size) - arr_len
    if pad_size <= 0:     # XXX size == -sys.maxint-1?
        return w_arr
    if size > 0:
        idx = _pad_array(space, w_arr, pairs, 0)
        for i in range(pad_size):
            pairs.append((space.newint(idx + i), w_value))
    else:
        idx = 0
        for i in range(size + arr_len, 0):
            pairs.append((space.newint(idx), w_value))
            idx += 1
        _pad_array(space, w_arr, pairs, idx)
    return space.new_array_from_pairs(pairs)


@wrap(['space', UniqueArray(accept_instance=False)])
def array_pop(space, w_arr):
    """ Pop the element off the end of array """
    if w_arr.arraylen() == 0:
        space.ec.hippy_warn('array_pop() has no effect on an empty array')
        return space.w_Null
    return w_arr._inplace_pop(space)


@wrap(['space', ArrayArg(None)])
def array_product(space, w_arr):
    """ Calculate the product of values in an array """
    if space.arraylen(w_arr) == 0:
        return space.newint(1)
    res = 1
    with space.iter(w_arr) as itr:
        while not itr.done():
            _, w_val = itr.next_item(space)
            w_num = space.as_number(w_val)
            if w_num.tp == space.tp_float:
                res *= space.float_w(w_num)
            if w_num.tp == space.tp_int:
                res *= space.int_w(w_num)
    return space.wrap(res)


@wrap(['space', UniqueArray(accept_instance=False), 'args_w'])
def array_push(space, w_arr, args_w):
    """ Push one or more elements onto the end of array """
    if len(args_w) < 1:
        space.ec.warn("array_push(): at least 2 parameters are required"
                      ", 1 given")
        return space.w_Null
    for w_arg in args_w:
        w_arr.appenditem_inplace(space, w_arg)
    return space.wrap(w_arr.arraylen())


@wrap(['space', ArrayArg(None), Optional(int)])
def array_rand(space, w_arr, num_req=1):
    """ Pick one or more random entries out of an array """
    if w_arr.arraylen() == 0 and num_req == 1:
        return space.w_Null
    if num_req > space.arraylen(w_arr) or num_req < 1:
        space.ec.warn("array_rand(): Second argument has to be between "
                      "1 and the number of elements in the array")
        return space.w_Null
    keys = []
    with space.iter(w_arr) as w_iter:
        while not w_iter.done():
            w_key, _ = w_iter.next_item(space)
            keys.append(w_key)
    #shuffle keys
    for i in range(num_req):
        j = i + int(_random.random() * (len(keys) - i))
        keys[i], keys[j] = keys[j], keys[i]
    if num_req > 1:
        return space.new_array_from_list(keys[:num_req])
    return keys[0]


@wrap(['space', ArrayArg(None), 'callback', Optional(W_Root)])
def array_reduce(space, w_arr, callback_func, w_initial=None):
    """ Iteratively reduce the array to a single
    value using a callback function """
    if not w_initial:
        w_initial = space.w_Null

    if w_arr.arraylen() == 0:
        return w_initial

    with space.iter(w_arr) as w_arr_iter:
        while not w_arr_iter.done():
            w_key, w_val = w_arr_iter.next_item(space)
            w_initial = space.call_args(callback_func, [w_initial, w_val])
    return w_initial


def _array_replace(space, w_arr_a, w_arr_b):
    with space.iter(w_arr_b) as w_iter:
        while not w_iter.done():
            w_key, w_value = w_iter.next_item(space)
            w_value = w_value.deref()
            if w_value.tp == space.tp_array:
                w_val_a = space.getitem(w_arr_a, w_key)
                if w_val_a.tp == space.tp_array:
                    w_val_a = _array_replace(space, w_val_a, w_value)
                    w_arr_a = space.setitem(w_arr_a, w_key, w_val_a)
                else:
                    w_arr_a = space.setitem(w_arr_a, w_key, w_value)
            else:
                w_arr_a = space.setitem(w_arr_a, w_key, w_value)
    return w_arr_a


@wrap(['space', ArrayArg(None), 'args_w'])
def array_replace_recursive(space, w_arr, args_w):
    """ Replaces elements from passed arrays
    into the first array recursively """
    for i, w_arr in enumerate(args_w):
        if w_arr.tp != space.tp_array:
            space.ec.warn("array_replace_recursive(): Argument #%d "
                          "should be an array" % (i+1))
            return space.w_Null

    for w_arg in args_w:
        w_arr = _array_replace(space, w_arr, w_arg)
    return w_arr


@wrap(['space', ArrayArg(None), 'args_w'])
def array_replace(space, w_arr, args_w):
    """ Replaces elements from passed arrays into the first array """
    for i, w_arr in enumerate(args_w):
        if w_arr.tp != space.tp_array:
            space.ec.warn("array_replace_recursive(): Argument #%d "
                          "should be an array" % (i+1))
            return space.w_Null

    for w_arg in args_w:
        with space.iter(w_arg) as w_iter:
            while not w_iter.done():
                w_key, w_value = w_iter.next_item(space)
                w_arr = space.setitem(w_arr, w_key, w_value)
    return w_arr


@wrap(['space', ArrayArg(None), Optional(bool)])
def array_reverse(space, w_arr, preserve=False):
    """ Return an array with elements in reverse order """
    items = w_arr.as_rdict().items()
    d = OrderedDict()
    idx = 0
    for i in range(len(items) - 1, -1, -1):
        key, w_value = items[i]
        if not preserve:
            try:
                try_convert_str_to_int(key)
            except ValueError:
                pass
            else:
                key = str(idx)
                idx += 1
        d[key] = w_value
    return space.new_array_from_rdict(d)


@wrap(['space', W_Root, ArrayArg(None), Optional(bool)])
def array_search(space, w_needle, w_haystack, strict=False):
    """ Searches the array for a given value and
    returns the corresponding key if successful """
    with space.iter(w_haystack) as itr:
        while not itr.done():
            w_key, w_val = itr.next_item(space)
            w_res = space.eq(w_needle, w_val)
            if space.is_true(w_res):
                if strict:
                    if w_val.tp == w_needle.tp:
                        return w_key
                    else:
                        return space.w_False
                else:
                    return w_key
            else:
                continue
    return space.w_False


@wrap(['space', 'reference'])
def array_shift(space, w_ref):
    """ Shift an element off the beginning of array """
    w_arr = w_ref.deref()
    if w_arr.tp != space.tp_array:
        space.ec.warn("array_shift() expects parameter 1 "
                      "to be array, %s given" %
                      space.get_type_name(w_arr.tp))
        return space.w_Null
    new_arr = space.new_array_from_list([])
    first = True
    w_res = space.w_Null
    with space.iter(w_arr) as itr:
        while not itr.done():
            w_key, w_val = itr.next_item(space)
            if first:
                w_res = w_val
                first = False
                continue
            new_arr = new_arr.packitem_maybe_inplace(space, w_key, w_val)
    w_ref.store(new_arr, unique=True)
    return w_res


@wrap(['space', ArrayArg(None), int, Optional(W_Root), Optional(bool)])
def array_slice(space, w_arr, start=0, w_shift=None, keep_keys=False):
    """ Extract a slice of the array """
    if w_shift is None:
        shift = space.arraylen(w_arr)
    elif w_shift.tp == space.tp_null:
        shift = space.arraylen(w_arr)
    else:
        shift = space.int_w(w_shift)
    if start < 0 and abs(start) > space.arraylen(w_arr):
        start = 0
    return space.slice(w_arr, start, shift, keep_keys, keep_str_keys=True)


@wrap(['space', 'reference', int, 'num_args', Optional(int), Optional(W_Root)])
def array_splice(space, w_ref, offset, num_args, length=0, w_subs=None):
    """ Remove a portion of the array and replace it with something else """
    w_arr = w_ref.deref()
    if w_arr.tp != space.tp_array:
        space.ec.warn("array_splice() expects parameter 1 "
                      "to be array, %s given" % space.get_type_name(w_arr.tp))
        return space.w_Null
    arrlen = space.arraylen(w_arr)
    if offset < 0:
        offset += arrlen
        if offset < 0:
            offset = 0
    if num_args == 2:
        length = sys.maxint
    elif length < 0:
        length = arrlen + length - offset

    new_arr = space.new_array_from_list([])
    new_res = space.new_array_from_list([])

    with space.iter(w_arr) as itr:
        while not itr.done():
            w_key, w_val = itr.next_item(space)
            if offset > 0:
                new_arr = new_arr.packitem_maybe_inplace(space, w_key, w_val)
                offset -= 1
            elif length > 0:
                new_res = new_res.packitem_maybe_inplace(space, w_key, w_val)
                length -= 1
            else:
                if w_subs is not None:
                    _splice_add(space, new_arr, w_subs)
                    w_subs = None
                new_arr = new_arr.packitem_maybe_inplace(space, w_key, w_val)
    if w_subs is not None:
        _splice_add(space, new_arr, w_subs)

    w_ref.store(new_arr)
    return new_res


def _splice_add(space, new_arr, w_subs):
    if w_subs.tp == space.tp_array:
        with space.iter(w_subs) as w_iter:
            while not w_iter.done():
                w_val = w_iter.next(space)
                new_arr.appenditem_inplace(space, w_val)
    else:
        new_arr.appenditem_inplace(space, w_subs)


@wrap(['space', ArrayArg(None)])
def array_sum(space, w_arr):
    """ Calculate the sum of values in an array """
    res = 0
    is_float = False
    with space.iter(w_arr) as itr:
        while not itr.done():
            _, w_val = itr.next_item(space)
            w_val_n = space.as_number(w_val)
            if w_val_n.tp == space.tp_float:
                res += space.float_w(w_val_n)
                is_float = True
            else:
                res += space.int_w(w_val_n)
    if is_float:
        return space.newfloat(res)
    return space.newint(int(res))


@wrap(['space', 'args_w'])
def array_udiff_assoc(space, args_w):
    """ Computes the difference of arrays with additional index check,
    compares data by a callback function """
    if len(args_w) < 3:
        space.ec.warn("array_udiff_assoc(): at least 3 parameters "
                      "are required, %d given" % len(args_w))
        return space.w_Null
    w_callback = args_w.pop()
    callback_func = space.get_callback('array_udiff_assoc',
                                       4, w_callback)
    if callback_func is None:
        return space.w_Null

    for i, w_arg in enumerate(args_w):
        if w_arg.tp != space.tp_array:
            raise _not_an_array(i + 1)
    w_arr = args_w[0]
    rdict = space.get_rdict_from_array(w_arr)
    with space.iter(w_arr) as w_iter:
        while not w_iter.done():
            w_df_key, w_df_val = w_iter.next_item(space)
            for w_arg in args_w[1:]:
                with space.iter(w_arg) as w_arg_iter:
                    while not w_arg_iter.done():
                        w_key, w_val = w_arg_iter.next_item(space)
                        w_res = space.call_args(
                            callback_func, [w_df_val, w_val])
                        if space.int_w(w_res) == 0:
                            if space.eq_w(space.as_string(w_df_key),
                                          space.as_string(w_key)):
                                rdict = space.rdict_remove(rdict, w_df_key)
    return space.new_array_from_rdict(rdict)


@wrap(['space', 'args_w'])
def array_udiff_uassoc(space, args_w):
    """ Computes the difference of arrays with additional index check,
    compares data and indexes by a callback function """
    if len(args_w) < 4:
        space.ec.warn("array_udiff_uassoc(): at least 4 parameters "
                      "are required, %d given" % len(args_w))
        return space.w_Null
    w_callback = args_w.pop()
    callback_func = space.get_callback('array_udiff_uassoc',
                                       len(args_w) + 1, w_callback)
    if callback_func is None:
        return space.w_Null

    w_key_w_callback = args_w.pop()
    key_callback_func = space.get_callback('array_udiff_uassoc',
                                           len(args_w) + 1, w_key_w_callback)
    if key_callback_func is None:
        return space.w_Null

    for i, w_arg in enumerate(args_w):
        if w_arg.tp != space.tp_array:
            raise _not_an_array(i + 1)
    w_arr = args_w[0]
    rdict = space.get_rdict_from_array(w_arr)
    with space.iter(w_arr) as w_iter:
        while not w_iter.done():
            w_df_key, w_df_val = w_iter.next_item(space)
            for w_arg in args_w[1:]:
                with space.iter(w_arg) as w_arg_iter:
                    while not w_arg_iter.done():
                        w_key, w_val = w_arg_iter.next_item(space)
                        w_res = space.call_args(
                            callback_func, [w_df_val, w_val])
                        if space.int_w(w_res) == 0:
                            w_key_res = space.call_args(
                                key_callback_func, [w_df_key, w_key])
                            if space.int_w(w_key_res) == 0:
                                rdict = space.rdict_remove(rdict, w_df_key)
    return space.new_array_from_rdict(rdict)


@wrap(['space', 'args_w'])
def array_udiff(space, args_w):
    """ Computes the difference of arrays by "
    "using a callback function for data comparison """
    if len(args_w) < 3:
        space.ec.warn("array_udiff(): at least 3 parameters "
                      "are required, %d given" % len(args_w))
        return space.w_Null
    w_callback = args_w.pop()
    callback_func = space.get_callback('array_udiff',
                                  len(args_w) + 1, w_callback)
    if callback_func is None:
        return space.w_Null

    for i, w_arg in enumerate(args_w):
        if w_arg.tp != space.tp_array:
            raise _not_an_array(i + 1)
    args_w = args_w[1:]
    w_arr = args_w[0]
    rdict = space.get_rdict_from_array(w_arr)
    with space.iter(w_arr) as w_df_iter:
        while not w_df_iter.done():
            w_df_key, w_df_val = w_df_iter.next_item(space)
            for w_arg in args_w:
                with space.iter(w_arg) as w_iter:
                    while not w_iter.done():
                        _, w_val = w_iter.next_item(space)
                        w_res = space.call_args(
                            callback_func, [w_df_val, w_val])
                        if space.int_w(w_res) == 0:
                            space.rdict_remove(rdict, w_df_key)
    return space.new_array_from_rdict(rdict)


@wrap(['space', 'args_w'])
def array_uintersect_assoc(space, args_w):
    """ Computes the intersection of arrays with additional index check,
    compares data by a callback function """
    # XXX needs tests
    if len(args_w) < 3:
        space.ec.warn("array_uintersect_assoc(): at least 3 "
                      "parameters are required, %d given"
                      % len(args_w))
        return space.w_Null
    w_callback = args_w[-1]
    callback_func = space.get_callback('array_uintersect_assoc',
                                       len(args_w), w_callback)
    if callback_func is None:
        return space.w_Null
    stop = len(args_w) - 2
    assert stop >= 0
    for i, w_arg in enumerate(args_w[:stop]):
        if w_arg.tp != space.tp_array:
            raise _not_an_array(i + 1)

    w_arr = args_w[0]
    rdict = space.get_rdict_from_array(w_arr)
    stop = len(args_w) - 1
    assert stop >= 0
    args_w = args_w[1:stop]

    with space.iter(w_arr) as w_arr_iter:
        while not w_arr_iter.done():
            w_arr_key, w_arr_val = w_arr_iter.next_item(space)
            exists = 0
            for w_arg in args_w:
                with space.iter(w_arg) as w_arg_iter:
                    while not w_arg_iter.done():
                        w_arg_key, w_arg_val = w_arg_iter.next_item(space)
                        w_cb_res = space.call_args(
                            callback_func, [w_arr_val,
                                            w_arg_val])
                        if space.int_w(w_cb_res) == 0:
                            w_one = space.as_string(w_arr_key)
                            w_two = space.as_string(w_arg_key)
                            if space.is_w(w_one, w_two):
                                exists += 1
            if exists < len(args_w):
                space.rdict_remove(rdict, w_arr_key)
    return space.new_array_from_rdict(rdict)


@wrap(['space', 'args_w'])
def array_uintersect_uassoc(space, args_w):
    """ Computes the intersection of arrays with additional index check,
    compares data and indexes by a callback functions """
    if len(args_w) < 4:
        space.ec.warn("array_uintersect_uassoc(): at least 4 "
                      "parameters are required, %d given"
                      % len(args_w))
        return space.w_Null
    w_key_callback = args_w[-1]
    key_callback_func = space.get_callback('array_uintersect_uassoc',
                                           len(args_w), w_key_callback)
    if key_callback_func is None:
        return space.w_Null
    w_val_callback = args_w[-2]
    val_callback_func = space.get_callback('array_uintersect_uassoc',
                                  len(args_w) - 1, w_val_callback)
    if val_callback_func is None:
        return space.w_Null
    stop = len(args_w) - 2
    assert stop >= 0
    for i, w_arg in enumerate(args_w[:stop]):
        if w_arg.tp != space.tp_array:
            raise _not_an_array(i + 1)

    w_arr = args_w[0]
    rdict = space.get_rdict_from_array(w_arr)
    args_w = args_w[1:stop]
    with space.iter(w_arr) as w_arr_iter:
        while not w_arr_iter.done():
            w_arr_key, w_arr_val = w_arr_iter.next_item(space)
            exists = 0
            for w_arg in args_w:
                with space.iter(w_arg) as w_arg_iter:
                    while not w_arg_iter.done():
                        w_arg_key, w_arg_val = w_arg_iter.next_item(space)
                        w_cb_res = space.call_args(
                            val_callback_func, [w_arr_val,
                                                w_arg_val])
                        if space.int_w(w_cb_res) == 0:
                            w_cb_res = space.call_args(
                                key_callback_func, [w_arr_key,
                                                    w_arg_key])
                            if space.int_w(w_cb_res) == 0:
                                exists += 1
            if exists < len(args_w):
                space.rdict_remove(rdict, w_arr_key)
    return space.new_array_from_rdict(rdict)


@wrap(['space', 'args_w'])
def array_uintersect(space, args_w):
    """ Computes the intersection of arrays,
    compares data by a callback function """
    if len(args_w) < 3:
        space.ec.warn("array_uintersect(): at least 3 "
                      "parameters are required, %d given"
                      % len(args_w))
        return space.w_Null

    w_callback = args_w[-1]
    callback_func = space.get_callback('array_uintersect',
                                  4, w_callback)
    if callback_func is None:
        return space.w_Null

    stop = len(args_w) - 1
    assert stop >= 0
    for i, w_arg in enumerate(args_w[:stop]):
        if w_arg.tp != space.tp_array:
            raise _not_an_array(i + 1)

    w_arr = args_w[0]
    args_w = args_w[1:stop]
    rdict = space.get_rdict_from_array(w_arr)

    with space.iter(w_arr) as w_arr_iter:
        while not w_arr_iter.done():
            w_arr_key, w_arr_val = w_arr_iter.next_item(space)
            exists = 0
            for w_arg in args_w:
                with space.iter(w_arg) as w_arg_iter:
                    while not w_arg_iter.done():
                        w_arg_key, w_arg_val = w_arg_iter.next_item(space)
                        w_cb_res = space.call_args(
                            callback_func, [w_arr_val,
                                            w_arg_val])
                        if space.int_w(w_cb_res) == 0:
                            exists += 1
            if exists < len(args_w):
                try:
                    del rdict[space.str_w(w_arr_key)]
                except:
                    pass
    return space.new_array_from_rdict(rdict)


@wrap(['space', ArrayArg(None), Optional(int)])
def array_unique(space, w_arr, sort_type=0):
    """ Removes duplicate values from an array """
    pairs = [(w_k, space.as_string(w_v))
             for w_k, w_v in w_arr.as_pair_list(space)]
    _sort(space, pairs, sort_type=sort_type, elem=VALUE)
    last_val = None
    d = w_arr.get_rdict_from_array()
    for w_k, w_v in pairs:
        next_val = space.str_w(w_v)
        if last_val == next_val:
            del d[space.str_w(w_k)]
        last_val = next_val
    return space.new_array_from_rdict(d)


@wrap(['space', 'reference', 'args_w'])
def array_unshift(space, w_ref, args_w):
    """ Prepend one or more elements to the beginning of an array """
    w_arr = w_ref.deref()
    if w_arr.tp != space.tp_array:
        space.ec.warn("array_unshift() expects parameter 1 "
                      "to be array, %s given"
                      % space.get_type_name(w_arr.tp))
        return space.w_Null
    new_arr = space.new_array_from_list(args_w)
    with space.iter(w_arr) as w_arr_iter:
        while not w_arr_iter.done():
            w_key, w_val = w_arr_iter.next_item(space)
            new_arr = new_arr.packitem_maybe_inplace(space, w_key, w_val)
    w_ref.store(new_arr, unique=True)
    return space.wrap(new_arr.arraylen())


@wrap(['space', ArrayArg(None)])
def array_values(space, w_arr):
    """ Return all the values of an array """
    lst = []
    with space.iter(w_arr) as itr:
        while not itr.done():
            w_val = itr.next(space)
            lst.append(w_val)
    return space.new_array_from_list(lst)


@wrap(['space', 'reference', W_Root, Optional(W_Root)])
def array_walk_recursive(space, r_arr, w_callback, w_user_data=None):
    """ Apply a user function recursively to every member of an array """
    w_arr = r_arr.deref_temp()
    if w_arr.tp != space.tp_array:
        space.ec.warn("array_walk_recursive() expects parameter 1 "
                      "to be array, %s given"
                      % space.get_type_name(w_arr.tp))
        return space.w_Null
    callback_func = space.get_callback('array_walk_recursive', 2, w_callback)
    if callback_func is None:
        return space.w_Null
    _array_walk(space, r_arr, callback_func, w_user_data, recursive=True)
    return space.newbool(True)


def _array_walk(space, r_arr, callback_func, w_user_data, recursive=False):
    w_arr_iter = r_arr.deref_unique().create_iter_ref(space, r_arr)
    while not w_arr_iter.done():
        w_key, r_val = w_arr_iter.next_item(space)
        if r_val.deref_temp().tp == space.tp_array and recursive:
            _array_walk(space, r_val, callback_func, w_user_data,
                        recursive=True)
        else:
            if w_user_data is None:
                space.call_args(callback_func, [r_val, w_key])
            else:
                space.call_args(callback_func, [r_val, w_key, w_user_data])


@wrap(['space', 'reference', W_Root, Optional(W_Root)])
def array_walk(space, r_arr, w_callback, w_user_data=None):
    """ Apply a user function to every member of an array """
    w_arr = r_arr.deref_temp()
    if w_arr.tp != space.tp_array:
        space.ec.warn("array_walk() expects parameter 1 "
                      "to be array, %s given"
                      % space.get_type_name(w_arr.tp))
        return space.w_Null
    callback_func = space.get_callback('array_walk', 2, w_callback)
    if callback_func is None:
        return space.w_Null
    _array_walk(space, r_arr, callback_func, w_user_data)
    return space.newbool(True)


@wrap(['space', 'reference', Optional(int)], error=False)
def arsort(space, w_ref, sort_type=0):
    """ Sort an array in reverse order and maintain index association """
    w_arr = w_ref.deref()
    if w_arr.tp != space.tp_array:
        space.ec.warn("arsort() expects parameter 1 "
                      "to be array, %s given" %
                      space.get_type_name(w_arr.tp))
        return space.w_False
    pairs = w_arr.as_pair_list(space)
    _sort(space, pairs, sort_type=sort_type, elem=VALUE)
    pairs.reverse()
    w_ref.store(space.new_array_from_pairs(pairs), unique=True)
    return space.w_True


@wrap(['space', 'reference', Optional(int)], error=False)
def asort(space, w_ref, sort_type=0):
    """ Sort an array and maintain index association """
    w_arr = w_ref.deref()
    if w_arr.tp != space.tp_array:
        space.ec.warn("asort() expects parameter 1 "
                      "to be array, %s given" %
                      space.get_type_name(w_arr.tp))
        return space.w_False
    pairs = w_arr.as_pair_list(space)
    _sort(space, pairs, sort_type=sort_type, elem=VALUE)
    w_ref.store(space.new_array_from_pairs(pairs), unique=True)
    return space.w_True


def _compact(space, accum, w_obj):
    if w_obj.tp == space.tp_str:
        accum.append(space.str_w(w_obj))
    if w_obj.tp == space.tp_array:
        with space.iter(w_obj) as w_arr_iter:
            while not w_arr_iter.done():
                _, w_val = w_arr_iter.next_item(space)
                if w_val.tp == space.tp_str:
                    accum.append(space.str_w(w_val))
                if w_val.tp == space.tp_array:
                    return _compact(space, accum, w_val)
    return accum


@wrap(['space', 'args_w'])
def compact(space, args_w):
    """ Create array containing variables and their values """
    if len(args_w) < 1:
        space.ec.warn("compact() expects at least "
                      "1 parameter, %d given" % len(args_w))
        return space.w_Null

    fnames = []
    for w_arg in args_w:
        fnames += _compact(space, [], w_arg)
    d = new_rdict()
    for fname in fnames:
        w_var = space.lookup_local_vars(fname)
        if w_var:
            d[fname] = w_var
    return space.new_array_from_rdict(d)


def _count_recursive(space, w_arr, references=None):
    if references is None:
        references = {}
    _len = space.arraylen(w_arr)

    with space.iter(w_arr) as w_iter:
        while not w_iter.done():
            _, w_val = w_iter.next_item(space)
            w_val = w_val.deref()

            if isinstance(w_val, W_ArrayObject):
                if w_val in references:
                    references[w_val] += 1
                else:
                    references[w_val] = 0

                if references[w_val] > 1:
                    space.ec.warn("count(): recursion detected")
                    return _len
                _len = _len + _count_recursive(space, w_val, references)

    return _len

@wrap(['interp', W_Root, Optional(int)], aliases=['sizeof'])
def count(interp, w_arr, recursive=0):
    """Count all elements in an array, or something in an object"""
    if isinstance(w_arr, W_InstanceObject):
        k = w_arr.klass
        if k.is_subclass_of_class_or_intf_name('Countable'):
            return k.methods['count'].method_func.call_args(
                interp.space.ec.interpreter, [], w_this=w_arr, thisclass=k)

    if isinstance(w_arr, W_ArrayObject):
        if recursive == 1:
            result = _count_recursive(interp.space, w_arr)
        else:
            result = interp.space.arraylen(w_arr)
    else:
        result = int(w_arr is not interp.space.w_Null)
    return interp.space.wrap(result)


@wrap(['space', 'unique_array'], aliases=["pos"])
def current(space, w_arr):
    """ Return the current element in an array """
    return w_arr._current(space)


@wrap(['space', 'unique_array'])
def each(space, w_arr):
    """ Return the current key and value pair "
    "from an array and advance the array cursor """
    if w_arr.arraylen() == 0:
        return space.w_False
    w_key = w_arr._key(space)
    if w_key is space.w_Null:
        return space.w_False
    w_value = w_arr._current(space)
    w_arr.current_idx += 1

    pairs = [
        (space.wrap(1), w_value),
        (space.wrap('value'), w_value),
        (space.wrap(0), w_key),
        (space.wrap('key'), w_key)]
    return space.new_array_from_pairs(pairs)


@wrap(['space', 'unique_array'])
def end(space, w_arr):
    """ Set the internal pointer of an array to its last element """
    length = w_arr.arraylen()
    if length == 0:
        return space.w_False
    w_arr.current_idx = length - 1
    return w_arr._current(space)


@wrap(['space', 'frame', ArrayArg(None), Optional(W_Root), Optional(str)])
@jit.unroll_safe
def extract(space, frame, w_arr, w_extr=None, prefix=None):
    if w_extr is not None:
        w_extr = space.is_really_int(w_extr)
        if w_extr is None:
            space.ec.notice("A non well formed numeric value encountered")
            space.ec.warn("extract(): Invalid extract type")
            return space.w_Null
        extr = space.int_w(w_extr)
    else:
        extr = 0

        
    as_ref = extr & 0x100
    extr = extr & ~0x100

    if extr < 0 or extr > 6:
        space.ec.warn("extract(): Invalid extract type")
        return space.w_Null
    if extr in [2, 3, 4, 5] and prefix is None:
        space.ec.warn("extract(): specified extract type "
                      "requires the prefix parameter")
        return space.w_Null

    res = 0
    with space.iter(w_arr) as itr:
        while not itr.done():
            create = True
            w_key, w_val = itr.next_item(space)
            key = space.str_w(w_key)
            key = jit.promote_string(key)
            valid = space.is_valid_varname(key)

            exists = False
            if frame.extra_variables:
                exists = key in frame.extra_variables

            if extr == 0:  # EXTR_OVERWRITE
                if key == 'GLOBALS':
                    break
                if key == 'this':
                    break
                pass
            if extr == 1:  # EXTR_SKIP
                if exists:
                    break
            if extr == 2:  # EXTR_PREFIX_SAME
                if exists:
                    key = prefix + '_' + key
            if extr == 3:  # EXTR_PREFIX_ALL
                if len(key) == 0:
                    create = False
                key = prefix + '_' + key
            if extr == 4:  # EXTR_PREFIX_INVALID
                if not valid:
                    key = prefix + '_' + key
            if extr == 5:  # EXTR_PREFIX_IF_EXISTS
                if exists:
                    key = prefix + '_' + key
                else:
                    create = False
            if extr == 6:  # EXTR_IF_EXISTS
                if not exists:
                    create = False

            valid = space.is_valid_varname(key)
            if create and valid:
                if as_ref:
                    raise NotImplementedError()
                else:
                    frame.get_ref_by_name(key).store(w_val)
                res += 1
    return space.wrap(res)


@wrap(['space', W_Root, ArrayArg(None), Optional(bool)])
def in_array(space, w_needle, w_haystack, strict=False):
    """ Checks if a value exists in an array """
    with space.iter(w_haystack) as itr:
        while not itr.done():
            w_key, w_val = itr.next_item(space)
            if space.eq_w(w_val, w_needle):
                if strict:
                    if w_val.tp == w_needle.tp:
                        return space.w_True
                else:
                    return space.w_True
    return space.w_False


@wrap(['space', 'unique_array'])
def key(space, w_arr):
    """ Fetch a key from an array """
    return w_arr._key(space)


@wrap(['space', 'reference', Optional(int)], error=False)
def krsort(space, w_ref, sort_type=0):
    """ Sort an array by key in reverse order """
    w_arr = w_ref.deref()
    if w_arr.tp != space.tp_array:
        space.ec.warn("krsort() expects parameter 1 "
                      "to be array, %s given" %
                      space.get_type_name(w_arr.tp))
        return space.w_False
    pairs = w_arr.as_pair_list(space)
    _sort(space, pairs, sort_type=sort_type, elem=KEY)
    pairs.reverse()
    w_ref.store(space.new_array_from_pairs(pairs))
    return space.w_True


@wrap(['space', 'reference', Optional(int)], error=False)
def ksort(space, w_ref, sort_type=0):
    """ Sort an array by key """
    w_arr = w_ref.deref()
    if w_arr.tp != space.tp_array:
        space.ec.warn("ksort() expects parameter 1 "
                      "to be array, %s given" %
                      space.get_type_name(w_arr.tp))
        return space.w_False
    pairs = w_arr.as_pair_list(space)
    _sort(space, pairs, sort_type=sort_type, elem=KEY)
    w_ref.store(space.new_array_from_pairs(pairs))
    return space.w_True

# @wrap(['space', 'args_w'])
# def list(space, args_w):
#     """ Assign variables as if they were an array """
#     raise NotImplementedError()


@wrap(['interp', 'reference'])
def natsort(interp, w_ref):
    """ Sort an array using a "natural order" algorithm """
    # from hippy.string_funcs import _strnatcmp
    space = interp.space
    w_arr = w_ref.deref()
    if w_arr.tp != space.tp_array:
        interp.warn("natsort() expects parameter 1 "
                      "to be array, %s given" %
                      space.get_type_name(w_arr.tp))
        return space.w_False
    pairs = w_arr.as_pair_list(space)
    w_natsort_func = interp.lookup_function('strnatcmp')
    _sort(space, pairs, sort_type=2, elem=VALUE, cmp=w_natsort_func)
    w_ref.store(space.new_array_from_pairs(pairs))
    return space.w_True


@wrap(['interp', 'reference'])
def natcasesort(interp, w_ref):
    space = interp.space
    """ Sort an array using a "natural order" algorithm """
    # from hippy.string_funcs import _strnatcasecmp
    w_arr = w_ref.deref()
    if w_arr.tp != space.tp_array:
        interp.warn("natcasesort() expects parameter 1 "
                      "to be array, %s given" %
                      space.get_type_name(w_arr.tp))
        return space.w_Null
    pairs = w_arr.as_pair_list(space)
    w_natsort_func = interp.lookup_function('strnatcasecmp')
    _sort(space, pairs, sort_type=2, elem=VALUE, cmp=w_natsort_func)
    w_ref.store(space.new_array_from_pairs(pairs))
    return space.w_True


@wrap(['space', 'unique_array'])
def next(space, w_arr):
    """ Advance the internal array pointer of an array """
    length = w_arr.arraylen()
    current_idx = w_arr.current_idx + 1
    if current_idx >= length:
        w_arr.current_idx = length
        return space.w_False
    w_arr.current_idx = current_idx
    return w_arr._current(space)


@wrap(['space', 'unique_array'])
def prev(space, w_arr):
    """ Rewind the internal array pointer """
    length = w_arr.arraylen()
    current_idx = min(w_arr.current_idx, length) - 1
    if current_idx < 0:
        return space.w_False
    w_arr.current_idx = current_idx
    return w_arr._current(space)


def _xrange(start, end, inc):
    rev = False
    if start > end:
        end, start = start, end
        rev = True
    count = int((end - start) / inc)
    if count == 0:
        return [start]
    res = [start + n * inc for n in range(count)]
    if res[-1] + inc <= end:
        res.append(float(res[-1] + inc))
    if rev:
        res.reverse()
    return res


def _range_prepare_str_params(space, s, e):
    if s.is_really_valid_number(space) and e.is_really_valid_number(space):
        sn = space.as_number(s)
        en = space.as_number(e)
        return False, space.float_w(sn), space.float_w(en)
    elif s.is_really_valid_number(space) \
            and not e.is_really_valid_number(space):
        sn = space.as_number(s)
        return False, space.float_w(sn), 0
    elif not s.is_really_valid_number(space) \
            and e.is_really_valid_number(space):
        en = space.as_number(e)
        return False, 0, space.float_w(en)
    else:
        s = space.str_w(s)
        if len(s) == 0:
            s = 0
        else:
            s = ord(s[0])

        e = space.str_w(e)
        if len(e) == 0:
            e = 0
        else:
            e = ord(e[0])
        return True, s, e


@wrap(['space', W_Root, W_Root, Optional(W_Root)], name="range", error=False)
def _range(space, w_start, w_end, step=None):
    """ Create an array containing a range of elements """
    # XXX very naive implementation, needs more work
    if not step:
        step = 1
    else:
        step = space.float_w(space.as_number(step))
        if step == 0:
            space.ec.warn("range(): step exceeds the specified range")
            return space.w_False
    if w_start.tp == w_end.tp == space.tp_float:
        s = space.float_w(w_start)
        e = space.float_w(w_end)
        l = [space.wrap(x) for x in _xrange(s, e, step)]
    elif w_start.tp == w_end.tp == space.tp_int:
        s = space.int_w(w_start)
        e = space.int_w(w_end)
        if step == int(step):
            l = [space.wrap(int(x)) for x in _xrange(s, e, step)]
        else:
            l = [space.wrap(x) for x in _xrange(s, e, step)]
    elif w_start.tp == w_end.tp == space.tp_str:
        is_str, s, e = _range_prepare_str_params(space, w_start, w_end)
        if is_str:
            if step == int(step):
                l = [space.wrap(chr(int(x))) for x in _xrange(s, e, step)]
            else:
                l = [space.wrap(0)]
        else:
            if s == int(s) and e == int(e) and step == int(step):
                l = [space.wrap(int(x)) for x in _xrange(s, e, step)]
            else:
                l = [space.wrap(x) for x in _xrange(s, e, step)]
    else:
        if w_start.tp == space.tp_str:
            s = 0
            e = space.int_w(w_end)
        elif w_end.tp == space.tp_str:
            s = space.int_w(w_start)
            e = 0
        else:
            s = space.float_w(w_start)
            e = space.float_w(w_end)
        l = [space.wrap(x) for x in _xrange(s, e, step)]
    if abs(s - e) < step and abs(s - e) != 0:
        space.ec.warn("range(): step exceeds the specified range")
        return space.w_False
    return space.new_array_from_list(l)


@wrap(['space', 'unique_array'])
def reset(space, w_arr):
    """ Set the internal pointer of an array to its first element """
    w_arr.current_idx = 0
    return w_arr._current(space)


@wrap(['space', 'reference', Optional(int)], error=False)
def rsort(space, w_ref, sort_type=0):
    """ Sort an array in reverse order """
    w_arr = w_ref.deref()
    if w_arr.tp != space.tp_array:
        space.ec.warn("rsort() expects parameter 1 "
                      "to be array, %s given"
                      % space.get_type_name(w_arr.tp))
        return space.w_False
    values = w_arr._values(space)
    _sort(space, values, sort_type=sort_type)
    values.reverse()
    w_ref.store(space.new_array_from_list(values))
    return space.w_True


@wrap(['space', 'reference'])
def shuffle(space, w_ref):
    """ Shuffle an array """
    w_arr = w_ref.deref()
    if w_arr.tp != space.tp_array:
        space.ec.warn("shuffle() expects parameter 1 "
                      "to be array, %s given"
                      % space.get_type_name(w_arr.tp))
        return space.w_False
    values = []
    with space.iter(w_arr) as w_iter:
        while not w_iter.done():
            w_val = w_iter.next(space)
            values.append(w_val)
    for i in xrange(len(values) - 1, 0, -1):
        j = int(_random.random() * (i + 1))
        values[i], values[j] = values[j], values[i]
    w_ref.store(space.new_array_from_list(values), unique=True)
    return space.w_True

# # sizeof - Alias of count
# @wrap(['space', 'args_w'])
# def sizeof(space, args_w):
#     raise NotImplementedError()


@wrap(['space', 'reference', Optional(int)], error=False)
def sort(space, w_ref, sort_type=0):
    """ Sort an array """
    w_arr = w_ref.deref()
    if w_arr.tp != space.tp_array:
        space.ec.warn("sort() expects parameter 1 "
                      "to be array, %s given"
                      % space.get_type_name(w_arr.tp))
        return space.w_False
    values = list(w_arr._values(space))
    _sort(space, values, sort_type=sort_type)
    w_ref.store(space.new_array_from_list(values))
    return space.w_True


@wrap(['space', 'reference', 'callback'])
def uasort(space, w_ref, w_callback):
    """ Sort an array with a user-defined comparison "
    "function and maintain index association """
    w_arr = w_ref.deref()
    if w_arr.tp != space.tp_array:
        space.ec.warn("uasort() expects parameter 1 "
                      "to be array, %s given" %
                      space.get_type_name(w_arr.tp))
        return space.w_Null
    pairs = w_arr.as_pair_list(space)
    _sort(space, pairs, cmp=w_callback, elem=VALUE)
    w_ref.store(space.new_array_from_pairs(pairs))
    return space.w_True


@wrap(['space', 'reference', 'callback'])
def uksort(space, w_ref, w_callback):
    """ Sort an array by keys using a user-defined comparison function """
    w_arr = w_ref.deref()
    if w_arr.tp != space.tp_array:
        space.ec.warn("uksort() expects parameter 1 "
                      "to be array, %s given" %
                      space.get_type_name(w_arr.tp))
        return space.w_Null
    pairs = w_arr.as_pair_list(space)
    _sort(space, pairs, cmp=w_callback, elem=KEY)
    w_ref.store(space.new_array_from_pairs(pairs))
    return space.w_True


@wrap(['space', 'reference', 'callback'])
def usort(space, w_ref, w_callback):
    """ Sort an array by values using a user-defined comparison function """
    w_arr = w_ref.deref()
    if w_arr.tp != space.tp_array:
        space.ec.warn("usort() expects parameter 1 "
                      "to be array, %s given"
                      % space.get_type_name(w_arr.tp))
        return space.w_Null
    values = list(w_arr._values(space))
    _sort(space, values, cmp=w_callback)
    w_ref.store(space.new_array_from_list(values))
    return space.w_True
