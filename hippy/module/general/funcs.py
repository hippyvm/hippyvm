from hippy.builtin import wrap, Optional, LongArg, BoolArg, StringArg
from collections import OrderedDict
from hippy.objects.base import W_Root
from hippy.objects.instanceobject import W_InstanceObject, demangle_property
from rpython.rlib.rarithmetic import intmask
from rpython.rlib.rstring import StringBuilder
from hippy.module import serialize as serialize_mod
from hippy.phpcompiler import compile_php
from hippy.constants import get_const
from hippy.config import EXTENSIONS
import os
import time


@wrap(['space', W_Root])
def boolval(space, w_obj):
    """ Get the boolean value of a variable"""
    return space.newbool(space.is_true(w_obj))


@wrap(['space', W_Root], aliases=["doubleval"])
def floatval(space, w_obj):
    """ Get float value of a variable"""
    return space.newfloat(w_obj.float_w(space))


@wrap(['frame', 'interp'])
def get_defined_vars(frame, interp):
    """ Returns an array of all defined variables"""
    space = interp.space
    pairs = []
    if frame.context:
        is_method = (frame.get_contextclass() is not None)
        vars = frame.vars_w
        for k in frame.bytecode.varnames:
            if k == 'this' and is_method:
                continue
            v = vars[frame.bytecode.var_to_pos[k]]
            if v:
                pairs.append((space.wrap(k), v.deref()))
    else:
        for k, v in frame.extra_variables.items():
            if k != 'GLOBALS':
                pairs.append((space.wrap(k), v.deref()))
    return space.new_array_from_pairs(pairs)


@wrap(['space', W_Root])
def gettype(space, w_obj):
    """ Get the type of a variable"""
    return space.newstr(space.TYPENAMES[w_obj.tp])


@wrap(['interp', 'reference', str])
def settype(interp, w_ref, type):
    space = interp.space
    if type == "string":
        w_ref.store(space.newstr(space.str_w(w_ref.deref())))
    elif type == "integer" or type == "int":
        w_ref.store(space.newint(space.int_w(w_ref.deref())))
    elif type == "boolean" or type == "bool":
        w_ref.store(space.newbool(space.is_true(w_ref.deref())))
    elif type == "float":
        w_ref.store(space.newfloat(space.float_w(w_ref.deref())))
    elif type == "array":
        w_ref.store(space.as_array(w_ref.deref()))
    elif type == "object":
        w_ref.store(space.as_object(interp, w_ref.deref()))
    elif type == "null":
        w_ref.store(space.w_Null)
    else:
        return space.w_False
    return space.w_True


def _fits_in_base(c, base):
    if ord('0') <= ord(c) <= ord('9'):
        if ord(c) - ord('0') < base:
            return True
        return False
    if ord('a') <= ord(c) <= ord('z'):
        if ord(c) - ord('a') < base - 10:
            return True
        return False
    return False


@wrap(['space', W_Root, Optional(LongArg(None))])
def intval(space, w_obj, base=10):
    """ Get the integer value of a variable"""
    if w_obj.tp == space.tp_array:
        if space.arraylen(w_obj) == 0:
            return space.wrap(0)
        return space.wrap(1)
    elif w_obj.tp == space.tp_int:
        return w_obj
    elif w_obj.tp == space.tp_bool:
        return space.as_number(w_obj)
    elif w_obj.tp == space.tp_null:
        return space.wrap(0)
    elif w_obj.tp == space.tp_float:
        try:
            res = intmask(int(space.float_w(w_obj)))
            if abs(res - space.float_w(w_obj)) > 1.0:
                return space.wrap(0)
            return space.wrap(int(str(res), base))
        except OverflowError:
            return space.wrap(0)
    elif w_obj.tp == space.tp_str:
        s = space.str_w(w_obj)
        s = s.lower()
        if not s:
            return space.wrap(0)
        if base == 16 and (s.startswith('0x') or s.startswith('0X')):
            s = s[2:]
        if base < 0:
            return space.wrap(0)
        i = 0
        if s[0] == '-' or s[0] == '+':
            i += 1
        while i < len(s):
            c = s[i]
            if _fits_in_base(c, base):
                i += 1
            else:
                break
        if i == 0:
            return space.wrap(0)
        try:
            res = intmask(int(s[:i], base))
            return space.wrap(res)
        except OverflowError:
            return space.wrap(0)
    elif w_obj.tp == space.tp_dir_res:
        return space.wrap(0)
    elif w_obj.tp == space.tp_file_res:
        return space.wrap(0)
    elif w_obj.tp == space.tp_object:
        return w_obj.as_number(space)
    raise NotImplementedError(w_obj)


