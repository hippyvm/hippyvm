import sys
import operator
import signal
from collections import OrderedDict
from rpython.rlib.objectmodel import specialize, we_are_translated
from rpython.rlib.rarithmetic import intmask
from rpython.rlib.rstring import StringBuilder
from rpython.rlib.signature import signature, types
from rpython.rlib import jit, rsignal
from hippy.consts import BINOP_LIST, BINOP_COMPARISON_LIST
from hippy.error import VisibilityError, InvalidCallback
from hippy.objects.reference import W_Reference
from hippy.ast import W_Constant
from hippy.klass import DelayedClassConstant, all_builtin_classes
from hippy.objects.boolobject import W_BoolObject, w_True, w_False
from hippy.objects.nullobject import W_NullObject, w_Null
from hippy.objects.intobject import W_IntObject
from hippy.objects.floatobject import W_FloatObject
from hippy.objects.strobject import W_StringObject
from hippy.objects.arrayobject import W_ArrayObject
from hippy.objects.resources.resource import W_Resource
from hippy.objects.instanceobject import W_InstanceObject
from hippy.objects.resources.file_resource import W_FileResource
from hippy.objects.resources.dir_resource import W_DirResource
from hippy.objects.resources.stream_context import W_StreamContext
from hippy.objects.convert import convert_string_to_number
from hippy.module.regex.cache import RegexpCache
from hippy.builtin_klass import k_stdClass
from hippy.bytecode_cache import BytecodeCache
from hippy.constants import get_constants_by_module
from hippy.immut_cache import GlobalImmutCache
from hippy.builtin import BUILTIN_FUNCTIONS


PHP_WHITESPACE = ' \t\n\r\x0b\0'
MASK_31_63 = 31 if sys.maxint == 2**31 - 1 else 63



@specialize.memo()
def getspace():
    return ObjSpace()


@specialize.argtype(0)
def my_cmp(one, two, ignore_order=False):
    if one == two:
        return 0
    if ignore_order or one < two:
        return -1
    return 1


class ExecutionContext(object):
    def __init__(self, space):
        self.interpreter = None
        self.initialized = False

    def init_signals(self):
        if self.initialized:
            return
        self.initialized = True
        rsignal.pypysig_setflag(signal.SIGINT)

    def clear_signals(self):
        rsignal.pypysig_getaddr_occurred().c_value = 0
        rsignal.pypysig_default(signal.SIGINT)
        self.initialized = False

    def notice(self, msg):
        self.interpreter.notice(msg)

    def warn(self, msg):
        self.interpreter.warn(msg)

    def error(self, msg):
        self.interpreter.error(msg)

    def hippy_warn(self, msg):
        self.interpreter.hippy_warn(msg)

    def fatal(self, msg):
        self.interpreter.fatal(msg)

    def deprecated(self, msg):
        self.interpreter.deprecated(msg)

    def catchable_fatal(self, msg):
        self.interpreter.catchable_fatal(msg)

    def recoverable_fatal(self, msg):
        self.interpreter.recoverable_fatal(msg)

    def strict(self, msg):
        self.interpreter.strict(msg)


class ObjSpaceWithIter(object):
    def __init__(self, space, w_arr):
        self.iter = space.create_iter(w_arr)

    def __enter__(self):
        return self.iter

    def __exit__(self, exception_type, exception_val, trace):
        pass  # self.iter.mark_invalid()


