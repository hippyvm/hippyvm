"""
This module implements the machinery for creating builtin functions.

To create one, use the `@wrap` decorator on a RPython function. It takes a
list of unwrapper specifications, one for each RPython argument. The
unwrappers translate wrapped PHP objects into unwrapped RPython arguments for
the function.

Available unwrappers include:

* `int`, `bool`, `float`, `str`: cast the PHP object into the corresponding
  low-level type, following PHP typecasting rules.
* `W_Root`: pass the wrapped object through.
* `"space"`: give the RPython function access to the ObjSpace. Doesn't consume
  a PHP argument.
* `"args_w"`: consumes all remaining PHP arguments. The RPython function
  receives a tuple of wrapped objects.
* 'reference': pass the PHP argument by reference. The RPython function
  receives a wrapped object.

Additionally, there's a parametric unwrapper, `Optional()` to specify optional
PHP arguments. Its argument is the actual unwrapper for the PHP argument. When
the builtin is called without this argument, its RPython implementation is
also called without it. Therefore, the implementation must specify a default
value.

Examples
--------

The following declaration creates a builtin function with signature
incr(int $a[, int $increment = 0]):

>>> @wrap(int, Optional(int))
... def incr(space, a, increment=1):
...     return space.newint(a + increment)

A PHP call like `incr("123", 2)` will generate `incr(space, 123, 2)` at the
RPython level while `incr(0)` will generate `incr(space, 0)`.

"""
import py
import time
import math
import os
import inspect
from collections import OrderedDict
from rpython.rlib import jit
from rpython.rlib.objectmodel import newlist_hint
from hippy.error import (InterpreterError, ExplicitExitException,
                         ConvertError, FatalError, PHPException,
                         VisibilityError)
from hippy.objects.base import W_Root
from hippy.objects.reference import W_Reference
from hippy.objects.boolobject import w_False
from hippy.objects.instanceobject import W_InstanceObject
from hippy.objects.strobject import W_StringObject
from hippy.function import AbstractFunction
from hippy import config


dummy = object()


def _tuple_literal(names):
    if len(names) >= 2:
        return '(%s)' % ', '.join(names)
    elif len(names) == 1:
        return '(%s,)' % names[0]
    else:
        return '()'


def handle_as_warning(interp, message):
    raise WrongParameters(message)


def handle_as_exception(interp, message):
    from hippy.builtin_klass import k_Exception
    raise PHPException(k_Exception.call_args(
        interp, [interp.space.wrap(message)]))


def handle_as_void(interp, message):
    raise ExitSilently()


def argument_not(interp, _type, funcname, arg_num, given_tp, handler):
    message = "%s() expects parameter %d to be %s, %s given" % \
              (funcname, arg_num, _type, interp.space.get_type_name(given_tp))

    handler(interp, message)


def _bad_number_args(interp, funcname, text, expected_nb_args,
                     got_nb_args, handler):
    if expected_nb_args > 1 or expected_nb_args == 0:
        plural = "s"
    else:
        plural = ""

    handler(interp, "%s() expects %s %d parameter%s, %d given" % (
        funcname, text, expected_nb_args, plural, got_nb_args)
    )


def arguments_exactly(interp, funcname, expected_nb_args,
                      got_nb_args, handler):
    return _bad_number_args(
        interp, funcname, "exactly", expected_nb_args, got_nb_args, handler
    )


def arguments_at_least(interp, funcname, expected_nb_args,
                       got_nb_args, handler):
    return _bad_number_args(
        interp, funcname, "at least",
        expected_nb_args, got_nb_args, handler
    )


def arguments_at_most(interp, funcname, expected_nb_args,
                      got_nb_args, handler):
    return _bad_number_args(
        interp, funcname, "at most",
        expected_nb_args, got_nb_args, handler
    )


class ExitFunctionWithError(Exception):
    def __init__(self, msg, return_value=None):
        self.msg = msg
        self.return_value = return_value

    def handle(self, interp, fname):
        interp.warn(fname + "(): " + self.msg)

class WrongParameters(ExitFunctionWithError):
    def handle(self, interp, fname):
        interp.warn(self.msg)

class ExitFunctionWithHippyError(ExitFunctionWithError):
    def handle(self, interp, fname):
        interp.hippy_warn(fname + "(): " + self.msg)

class ExitSilently(ExitFunctionWithError):
    msg = ''

    def __init__(self, return_value=None):
        self.return_value = return_value

    def handle(self, interp, fname):
        pass

class Unwrapper(object):
    is_optional = False
    dummy = False

    def line_for_arg(self, i, input_i):
        raise NotImplementedError

    def register_extra_name(self, d, i):
        pass


class ArgsUnwrapper(Unwrapper):
    stacksize = None

    def line_for_arg(self, i, input_i):
        return ['    arg%d = args_w[%d:]' % (i, input_i,)]


class ThisClassUnwrapper(Unwrapper):
    stacksize = 0

    def line_for_arg(self, i, input_i):
        return ['    arg%d = thisclass' % i]


class SpaceUnwrapper(Unwrapper):
    stacksize = 0

    def line_for_arg(self, i, input_i):
        return ['    arg%d = space' % i]