@wrap(['space', W_Root], error=False)
def is_array(space, w_obj):
    """ Finds whether a variable is an array"""
    return space.wrap(w_obj.tp == space.tp_array)


@wrap(['space', W_Root], error=False)
def is_bool(space, w_obj):
    """ Finds out whether a variable is a boolean"""
    return space.wrap(w_obj.tp == space.tp_bool)


@wrap(['space', W_Root], error=False)
def is_double(space, w_obj):
    """ Alias of is_float"""
    return space.wrap(w_obj.tp == space.tp_float)


@wrap(['space', W_Root], error=False)
def is_unicode(space, w_obj):
    """ Finds whether the given variable is a unicode string."""
    return space.wrap(True)


@wrap(['space', W_Root], aliases=['is_real'], error=False)
def is_float(space, w_obj):
    """ Finds whether the type of a variable is float"""
    return space.wrap(w_obj.tp == space.tp_float)


@wrap(['space', W_Root], aliases=['is_int', 'is_long'], error=False)
def is_integer(space, w_obj):
    """ Find whether the type of a variable is integer"""
    return space.wrap(w_obj.tp == space.tp_int)


@wrap(['space', W_Root], error=False)
def is_null(space, w_obj):
    """ Finds whether a variable is NULL"""
    return space.wrap(w_obj.tp == space.tp_null)


@wrap(['space', W_Root])
def is_numeric(space, w_obj):
    """ Finds whether a variable is a number or a numeric string"""
    if w_obj.tp in [space.tp_float, space.tp_int]:
        return space.w_True
    if w_obj.tp == space.tp_str:
        return space.newbool(w_obj.is_really_valid_number(space))
    return space.w_False


@wrap(['space', W_Root], error=False)
def is_object(space, w_obj):
    """ Finds whether a variable is an object"""
    return space.wrap(space.is_object(w_obj))


@wrap(['space', W_Root], error=False)
def is_resource(space, w_obj):
    """ Finds whether a variable is a resource"""
    return space.wrap(space.is_resource(w_obj))


@wrap(['space', W_Root])
def is_scalar(space, w_obj):
    """ Finds whether a variable is a scalar"""
    return space.wrap(w_obj.tp in (space.tp_int, space.tp_float,
                                   space.tp_str, space.tp_bool))


@wrap(['space', W_Root], error=False)
def is_string(space, w_obj):
    """ Find whether the type of a variable is string"""
    return space.wrap(w_obj.tp == space.tp_str)