class ObjSpace(object):
    """ This implements all the operations on the object. Since this is
    prebuilt, it should not contain any state
    """
    (tp_int, tp_float, tp_str, tp_array, tp_null, tp_bool,
     tp_object, tp_file_res, tp_dir_res, tp_stream_context,
     tp_mysql_link, tp_mysql_result,
     tp_constant, tp_delayed_class_const, tp_xmlparser_res, tp_mcrypt_res) = range(16)

    # in the same order as the types above
    TYPENAMES = ["integer", "double", "string", "array", "NULL", "boolean",
                 "object", "resource", "resource", "resource",
                 "resource", "resource", "constant", "delayed constant",
                 "resource", "resource"]

    w_True = w_True
    w_False = w_False
    w_Null = w_Null

    def __init__(self):
        self.regex_cache = RegexpCache(self)
        self.ec = ExecutionContext(self)
        self.bytecode_cache = BytecodeCache()
        self.setup_constants()
        self.setup_functions()
        self.setup_classes()

    def _setup_constant_any_case(self, name, w_value, outdict):
        cases = [c.lower() + c.upper() for c in name]
        for x in range(1 << len(name)):
            l = [cases[i][(x >> i) & 1] for i in range(len(name))]
            outdict[''.join(l)] = w_value

    def setup_constants(self):
        dct = OrderedDict()
        for modulename, lst in get_constants_by_module(self):
            for k, w_obj in lst:
                dct[k] = w_obj
        dct['PHP_INT_MAX'] = self.wrap(sys.maxint)
        dct['PHP_INT_SIZE'] = self.wrap(4 if sys.maxint < 2 ** 32 else 8)

        self._setup_constant_any_case('true', self.w_True, dct)
        self._setup_constant_any_case('false', self.w_False, dct)
        self._setup_constant_any_case('null', self.w_Null, dct)

        self.prebuilt_constants = dct.keys()
        self.global_constant_cache = GlobalImmutCache(self, dct,
                                                      force_lowcase=False)

    def setup_functions(self):
        self.global_function_cache = GlobalImmutCache(self, BUILTIN_FUNCTIONS)

    def setup_classes(self):
        self.prebuilt_classes = all_builtin_classes.keys()
        self.global_class_cache = GlobalImmutCache(self, all_builtin_classes)

    def int_w(self, w_obj):
        return w_obj.deref().int_w(self)

    def float_w(self, w_obj):
        return w_obj.deref().float_w(self)

    def is_true(self, w_obj):
        return w_obj.deref().is_true(self)

    @signature(types.any(), types.int(), returns=types.any())
    def newint(self, v):
        return W_IntObject(v)

    def newfloat(self, v):
        return W_FloatObject(v)

    def newbool(self, v):
        if v:
            return self.w_True
        return self.w_False

    @signature(types.any(), types.str(can_be_None=True), returns=types.any())
    def newstr(self, v):
        return W_StringObject.newconststr(v)

    @signature(types.any(), types.bytearray(), returns=types.any())
    def newmutablestr(self, v):
        return W_StringObject.newmutablestr(v)

    def get_new_res_id(self):
        self.ec.interpreter.last_resource_id += 1
        return self.ec.interpreter.last_resource_id

    def str_w(self, w_v, quiet=False):
        res = w_v.deref().str(self, quiet=quiet)
        assert res is not None
        return res

    def str_w_quiet(self, w_v, quiet=True):
        return w_v.deref().str(self, quiet=quiet)

    def as_string(self, w_v, quiet=False):
        return w_v.deref().as_string(self, quiet=quiet)

    def as_object(self, interp, w_v):
        w_arg = w_v.deref()
        if w_arg.tp == self.tp_object:
            w_obj = w_arg
        else:
            w_obj = self.default_object(interp)
            w_obj.cast_object_from(self, w_arg)
        return w_obj

    def as_number(self, w_v):
        return w_v.deref().as_number(self)

    def uplus(self, w_v):
        return w_v.deref().uplus(self)

    def uminus(self, w_v):
        return w_v.deref().uminus(self)

    def uplusplus(self, w_v):
        return w_v.deref().uplusplus(self)

    def uminusminus(self, w_v):
        return w_v.deref().uminusminus(self)

    def getitem(self, w_obj, w_item, give_notice=False):
        return w_obj.deref_temp().getitem(self, w_item.deref(),
                                          give_notice=give_notice)

    def setitem(self, w_obj, w_item, w_newvalue):
        # Warning: this API always makes a copy of the string or array.
        # If you want to do several changes to a string or array, look
        # at the documentation in setitem_maybe_inplace().
        w_arr = w_obj.deref().copy()
        w_arr, w_val2 = w_arr.setitem2_maybe_inplace(self, w_item, w_newvalue)
        # w_val2 is generally ignored; it is generally just w_newvalue
        return w_arr

    def setitem_maybe_inplace(self, w_obj, w_arg, w_value):
        """Supports efficiently setting items into strings or arrays.
        Warning!  Use only on objects that are known to be unique,
        i.e. not shared.  These objects are:

            * the result of an earlier call to space.new_array_from_xxx()
              or space.newmutablestr(), as long as it didn't escape yet

            * or, the result of w_obj.deref_unique(), which will make
              a copy in case of doubt and give you a unique object.

        This returns a resulting object, often the same one but not always,
        and that result is still unique, so you can chain operations like
        setitem_maybe_inplace() on it.

        Known-unique objects can be stored in W_Reference objects by
        using 'w_reference.store(w_unique_obj, unique=True)'.  Then
        'w_reference.deref_unique()' will not need to make a copy.
        """
        w_modified, _ = w_obj.setitem2_maybe_inplace(self, w_arg, w_value)
        return w_modified

    def appenditem_maybe_inplace(self, w_obj, w_value):
        """Same as setitem_maybe_inplace(), but for appending instead"""
        w_obj.appenditem_inplace(self, w_value)
        return w_obj   # always for now, but may change in the future

    def packitem_maybe_inplace(self, w_obj, w_arg, w_value):
        """Same as setitem_maybe_inplace(), but if w_arg turns out to be
        a valid integer, ignore it and do a regular append instead."""
        w_modified = w_obj.packitem_maybe_inplace(self, w_arg, w_value)
        return w_modified

    def concat(self, w_left, w_right):
        return self.as_string(w_left).strconcat(self, self.as_string(w_right))

    def strlen(self, w_obj):
        return w_obj.deref_temp().strlen()

    def arraylen(self, w_obj):
        return w_obj.deref_temp().arraylen()

    def slice(self, w_arr, start, shift, keep_keys, keep_str_keys=False):
        if shift == 0:
            return self.new_array_from_list([])
        if self.arraylen(w_arr) == 0:
            return self.new_array_from_list([])
        if start > self.arraylen(w_arr):
            return self.new_array_from_list([])

        if start < 0:
            start = self.arraylen(w_arr) + start
        if shift < 0:
            shift = self.arraylen(w_arr) + shift - start

        next_idx = 0
        res_arr = []
        idx = 0
        with self.iter(w_arr) as itr:
            while not itr.done():
                w_key, w_value = itr.next_item(self)
                if start <= idx < start + shift:
                    if keep_keys:
                        res_arr.append((w_key, w_value))
                    else:
                        if keep_str_keys:
                            if w_key.tp == self.tp_str:
                                res_arr.append((w_key, w_value))
                            else:
                                res_arr.append((self.newint(next_idx),
                                                w_value))
                                next_idx += 1
                        else:
                            res_arr.append((self.newint(next_idx), w_value))
                            next_idx += 1
                idx += 1
        return self.new_array_from_pairs(res_arr)

    def getchar(self, w_obj):
        # get first character
        return w_obj.deref().as_string(self).getchar(self)

    @specialize.argtype(1)
    def wrap(self, v):
        if v is None:
            return self.w_Null
        if isinstance(v, bool):
            return self.newbool(v)
        elif isinstance(v, int):
            return self.newint(v)
        elif isinstance(v, str):
            return self.newstr(v)
        elif isinstance(v, float):
            return self.newfloat(v)
        elif not we_are_translated() and isinstance(v, long):
            raise TypeError("longs are not RPython!")
        elif isinstance(v, str):
            return self.newstr(v)
        else:
            raise NotImplementedError(v)

    def _freeze_(self):
        return True

    def call_args(self, w_callable, args_w):
        return w_callable.call_args(self.ec.interpreter, args_w)

    def new_array_from_list(self, lst_w):
        return W_ArrayObject.new_array_from_list(self, lst_w)

    def new_array_from_rdict(self, rdict_w):
        return W_ArrayObject.new_array_from_rdict(self, rdict_w)

    def get_rdict_from_array(self, w_arr):
        return w_arr.deref_temp().get_rdict_from_array()

    def rdict_remove(self, rdict, w_obj):
        rstr = w_obj.deref().str(self)
        try:
            del rdict[rstr]
        except KeyError:
            pass

    def new_array_from_dict(self, dict_w):
        "NOT_RPYTHON: for tests only (gets a random ordering)"
        rdict_w = OrderedDict()
        for key, w_value in dict_w.items():
            rdict_w[key] = w_value
        return W_ArrayObject.new_array_from_rdict(self, rdict_w)

    def new_array_from_pairs(self, pairs_ww, allow_bogus=False):
        return W_ArrayObject.new_array_from_pairs(self, pairs_ww,
                                                  allow_bogus=allow_bogus)

    new_map_from_pairs = new_array_from_pairs   # for now

    def iter(self, w_arr):
        return ObjSpaceWithIter(self, w_arr)

    def create_iter(self, w_arr, contextclass=None):
        w_arr = w_arr.deref()
        return w_arr.create_iter(self, contextclass)

    def create_iter_ref(self, r_array, contextclass=None):
        if not isinstance(r_array, W_Reference):
            raise self.ec.fatal("foreach(1 as &2): argument 1 must be a "
                                "variable")
        w_arr = r_array.deref_temp()
        return w_arr.create_iter_ref(self, r_array, contextclass)

    def str_eq(self, w_one, w_two, quiet=False):
        w_one = w_one.deref()
        w_two = w_two.deref()
        if w_one.tp != w_two.tp:
            w_one = self.as_string(w_one, quiet=quiet)
            w_two = self.as_string(w_two, quiet=quiet)
        return self._compare(w_one, w_two, ignore_order=True) == 0

    def get_globals_wrapper(self):
        return self.ec.interpreter.globals

    def lookup_local_vars(self, name):
        frame = self.ec.interpreter.topframeref()
        try:
            return frame.get_ref_by_name(name, create_new=False)
        except KeyError:
            return None

    def as_array(self, w_obj):
        w_obj = w_obj.deref()
        if w_obj.tp == self.tp_object:
            return w_obj.get_rdict_array(self)
        if w_obj.tp != self.tp_array:
            if w_obj is self.w_Null:
                return self.new_array_from_list([])
            w_obj = self.new_array_from_list([w_obj])
        assert isinstance(w_obj, W_ArrayObject)
        return w_obj

    def is_array(self, w_obj):
        return w_obj.deref().tp == self.tp_array

    def is_str(self, w_obj):
        return w_obj.deref().tp == self.tp_str

    def is_null(self, w_obj):
        return w_obj.deref().tp == self.tp_null

    def is_object(self, w_obj):
        return w_obj.deref().tp == self.tp_object

    def is_resource(self, w_obj):
        return isinstance(w_obj, W_Resource)

    def gettypename(self, w_obj):
        w_obj = w_obj.deref()
        if isinstance(w_obj, W_InstanceObject):
            return 'instance of ' + w_obj.klass.name
        else:
            return self.TYPENAMES[w_obj.tp].lower()

    def eq(self, w_left, w_right):
        res = self._compare(w_left, w_right, ignore_order=True)
        return self.newbool(res == 0)

    def eq_w(self, w_left, w_right):
        res = self._compare(w_left, w_right, ignore_order=True)
        return res == 0

    def ne(self, w_left, w_right):
        res = self._compare(w_left, w_right, ignore_order=True)
        return self.newbool(res != 0)

    def lt(self, w_left, w_right):
        res = self._compare(w_left, w_right)
        return self.newbool(res < 0)

    def gt(self, w_left, w_right):
        res = self._compare(w_left, w_right)
        return self.newbool(res > 0)

    def le(self, w_left, w_right):
        res = self._compare(w_left, w_right)
        return self.newbool(res <= 0)

    def ge(self, w_left, w_right):
        res = self._compare(w_left, w_right)
        return self.newbool(res >= 0)

    def mod(self, w_left, w_right):
        left = self.force_int(w_left)
        right = self.force_int(w_right)
        return self._mod(left, right)

    def _mod(self, left, right):
        if right == 0:
            self.ec.warn("Division by zero")
            return self.w_False
        elif right == -1:
            return self.newint(0)
        z = left % right
        if z != 0 and ((left < 0 and right > 0) or (left > 0 and right < 0)):
            z -= right
        return self.newint(z)

    def or_string(self, w_left, w_right):
        left = w_left.unwrap()
        right = w_right.unwrap()
        if len(left) < len(right):
            left, right = right, left
        s = StringBuilder(len(left))
        for i in range(len(right)):
            char = chr(ord(left[i]) | ord(right[i]))
            s.append(char)
        for i in range(len(right), len(left)):
            s.append(left[i])
        return self.newstr(s.build())

    def or_(self, w_left, w_right):
        if (isinstance(w_left, W_StringObject) and
                isinstance(w_right, W_StringObject)):
            return self.or_string(w_left, w_right)
        else:
            left = w_left.int_w(self)
            right = w_right.int_w(self)
            return self.newint(left | right)

    def lshift(self, w_left, w_right):
        left = self.force_int(w_left)
        right = self.force_int(w_right)
        z = intmask(left << (right & MASK_31_63))
        return W_IntObject(z)

    def rshift(self, w_left, w_right):
        left = self.force_int(w_left)
        right = self.force_int(w_right)
        z = intmask(left >> (right & MASK_31_63))
        return W_IntObject(z)

    def is_w(self, w_a, w_b):
        return self._compare(w_a, w_b, strict=True, ignore_order=True) == 0

    def _compare(self, w_left, w_right, strict=False, ignore_order=False):

        w_left = w_left.deref()
        w_right = w_right.deref()

        left_tp = w_left.tp
        right_tp = w_right.tp

        if strict:
            if left_tp != right_tp:
                return 1

        if(left_tp == self.tp_float and right_tp == self.tp_float):
            return my_cmp(self.float_w(w_left), self.float_w(w_right),
                          ignore_order)

        if(left_tp == self.tp_int and right_tp == self.tp_float):
            return my_cmp(self.float_w(w_left), self.float_w(w_right),
                          ignore_order)

        if(left_tp == self.tp_float and right_tp == self.tp_int):
            return my_cmp(self.float_w(w_left), self.float_w(w_right),
                          ignore_order)

        elif(left_tp == self.tp_int and right_tp == self.tp_int):
            return my_cmp(self.int_w(w_left), self.int_w(w_right),
                          ignore_order)

        elif(left_tp == self.tp_array and right_tp == self.tp_array):
            return self._compare_array(w_left, w_right, strict)

        elif(left_tp == self.tp_null and right_tp == self.tp_null):
            return 0

        elif(left_tp == self.tp_null and right_tp == self.tp_bool):
            if self.is_true(w_right):
                return -1
            return 0

        elif(left_tp == self.tp_bool and right_tp == self.tp_null):
            if self.is_true(w_left):
                return 1
            return 0

        elif(left_tp == self.tp_bool and right_tp == self.tp_bool):
            return my_cmp(self.is_true(w_left), self.is_true(w_right),
                          ignore_order)

        elif(left_tp == self.tp_str and right_tp == self.tp_str):
            left  = self.str_w(w_left)
            right = self.str_w(w_right)
            if not strict:
                # a small optimimization first, if both are single-char
                left_length  = len(left)
                right_length = len(right)
                if (jit.isconstant(left_length)  and left_length  == 1 and
                    jit.isconstant(right_length) and right_length == 1):
                    return my_cmp(ord(left[0]), ord(right[0]), ignore_order)
                #
                w_right_num, right_valid = convert_string_to_number(right)
                if right_valid:
                    w_left_num, left_valid = convert_string_to_number(left)
                    if left_valid:
                        return self._compare(w_left_num, w_right_num,
                                             ignore_order=ignore_order)
            return my_cmp(left, right, ignore_order)

        elif(left_tp == self.tp_null and right_tp == self.tp_str):
            return my_cmp("", self.str_w(w_right), ignore_order)

        elif(left_tp == self.tp_str and right_tp == self.tp_null):
            return my_cmp(self.str_w(w_left), "", ignore_order)

        elif(left_tp == self.tp_object and right_tp == self.tp_null):
            return 1

        elif(left_tp == self.tp_null and right_tp == self.tp_object):
            return -1

        elif(left_tp == self.tp_object and right_tp == self.tp_object):
            return w_left.compare(w_right, self, strict)

        else:
            if(left_tp == self.tp_null):
                if self.is_true(w_right):
                    return -1
                return 0
            elif(right_tp == self.tp_null):
                if self.is_true(w_left):
                    return 1
                return 0
            elif(left_tp == self.tp_bool or right_tp == self.tp_bool):
                return my_cmp(self.is_true(w_left), self.is_true(w_right),
                              ignore_order)
            elif(left_tp == self.tp_array):
                return 1
            elif(right_tp == self.tp_array):
                return -1
            elif(left_tp == self.tp_object):
                return 1
            elif(right_tp == self.tp_object):
                return -1
            else:
                return self._compare(self.as_number(w_left),
                                     self.as_number(w_right),
                                     ignore_order=ignore_order)
        raise NotImplementedError()

    def _compare_object(self, w_left, w_right, strict):
        if w_left is w_right:
            return 0
        elif strict or w_left.getclass() is not w_right.getclass():
            return 1

        left = w_left.get_instance_attrs()
        right = w_right.get_instance_attrs()
        if len(left) - len(right) < 0:
            return -1
        if len(left) - len(right) > 0:
            return 1

        for key, w_value in left.iteritems():
            try:
                w_right_value = right[key]
            except KeyError:
                return 1
            cmp_res = self._compare(w_value, w_right_value)
            if cmp_res == 0:
                continue
            else:
                return cmp_res
        return 0

    def _compare_array(self, w_left, w_right, strict):
        if w_left.arraylen() - w_right.arraylen() < 0:
            return -1
        if w_left.arraylen() - w_right.arraylen() > 0:
            return 1
        with self.iter(w_left) as itr:
            while not itr.done():
                w_key, w_value = itr.next_item(self)
                if w_right.isset_index(self, w_key):
                    w_right_value = self.getitem(w_right, w_key)
                    if strict:
                        cmp_res = self._compare(w_value,
                                                w_right_value,
                                                strict=True)
                    else:
                        cmp_res = self._compare(w_value, w_right_value)
                    if cmp_res == 0:
                        continue
                    else:
                        return cmp_res
                else:
                    return 1
        return 0


    def getclass(self, w_obj):
        return w_obj.deref().getclass()

    def get_type_name(self, tp):
        return self.TYPENAMES[tp].lower()

    def is_really_int(self, w_obj):
        if w_obj.tp == self.tp_str:
            w_obj, fully_processed = convert_string_to_number(
                self.str_w(w_obj))
            if not fully_processed:
                return None
        if w_obj.tp == self.tp_int:
            return w_obj

    def overflow_convert(self, w_obj):
        return w_obj.overflow_convert(self)

    def _force_int_from_str(self, w_obj):
        s = self.str_w(w_obj)
        decstr = ""
        i = 0
        while i < len(s) and s[i] in PHP_WHITESPACE:
            i += 1
        for c in s[i:]:
            if ('0' <= c <= '9'):
                decstr += c
            elif c == '-':
                decstr += c
            elif c == '+':
                decstr += c
            else:
                break
        if decstr == '':
            return 0
        return int(decstr)

    def force_int(self, w_obj):
        if w_obj.tp == self.tp_str:
            return self._force_int_from_str(w_obj)
        elif w_obj.tp == self.tp_int:
            return self.int_w(w_obj)
        return w_obj.as_number(self).int_w(self)

    @jit.elidable
    def is_valid_varname(self, name):
        if len(name) == 0:
            return False
        c = name[0]
        if not('a' <= c <= 'z' or 'A' <= c <= 'Z' or c == '_'):
            return False
        for i in range(1, len(name)):
            c = name[i]
            if not('a' <= c <= 'z' or 'A' <= c <= 'Z' or c == '_'
                   or '0' <= c <= '9'):
                return False
        return True

    def is_integer(self, w_obj):
        if w_obj.tp == self.tp_int:
            return True
        if isinstance(w_obj, W_StringObject):
            return w_obj.is_really_valid_number()
        return False

    def getclassintfname(self, w_obj):
        w_obj = w_obj.deref()
        if isinstance(w_obj, W_InstanceObject):
            classname = w_obj.klass.get_identifier()
            return classname
        else:
            class_or_interface_name = self.str_w(w_obj)
            return class_or_interface_name

    def instanceof_w(self, w_left, w_right):
        from hippy.klass import ClassBase

        if isinstance(w_right, ClassBase):
            classintfname = w_right.name
        elif self.is_null(w_right):
            return False
        else:
            classintfname = self.getclassintfname(w_right)
        klass = self.getclass(w_left)
        if klass is None:
            return False
        return klass.is_subclass_of_class_or_intf_name(classintfname)

    def is_string(self, w_obj):
        s = self.str_w(w_obj)
        if not s:
            return True
        if s[0] == "0" and len(s) != 1:
            return True
        if s[0] < '0' or s[0] > '9':
            return True
        return False

    def instanceof(self, w_left, w_right):
        return self.newbool(self.instanceof_w(w_left, w_right))

    def empty_ref(self):
        return W_Reference(self.w_Null)

    def default_object(self, interp):
        """Create a default object instance"""
        return k_stdClass.call_args(interp, [])

    def array_to_string_conversion(self, w_arr):
        out = ""
        with self.iter(w_arr) as itr:
            while not itr.done():
                w_key, w_value = itr.next_item(self)
                if w_value.tp == self.tp_array:
                    self.ec.notice("Array to string conversion")
                out += self.str_w(w_value)
        return self.newstr(out)

    def _get_callback_from_string(self, name):
        pos = name.find('::')
        if pos >= 0:
            clsname = name[:pos]
            methname = name[pos + 2:]
            return self._get_callback_from_class(clsname, methname)
        try:
            return self.ec.interpreter.lookup_function(name)
        except KeyError:
            raise InvalidCallback("function '%s' not found or invalid "
                                    "function name" % (name))

    def _get_callback_from_class(self, clsname, methname):
        interp = self.ec.interpreter
        klass = interp.lookup_class_or_intf(clsname)
        if klass is None:
            raise InvalidCallback("class '%s' not found" % (clsname))
        contextclass = interp.get_contextclass()
        w_this = interp.get_frame().w_this
        try:
            meth = klass.getstaticmeth(methname, contextclass, w_this, interp)
        except VisibilityError as e:
            raise InvalidCallback(e.msg_callback(static=True))
        return meth.bind(w_this, klass)

    def _get_callback_from_instance(self, w_instance, methname):
        contextclass = self.ec.interpreter.get_contextclass()
        try:
            meth = w_instance.getmeth(self, methname, contextclass)
        except VisibilityError as e:
            raise InvalidCallback(e.msg_callback(static=False))
        return meth

    def get_callback(self, fname, arg_no, w_obj, give_warning=True):
        try:
            return self._get_callback(w_obj)
        except InvalidCallback as e:
            if give_warning:
                err_msg = ("%s() expects parameter %d to be a valid callback, %s" %
                           (fname, arg_no, e.msg))
                self.ec.warn(err_msg)
            return None

    def _get_callback(self, w_obj):
        from hippy.objects.closureobject import W_ClosureObject
        if w_obj.tp == self.tp_str:
            name = self.str_w(w_obj)
            return self._get_callback_from_string(name)
        elif w_obj.tp == self.tp_array:
            if w_obj.arraylen() != 2:
                raise InvalidCallback("array must have exactly two members")
            w_instance = self.getitem(w_obj, self.wrap(0)).deref()
            if isinstance(w_instance, W_InstanceObject):
                methname = self.str_w(self.getitem(w_obj, self.wrap(1)))
                return self._get_callback_from_instance(w_instance, methname)
            clsname = self.str_w(w_instance)
            if not self.is_valid_varname(clsname):
                raise InvalidCallback("first array member is not a valid "
                                      "class name or object")
            methname = self.str_w(self.getitem(w_obj, self.wrap(1)))
            return self._get_callback_from_class(clsname, methname)
        elif isinstance(w_obj, W_InstanceObject):
            callable = w_obj.get_callable()
            if callable is not None:
                return callable
        raise InvalidCallback("no array or string given")

    def serialize(self, w_obj):
        from hippy.module.serialize import SerializerMemo

        assert not isinstance(w_obj, W_Reference)
        builder = StringBuilder()
        w_obj.serialize(self, builder, SerializerMemo())
        return builder.build()

    def set_errno(self, errno):
        self.ec.interpreter.last_posix_errno = errno

    def get_errno(self):
        return self.ec.interpreter.last_posix_errno

    def compile_file(self, filename):
        return self.bytecode_cache.compile_file(filename, self)