class InterpreterUnwrapper(Unwrapper):
    stacksize = 0

    def line_for_arg(self, i, input_i):
        return ['    arg%d = interp' % i]


class FrameUnwrapper(Unwrapper):
    stacksize = 0

    def line_for_arg(self, i, input_i):
        return ['    arg%d = interp.topframeref()' % i]


class RegularUnwrapper(Unwrapper):
    stacksize = 1

    def line_for_arg(self, i, input_i):
        lines = ['    w_arg = args_w[%d].deref_unique()' % (input_i,)]
        lines += ['    arg%d = w_arg' % (i,)]
        return lines


class ValueUnwrapper(RegularUnwrapper):
    is_byref = False


class RefUnwrapper(RegularUnwrapper):
    is_byref = True

    def line_for_arg(self, i, input_i):
        lines = ['    w_arg = args_w[%d]' % (input_i,)]
        lines += ['    arg%d = check_reference(space, w_arg, fname)' % (i,)]
        return lines


class ParametricUnwrapper(RegularUnwrapper):
    def __init__(self, base):
        self.base = as_unwrapper(base)

    @property
    def is_byref(self):
        return self.base.is_byref

    def register_extra_name(self, d, i):
        self.base.register_extra_name(d, i)


class Optional(ParametricUnwrapper):
    """
    Optional argument to a builtin function.

    Example
    -------

    The following declaration creates a builtin function with signature
    incr(int $a[, int $increment = 0]).

    >>> @wrap(int, Optional(int))
    ... def incr(space, a, increment=1):
    ...     return space.newint(a + increment)
    """
    is_optional = True

    def line_for_arg(self, i, input_i):
        lines = ['    if nb_args > %d:' % (input_i,)]
        base_lines = self.base.line_for_arg(i, input_i)
        lines.extend([' ' * 4 + line for line in base_lines])
        return lines

class Nullable(ParametricUnwrapper):
    def line_for_arg(self, i, input_i):
        lines = ['    w_arg = args_w[%d].deref_temp()' % (input_i,)]
        lines += ['    if w_arg.tp == space.tp_null:']
        lines += ['        arg%d = None' % i]
        lines += ['    else:']
        base_lines = self.base.line_for_arg(i, input_i)
        lines.extend([' ' * 4 + line for line in base_lines])
        return lines


class ObjectUnwrapper(RegularUnwrapper):
    is_byref = False

    def __init__(self, cls, error_value=dummy):
        self.cls = cls
        self.error_value = error_value

    def line_for_arg(self, i, input_i):
        lines = ['    arg%d = args_w[%d].deref_unique()' % (i, input_i,),
                 '    if not isinstance(arg%d, CLS%d):' % (i, i),
                 '        raise argument_not(interp, "object", fname, %d, arg%d.tp, error_handler)'
                 % (input_i + 1, i)]
        return lines

    def register_extra_name(self, d, i):
        assert 'CLS%d' % i not in d
        d['CLS%d' % i] = self.cls


class InstanceUnwrapper(ObjectUnwrapper):

    def __init__(self, cls, phpclassname, error_value=None, null=True):
        self.cls = cls
        self.phpclassname = phpclassname
        self.error_value = error_value
        self.null = null

    def line_for_arg(self, i, input_i):
        lines = ['    arg%d = args_w[%d].deref_unique()' % (i, input_i,)]
        if self.null:
            lines += ['    if arg%d.tp == space.tp_null:' % (i,),
                      '        arg%d = None' % (i,),
                      '    elif not isinstance(arg%d, CLS%d):' % (i, i),
                      '        raise argument_not(interp, "%s", fname, %d, arg%d.tp, error_handler)'
                      % (self.phpclassname, input_i + 1, i)]
        else:
            lines += ['    if not isinstance(arg%d, CLS%d):' % (i, i),
                      '        raise argument_not(interp, "%s", fname, %d, arg%d.tp, error_handler)'
                      % (self.phpclassname, input_i + 1, i)]
        return lines


class ThisUnwrapper(ObjectUnwrapper):
    stacksize = 0

    def line_for_arg(self, i, input_i):

        lines = ['    arg%d = w_this' % (i,),
                 '    assert isinstance(arg%d, CLS%d)' % (i, i)]
        return lines


class ArrayArg(ValueUnwrapper):
    def __init__(self, error_value=dummy):
        self.error_value = error_value

    def line_for_arg(self, i, input_i):
        lines = ['    arg%d = args_w[%d].deref_unique()' % (i, input_i)]
        lines += ['    if arg%d.tp != space.tp_array:' % (i)]
        lines += ['        warn_not_array(space, fname, %d, arg%d.tp)'
                  % (input_i + 1, i)]
        return lines


class UniqueArray(ValueUnwrapper):
    is_byref = True

    def __init__(self, error_value=dummy, accept_instance=True):
        self.error_value = error_value
        self.accept_instance = accept_instance

    def line_for_arg(self, i, input_i):
        lines = ['    r = args_w[%d]' % (input_i,)]
        lines += ['    r = check_reference(space, r, fname)']
        lines += ['    arg%d = r.deref_unique()' % (i,)]
        lines += ['    if not isinstance(arg%d, W_ArrayObject):' % (i,)]
        lines += ['        if %s and isinstance(arg%d, W_InstanceObject):'
                  % (self.accept_instance, i,)]
        lines += ['            arg%d = arg%d.get_rdict_array(space)' % (i, i)]
        lines += ['        else:']
        lines += ['            warn_not_array(space, fname, %d, arg%d.tp)'
                  % (input_i + 1, i)]
        return lines