def _print_r(space, w_x, indent, recursion, builder):
    if w_x.tp == space.tp_array:
        if w_x in recursion:
            builder.append('Array\n *RECURSION*')
            return
        recursion[w_x] = None
        builder.append('Array\n%s(' % indent)
        subindent = indent + '        '
        with space.iter(w_x) as w_iter:
            while not w_iter.done():
                w_key, w_value = w_iter.next_item(space)
                if w_key.tp == space.tp_int:
                    key = space.int_w(w_key)
                    s = '\n%s    [%d] => ' % (indent, key)
                else:
                    key = space.str_w(w_key)
                    s = '\n%s    [%s] => ' % (indent, key)
                builder.append(s)
                _print_r(space, w_value.deref(), subindent, recursion, builder)
        builder.append('\n%s)\n' % indent)
        del recursion[w_x]
    elif isinstance(w_x, W_InstanceObject):
        builder.append('%s Object\n' % w_x.klass.name)
        if w_x in recursion:
            builder.append(' *RECURSION*')
            return
        recursion[w_x] = None
        builder.append('%s(' % indent)
        keyindent = indent + ' ' * 4
        subindent = indent + ' ' * 8
        dct_w = w_x.get_instance_attrs()
        for name, w_value in dct_w.iteritems():
            name, access = demangle_property(name)
            if access == '':
                key = '%s' % name
            elif access == '*':
                key = '%s:protected' % name
            else:
                key = '%s:%s:private' % (name, access)
            builder.append('\n%s[%s] => ' % (keyindent, key))
            _print_r(space, w_value.deref(), subindent, recursion, builder)
        builder.append('\n%s)\n' % indent)
        del recursion[w_x]
    else:
        builder.append(space.str_w(w_x))


@wrap(['space', W_Root, Optional(bool)])
def print_r(space, w_expression, returns=False):
    """ Prints human-readable information about a variable"""
    builder = StringBuilder()
    _print_r(space, w_expression, '', {}, builder)
    result = builder.build()
    if returns:
        return space.newstr(result)
    else:
        space.ec.interpreter.writestr(result)
        return space.w_True


@wrap(['space', W_Root])
def serialize(space, w_obj):
    """ Generates a storable representation of a value"""
    return space.newstr(space.serialize(w_obj))


@wrap(['space', W_Root])
def strval(space, w_obj):
    """ Get string value of a variable"""
    return space.wrap(w_obj.str(space, quiet=False))


@wrap(['space', StringArg(None)], error=False)
def unserialize(space, data):
    """ Creates a PHP value from a stored representation"""
    return serialize_mod.unserialize(space, data)


@wrap(['interp', 'args_w'])
def var_dump(interp, args_w):
    """ Dumps information about a variable"""
    for w_x in args_w:
        if w_x:
            w_x = w_x.copy()    # xxx ideally we should ask and get a
                                # unique object, but that's not supported
                                # so far
            interp.writestr(w_x.var_dump(
                interp.space, indent='', recursion={}))
    return interp.space.w_Null


@wrap(['space', W_Root, Optional(BoolArg(None))])
def var_export(space, w_obj, ret=False):
    """ Outputs or returns a parsable string representation of a variable"""
    from hippy.objects.instanceobject import W_InstanceObject
    from hippy.objects.arrayobject import W_ArrayObject

    if isinstance(w_obj, W_ArrayObject):
        suffix = 'array'
    elif isinstance(w_obj, W_InstanceObject):
        suffix = ')'
    else:
        suffix = ''
    res = w_obj.var_export(space, '', {}, suffix=suffix)
    if res:
        if ret:
            return space.newstr(res)
        space.ec.interpreter.writestr(res)
    return space.w_False


@wrap(['frame', 'interp', W_Root, Optional(StringArg(None))],
      name="_assert", error=False, aliases=['assert', ])
def _assert(frame, interp, w_check, desc=None):
    """ Checks if assertion is FALSE"""
    space = interp.space
    if w_check.tp == space.tp_str:
        source_orig = space.str_w(w_check)
        source = "<? return %s ?>" % source_orig
        bc = compile_php('<assert>', source, space)
        interp = space.ec.interpreter
        w_res = interp.run_local_include(bc, frame)
        if not w_res.is_true(space):
            space.ec.warn('assert(): Assertion "%s" failed' % source_orig)
            return space.w_Null
    if not w_check.is_true(space):
            space.ec.warn('assert(): Assertion failed')
            return space.w_Null
    return space.wrap(w_check.is_true(space))