def _new_binop(name):
    def func(self, w_left, w_right):
        w_left = w_left.deref()
        w_right = w_right.deref()
        if name == "add" and self.is_array(w_left) and self.is_array(w_right):
            # obscure case
            return w_left.add(self, w_right)
        if not w_left.supports_arithmetics or not w_right.supports_arithmetics:
            self.ec.fatal("Unsupported operand types")
            return self.w_Null
        w_left = w_left.as_number(self)
        w_right = w_right.as_number(self)
        if w_left.tp == self.tp_int:
            if w_right.tp == self.tp_int:
                return getattr(w_left, name)(self, w_right)
            w_left = self.newfloat(w_left.float_w(self))
        else:
            if w_right.tp == self.tp_int:
                w_right = self.newfloat(w_right.float_w(self))
        assert w_left.tp == self.tp_float
        assert w_right.tp == self.tp_float
        return getattr(w_left, name)(self, w_right)
    func.func_name = name
    return func

for _name in set(BINOP_LIST) - set(BINOP_COMPARISON_LIST):
    if not hasattr(ObjSpace, _name):
        setattr(ObjSpace, _name, _new_binop(_name))

def _new_bitwise(name):
    bitwise_op = getattr(operator, name)
    def string_func(space, w_left, w_right):
        left = w_left.unwrap()
        right = w_right.unwrap()
        n = min(len(left), len(right))
        s = StringBuilder(n)
        for i in range(n):
            char = chr(bitwise_op(ord(left[i]), ord(right[i])))
            s.append(char)
        return space.newstr(s.build())

    def func(self, w_left, w_right):
        if (isinstance(w_left, W_StringObject) and
                isinstance(w_right, W_StringObject)):
            return string_func(self, w_left, w_right)

        left = w_left.int_w(self)
        right = w_right.int_w(self)
        return self.newint(bitwise_op(left, right))
    func.func_name = name
    return func