class FileResourceArg(ValueUnwrapper):
    def __init__(self, error_value=dummy):
        self.error_value = error_value

    def line_for_arg(self, i, input_i):
        lines = ['    arg%d = args_w[%d].deref_unique()' % (i, input_i)]
        lines += ['    if arg%d.tp != space.tp_file_res and arg%d.tp != space.tp_bool:' % (i, i)]
        lines += ['        warn_not_file_resource(space, fname, %d, arg%d.tp)'
                  % (input_i + 1, i)]
        return lines


class Resource(ValueUnwrapper):
    def __init__(self, resource_class, check_valid):
        self.resource_class = resource_class
        self.res_name = resource_class.resource_name
        self.check_valid = check_valid

    def line_for_arg(self, i, input_i):
        lines = [
            '    w_arg = args_w[%d].deref_unique()' % (input_i,),
            '    if not space.is_resource(w_arg):',
            '        warn_not_resource(space, fname, %d, space.int_w(w_arg)'
            ', w_arg.tp)' % input_i,
            '    if not isinstance(w_arg, ResourceClass%d):' % i,
            '        warn_not_valid_resource(space, fname, %d, "%s")' % (
                input_i + 1, self.res_name),
        ]
        if self.check_valid:
            lines += [
                '    if not w_arg.is_valid():',
                '        warn_not_valid_resource(space, fname, %d, "%s")' % (
                    input_i + 1, self.res_name),
            ]

        lines.append('    arg%d = w_arg' % i)
        return lines

    def register_extra_name(self, d, i):
        assert 'ResourceClass%d' % i not in d
        d['ResourceClass%d' % i] = self.resource_class


class StreamContextArg(ValueUnwrapper):
    def __init__(self, error_value=dummy):
        self.error_value = error_value

    def line_for_arg(self, i, input_i):
        lines = ['    w_arg = args_w[%d].deref_unique()' % input_i]
        lines += ['    if space.is_resource(w_arg):']
        lines += ['        if w_arg.tp != space.tp_stream_context:']
        lines += ['            interp.warn("%s(): supplied resource is not a valid Stream-Context resource" % fname)']
        lines += ['            arg%d = None' % i]
        lines += ['        else:']
        lines += ['            arg%d = w_arg' % i]
        lines += ['    else:']
        lines += ['        raise warn_not_stream_context(space, fname'
                  ', %d, space.int_w(w_arg), w_arg.tp)' % (input_i + 1)]
        return lines


class FilenameArg(ValueUnwrapper):
    def __init__(self, error_value=dummy, expect="a valid path"):
        self.error_value = error_value
        self.expect = expect

    def line_for_arg(self, i, input_i):
        lines = ['    w_arg = args_w[%d].deref_unique()' % input_i]
        lines += ['    if w_arg.tp == space.tp_dir_res or w_arg.tp == space.tp_file_res or w_arg.tp == space.tp_array:']
        lines += ['        raise argument_not(interp, "%s", fname, %d, w_arg.tp, error_handler)'
                  % (self.expect, input_i + 1)]
        lines += ['    arg = w_arg.maybe_str(space)']
        lines += ['    if arg is None:']
        lines += ['        raise argument_not(interp, "%s", fname, %d, w_arg.tp, error_handler)'
                  % (self.expect, input_i + 1)]
        lines += ['    arg%d = arg' % i]
        return lines


class LongArg(ValueUnwrapper):
    def __init__(self, error_value=dummy):
        self.error_value = error_value

    def line_for_arg(self, i, input_i):
        lines = ['    w_arg = args_w[%d].deref_unique()' % input_i]
        lines += ['    try:']
        lines += ['        arg%d = w_arg.as_int_arg(space)' % i]
        lines += ['    except ConvertError:']
        lines += ['        raise argument_not(interp, "long", fname, %d, w_arg.tp, error_handler)'
                  % (input_i + 1)]
        return lines


class DoubleArg(ValueUnwrapper):
    def __init__(self, error_value=dummy):
        self.error_value = error_value

    def line_for_arg(self, i, input_i):
        lines = ['    w_arg = args_w[%d].deref_unique()' % input_i]
        lines += ['    try:']
        lines += ['        w_long = space.overflow_convert(w_arg)']
        lines += ['    except TypeError:']
        lines += ['        raise argument_not(interp, "double", fname, %d, w_arg.tp, error_handler)'
                    % (input_i + 1,)]
        lines += ['    arg%d = space.float_w(w_long)' % i]
        return lines


class BoolArg(ValueUnwrapper):
    def __init__(self, error_value=dummy):
        self.error_value = error_value

    def line_for_arg(self, i, input_i):
        lines = ['    w_arg = args_w[%d].deref_unique()' % input_i]
        lines += ['    if w_arg.tp == space.tp_object or w_arg.tp == space.tp_array or w_arg.tp == space.tp_file_res or w_arg.tp == space.tp_dir_res:']
        lines += ['        raise argument_not(interp, "boolean", fname, %d, w_arg.tp, error_handler)'
                  % (input_i + 1,)]
        lines += ['    arg%d = space.is_true(w_arg)' % i]
        return lines