def cli_get_process_title():
    """ Returns the current process title"""
    raise NotImplementedError()


def cli_set_process_title():
    """ Sets the process title"""
    raise NotImplementedError()


def dl():
    """ Loads a PHP extension at runtime"""
    raise NotImplementedError()


def gc_collect_cycles():
    """ Forces collection of any existing garbage cycles"""
    raise NotImplementedError()


def gc_disable():
    """ Deactivates the circular reference collector"""
    raise NotImplementedError()


def gc_enable():
    """ Activates the circular reference collector"""
    raise NotImplementedError()


def gc_enabled():
    """ Returns status of the circular reference collector"""
    raise NotImplementedError()


@wrap(['interp', StringArg(None)])
def get_cfg_var(interp, var):
    """ Gets the value of a PHP configuration option"""
    w_value = interp.config.get_ini_w(var)
    if w_value is None:
        return interp.space.w_False
    return w_value


@wrap(['space'])
def get_current_user(space):
    """ Gets the name of the owner of the current PHP script"""
    return space.newstr(os.getlogin())


@wrap(['interp', Optional(bool)])
def get_defined_constants(interp, categorize=False):
    from hippy.constants import get_constants_by_module
    if not categorize:
        od = OrderedDict()
        for name in (interp.space.prebuilt_constants +
                     interp.constant_names):
            od[name] = interp.lookup_constant(name)
        return interp.space.new_array_from_rdict(od)
    else:
        rdct_w = OrderedDict()
        for module, lst in get_constants_by_module(interp.space):
            inner_rdct_w = OrderedDict()
            for k, w_obj in lst:
                inner_rdct_w[k] = w_obj
            rdct_w[module] = interp.space.new_array_from_rdict(inner_rdct_w)
        inner_rdct_w = OrderedDict()
        for name in interp.constant_names:
            inner_rdct_w[name] = interp.lookup_constant(name)
        rdct_w['user'] = interp.space.new_array_from_rdict(inner_rdct_w)
        return interp.space.new_array_from_rdict(rdct_w)


def get_extension_funcs():
    """ Returns an array with the names of the functions of a module"""
    raise NotImplementedError()


@wrap(['space'])
def get_include_path(space):
    """ Gets the current include_path configuration option"""
    res = os.pathsep.join(space.ec.interpreter.include_path)
    return space.newstr(res)


@wrap(['interp'])
def get_included_files(interp):
    """ Returns an array with the names of included or required files"""
    files = interp.cached_files.keys()
    space = interp.space
    arr_list = []
    for f in files:
        arr_list.append(space.newstr(f))
    return space.new_array_from_list(arr_list)


def get_magic_quotes_gpc():
    """ Gets the current configuration setting of magic_quotes_gpc"""
    raise NotImplementedError()


def get_magic_quotes_runtime():
    """ Gets the current active configuration
    setting of magic_quotes_runtime"""
    raise NotImplementedError()


def get_required_files():
    """ Alias of get_included_files"""
    raise NotImplementedError()


@wrap(['space',  StringArg(None)])
def getenv(space, var):
    """ Gets the value of an environment variable"""
    e = os.environ.get(var)
    if e is None:
        return space.w_False
    return space.newstr(e)


def getlastmod():
    """ Gets time of last page modification"""
    raise NotImplementedError()


@wrap(['space'])
def getmygid(space):
    """ Get PHP script owner's GID"""
    res = os.getpid()
    return space.newint(res)


def getmyinode():
    """ Gets the inode of the current script"""
    raise NotImplementedError()


def getmypid():
    """ Gets PHP's process ID"""
    raise NotImplementedError()


def getmyuid():
    """ Gets PHP script owner's UID"""
    raise NotImplementedError()


def getopt():
    """ Gets options from the command line argument list"""
    raise NotImplementedError()