for _name in ['and_', 'xor']:
    setattr(ObjSpace, _name, _new_bitwise(_name))

W_FloatObject.tp = ObjSpace.tp_float
W_BoolObject.tp = ObjSpace.tp_bool
W_IntObject.tp = ObjSpace.tp_int
W_StringObject.tp = ObjSpace.tp_str
W_ArrayObject.tp = ObjSpace.tp_array
W_NullObject.tp = ObjSpace.tp_null
W_InstanceObject.tp = ObjSpace.tp_object
W_FileResource.tp = ObjSpace.tp_file_res
W_DirResource.tp = ObjSpace.tp_dir_res
W_StreamContext.tp = ObjSpace.tp_stream_context

from hippy.hippyoption import is_optional_extension_enabled
if is_optional_extension_enabled("mysql"):
    from ext_module.mysql.link_resource import W_MysqlLinkResource
    from ext_module.mysql.result_resource import W_MysqlResultResource
    W_MysqlLinkResource.tp = ObjSpace.tp_mysql_link
    W_MysqlResultResource.tp = ObjSpace.tp_mysql_result

if is_optional_extension_enabled("xml"):
    from ext_module.xml.xmlparser import XMLParserResource
    XMLParserResource.tp = ObjSpace.tp_xmlparser_res

if is_optional_extension_enabled("mcrypt"):
    from ext_module.mcrypt.mcrypt_resource import W_McryptResource
    W_McryptResource.tp = ObjSpace.tp_mcrypt_res

W_Constant.tp = ObjSpace.tp_constant
DelayedClassConstant.tp = ObjSpace.tp_delayed_class_const