class CallbackUnwrapper(ValueUnwrapper):

    def __init__(self, error_value=dummy):
        self.error_value = error_value

    def line_for_arg(self, i, input_i):
        return ['    w_arg = args_w[%d].deref_unique()' % input_i,
                '    w_callback = space.get_callback(fname, %d, w_arg)' % (input_i + 1),
                '    if w_callback is None:',
                '        raise ExitSilently()',
                '    arg%d = w_callback' % i,
                ]


class StringArg(ValueUnwrapper):
    def __init__(self, error_value=dummy):
        self.error_value = error_value

    def line_for_arg(self, i, input_i):
        lines = ['    w_arg = args_w[%d].deref_unique()' % input_i]
        lines += ['    if w_arg.tp == space.tp_dir_res or w_arg.tp == space.tp_file_res or w_arg.tp == space.tp_array:']
        lines += ['        raise argument_not(interp, "string", fname, %d, w_arg.tp, error_handler)'
                  % (input_i + 1,)]
        lines += ['    if w_arg.tp == space.tp_object:']
        lines += ['        w_arg = w_arg.as_string(space, quiet=True)']
        lines += ['        if w_arg is None:']
        lines += ['            raise argument_not(interp, "string", fname, %d, space.tp_object, error_handler)'
                  % (input_i + 1,)]
        lines += ['    arg%d = space.str_w(w_arg)' % i]
        return lines


class CharArg(ValueUnwrapper):
    def __init__(self):
        pass

    def line_for_arg(self, i, input_i):
        return ['    w_arg = args_w[%d].deref_unique()' % input_i,
                '    arg%d = None' % i,
                '    if w_arg.tp == space.tp_int:',
                '        val = space.int_w(w_arg)',
                '        if val >= 0 and val <= 256:',
                '            arg%d = chr(val)' % i,
                '        elif val >= -128 and val < 0:',
                '            arg%d = chr(val + 256)' % i,
                '        else:',
                '            w_arg = space.as_string(w_arg)',
                '    if w_arg.tp == space.tp_str:',
                '        arg%d = space.str_w(w_arg)' % i,
                '    elif arg%d is None:' % i,
                '        raise ExitSilently(space.w_False)']


class NumArgsUnwrapper(Unwrapper):
    stacksize = 0
    dummy = True

    def line_for_arg(self, i, input_i):
        return ['    arg%d = len(args_w)' % i]


UNWRAPPERS = {}

def as_unwrapper(unwrapper):
    if not UNWRAPPERS:
        UNWRAPPERS.update({
            'args_w': ArgsUnwrapper(),
            'space': SpaceUnwrapper(),
            'frame': FrameUnwrapper(),
            'interp': InterpreterUnwrapper(),
            int: LongArg(),
            bool: BoolArg(),
            float: DoubleArg(),
            str: StringArg(),
            'char': CharArg(),
            W_Root: ValueUnwrapper(),
            'this': ThisUnwrapper(W_InstanceObject),
            'thisclass': ThisClassUnwrapper(),
            'callback': CallbackUnwrapper(),
            'reference': RefUnwrapper(),
            'num_args': NumArgsUnwrapper(),
            'object': ObjectUnwrapper(W_InstanceObject),
            'unique_array': UniqueArray(),
        })

    if isinstance(unwrapper, Unwrapper):
        return unwrapper
    else:
        return UNWRAPPERS[unwrapper]


class BuiltinSignature(object):
    def __init__(self, unwrappers):
        self.unwrappers = map(as_unwrapper, unwrappers)
        self.references = [uw.is_byref for uw in self.unwrappers
                           if isinstance(uw, RegularUnwrapper)]
        self.has_references = any(self.references)
        min_args = 0
        php_indices = []
        curr_index = 0
        has_optional = False
        for uw in self.unwrappers:
            if uw.is_optional:
                has_optional = True
            if not uw.dummy:
                php_indices.append(curr_index)
                if uw.stacksize is None:
                    if has_optional:
                        raise ValueError(
                            "Cannot combine optional arguments and 'args_w'")
                    curr_index = None
                    continue
                if curr_index is None:
                    raise ValueError("'args_w' should come last.")
                if not uw.is_optional:
                    min_args += uw.stacksize
                curr_index += uw.stacksize
            else:
                php_indices.append(curr_index)
        self.min_args = min_args
        self.max_args = curr_index
        self.php_indices = php_indices

    def __iter__(self):
        return iter(self.unwrappers)

    def __len__(self):
        return len(self.unwrappers)