@wrap(['space', Optional(int)])
def getrusage(space, who=1):
    """ Gets the current resource usages"""
    pairs = [
        (space.newstr('ru_utime.tv_sec'), space.wrap(time.time())),
        (space.newstr('ru_utime.tv_usec'), space.wrap(0)),
        (space.newstr('ru_stime.tv_sec'), space.wrap(0)),
        (space.newstr('ru_stime.tv_usec'), space.wrap(0))
        ]
    return space.new_array_from_pairs(pairs)


def ini_alter():
    """ Alias of ini_set"""
    raise NotImplementedError()


def ini_get_all():
    """ Gets all configuration options"""
    raise NotImplementedError()


@wrap(['interp', StringArg(None)])
def ini_get(interp, vname):
    """ Gets the value of a configuration option"""
    w_value = interp.config.get_ini_w(vname)
    if w_value is None:
        return interp.space.w_False
    return interp.space.as_string(w_value)


def ini_restore():
    """ Restores the value of a configuration option"""
    raise NotImplementedError()


@wrap(['interp', StringArg(None), W_Root])
def ini_set(interp, key, w_value):
    """ Sets the value of a configuration option"""
    w_oldvalue = interp.config.get_ini_w(key)
    interp.config.set_ini_w(key, w_value)
    if w_oldvalue is None:
        return interp.space.w_Null
    return interp.space.as_string(w_oldvalue)


def magic_quotes_runtime():
    """ Alias of set_magic_quotes_runtime"""
    raise NotImplementedError()


def main():
    """ Dummy for main"""
    raise NotImplementedError()


@wrap(['interp',  Optional(bool)])
def memory_get_peak_usage(interp, real_usage=False):
    """ Returns the peak of memory allocated by PHP"""
    return interp.space.newint(0)


@wrap(['interp',  Optional(bool)])
def memory_get_usage(interp, real_usage=False):
    """ Returns the amount of memory allocated to PHP"""
    return interp.space.newint(0)


def php_ini_loaded_file():
    """ Retrieve a path to the loaded php.ini file"""
    raise NotImplementedError()


def php_ini_scanned_files():
    """ Return a list of .ini files parsed from the additional ini dir"""
    raise NotImplementedError()


def php_logo_guid():
    """ Gets the logo guid"""
    raise NotImplementedError()


@wrap(['space'])
def php_sapi_name(space):
    """ Returns the type of interface between web server and PHP"""
    return space.newstr('cli')


@wrap(['space', Optional(StringArg(None))])
def php_uname(space, mode="a"):
    """ Returns information about the operating system PHP is running on"""
    t = os.uname()
    return space.newstr(' '.join([t[0], t[1], t[2], t[3], t[4]]))


def phpcredits():
    """ Prints out the credits for PHP"""
    raise NotImplementedError()


@wrap(['interp', int])
def phpinfo(interp, arg):
    """ Outputs information about PHP's configuration"""
    if arg & get_const('standard', 'INFO_MODULES'):
        for ext in EXTENSIONS:
            interp.writestr(ext + "\n")
    return interp.space.w_True


@wrap(['interp',  Optional(str)])
def phpversion(interp, ext=None):
    """ Gets the current PHP version"""
    if ext:
        return interp.space.w_False
    return interp.config.get_ini_w('php_version')


@wrap(['space', StringArg(None)])
def putenv(space, envstr):
    """ Sets the value of an environment variable"""
    try:
        key, value = envstr.split("=")
    except ValueError:
        return space.w_True
    os.environ[key] = value
    return space.w_True


@wrap(['space'])
def restore_include_path(space):
    """ Restores the value of the include_path configuration option"""
    res = os.pathsep.join(space.ec.interpreter.include_path)
    return space.newstr(res)


@wrap(['space',  StringArg(None)])
def set_include_path(space, paths):
    """ Sets the include_path configuration option"""
    interp = space.ec.interpreter
    old = os.pathsep.join(interp.include_path)
    interp.include_path = []
    for p in paths.split(os.pathsep):
        interp.include_path.append(p)
    return space.newstr(old)


def set_magic_quotes_runtime():
    """ Sets the current active configuration
    setting of magic_quotes_runtime"""
    raise NotImplementedError()


@wrap([int])
def set_time_limit(arg):
    """ Limits the maximum execution time"""
    pass


@wrap(['space'])
def sys_get_temp_dir(space):
    """ Returns directory path used for temporary files"""
    return space.newstr('/tmp')


def canonicalize_version(ver):
    res = ""
    last_char = None
    for l in ver:
        if l.isdigit():
            if last_char and last_char.isalpha():
                res += "."
            res += l
        elif l in ("-", "_", "+"):
            res += "."
        elif l == ".":
            res += l
        else:
            if not res.endswith(".") and (last_char and last_char.isdigit()):
                res += "." + l
            else:
                res += l
        last_char = l
    return res


special_forms = {
    "dev": 0,
    "alpha": 1,
    "a": 1,
    "beta": 2,
    "b": 2,
    "RC": 3,
    "rc": 3,
    "#": 4,
    "#N#": 4,
    "pl": 5,
    "p": 5,
    "": 0,
}


def _compare_special_forms(ver1, ver2):
    f1, f2 = -1, -1
    for k, v in special_forms.items():
        if k == ver1:
            f1 = v
        if k == ver2:
            f2 = v
    if f1 < f2:
        return -1
    elif f1 == f2:
        return 0
    return 1


def _version_compare(ver1, ver2):

    lver1 = canonicalize_version(ver1).split(".")
    lver2 = canonicalize_version(ver2).split(".")

    max_len = max(len(lver1), len(lver2))
    compare = 0

    if len(lver1) > len(lver2):
        lver2 += [''] * (max_len - len(lver2))
    else:
        lver1 += [''] * (max_len - len(lver1))

    for i in range(max_len):
        l, r = lver1[i], lver2[i]

        if l == "":
            if r.isdigit():
                return -1
            else:
                return _version_compare("#N#", r)
        if r == "":
            if l.isdigit():
                return 1
            else:
                return _version_compare(l, "#N#")

        if l.isdigit() and r.isdigit():
            i_l = int(l)
            i_r = int(r)
            if i_l < i_r:
                compare = -1
            elif i_l == i_r:
                compare = 0
            else:
                compare = 1
        elif not l.isdigit() and not r.isdigit():
            compare = _compare_special_forms(l, r)
        else:
            if l.isdigit():
                compare = _compare_special_forms("#N#", r)
            else:
                compare = _compare_special_forms(l, "#N#")
    return compare


@wrap(['space', StringArg(None), StringArg(None), Optional(StringArg(None))])
def version_compare(space,  ver1, ver2, operator=None):
    """ Compares two "PHP" "standardized" version number strings"""
    ver1 = canonicalize_version(ver1)
    ver2 = canonicalize_version(ver2)

    compare = _version_compare(ver1, ver2)

    if operator is None:
        return space.newint(compare)

    if operator in ("==", "=", "eq"):
        return space.newbool(compare == 0)
    if operator in ("!=", "ne", "<>"):
        return space.newbool(compare != 0)
    if operator in (">", "gt"):
        return space.newbool(compare == 1)
    if operator in ("<", "lt"):
        return space.newbool(compare == -1)
    if operator in (">=", "ge"):
        return space.newbool(compare != -1)
    if operator in ("<=", "le"):
        return space.newbool(compare != 1)
    return space.w_Null


def zend_logo_guid():
    """ Gets the Zend guid"""
    raise NotImplementedError()


def zend_thread_id():
    """ Returns a unique identifier for the current thread"""
    raise NotImplementedError()


@wrap(['interp'])
def zend_version(interp):
    """ Gets the version of the current Zend engine"""
    return interp.config.get_ini_w('zend_version')