class BuiltinFunctionBuilder(object):
    def __init__(self, signature, functocall, funcname=None):
        self.signature = BuiltinSignature(signature)
        self.functocall = functocall
        self.funcname = funcname or functocall.func_name
        self.internal_funcname = "php_%s" % self.funcname.replace('::', '__')
        self.defaults = inspect.getargspec(functocall)[3]

    @property
    def default_indices(self):
        args, _, _, defaults = inspect.getargspec(self.functocall)
        return range(len(args) - len(defaults), len(args))

    def make_source(self, check_num_args=True):
        sig = self.signature
        lines = []
        if self.defaults:
            indices = self.default_indices
            args_with_defaults = ', '.join('arg%s' % i for i in indices)
            default_vars = ', '.join('default%s' % i for i in indices)
            lines.append('    %s = %s' % (args_with_defaults, default_vars))
        for i, (unwrapper, input_i) in enumerate(zip(sig, sig.php_indices)):
            lines.extend(unwrapper.line_for_arg(i, input_i))
        lines = self.header(check_num_args) + lines + self.footer()
        return '\n'.join(lines)

    def build(self, error_handler, check_num_args=True):
        from hippy.objects.resources.file_resource import W_FileResource
        from hippy.objects.resources.dir_resource import W_DirResource
        from hippy.objects.arrayobject import W_ArrayObject

        source = self.make_source(check_num_args)
        d = {
            'fname': self.funcname,
            'argument_not': argument_not,
            'arguments_exactly': arguments_exactly,
            'error_handler': error_handler,

            'warn_exactly': warn_exactly,
            'warn_not_array': warn_not_array,

            'warn_not_file_resource': warn_not_file_resource,
            'warn_not_valid_file_resource': warn_not_valid_file_resource,

            'warn_not_resource': warn_not_resource,
            'warn_not_valid_resource': warn_not_valid_resource,

            'warn_not_stream_context': warn_not_stream_context,
            'warn_not_valid_stream_context': warn_not_valid_stream_context,

            'warn_not_mysql_link': warn_not_mysql_link,
            'warn_not_valid_mysql_link': warn_not_valid_mysql_link,

            'warn_not_mysql_result': warn_not_mysql_result,
            'warn_not_valid_mysql_result': warn_not_valid_mysql_result,

            'warn_not': warn_not,
            'warn_could_not_convert_to_str': warn_could_not_convert_to_str,
            'warn_at_least': warn_at_least,
            'warn_at_most': warn_at_most,
            'warn_not_mcrypt_res': warn_not_mcrypt_res,
            'check_reference': check_reference,
            'unroll_safe': jit.unroll_safe,
            'W_FileResource': W_FileResource,
            'W_DirResource': W_DirResource,
            'W_ArrayObject': W_ArrayObject,
            'W_InstanceObject': W_InstanceObject,
            'FatalError': FatalError,
            'ConvertError': ConvertError,
            'ExitSilently': ExitSilently,
        }

        from hippy.hippyoption import is_optional_extension_enabled
        if is_optional_extension_enabled("mysql"):
            from ext_module.mysql.link_resource import W_MysqlLinkResource
            from ext_module.mysql.result_resource import W_MysqlResultResource
            d['W_MysqlLinkResource'] = W_MysqlLinkResource
            d['W_MysqlResultResource'] = W_MysqlResultResource

        if self.defaults:
            for i, default_value in zip(self.default_indices, self.defaults):
                d['default%s' % i] = default_value
        for i, unwrapper in enumerate(self.signature):
            unwrapper.register_extra_name(d, i)
        try:
            exec py.code.Source(source).compile() in d
        except:
            print source
            raise
        return d[self.internal_funcname]

    def header(self, check_num_args=True):
        lines = []
        lines.append("@unroll_safe")
        lines.append("def %s(interp, args_w, w_this, thisclass):" % (
            self.internal_funcname,))
        lines.append("    nb_args = len(args_w)")
        lines.append("    space = interp.space")
        if not check_num_args:
            return lines
        min_args = self.signature.min_args
        max_args = self.signature.max_args
        if max_args == min_args:
            lines.append("    if nb_args != %d:" % (min_args,))
            lines.append("        arguments_exactly(interp, fname, %d, nb_args, error_handler)"
                         % (min_args,))
            lines.append("    nb_args = %d  # constant below" % (min_args,))
        else:
            lines.append("    if nb_args < %d:" % (min_args,))
            lines.append("        warn_at_least(space, fname, %d, nb_args)"
                         % (min_args,))
            if max_args is not None:
                lines.append("    if nb_args > %d:" % (max_args,))
                lines.append("        warn_at_most(space, fname, %d, nb_args)"
                             % (max_args))
        return lines

    def footer(self):
        allargs = ['arg%d' % i for i in range(len(self.signature))]
        return ['    return %s\n' % _tuple_literal(allargs)]


def warn_bad_nb_args(space, funcname, text, expected_nb_args, got_nb_args):

    if expected_nb_args > 1 or expected_nb_args == 0:
        plural = "s"
    else:
        plural = ""
    raise WrongParameters("%s() expects %s %d parameter%s, %d given"
                  % (funcname, text, expected_nb_args, plural, got_nb_args))
    return space.w_Null


def warn_exactly(space, funcname, expected_nb_args, got_nb_args):
    return warn_bad_nb_args(space, funcname, "exactly",
                            expected_nb_args, got_nb_args)


def warn_at_least(space, funcname, expected_nb_args, got_nb_args):
    return warn_bad_nb_args(space, funcname, "at least",
                            expected_nb_args, got_nb_args)


def warn_at_most(space, funcname, expected_nb_args, got_nb_args):
    return warn_bad_nb_args(space, funcname, "at most",
                            expected_nb_args, got_nb_args)


def warn_not_array(space, funcname, arg_num, given_tp):
    if funcname == 'each':   # bah
        raise WrongParameters("Variable passed to each() is not "
                                    "an array or object")
    given = space.get_type_name(given_tp)
    if given == "NULL":
        given = "null"
    raise WrongParameters("%s() expects parameter %d to be array, "
                                "%s given" % (funcname, arg_num, given))


def warn_not_file_resource(space, funcname, arg_num, given_tp):
    raise WrongParameters("%s() expects parameter %d to be resource, "
                                "%s given" % (
                                    funcname, arg_num,
                                    space.get_type_name(given_tp).lower()))


def warn_not_valid_file_resource(space, funcname, res_id):
    raise WrongParameters("%s(): %d is not a valid stream resource"
                  % (funcname, res_id))


def warn_not_resource(space, funcname, arg_num, res_id, given_tp):
    raise WrongParameters("%s() expects parameter %d to be resource, "
                                "%s given" % (
                                    funcname, arg_num,
                                    space.get_type_name(given_tp).lower()))


def warn_not_valid_resource(space, funcname, res_id, resname):
    raise WrongParameters("%s(): %d is not a valid %s resource"
                  % (funcname, res_id, resname), w_False)


def warn_not(space, _type, funcname, arg_num, given_tp):
    raise WrongParameters("%s() expects parameter %d to be %s, %s given" %
                  (funcname, arg_num, _type, space.get_type_name(given_tp)))


def warn_not_stream_context(space, funcname, arg_num, res_id, given_tp):
    if given_tp in [space.tp_file_res, space.tp_dir_res]:
        raise WrongParameters("%s(): supplied resource is not "
                      "a valid Stream-Context resource" % funcname)
    else:
        raise WrongParameters("%s() expects parameter %d to be resource, %s given" %
                      (funcname, arg_num,
                       space.get_type_name(given_tp).lower()))


def warn_not_valid_stream_context(space, funcname):
    raise WrongParameters("%s(): supplied resource is not a valid Stream-Context resource" % funcname)


def warn_not_mysql_link(space, funcname, arg_num, res_id, given_tp):
    raise WrongParameters("%s() expects parameter %d to be resource, %s given" %
                  (funcname, arg_num,
                   space.get_type_name(given_tp).lower()), w_False)


def warn_not_valid_mysql_link(space, funcname, arg_num, res_id, given_tp):
    raise WrongParameters("%s(): %d is not a valid MySQL-Link resource" %
                          (funcname, res_id), w_False)


def warn_not_mysql_result(space, funcname, arg_num, res_id, given_tp):
    raise WrongParameters("%s() expects parameter %d to be resource, %s given" %
                  (funcname, arg_num,
                   space.get_type_name(given_tp).lower()), w_False)


def warn_not_valid_mysql_result(space, funcname, arg_num, res_id, given_tp):
    raise WrongParameters("%s(): %d is not a valid MySQL result resource" %
                          (funcname, res_id), w_False)


def warn_not_mcrypt_res(space, funcname, arg_num, res_id, given_tp):
    raise WrongParameters("%s(): %d is not a valid MCrypt resource" %
                          (funcname, res_id), w_False)


def warn_could_not_convert_to_str(space, w_obj):
    klass = w_obj.getclass(space).name
    space.ec.catchable_fatal("Object of class %s could not be "
                             "converted to int" % klass)


def check_reference(space, w_ref, fname):
    if not isinstance(w_ref, W_Reference):
        space.ec.hippy_warn("The built-in function %s() takes an argument "
                            "by reference, but didn't get a reference in "
                            "the indirect call" % (fname,))
        w_ref = W_Reference(w_ref)
    return w_ref


class ArgumentError(InterpreterError):
    """ An exception raised when function is called with a wrong
    number or type of args
    """


class BuiltinFunction(AbstractFunction):
    _immutable_fields_ = ['runner']

    def __init__(self, funcname, runner):
        self.name = funcname.split('::')[-1]
        self._fullname = funcname
        self.runner = runner

    def __repr__(self):
        return "BuiltinFunction(%s)" % (self.name,)

    def needs_ref(self, i):
        return False

    def call_args(self, interp, args_w, w_this=None, thisclass=None,
                  closureargs=None):
        return self.runner(interp, args_w, w_this, thisclass)

    def get_fullname(self):
        return self._fullname

    def get_signature(self):
        return None


class BuiltinFunctionWithReferences(BuiltinFunction):
    _immutable_fields_ = ['references', 'runner']

    def __init__(self, signature, funcname, runner):
        BuiltinFunction.__init__(self, funcname, runner)
        self.references = signature.references

    def needs_ref(self, i):
        if i >= len(self.references):
            return False
        return self.references[i]


BUILTIN_FUNCTIONS = OrderedDict()


def register_builtin_function(name, func):
    if name in BUILTIN_FUNCTIONS:
        raise ValueError("Duplicate definition for builtin %s()" % name)
    BUILTIN_FUNCTIONS[name] = func


def make_runner(signature, ll_func, fname, error, error_handler,
                check_num_args=True):
    builder = BuiltinFunctionBuilder(signature, ll_func, fname)
    parse_args = builder.build(error_handler, check_num_args)

    def call_args(interp, args_w, w_this=None, thisclass=None):
        space = interp.space
        try:
            ll_args = parse_args(interp, args_w, w_this, thisclass)
            res = ll_func(*ll_args)
        except ExitFunctionWithError as e:
            e.handle(interp, fname)
            if e.return_value is not None:
                return e.return_value
            return space.wrap(error)
        if res is None:
            return space.w_Null
        return res
    call_args.ll_func = ll_func  # for debugging
    return call_args


def wrap(signature, name=None, aliases=(), error=None,
         error_handler=handle_as_warning, check_num_args=True):
    assert name is None or isinstance(name, str)
    assert isinstance(aliases, (tuple, list))

    def inner(ll_func):
        sig = BuiltinSignature(signature)
        fname = name or ll_func.func_name
        runner = make_runner(signature, ll_func, fname, error,
                             error_handler, check_num_args)
        if sig.has_references:
            res = BuiltinFunctionWithReferences(sig, fname, runner)
        else:
            res = BuiltinFunction(fname, runner)
        register_builtin_function(fname, res)
        for alias in aliases:
            # not so nice, but allows to raise warinings
            # with funcname set to called alias
            runner = make_runner(signature, ll_func, alias, error,
                                 error_handler, check_num_args)
            res = BuiltinFunction(alias, runner)
            register_builtin_function(alias, res)
        return res
    return inner


def wrap_method(signature, name, error=None, flags=0,
                error_handler=handle_as_warning, check_num_args=True):
    def inner(ll_func):
        sig = BuiltinSignature(signature)
        assert '::' in name   # should be "Class::method"
        fname = name
        runner = make_runner(signature, ll_func, fname, error,
                             error_handler, check_num_args)
        if sig.has_references:
            res = BuiltinFunctionWithReferences(sig, fname, runner)
        else:
            res = BuiltinFunction(fname, runner)
        res.flags = flags
        return res
    return inner


@wrap(['space', Optional(int)])
def error_reporting(space, level=-1):
    interp = space.ec.interpreter
    if level == -1:
        return space.newint(interp.error_level)
    else:
        interp.error_level = level


@wrap(['space',   Optional(bool)])
def microtime(space,   is_float=False):
    from hippy.module.standard.strings.funcs import _printf
    t = time.time()
    if is_float:
        return space.wrap(t)
    f,  i = math.modf(t)
    w_f = space.newfloat(f)
    w_i = space.newint(int(i))
    res = _printf(space,  "%.8f %d",  [w_f,  w_i],  'microtime')
    return space.newstr(res)


@wrap(['interp', str])
def function_exists(interp, funcname):
    try:
        interp.lookup_function(funcname)
    except KeyError:
        return interp.space.w_False
    return interp.space.w_True


@wrap(['space', str, Optional(bool)])
def class_exists(space, name, autoload=True):
    klass = space.ec.interpreter.lookup_class_or_intf(name, autoload=autoload)
    return space.newbool(klass is not None and not klass.is_interface())


@wrap(['interp', W_Root, str])
def property_exists(interp, w_obj, property_name):
    if not property_name:
        return interp.space.w_False
    if isinstance(w_obj, W_InstanceObject):
        klass = w_obj.klass
        result = (property_name in klass.properties or
                  w_obj.map.lookup(property_name) is not None)
        return interp.space.newbool(result)
    elif isinstance(w_obj, W_StringObject):
        klass = interp.lookup_class_or_intf(w_obj.unwrap())
        if klass is None:
            return interp.space.w_False
        return interp.space.newbool(property_name in klass.properties)
    else:
        interp.warn("First parameter must either be an object or the name of "
                    "an existing class")
        return interp.space.w_Null


@wrap(['space', str, Optional(bool)])
def interface_exists(space, name, autoload=True):
    intf = space.ec.interpreter.lookup_class_or_intf(name, autoload=autoload)
    return space.newbool(intf is not None and intf.is_interface())


@wrap(['space', W_Root])
def ___exit(space, w_code_or_message):
    code = 0
    message = ""
    if w_code_or_message.tp == space.tp_int:
        code = space.int_w(w_code_or_message)
    else:
        message = space.str_w(w_code_or_message)
    raise ExplicitExitException(code, message)


def _is_a(space, w_obj, classname, allow_string, must_be_different):
    if space.is_object(w_obj):
        klass = space.getclass(w_obj)
    elif allow_string:
        klass = space.ec.interpreter.lookup_class_or_intf(space.str_w(w_obj))
    else:
        klass = None
    #
    if klass is None:
        result = False
    elif must_be_different and klass.get_identifier() == classname.lower():
        result = False    # aaaargh
    else:
        result = klass.is_subclass_of_class_or_intf_name(classname)
    return space.newbool(result)


@wrap(['space', W_Root, str, Optional(bool)])
def is_a(space, w_obj, classname, allow_string=False):
    return _is_a(space, w_obj, classname, allow_string,
                 must_be_different=False)


@wrap(['space', W_Root, str, Optional(bool)])
def is_subclass_of(space, w_obj, classname, allow_string=False):
    return _is_a(space, w_obj, classname, allow_string,
                 must_be_different=True)


def _get_class(interp, w_obj):
    '''Returns a class object starting from either a string or object.'''
    klass = None
    space = interp.space
    if w_obj.tp == space.tp_str:
        klass = interp._lookup_class(space.str_w(w_obj))
    elif w_obj.tp == space.tp_object:
        klass = space.getclass(w_obj)

    return klass


@wrap(['interp', W_Root, str])
def method_exists(interp, w_obj, method_name):
    klass = _get_class(interp, w_obj)
    space = interp.space
    if not klass:
        return space.w_False

    contextclass = interp.get_contextclass()
    try:
        klass.locate_static_method(method_name, contextclass,
                                    check_visibility=False)
        return space.w_True
    except VisibilityError:
        return space.w_False


@wrap(['space', Optional(W_Root)])
def get_class(space, w_object=None):
    if w_object is None or w_object is space.w_Null:
        bc = space.ec.interpreter.get_current_bytecode()
        if bc is None or bc.method_of_class is None:
            space.ec.warn("get_class() called without object "
                          "from outside a class")
            return space.w_False
        klass = bc.method_of_class
    else:
        if not space.is_object(w_object):   # XXX factor this check out?
            space.ec.warn("get_class() expects parameter 1 to be object, "
                          "%s given" % space.get_type_name(w_object.tp))
            return space.w_False
        klass = space.getclass(w_object)
    #
    return space.newstr(klass.name)


@wrap(['interp', W_Root])
def get_class_methods(interp, w_obj):
    '''Gets the class methods' names.'''
    klass = _get_class(interp, w_obj)
    space = interp.space
    if not klass:
        return space.w_Null

    contextclass = interp.get_contextclass()
    methods = klass.get_methods(contextclass)
    class_methods = newlist_hint(len(klass.methods))
    for method in methods:
        class_methods.append(space.newstr(method))

    return space.new_array_from_list(class_methods)


@wrap(['space'])
def get_declared_classes(space):
    list = []
    for c in space.ec.interpreter.get_all_defined_classes():
        if not c.is_interface():
            list.append(space.newstr(c.name))
    return space.new_array_from_list(list)


@wrap(['space'])
def get_declared_interfaces(space):
    list = []
    for c in space.ec.interpreter.get_all_defined_classes():
        if c.is_interface():
            list.append(space.newstr(c.name))
    return space.new_array_from_list(list)


@wrap(['space', str])
def get_class_vars(space, classname):
    inside = True
    klass = space.ec.interpreter.get_current_thisclass()
    if not klass:
        inside = False
        klass = space.ec.interpreter._lookup_class(classname)
    if not klass:
        return space.w_False
    pairs = []
    for v, p in klass.properties.items():
        if inside:
            if p.value:
                pairs.append((space.newstr(v), p.value.eval_static(space)))
        else:
            if p and not p.is_private():
                if p.value:
                    pairs.append((space.newstr(v), p.value.eval_static(space)))
    return space.new_array_from_pairs(pairs)


@wrap(['space'])
def get_called_class(space):
    klass = space.ec.interpreter.get_current_thisclass()
    if klass is None:
        space.ec.warn("get_called_class() called from outside a class")
        return space.w_False
    return space.newstr(klass.name)


@wrap(['space', Optional(W_Root)])
def get_parent_class(space, w_object=None):
    if w_object is None or w_object is space.w_Null:
        klass = space.ec.interpreter.get_contextclass()
    elif space.is_object(w_object):
        klass = space.getclass(w_object)
    elif space.is_str(w_object):
        classname = space.str_w(w_object)
        klass = space.ec.interpreter._lookup_class(classname)
    else:
        return space.w_False
    if klass is None or klass.parentclass is None:
        return space.w_False
    return space.newstr(klass.parentclass.name)


@wrap(['space'])
def sys_getloadavg(space):
    try:
        load = os.getloadavg()
    except OSError:
        space.ec.warn("sys_getloadavg() failed")
        return space.w_Null
    return space.new_array_from_list([space.newfloat(load[0]),
                                      space.newfloat(load[1]),
                                      space.newfloat(load[2])])


# def get_defined_vars(space):
#     # XXX NOT WORKING CORRECTLY GLOBALS keeps refs, we need vals
#     frame = space.ec.interpreter.topframeref()
#     return space.new_array_from_rdict(frame.extra_variables)


@wrap(['space', str])
def extension_loaded(space, ext):
    if ext in config.EXTENSIONS:
        return space.w_True
    return space.w_False


@wrap(['space', 'callback'])
def set_error_handler(space, callback):
    interp = space.ec.interpreter
    interp.last_error_handler = interp.error_handler
    interp.error_handler = callback
    return space.w_True


@wrap(['space'])
def restore_error_handler(space):
    interp = space.ec.interpreter
    interp.error_handler = interp.last_error_handler
    return space.w_True


@wrap(['space', 'args_w'])
def flush(space, args_w):
    pass


@wrap(['space', str])
def error_log(space, msg):
    space.ec.error(msg)
    return space.w_True


@wrap(['space', str])
def utf8_encode(space, input):
    """ Convert latin-1 to utf8
    """
    return space.wrap(input.decode("latin-1").encode("utf-8"))


@wrap(['space', str])
def utf8_decode(space, input):
    """ Convert utf8 to latin-1
    """
    try:
        return space.wrap(input.decode("utf-8").encode("latin-1"))
    except UnicodeDecodeError:
        return space.w_False
