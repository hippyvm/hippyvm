import os
from collections import OrderedDict

from hippy.hippyoption import is_optional_extension_enabled

from hippy.consts import BYTECODE_HAS_ARG, BYTECODE_NAMES,\
    BINOP_LIST, BINOP_BITWISE, RETURN
from hippy.function import AbstractFunction
from hippy.error import (IllegalInstruction, FatalError, PHPException,
                         ExplicitExitException, VisibilityError, SignalReceived)
from hippy.lexer import LexerError
from hippy.sourceparser import ParseError
from hippy.phpcompiler import compile_php
from hippy.ast import CompilerError
from hippy.objects.reference import W_Reference
from hippy.objects.interpolate import W_StrInterpolation
from hippy.objects.iterator import W_BaseIterator
from hippy.objects.arrayobject import (
        new_rdict, W_RDictArrayObject, W_ArrayObject)
from hippy.objects.closureobject import W_ClosureObject, new_closure
from hippy.objects.instanceobject import W_InstanceObject
from hippy.objects.strobject import W_StringObject
from hippy.builtin_klass import W_ExceptionObject
from hippy.klass import ClassDeclaration, ClassBase, get_interp_decl_key
from hippy.function import Function
from hippy.frame import Frame, CatchBlock, Unsilence
from hippy.config import Config
from hippy import constants
from hippy import pointer
from hippy.sourceparser import parse
from hippy.astcompiler import compile_ast
from hippy.module.standard.directory import php_dir
from hippy.module.standard.glob import php_glob
from hippy.module.spl import spl
from rpython.rlib.objectmodel import we_are_translated
from rpython.rlib import jit
from rpython.rlib import rpath, rsignal
from rpython.rlib.unroll import unrolling_iterable
from rpython.rlib.rfile import create_popen_file
from rpython.rlib.rpath import exists, dirname, join, abspath

from hippy.module.session import Session

# side-effect of registering functions
import hippy.module.standard.array.funcs
import hippy.module.standard.strings.funcs
import hippy.module.standard.math.funcs
import hippy.module.standard.file.funcs
import hippy.module.standard.network.funcs
import hippy.module.standard.misc.funcs
import hippy.module.standard.streams.funcs
from hippy.module.standard.directory import php_dir

import hippy.module.posix.funcs
import hippy.module.session.funcs

import hippy.module.internal
import hippy.module.regex.interface
import hippy.module.url

import hippy.module.mbstring.funcs
import hippy.module.date.funcs

import hippy.module.standard.exec_
import hippy.module.spl
import hippy.module.ctype
import hippy.module.general.funcs
import hippy.module.reflections
import hippy.module.mail
import hippy.localemodule
import hippy.builtin_klass
import hippy.buffering
import hippy.module.spl
import hippy.module.ctype
import hippy.module.date.datetime_klass
import hippy.module.date.dateinterval_klass
import hippy.module.date.datetimezone_klass

from hippy.module.date import default_timezone
from hippy.buffering import Buffer

if is_optional_extension_enabled("mysql"):
    import ext_module.mysql.funcs

if is_optional_extension_enabled("hash"):
    import ext_module.hash.funcs

if is_optional_extension_enabled("xml"):
    import ext_module.xml.interface

if is_optional_extension_enabled("mcrypt"):
    import ext_module.mcrypt.funcs


def get_printable_location(pc, bytecode, contextclass=None):
    if 0 <= pc < len(bytecode.bc_mapping):
        lineno = str(bytecode.bc_mapping[pc])
    elif pc == len(bytecode.bc_mapping):
        lineno = 'END'
    else:
        lineno = '?'
    if 0 <= pc < len(bytecode.code):
        opcode = ord(bytecode.code[pc])
    else:
        opcode = 999
    if opcode < len(BYTECODE_NAMES):
        opname = BYTECODE_NAMES[opcode]
    else:
        opname = '?'
    return "%s %s %s" % (bytecode.name, lineno, opname)

driver = jit.JitDriver(reds=['frame', 'self'],
                       greens=['pc', 'bytecode', 'contextclass'],
                       virtualizables=['frame'],
                       get_printable_location=get_printable_location,
                       )


class W_Globals(W_RDictArrayObject):
    """The $GLOBALS array."""
    def __init__(self, space):
        W_RDictArrayObject.__init__(self, space, new_rdict(), 0)

    def as_unique_arraydict(self):
        return self

    def lookup_var(self, name):
        try:
            return self.dct_w[name]
        except KeyError:
            return None

    def get_var(self, space, name, give_notice=False):
        r_glob = self.lookup_var(name)
        if r_glob is None:
            r_glob = space.empty_ref()
            self._setitem_str(name, r_glob, as_ref=True)
        return r_glob

    def set_var(self, name, r_var):
        assert isinstance(r_var, W_Reference)
        self.dct_w[name] = r_var

    def _setitem_str(self, key, w_value, as_ref,
                     unique_array=False, unique_item=False):
        dct_w = self.dct_w
        if not as_ref:
            try:
                w_old = dct_w[key]
            except KeyError:
                w_value = W_Reference(w_value)
            else:
                assert isinstance(w_old, W_Reference)
                w_old.store(w_value, unique_item)
                return self
        assert isinstance(w_value, W_Reference)

        dct_w[key] = w_value
        gframe = self.space.ec.interpreter.global_frame
        if gframe is not None:
            gframe.set_ref_by_name(key, w_value)
        return self

    def unset_var(self, name):
        try:
            del self.dct_w[name]
        except KeyError:
            pass

    def _unsetitem_str(self, key):
        self.unset_var(key)
        gframe = self.space.ec.interpreter.global_frame
        if gframe is not None:
            gframe.set_ref_by_name(key, None)
        return self

    def _inplace_pop(self, space):
        space.ec.hippy_warn("array_pop($GLOBALS) ignored")
        return space.w_Null


err_dct = {
    constants.E_ERROR: 'Fatal error',
    constants.E_RECOVERABLE_ERROR: 'Catchable fatal error',
    constants.E_WARNING: 'Warning',
    constants.E_PARSE: 'Parse error',
    constants.E_NOTICE: 'Notice',
    constants.E_STRICT: 'Strict Standards',
    constants.E_DEPRECATED: 'Deprecated',
    constants.E_HIPPY_WARN: 'Hippy warning'}


class OutputBufferingLock(object):
    def __init__(self, interp):
        self.interp = interp

    def __enter__(self):
        self.interp.ob_lock = True

    def __exit__(self, exc_type, exc_val, trace):
        self.interp.ob_lock = False


@jit.elidable
def is_constant_self_or_parent(name):
    key = name.lower()
    return key == 'self' or key == 'parent'


class Interpreter(object):
    """ Interpreter keeps the state of the current run. There will be a new
    interpreter instance per run of script
    """
    _immutable_fields_ = ['debugger?']
    cgi = 0
    web_config = None
    debugger = None
    allow_direct_class_access = False
    last_strtok_str = None
    last_strtok_pos = 0

    def __init__(self, space):
        self.space = space
        self.constant_names = []
        self.class_names = []
        space.global_constant_cache.reset()
        space.global_function_cache.reset()
        space.global_class_cache.reset()

        self.error_level = 0xffffff
        self.topframeref = jit.vref_None
        self.error_handler = None
        space.ec.interpreter = self  # one interpreter at a time
        self._autoloading = {}
        self.autoload_stack = []
        self.autoload_extensions = ['.inc', '.php']
        self.constants = OrderedDict()
        self.globals = W_Globals(space)
        self.w_globals_ref = W_Reference(self.globals)
        self.config = Config(space)
        self.cached_files = OrderedDict()
        self.session = Session(self)
        self.w_exception_handler = None
        self.last_error_handler = None
        self.last_error_type = 0
        self.last_error_msg = None
        self.last_error_file = None
        self.last_error_line = 0
        self.silence_stack = []
        self.global_frame = None
        self.output_buffer = None
        self.ob_lock = False
        self.any_output = False
        self.last_resource_id = 4
        self.last_dir_resource = None
        self.include_path = [space.str_w(self.config.get_ini_w(
            'include_path'))]
        self.timezone = default_timezone(self)
        self.timezone_set = False
        self.last_posix_errno = 0
        self.mysql_links = {}            # k: credentials v: resource
        self.mysql_links_cnt = 0         # just conter
        self.persistent_mysql_links = 0  # just counter
        self.last_mysql_link = None
        self.regexp_backtrack_limit = 1000000   # XXX
        self.regexp_recursion_limit = 100000    # XXX
        self.regexp_error_code = hippy.module.regex.interface.PREG_NO_ERROR
        self._setup = False
        self.header_keys = {"content-type": 0}
        self.headers = ['Content-Type: text/html']
        self.extra_headers = []
        self.implicit_flush = False
        self.static_values = {}
        self.http_status_code = -1
        self.shutdown_functions = []
        self.shutdown_arguments = []
        self.open_fd = {}

    def register_fd(self, w_fd):
        self.open_fd[w_fd.res_id] = w_fd

    def unregister_fd(self, w_fd):
        del self.open_fd[w_fd.res_id]

    def handle_signal_if_necessary(self):
        n = rsignal.pypysig_getaddr_occurred().c_value
        if n < 0:
            n = rsignal.pypysig_poll()
            if n < 0:
                rsignal.pypysig_getaddr_occurred().c_value = 0
                raise SignalReceived()

    def _class_get(self, class_name):
        kls = self.space.global_class_cache.locate(class_name)
        assert kls is None or isinstance(kls, ClassBase)
        return kls

    def load_static(self, bc, arg):
        cm = bc.consts[arg]
        try:
            return self.static_values[cm]
        except KeyError:
            w_ref = W_Reference(bc.static_vars[cm].eval_static(self.space))
            self.static_values[cm] = w_ref
            return w_ref

    def _class_is_defined(self, class_name):
        return self.space.global_class_cache.has_definition(class_name)

    def create_class(self, cls_id, cls_decl):
        key = get_interp_decl_key(self, cls_decl)
        self.space.global_class_cache.create_class(self, cls_id, cls_decl, key)
        self.class_names.append(cls_id)

    def get_all_defined_classes(self):
        return [self._class_get(name) for name in (
                    self.space.prebuilt_classes + self.class_names)]

    def open_stdin_stream(self):
        # can be overloaded by tests
        from rpython.rlib.streamio import fdopen_as_stream

        return fdopen_as_stream(0, "r")

    # Needs to be a separate method so flowspace doesn't say import cannot
    # succeed when there is no mysql module source around.
    def _call_initialize_mysql(self):
        from ext_module.mysql.link_resource import initialize_mysql
        self.mysql_ptr = initialize_mysql()

    def _setup_timezone(self):
        w_timezone_name = self.config.get_ini_w('date.timezone')
        if w_timezone_name is not None:
            timezone_name = self.space.str_w(w_timezone_name)
            if timezone_name:
                self.timezone = default_timezone(self, timezone_name)
                self.timezone_set = True

    def setup(self, cgi=constants.CGI_NONE, cgi_params=None, argv=None,
              post_data=None):
        if self._setup:
            return
        space = self.space
        get, post = None, None
        if cgi:
            from hippy.cgisupport import setup_cgi
            self.web_config = setup_cgi(self, cgi_params, argv,
                                        post_data=post_data)
            self.cgi = cgi

        if is_optional_extension_enabled("mysql"):
            self._call_initialize_mysql()
        self._setup_timezone()

        self.error_level = space.int_w(self.config.get_ini_w(
            'error_reporting'))
        self._setup = True
        self.setup_globals(space, argv)
        self.setup_stdxx(space, cgi)

    def setup_stdxx(self, space, cgi):
        from hippy.objects.resources.file_resource import W_STDIN
        from hippy.objects.resources.file_resource import W_STDOUT
        from hippy.objects.resources.file_resource import W_STDERR
        stdout = W_STDOUT(space)
        stdout.open()
        stdin = W_STDIN(space)
        stdin.open()
        stderr = W_STDERR(space)
        stderr.open()
        self.declare_new_constant('STDIN', stdin)
        self.declare_new_constant('STDOUT', stdout)
        self.declare_new_constant('STDERR', stderr)

    def setup_debugger(self, read_fd, write_fd, start_paused=False):
        from hippy.debugger import Debugger
        self.debugger = Debugger(read_fd, write_fd)
        if start_paused:
            self.debugger.run_debugger_loop(self)

    def shutdown(self):
        # this is mostly important for tests
        self.flush_buffers()
        if self.session is not None:
            self.session.write_close(self)
        for i, func in enumerate(self.shutdown_functions):
            func.call_args(self, self.shutdown_arguments[i])
        for _,  mysql_link in self.mysql_links.items():
            if not mysql_link.persistent:
                mysql_link.close()
        for _, fd in self.open_fd.items():
            fd.close()

    def _get_server_env(self):
        if self.web_config is None:
            initial_server_dict = OrderedDict()
            for k, v in os.environ.items():
                if k not in initial_server_dict:
                    initial_server_dict[k] = self.space.wrap(v)
        else:
            initial_server_dict = self.web_config.initial_server_dict
        return initial_server_dict

    def initialize_cookie_variable(self, space):
        if self.web_config is not None and self.web_config.cookie is not None:
            d = OrderedDict()
            v = self.web_config.cookie
            l = v.split(";")
            for item in l:
                l2 = item.strip().split("=")
                if len(l2) != 2:
                    # XXX issue a warning?
                    continue
                d[l2[0]] = space.wrap(l2[1])
            return space.new_array_from_rdict(d)
        return space.w_Null

    def _cleanup_(self):
        raise Exception("should not see prebuilt interpreters")

    def setup_globals(self, space, argv=None):
        self.globals.set_var('GLOBALS', self.w_globals_ref)
        server_dict = self._get_server_env()
        if argv:
            w_argc = space.wrap(len(argv))
            w_argv = space.new_array_from_list([space.wrap(x) for x in argv])
            self.globals.set_var('argc', W_Reference(w_argc))
            self.globals.set_var('argv', W_Reference(w_argv))
            server_dict['argc'] = w_argc
            server_dict['argv'] = w_argv
        self.r_server = W_Reference(
            self.space.new_array_from_rdict(server_dict))
        self.globals.set_var('_SERVER', self.r_server)

        if self.web_config is not None:
            get = self.web_config.w_get
            getref = W_Reference(get)
            self.globals.set_var('_GET', getref)
            post = self.web_config.w_post
            postref = W_Reference(post)
            self.globals.set_var('_POST', postref)
            files = self.web_config.w_files
            filesref = W_Reference(files)
            self.globals.set_var('_FILES', filesref)
        else:
            getref = None
            postref = None
        w_session = W_Reference(space.new_array_from_rdict(OrderedDict()))
        self.globals.set_var('_SESSION', w_session)
        w_cookie = self.initialize_cookie_variable(space)
        if w_cookie is not None:
            w_cookie = W_Reference(w_cookie)
            self.globals.set_var("_COOKIE", w_cookie)
        self.superglobals = [self.w_globals_ref, self.r_server,
                             getref, postref,
                             w_cookie, w_session]

    def lookup_constant(self, name):
        if name and name[0] == '\\':
            name = name[1:]
        return self.space.global_constant_cache.locate(name)

    def declare_new_constant(self, name, w_value):
        self.space.global_constant_cache.declare_new(name, w_value)
        self.constant_names.append(name)

    def locate_constant(self, name, complain=True):
        c = self.lookup_constant(name)
        if c is not None:
            return c
        if not complain:
            return None
        self.notice("Use of undefined constant %s - "
                "assumed '%s'" % (name, name))
        return self.space.wrap(name)

    def lookup_function(self, name):
        if not name:
            return None
        if name[0] == '\\':
            name = name[1:]
        func = self.space.global_function_cache.locate(name)
        if func is None:
            return None 
        assert isinstance(func, AbstractFunction)
        return func

    def locate_function(self, name):
        func = self.lookup_function(name)
        if func is not None:
            return func
        self.fatal("Call to undefined function %s()" % name)

    def get_this(self, frame):
        w_this = frame.w_this
        if w_this is None:
            self.fatal("Using $this when not in object context")
        return w_this

    def get_frame(self):
        return self.topframeref()

    def check_valid_class_name(self, name):
        name = name.lower()
        if name in ['self', 'parent', 'static']:
            self.fatal("Cannot use '%s' as class name as it is reserved" % name)

    def _lookup_class(self, name, autoload=True):
        if not name:
            return None
        if name and name[0] == '\\':
            name = name[1:]
        if not name:
            return None
        kls = self._class_get(name)
        if kls is None:
            if autoload:
                kls = self._autoload(name)
            else:
                return None
        return kls

    def _get_self_class(self):
        contextclass = self.get_contextclass()
        if contextclass is None:
            self.fatal("Cannot access self:: when no class scope is active")
        return contextclass

    def _get_parent_class(self):
        contextclass = self.get_contextclass()
        if contextclass is None:
            self.fatal("Cannot access parent:: when no class scope "
                    "is active")
        result = contextclass.parentclass
        if result is None:
            self.fatal("Cannot access parent:: when current class "
                    "scope has no parent")
        return result

    def _get_static_class(self):
        frame = self.get_frame()
        if frame.thisclass is None:
            self.fatal("Cannot access static:: when no class scope "
                    "is active")
        return frame.thisclass

    def lookup_class_or_intf(self, name, autoload=True):
        cls_id = name.lower()
        if cls_id == 'self':
            return self._get_self_class()
        if cls_id == 'parent':
            return self._get_parent_class()
        if cls_id == 'static':
            return self._get_static_class()
        return self._lookup_class(name, autoload=autoload)

    def lookup_class_or_intf_for_clsdecl(self, name):
        self.check_valid_class_name(name)
        return self._lookup_class(name, autoload=True)

    def _autoload_from_stack(self, class_name):
        class_id = class_name.lower()
        space = self.space
        for _, callback_func in self.autoload_stack:
            self.call(callback_func, [space.newstr(class_name)])
            klass = self.lookup_class_or_intf(class_id, autoload=False)
            if klass:
                return klass
        return None

    def _autoload(self, name):
        cls_id = name.lower()

        if cls_id in self._autoloading:
            return None

        if self.autoload_stack:
            return self._autoload_from_stack(name)

        autoload_func = self.lookup_function('__autoload')
        if autoload_func is None:
            return None
        self._autoloading[cls_id] = None
        try:
            autoload_func.call_args(self, [self.space.newstr(name)])
        finally:
            del self._autoloading[cls_id]
        return self.lookup_class_or_intf(cls_id, autoload=False)

    def locate_class_or_intf(self, name):
        "Like lookup_class_or_intf(), but raise a fatal error if not found."
        klass = self.lookup_class_or_intf(name)
        if klass is None:
            self.fatal("Class '%s' not found" % name)
        return klass

    def lock_ob(self, fname):
        if self.ob_lock:
            self.output_buffer = None  # kill the whole buffer stack
            self.fatal("%s(): Cannot use output buffering in output "
                       "buffering display handlers" % fname)
        return OutputBufferingLock(self)

    def start_buffering(self, space, name, callback=None,
                        chunk_size=4096, flags=112):
        self.output_buffer = Buffer(space, name, callback, chunk_size, flags,
                                    self.output_buffer)

    def flush_buffers(self):
        if self.headers:
            self.send_headers()
        while self.output_buffer:
            self.output_buffer.flush()
            self.output_buffer = self.output_buffer.prev

    def clean_buffers(self):
        while self.output_buffer:
            prev = self.output_buffer.prev
            self.output_buffer.clean()
            self.output_buffer = prev

    def header(self, item, replace, give_warn=True):
        if self.any_output:
            if give_warn:
                self.warn("Cannot modify header information - headers already"
                          " sent")
            return
        pos = item.find(": ")
        if pos >= 0:
            k = item[:pos]
            lower_k = k.lower()
            if lower_k in self.header_keys and replace:
                self.headers[self.header_keys[lower_k]] = item
            else:
                self.headers.append(item)
        else:
            self.extra_headers.append(item)

    def writestr(self, str, buffer=True):
        if not str:
            return
        if self.implicit_flush:
            if self.output_buffer:
                self.output_buffer.flush()
                return
        if buffer and self.output_buffer is not None:
            self.output_buffer.write(str)
        else:
            if not self.any_output:
                if self.headers:
                    self.send_headers()
                self.any_output = True
            assert str is not None
            self._writestr(str)

    def _writestr(self, string):
        os.write(1, string)

    def err_write(self, string):
        os.write(2, string)

    def send_headers(self):
        self.any_output = True
        if self.cgi:
            if self.http_status_code != -1:
                self._writestr('Status: %d\r\n' % self.http_status_code)
            for k in self.headers:
                self._writestr(k + "\r\n")
            for elem in self.extra_headers:
                self._writestr(elem + "\r\n")
            self._writestr("\r\n")
        self.headers = None
        self.extra_headers = None

    def handle_error(self, level, msg):
        if self.error_level & level == 0:
            return
        self._handle_error(level, msg)

    def _handle_error(self, level, msg):
        space = self.space
        tb = list(self.get_traceback())
        tb.reverse()
        if self.error_handler is not None:
            for filename, funcname, line, source in tb:
                args_w = [space.newstr(str(level)),
                          space.newstr(msg),
                          space.newstr(filename),
                          space.newstr(str(line)),
                          space.newstr("missing functionality")]
                self.call(self.error_handler, args_w)
            return
        if not tb:  # during shutdown
            self._log(level, msg, 'Unknown', 0)
        else:
            for filename, funcname, line, source in tb:
                self._log_traceback(filename, funcname, line, source)
            filename, funcname, line, source = tb[-1]
            self.last_error_type = level
            self.last_error_msg = msg
            if filename:
                self.last_error_file = rpath.join(os.getcwd(), [filename])
            self.last_error_line = line
            self._log(level, msg, filename, line)
        if level == constants.E_RECOVERABLE_ERROR:
            raise FatalError(msg, self.get_traceback())

    def _log_traceback(self, filename, funcname, line, source):
        self.err_write("In function %s, file %s, line %d\n" %
                       (funcname, filename, line))
        self.err_write("  " + source + "\n")

    def _log(self, level, msg, filename='', line=-1):
        if filename:
            msg = "%s in %s on line %d" % (msg, filename, line)
        self.log_error(level, msg)

    def log_error(self, level, msg):
        self.err_write("%s: %s\n" % (err_dct[level], msg))

    def notice(self, msg):
        self.handle_error(constants.E_NOTICE, msg)

    def warn(self, msg):
        self.handle_error(constants.E_WARNING, msg)

    def error(self, msg):
        self.handle_error(constants.E_ERROR, msg)

    def hippy_warn(self, msg):
        self.handle_error(constants.E_HIPPY_WARN, msg)

    def fatal(self, msg):
        # This one is supposed to raise FatalError.  If needed, in the
        # caller, write "raise self.fatal(...)" to make it clear that
        # it cannot return (useful for RPython)
        self.handle_error(constants.E_ERROR, msg)
        raise FatalError(msg, self.get_traceback())

    def recoverable_fatal(self, msg):
        # May raise FatalError.
        self.handle_error(constants.E_RECOVERABLE_ERROR, msg)
    catchable_fatal = recoverable_fatal

    def strict(self, msg):
        self.handle_error(constants.E_STRICT, msg)

    def parse_error(self, msg):
        self.handle_error(constants.E_PARSE, msg)
        raise FatalError(msg, self.get_traceback())

    def deprecated(self, msg):
        self.handle_error(constants.E_DEPRECATED, msg)

    def fallback_handle_exception(self, w_exc):
        assert isinstance(w_exc, W_ExceptionObject)
        tb = w_exc.traceback
        assert tb
        filename, _, lineno, _ = tb[0]
        message = self.space.str_w(w_exc.get_message(self))
        if message:
            exc_msg = "with message '%s' " % message
        else:
            exc_msg = ""
        msg = "Uncaught exception '%s' %sin %s:%d" % (
            w_exc.klass.name, exc_msg, filename, lineno)
        self.log_error(constants.E_ERROR, msg)
        self.err_write('Stack trace:\n')
        for i, (filename, funcname, line, source) in enumerate(tb):
            if funcname == '<main>':
                msg = '{main}'
            else:
                msg = '%s(%s)' % (filename, line)
            self.err_write("#%d %s\n" % (i, msg))
        filename, _, line, _ = tb[len(tb) - 1]
        self.err_write("  thrown in %s on line %d\n" % (filename, line))
        raise ExplicitExitException(255, '')

    def compile_bytecode(self, filename, source):
        try:
            return compile_php(filename, source, self.space, self)
        except (ParseError, LexerError) as exc:
            self._log(constants.E_PARSE, exc.message, filename,
                      exc.source_pos)
            return None
        except CompilerError as exc:
            self._log(constants.E_ERROR, exc.msg, exc.filename, exc.lineno)
            return None

    def run_main(self, space, bytecode, top_main=False):
        if not self._setup:
            self.setup()
        frame = Frame(self, bytecode, is_global_level=True)
        frame.load_from_scope(self.globals)
        old_global_frame = self.global_frame
        self.global_frame = frame
        if top_main:
            try:
                try:
                    w_result = self.interpret(frame)
                except PHPException as e:
                    if self.w_exception_handler is not None:
                        try:
                            self.call(self.w_exception_handler, [e.w_exc])
                        except PHPException as e2:
                            self.fallback_handle_exception(e2.w_exc)
                    else:
                        self.fallback_handle_exception(e.w_exc)
                    return space.w_Null
            finally:
                with self.lock_ob('<shutdown>'):
                    self.flush_buffers()
        else:
            w_result = self.interpret(frame)
            self.global_frame = old_global_frame
        return w_result

    def run_local_include(self, bytecode, parent_frame):
        frame = Frame(self, bytecode)
        frame.load_from_frame(parent_frame)
        w_result = self.interpret(frame)
        parent_frame.clear()
        parent_frame.load_from_frame(frame)
        return w_result

    def debug_eval(self, source, parent_frame=None,
                   allow_direct_class_access=False):
        ast = parse(self.space, source, 0, '<eval>')
        bc = compile_ast('<eval>', source, ast,
                         self.space, print_exprs=True)
        frame = Frame(self, bc)
        if parent_frame is not None:
            frame.load_from_frame(parent_frame)
        prev_class_access = self.allow_direct_class_access
        self.allow_direct_class_access = allow_direct_class_access
        try:
            self._interpret(frame, bc)
        finally:
            self.allow_direct_class_access = prev_class_access
            if parent_frame is not None:
                parent_frame.load_from_frame(frame)

    def compile_file(self, filename):
        absname = rpath.abspath(filename)
        try:
            return self.cached_files[absname]
        except KeyError:
            bc = self.space.compile_file(absname)
            self.cached_files[absname] = bc
            return bc

    def run_include(self, bc, parent_frame):
        if parent_frame.is_global_level:
            w_res = self.run_main(self.space, bc)
            parent_frame.load_from_scope(self.globals)
        else:
            w_res = self.run_local_include(bc, parent_frame)
        if w_res is None:
            return self.space.newint(1)
        else:
            return w_res

    def interpret(self, frame):
        self.enter(frame)
        try:
            return self._interpret(frame, frame.bytecode)
        finally:
            self.leave(frame)

    def _interpret(self, frame, bytecode):
        space = self.space
        for decl in bytecode.classes:
            frame.known_line = decl.lineno
            self.declare_class(decl)
        for func in bytecode.functions:
            frame.known_line = func.bytecode.startlineno
            self.declare_func(func)
        frame.known_line = -1
        pc = 0
        while True:
            driver.jit_merge_point(bytecode=bytecode, frame=frame,
                                   pc=pc, self=self,
                                   contextclass=frame.get_contextclass())
            code = bytecode.code
            frame.next_instr = pc
            if pc >= len(code):
                return None
            if self.debugger is not None:
                # the point is that we can use quasi-immutable for the
                # above checks so even if there is a debugger and session
                # is not active, we'll not call it
                self.debugger.bytecode_trace(self, frame, pc)
            next_instr = ord(code[pc])
            pc += 1
            if next_instr >= BYTECODE_HAS_ARG:
                pc, arg = bytecode.next_arg(pc)
            else:
                arg = 0  # don't make it negative
            if next_instr == RETURN:
                #assert frame.stackpos == 1 -- not if 'return;' appears
                # inside a 'foreach'
                assert frame.ptrs is None
                w_res = frame.peek()
                frame.clean(bytecode)
                return w_res
            if we_are_translated():
                for i, name in unrolling_bc:
                    if next_instr == i:
                        bc_impl = getattr(self, name)
                        try:
                            pc = bc_impl(bytecode, frame, space, arg, pc)
                        except PHPException as e:
                            pc = self.handle_exception(frame, e)
                        break
                else:
                    raise IllegalInstruction("illegal instruction")
            else:
                bytecode._marker = frame.next_instr
                bc_impl = getattr(self, BYTECODE_NAMES[next_instr])
                try:
                    pc = bc_impl(bytecode, frame, space, arg, pc)
                except PHPException as e:
                    pc = self.handle_exception(frame, e)

    def enter(self, frame):
        frame.f_backref = self.topframeref
        self.topframeref = jit.virtual_ref(frame)
        if self.debugger is not None:
            self.debugger.enter_frame(self, frame)

    def get_traceback(self):
        tb = []
        frame = self.topframeref()
        while frame is not None:
            filename, funcname, line = frame.get_position()
            source = frame.bytecode.getline(line)
            tb.append((filename, funcname, line, source))
            frame = frame.f_backref()
        return tb

    def get_current_bytecode(self):
        frame = self.topframeref()
        if frame is not None:
            return frame.bytecode
        return None

    def get_current_thisclass(self):
        frame = self.topframeref()
        if frame is not None:
            return frame.thisclass
        return None

    def get_contextclass(self):
        frame = self.topframeref()
        if frame is not None:
            return frame.get_contextclass()
        return None

    def get_default_timezone(self, func):
        if not self.timezone_set:
            self.warn(func + "(): " + "It is not safe to rely on the "
                    "system's timezone settings. You are *required* to use "
                    "the date.timezone setting or the "
                    "date_default_timezone_set() function. In case you used "
                    "any of those methods and you are still getting this "
                    "warning, you most likely misspelled the timezone "
                    "identifier. We selected the timezone 'UTC' for now, but "
                    "please set date.timezone to select your timezone.")

        return self.timezone

    def leave(self, frame):
        if self.debugger is not None:
            self.debugger.leave_frame(self, frame)
        jit.virtual_ref_finish(self.topframeref, frame)
        self.topframeref = frame.f_backref

    def echo(self, space, v):
        self.writestr(space.str_w(v))

    def print_expr(self, space, v):
        s = v.deref().var_dump(space, indent='', recursion={})
        if self.debugger is not None:
            if s.endswith('\n'):
                s = s[:-1]
            self.debugger.send_echo(s)
        else:
            self.writestr(s)

    def ILLEGAL(self, bytecode, frame, space, arg, pc):
        raise IllegalInstruction("illegal instruction")

    RETURN = ILLEGAL      # handled separately

    def LOAD_NONE(self, bytecode, frame, space, arg, pc):
        frame.push(None)
        return pc

    def LOAD_NULL(self, bytecode, frame, space, arg, pc):
        frame.push(space.w_Null)
        return pc

    def LOAD_CONST(self, bytecode, frame, space, arg, pc):
        w_obj = bytecode.consts[arg].eval_static(self.space)
        frame.push(w_obj)
        return pc

    def LOAD_STATIC(self, bytecode, frame, space, arg, pc):
        frame.push(self.load_static(bytecode, arg))
        return pc

    def INTERPOLATE(self, bytecode, frame, space, arg, pc):
        w_const = frame.pop()
        assert isinstance(w_const, W_StrInterpolation)
        frame.push(w_const.interpolate(space, frame, bytecode, arg))
        return pc

    def LOAD_NAMED_CONSTANT(self, bytecode, frame, space, arg, pc):
        frame.push(self.locate_constant(bytecode.names[arg]))
        return pc

    def GETCONSTANT_NS(self, bytecode, frame, space, arg, pc):
        w_name = frame.pop().deref()
        name = space.str_w(w_name)
        w_base_name = frame.pop().deref()
        const = self.lookup_constant(name)
        if const is None:
            base_name = space.str_w(w_base_name)
            const = self.locate_constant(base_name)
        frame.push(const)
        return pc


    def VAR_PTR(self, bytecode, frame, space, arg, pc):
        p = pointer.VariablePointer(frame, arg)
        frame.push_ptr(p)
        return pc

    def THIS_PTR(self, bytecode, frame, space, arg, pc):
        w_this = self.get_this(frame)
        frame.push_ptr(pointer.ThisPointer(w_this))
        return pc

    def VAR_INDIRECT_PTR(self, bytecode, frame, space, arg, pc):
        w_name = frame.pop()
        name = space.str_w(w_name)
        try:
            no = bytecode.var_to_pos[name]
        except KeyError:
            p = pointer.UndeclaredVariablePointer(frame, name)
        else:
            p = pointer.VariablePointer(frame, no)
        frame.push_ptr(p)
        return pc

    def REF_PTR(self, bytecode, frame, space, arg, pc):
        w_ref = frame.pop()
        if isinstance(w_ref, W_Reference):
            p = pointer.CallResultPointer(w_ref)
        else:
            p = pointer.ValuePointer(w_ref)
        frame.push_ptr(p)
        return pc

    def DISCARD_TOP(self, bytecode, frame, space, arg, pc):
        frame.pop()
        return pc

    @jit.unroll_safe
    def ROT(self, bytecode, frame, space, arg, pc):
        w_move_forward = frame.peek_nth(arg)
        arg -= 1
        while arg >= 0:
            frame.poke_nth(arg + 1, frame.peek_nth(arg))
            arg -= 1
        frame.poke_nth(0, w_move_forward)
        return pc

    def DUP(self, bytecode, frame, space, arg, pc):
        w_obj = frame.peek()
        frame.push(w_obj)
        return pc

    def SWAP(self, bytecode, frame, space, arg, pc):
        w_obj1 = frame.pop()
        w_obj2 = frame.pop()
        frame.push(w_obj1)
        frame.push(w_obj2)
        return pc

    def LOAD_NAME(self, bytecode, frame, space, arg, pc):
        frame.push(space.newstr(bytecode.names[arg]))
        return pc

    def LOAD_VAR(self, bytecode, frame, space, arg, pc):
        frame.push(frame.lookup_deref(arg, give_notice=True))
        return pc

    def LOAD_VAR_SWAP(self, bytecode, frame, space, arg, pc):
        w_other = frame.pop()
        frame.push(frame.lookup_deref(arg, give_notice=True))
        frame.push(w_other)
        return pc

    def LOAD_VAR_INDIRECT(self, bytecode, frame, space, arg, pc):
        w_name = frame.pop()
        name = space.str_w(w_name)
        frame.push(frame.get_ref_by_name(name).deref())
        return pc

    def LOAD_VAR_ITEM_PTR(self, bytecode, frame, space, arg, pc):
        p_base = frame.pop_ptr()
        p = pointer.VarItemPointer(p_base, frame, arg)
        frame.push_ptr(p)
        return pc

    def PTR_DEREF(self, bytecode, frame, space, arg, pc):
        # Only used for inplace assignments, so it leaves the pointer on
        # the stack.
        p = frame.peek_ptr()
        frame.push(p.deref(self))
        return pc

    def RESOLVE_FOR_WRITING(self, bytecode, frame, space, arg, pc):
        p = frame.pop_ptr()
        if not p.isref:
            space.ec.strict("Only variables should be assigned by reference")
        frame.push(p.get_ref(self))
        return pc

    def STORE(self, bytecode, frame, space, arg, pc):
        p = frame.pop_ptr()
        w_value = frame.pop().deref()
        frame.push(p.store(self, w_value))
        return pc

    def STORE_UNIQUE(self, bytecode, frame, space, arg, pc):
        p = frame.pop_ptr()
        w_value = frame.pop()
        assert not isinstance(w_value, W_Reference)
        frame.push(p.store(self, w_value, unique_item=True))
        return pc

    def STORE_REF(self, bytecode, frame, space, arg, pc):
        p = frame.pop_ptr()
        w_ref = frame.pop()
        frame.push(p.store_ref(self, w_ref))
        return pc

    def SET_FAST(self, bytecode, frame, space, arg, pc):
        w_ref = frame.peek()
        frame.store_ref(arg, w_ref)
        return pc

    def SET_REF_INDIRECT(self, bytecode, frame, space, arg, pc):
        w_name = frame.pop()
        w_ref = frame.peek()
        name = space.str_w(w_name)
        frame.set_ref_by_name(name, w_ref)
        return pc

    def PTR_UNSET(self, bytecode, frame, space, arg, pc):
        p = frame.pop_ptr()
        p.unset_ref(self)
        return pc

    def UNSET_FAST(self, bytecode, frame, space, arg, pc):
        frame.unset_ref(arg)
        return pc

    def UNSET_VAR_INDIRECT(self, bytecode, frame, space, arg, pc):
        w_name = frame.pop()
        name = space.str_w(w_name)
        frame.unset_ref_by_name(name)
        return pc

    def PTR_ISSET(self, bytecode, frame, space, arg, pc):
        p = frame.pop_ptr()
        frame.push(space.newbool(p.isset_ref(self)))
        return pc

    def PTR_EMPTY(self, bytecode, frame, space, arg, pc):
        p = frame.pop_ptr()
        if p.isset_ref(self):
            w_res = space.eq(p.deref(self), space.w_False)
        else:
            w_res = space.w_True
        frame.push(w_res)
        return pc

    def ECHO(self, bytecode, frame, space, arg, pc):
        w_arg = frame.pop()
        self.echo(space, w_arg)
        return pc

    def PRINT_EXPR(self, bytecode, frame, space, arg, pc):
        # for interactive usage only, in hip.py or in the debugger
        w_arg = frame.pop()
        self.print_expr(space, w_arg)
        return pc

    def JUMP_IF_FALSE(self, bytecode, frame, space, arg, pc):
        if not space.is_true(frame.pop()):
            return arg
        return pc

    def JUMP_BACK_IF_TRUE(self, bytecode, frame, space, arg, pc):
        if space.is_true(frame.pop()):
            self.handle_signal_if_necessary()
            driver.can_enter_jit(pc=arg, bytecode=bytecode, frame=frame,
                             self=self, contextclass=frame.get_contextclass())
            return arg
        return pc

    def JUMP_IF_FALSE_NO_POP(self, bytecode, frame, space, arg, pc):
        if not space.is_true(frame.peek()):
            return arg
        return pc

    def JUMP_IF_TRUE_NO_POP(self, bytecode, frame, space, arg, pc):
        if space.is_true(frame.peek()):
            return arg
        return pc

    def CASE_IF_EQ(self, bytecode, frame, space, arg, pc):
        w_right = frame.pop()
        w_left = frame.peek()
        if space.eq_w(w_left, w_right):
            frame.pop()
            return arg
        return pc

    def JUMP_FORWARD(self, bytecode, frame, space, arg, pc):
        return arg

    def JUMP_BACKWARD(self, bytecode, frame, space, arg, pc):
        self.handle_signal_if_necessary()
        driver.can_enter_jit(pc=arg, bytecode=bytecode, frame=frame,
                             self=self, contextclass=frame.get_contextclass())
        return arg

    def SUFFIX_PLUSPLUS(self, bytecode, frame, space, arg, pc):
        p = frame.pop_ptr()
        w_val = p.deref(self, give_notice=True)
        frame.push(w_val)
        p.store(self, space.uplusplus(w_val))
        return pc

    def SUFFIX_MINUSMINUS(self, bytecode, frame, space, arg, pc):
        p = frame.pop_ptr()
        w_val = p.deref(self, give_notice=True)
        frame.push(w_val)
        p.store(self, space.uminusminus(w_val))
        return pc

    def PREFIX_PLUSPLUS(self, bytecode, frame, space, arg, pc):
        p = frame.pop_ptr()
        w_val = p.deref(self, give_notice=True)
        frame.push(p.store(self, space.uplusplus(w_val)))
        return pc

    def PREFIX_MINUSMINUS(self, bytecode, frame, space, arg, pc):
        p = frame.pop_ptr()
        w_val = p.deref(self, give_notice=True)
        frame.push(p.store(self, space.uminusminus(w_val)))
        return pc

    def UNARY_PLUS(self, bytecode, frame, space, arg, pc):
        w_v = frame.pop()
        frame.push(space.uplus(w_v))
        return pc

    def UNARY_MINUS(self, bytecode, frame, space, arg, pc):
        w_v = frame.pop()
        frame.push(space.uminus(w_v))
        return pc

    def LOGICAL_NOT(self, bytecode, frame, space, arg, pc):
        frame.push(space.newbool(not space.is_true(frame.pop())))
        return pc

    def BITWISE_NOT(self, bytecode, frame, space, arg, pc):
        w_obj = frame.pop().deref()
        frame.push(w_obj.bitwise_not(space))
        return pc

    def _getfunc_from_class(self, clsname, methname, w_this, contextclass):
        klass = self.locate_class_or_intf(clsname)
        try:
            method = klass.getstaticmeth(methname, contextclass, w_this ,self)
        except VisibilityError as e:
            raise self.fatal(e.msg_fatal())
        return method.bind(w_this, klass)

    def getfunc(self, w_name, w_this, contextclass):
        space = self.space
        if space.is_str(w_name):
            name = space.str_w(w_name)
            return self.locate_function(name)
        elif isinstance(w_name, W_InstanceObject):
            func = w_name.get_callable()
            if func is None:
                raise self.fatal("Function name must be a string")
            return func
        elif isinstance(w_name, W_ArrayObject) and w_name.arraylen() == 2:
            w_instance = w_name._getitem_int(0)
            w_methname = w_name._getitem_int(1)
            if w_instance is None or w_methname is None:
                raise self.fatal(
                    "Array callback has to contain indices 0 and 1")
            w_instance = w_instance.deref()
            w_methname = w_methname.deref()
            if not (space.is_str(w_instance) or space.is_object(w_instance)):
                raise self.fatal("First array member is not "
                           "a valid class name or object")
            if space.is_str(w_methname):
                methname = space.str_w(w_methname)
            else:
                raise self.fatal("Second array member is not a valid method")
            if space.is_str(w_instance):
                clsname = space.str_w(w_instance)
                return self._getfunc_from_class(clsname, methname, w_this, contextclass)
            else:
                assert isinstance(w_instance, W_InstanceObject)
                try:
                    return w_instance.getmeth(
                        self.space, methname, contextclass)
                except VisibilityError:
                    self.fatal("Call to undefined method %s::%s()" %
                            (w_instance.klass.name, methname))
        else:
            self.fatal("Function name must be a string")


    def GETFUNC(self, bytecode, frame, space, arg, pc):
        w_name = frame.pop().deref()            
        func = self.getfunc(w_name, frame.w_this, frame.get_contextclass())
        assert func is not None
        frame.push(func)
        return pc

    def GETFUNC_NS(self, bytecode, frame, space, arg, pc):
        w_name = frame.pop().deref()
        name = space.str_w(w_name)
        w_base_name = frame.pop().deref()
        func = self.lookup_function(name)
        if func is None:
            func = self.getfunc(w_base_name, frame.w_this,
                    frame.get_contextclass())
        assert func is not None
        frame.push(func)
        return pc

    def GETCLASS(self, bytecode, frame, space, arg, pc):
        w_obj = frame.pop().deref()
        if isinstance(w_obj, W_InstanceObject):
            frame.push(w_obj.klass)
            return pc
        name = space.getclassintfname(w_obj)
        if arg:
            klass = self.locate_class_or_intf(name)
            klass.check_constructor_from_context(self, frame.get_contextclass())
        else:
            klass = self.lookup_class_or_intf(name, autoload=False)
            if klass is None:
                klass = space.w_Null
        frame.push(klass)
        return pc

    def getmeth(self, w_obj, name, contextclass=None):
        try:
            return w_obj.getmeth(self.space, name, contextclass)
        except VisibilityError as e:
            self.fatal(e.msg_fatal())

    def GETMETH(self, bytecode, frame, space, arg, pc):
        w_base = frame.pop_ptr().deref(self, give_notice=True)
        name = space.str_w(frame.pop())
        w_meth = self.getmeth(w_base, name,
                              contextclass=frame.get_contextclass())
        frame.push(w_meth)
        return pc

    def getstaticmeth(self, w_classname, methname, contextclass, w_this):
        if isinstance(w_classname, W_InstanceObject):
            thisclass = klass = w_classname.klass
        else:
            classname = self.space.str_w(w_classname)
            klass = self.locate_class_or_intf(classname)
            if is_constant_self_or_parent(classname):
                thisclass = self.get_current_thisclass()
            else:
                thisclass = klass
        if methname.lower() == '__construct':
            method = klass.constructor_method
            if method is None:
                self.fatal("Cannot call constructor")
            return method.bind(w_this, thisclass)
        try:
            method = klass.getstaticmeth(methname, contextclass, w_this, self)
        except VisibilityError as e:
            raise self.fatal(e.msg_fatal())
        return method.bind(w_this, thisclass)

    def GETSTATICMETH(self, bytecode, frame, space, arg, pc):
        w_meth = frame.pop()
        w_classname = frame.pop().deref()
        if not self.space.is_str(w_meth):
            raise self.fatal("Function name must be a string")
        else:
            methname = self.space.str_w(w_meth)
        w_meth = self.getstaticmeth(w_classname, methname,
                                    frame.get_contextclass(), frame.w_this)
        frame.push(w_meth)
        return pc

    def ARG_BY_VALUE(self, bytecode, frame, space, arg, pc):
        w_argument = frame.pop().deref()
        func = frame.pop()
        assert isinstance(func, AbstractFunction)
        if func.needs_ref(arg):
            raise self.fatal("Cannot pass parameter %d by reference"
                                 % (arg+1,))
        frame.push(w_argument)
        frame.push(func)
        return pc

    def ARG_BY_PTR(self, bytecode, frame, space, arg, pc):
        ptr_argument = frame.pop_ptr()
        func = frame.pop()
        assert isinstance(func, AbstractFunction)
        if func.needs_value(arg):
            w_argument = ptr_argument.deref(self, give_notice=True)
        else:
            if func.needs_ref(arg) and not ptr_argument.isref:
                space.ec.strict("Only variables should be passed by reference")
            w_argument = ptr_argument.get_ref(self)
        frame.push(w_argument)
        frame.push(func)
        return pc

    def call(self, callable, args_w):
        return callable.call_args(self, args_w)

    @jit.unroll_safe
    def CALL(self, bytecode, frame, space, arg, pc):
        func = frame.pop()
        args_w = [frame.peek_nth(arg - i - 1) for i in range(arg)]
        if isinstance(func, hippy.klass.W_BoundMethod):
            if func.method_func.name == '__clone':
                self.fatal("Cannot call __clone() method on "
                           "objects - use 'clone $obj' instead")
        w_res = self.call(func, args_w)
        frame.pop_n(arg)
        frame.push(w_res)
        return pc

    def GETITEM(self, bytecode, frame, space, arg, pc):
        w_item = frame.pop()
        w_obj = frame.pop()
        frame.push(space.getitem(w_obj, w_item, give_notice=True))
        return pc

    def GETITEM_NOPOP(self, bytecode, frame, space, arg, pc):
        w_item = frame.pop()
        w_obj = frame.peek()
        frame.push(space.getitem(w_obj, w_item, give_notice=True))
        return pc

    def GETITEM_VAR(self, bytecode, frame, space, arg, pc):
        w_item = frame.pop()
        w_obj = frame.lookup_variable_temp(arg)
        if w_obj is None:
            self.notice("Undefined variable: %s" % (
                bytecode.varnames[arg],))
            w_obj = space.w_Null
        frame.push(space.getitem(w_obj, w_item, give_notice=True))
        return pc

    def ITEM_PTR(self, bytecode, frame, space, arg, pc):
        p_base = frame.pop_ptr()
        w_item = frame.pop()
        p = pointer.ItemPointer(p_base, w_item)
        frame.push_ptr(p)
        return pc

    def APPEND_PTR(self, bytecode, frame, space, arg, pc):
        p_base = frame.pop_ptr()
        p = pointer.AppendPointer(p_base)
        frame.push_ptr(p)
        return pc

    def MAKE_REF_PTR(self, bytecode, frame, space, arg, pc):
        # this is only used by 'somefunc(new Aa)'
        w_obj = frame.pop()
        assert not isinstance(w_obj, W_Reference)
        p = pointer.CallResultPointer(W_Reference(w_obj))
        frame.push_ptr(p)
        return pc

    def BINARY_IS(self, bytecode, frame, space, arg, pc):
        w_right = frame.pop()
        w_left = frame.pop()
        frame.push(space.newbool(space.is_w(w_left, w_right)))
        return pc

    def BINARY_ISNOT(self, bytecode, frame, space, arg, pc):
        w_right = frame.pop()
        w_left = frame.pop()
        frame.push(space.newbool(not space.is_w(w_left, w_right)))
        return pc

    def IS_TRUE(self, bytecode, frame, space, arg, pc):
        frame.push(space.newbool(space.is_true(frame.pop())))
        return pc

    def DEREF(self, bytecode, frame, space, arg, pc):
        w_x = frame.pop()
        frame.push(w_x.deref())
        return pc

    @jit.unroll_safe
    def MAKE_ARRAY(self, bytecode, frame, space, arg, pc):
        args_w = [None] * arg
        for i in range(arg - 1, -1, -1):
            args_w[i] = frame.pop()
        frame.push(space.new_array_from_list(args_w))
        return pc

    @jit.unroll_safe
    def MAKE_HASH(self, bytecode, frame, space, arg, pc):
        args_w = [(None, None)] * arg
        for i in range(arg - 1, -1, -1):
            w_k = frame.pop()     # <= may be None
            w_v = frame.pop()
            args_w[i] = (w_k, w_v)
        frame.push(space.new_array_from_pairs(args_w))
        return pc

    def DECLARE_GLOBAL(self, bytecode, frame, space, arg, pc):
        name = bytecode.varnames[arg]
        w_ref = self.globals.get_var(space, name)
        frame.store_ref(arg, w_ref)
        return pc

    def DECLARE_GLOBAL_INDIRECT(self, bytecode, frame, space, arg, pc):
        w_name = frame.pop()
        name = space.str_w(w_name)
        r_global = self.globals.get_var(space, name)
        frame.set_ref_by_name(name, r_global)
        return pc

    def declare_func(self, func):
        name = func.name
        func_id = func.get_identifier()
        ldfunc = self.lookup_function(func_id)
        if ldfunc is not None:
            func = ldfunc
            if isinstance(func, Function):
                extra = ' (previously declared in %s:%d)' % (
                    func.bytecode.filename, func.bytecode.startlineno)
            else:
                extra = ''
            self.fatal("Cannot redeclare %s()%s" % (name, extra))
        self.space.global_function_cache.declare_new(func_id, func)

    def DECLARE_FUNC(self, bytecode, frame, space, arg, pc):
        func = bytecode.late_declarations[arg]
        self.declare_func(func)
        return pc

    def declare_class(self, cls_decl):
        assert isinstance(cls_decl, ClassDeclaration)
        name = cls_decl.name
        cls_id = cls_decl.get_identifier()
        if self._class_is_defined(cls_id):
            self.fatal("Cannot redeclare class %s" % name)
        if cls_id == 'self' or cls_id == 'parent':
            self.fatal("Cannot use '%s' as class name as it is reserved" %
                    name)
        self.create_class(cls_id, cls_decl)

    def DECLARE_CLASS(self, bytecode, frame, space, arg, pc):
        cls_decl = bytecode.late_declarations[arg]
        self.declare_class(cls_decl)
        return pc

    def LOAD_CLOSURE(self, bytecode, frame, space, arg, pc):
        func = bytecode.late_declarations[arg]
        w_res = new_closure(space, func, frame.w_this, static=False)
        frame.push(w_res)
        return pc

    def LOAD_STATIC_CLOSURE(self, bytecode, frame, space, arg, pc):
        func = bytecode.late_declarations[arg]
        w_res = new_closure(space, func, frame.w_this, static=True)
        frame.push(w_res)
        return pc

    @jit.unroll_safe
    def PUT_CLOSURE_VARS(self, bytecode, frame, space, arg, pc):
        w_closure = frame.peek_nth(arg)
        assert isinstance(w_closure, W_ClosureObject)
        args_w = [frame.pop() for i in range(arg)]
        w_closure.put_closure(args_w)
        return pc

    def CREATE_ITER(self, bytecode, frame, space, arg, pc):
        w_arr = frame.pop()
        contextclass = frame.get_contextclass()
        frame.push(space.create_iter(w_arr, contextclass=contextclass))
        return pc

    def CREATE_ITER_REF(self, bytecode, frame, space, arg, pc):
        r_array = frame.pop()
        contextclass = frame.get_contextclass()
        frame.push(space.create_iter_ref(r_array, contextclass=contextclass))
        return pc

    def NEXT_VALUE_ITER(self, bytecode, frame, space, arg, pc):
        w_iter = frame.peek()
        if w_iter is None:
            return arg
        assert isinstance(w_iter, W_BaseIterator)
        if w_iter.done():
            return arg
        w_value = w_iter.next(space)
        if w_value is None:
            return arg
        frame.push(w_value)
        return pc

    def NEXT_ITEM_ITER(self, bytecode, frame, space, arg, pc):
        w_iter = frame.peek()
        if w_iter is None:
            return arg
        assert isinstance(w_iter, W_BaseIterator)
        if w_iter.done():
            return arg
        w_key, w_value = w_iter.next_item(space)
        if w_value is None:
            return arg
        frame.push(w_key)
        frame.push(w_value)
        return pc

    def CAST_ARRAY(self, bytecode, frame, space, arg, pc):
        frame.push(space.as_array(frame.pop()))
        return pc

    def CAST_INT(self, bytecode, frame, space, arg, pc):
        frame.push(space.newint(space.int_w(frame.pop())))
        return pc

    def CAST_FLOAT(self, bytecode, frame, space, arg, pc):
        frame.push(space.newfloat(space.float_w(frame.pop())))
        return pc

    def CAST_STRING(self, bytecode, frame, space, arg, pc):
        frame.push(space.newstr(space.str_w(frame.pop())))
        return pc

    def CAST_OBJECT(self, bytecode, frame, space, arg, pc):
        frame.push(space.as_object(self, frame.pop().deref()))
        return pc

    def GETATTR(self, bytecode, frame, space, arg, pc):
        w_attr = frame.pop()
        w_obj = frame.pop().deref()
        try:
            frame.push(w_obj.getattr(self, space.str_w(w_attr),
                       contextclass= frame.get_contextclass(),
                       give_notice=True))
        except VisibilityError as e:
            self.fatal(e.msg_fatal())
        return pc

    def THIS_ATTR(self, bytecode, frame, space, arg, pc):
        w_attr = frame.pop()
        w_this = self.get_this(frame)
        try:
            frame.push(w_this.getattr(self, space.str_w(w_attr),
                                      contextclass= frame.get_contextclass(),
                                      give_notice=True))
        except VisibilityError as e:
            self.fatal(e.msg_fatal())
        return pc

    def ATTR_PTR(self, bytecode, frame, space, arg, pc):
        w_attr = frame.pop()
        p_base = frame.pop_ptr()
        p = pointer.AttrPointer(p_base, w_attr,
                                contextclass= frame.get_contextclass())
        frame.push_ptr(p)
        return pc

    def STATICMEMBER(self, bytecode, frame, space, arg, pc):
        membername = space.str_w(frame.pop())
        classname = space.str_w(frame.pop())
        klass = self.locate_class_or_intf(classname)
        p = pointer.StaticMemberPointer(klass, membername,
                                         frame.get_contextclass())
        frame.push(p.deref(self))
        return pc

    def STATICMEMBER_PTR(self, bytecode, frame, space, arg, pc):
        membername = space.str_w(frame.pop())
        classname = space.str_w(frame.pop())
        klass = self.locate_class_or_intf(classname)
        p = pointer.StaticMemberPointer(klass, membername,
                                         frame.get_contextclass())
        frame.push_ptr(p)
        return pc

    def CLASSCONST(self, bytecode, frame, space, arg, pc):
        classname = space.str_w(frame.pop())
        klass = self.locate_class_or_intf(classname)
        name = bytecode.names[arg]
        w_obj = klass.lookup_w_constant(space, name)
        if w_obj is None:
            self.fatal("Undefined class constant '%s'" % name)
        frame.push(w_obj)
        return pc

    def ABSTRACT_METHOD(self, bytecode, frame, space, arg, pc):
        raise self.fatal("Cannot call abstract method %s::%s()" % (
             frame.get_contextclass().name,
            bytecode.name))

    def CLONE(self, bytecode, frame, space, arg, pc):
        w_obj = frame.pop().deref()
        w_result = w_obj.clone(self, contextclass= frame.get_contextclass())
        frame.push(w_result)
        return pc

    def SILENCE(self, bytecode, frame, space, arg, pc):
        frame.catch_blocks.append(Unsilence(self.error_level))
        self.error_level = 0
        return pc

    def UNSILENCE(self, bytecode, frame, space, arg, pc):
        block = frame.catch_blocks.pop()
        assert isinstance(block, Unsilence), "Mismatched SILENCE/UNSILENCE"
        if self.error_level == 0:
            self.error_level = block.prev_level
        return pc

    def LOGICAL_XOR(self, bytecode, frame, space, arg, pc):
        right = space.is_true(frame.pop())
        left = space.is_true(frame.pop())
        frame.push(space.newbool(left ^ right))
        return pc

    def _CHECKSTACK(self, bytecode, frame, space, arg, pc):
        # debugging
        assert frame.stackpos == arg
        assert frame.ptrs is None
        return pc

    def BREAK_CONTINUE_POP(self, bytecode, frame, space, arg, pc):
        frame.pop_n(arg)
        return pc

    def _fail_typehint(self, frame, space, arg, expecting, w_obj):
        given = space.gettypename(w_obj)
        parentframe = frame.f_backref()
        if parentframe is not None:
            filename, funcname, line = parentframe.get_position()
            caller_location = ', called in %s on line %d and defined' % (
                filename, line)
        else:
            caller_location = ''
        self.catchable_fatal("Argument %d passed to %s() must %s, %s given%s"
                % (arg + 1, frame.context.get_fullname(), expecting,
                    given, caller_location))

    def TYPEHINT_CLASS(self, bytecode, frame, space, arg, pc):
        w_name = frame.pop()
        argnum = arg >> 1
        assert argnum >= 0
        w_obj = frame.lookup_deref_temp(argnum)
        if (arg & 1) and w_obj is space.w_Null:
            return pc
        assert isinstance(w_name, W_StringObject)
        name = w_name.unwrap()

        if self._class_is_defined(name):
            cls = self._class_get(name)
            assert cls is not None
        else:
            cls = None

        if cls is not None and cls.is_interface():
            msg = "implement interface "
        else:
            msg = "be an instance of "
        if (not space.is_object(w_obj)
                  or not space.instanceof_w(w_obj, w_name)):
            self._fail_typehint(frame, space, argnum, msg + name, w_obj)
        return pc

    def TYPEHINT_ARRAY(self, bytecode, frame, space, arg, pc):
        argnum = arg >> 1
        assert argnum >= 0
        w_obj = frame.lookup_deref_temp(argnum)
        if (arg & 1) and w_obj is space.w_Null:
            pass
        elif not space.is_array(w_obj):
            self._fail_typehint(frame, space, argnum,
                                "be of the type array", w_obj)
        return pc

    def _report_include_warning(self, frame, func_name, fname, exc, require):
        self.warn('%s(%s): failed to open stream: %s' %
                           (func_name, fname, os.strerror(exc.errno)))
        path = ':'.join(self.include_path)
        if require:
            raise self.fatal("%s(): Failed opening required '%s' "
                    "(include_path=%s)" % (func_name, fname, path))
        else:
            self.warn("%s(): Failed opening '%s' for inclusion "
                    "(include_path='%s')" % (func_name, fname, path))
            frame.push(self.space.w_False)
            return

    def find_file(self, fname):
        """Resolve a file name relative to the include_path and to
        the location of the current code"""
        for path in self.include_path:
            if exists(join(path, [fname])):
                return abspath(join(path, [fname]))
        code_dir = dirname(self.get_frame().bytecode.filename)
        if exists(join(code_dir, [fname])):
            return abspath(join(code_dir, [fname]))
        return abspath(fname)

    def _include(self, frame, func_name, require=False, once=False):
        name = self.space.str_w(frame.pop())
        use_path = not (name.startswith('/') or name.startswith('./') or
                        name.startswith('../'))
        if use_path:
            fname = self.find_file(name)
        else:
            fname = abspath(name)
        if once is True and fname in self.cached_files:
            frame.push(self.space.newint(1))
            return
        try:
            bc = self.compile_file(fname)
        except OSError as exc:
            self._report_include_warning(frame, func_name, name, exc,
                                         require)
            return
        except IOError as exc:
            if not we_are_translated():
                self._report_include_warning(frame, func_name, name, exc,
                                             require)
                return
            assert False # dead code
        w_result = self.run_include(bc, frame)
        frame.push(w_result)

    def REQUIRE(self, bytecode, frame, space, arg, pc):
        self._include(frame, 'require', require=True, once=False)
        return pc

    def REQUIRE_ONCE(self, bytecode, frame, space, arg, pc):
        self._include(frame, 'require_once', require=True, once=True)
        return pc

    def INCLUDE(self, bytecode, frame, space, arg, pc):
        self._include(frame, 'include', require=False, once=False)
        return pc

    def INCLUDE_ONCE(self, bytecode, frame, space, arg, pc):
        self._include(frame, 'include_once', require=False, once=True)
        return pc

    def PUSH_CATCH_BLOCK(self, bytecode, frame, space, arg, pc):
        class_name = space.str_w(frame.pop())
        frame.catch_blocks.append(CatchBlock(class_name, arg, frame.stackpos))
        return pc

    def DUMMY_STACK_PUSH(self, bytecode, frame, space, arg, pc):
        return pc

    @jit.unroll_safe
    def handle_exception(self, frame, exc):
        while frame.catch_blocks:
            block = frame.catch_blocks.pop()
            result = block.handle(exc.w_exc, frame)
            if result != -1:
                return result
        raise exc

    def THROW(self, bytecode, frame, space, arg, pc):
        w_exc = frame.pop().deref()
        if not isinstance(w_exc, W_ExceptionObject):
            self.fatal("Exceptions must be valid objects derived from "
                    "the Exception base class")
        raise PHPException(w_exc)

    def POPEN(self, bytecode, frame, space, arg, pc):
        cmd = space.str_w(frame.pop().deref())
        r_pfile = create_popen_file(cmd, 'r')
        res = r_pfile.read(-1)
        frame.push(space.wrap(res))
        return pc

    def EVAL(self, bytecode, frame, space, arg, pc):
        code = space.str_w(frame.pop().deref())
        source = "<? %s ?>" % code
        fname = "%s(%s) : eval()'d code" % (bytecode.filename, arg)
        bc = compile_php(fname, source, space)
        w_res = self.run_local_include(bc, self.get_frame())
        if not w_res:
            frame.push(space.w_Null)
        else:
            frame.push(w_res)
        return pc


def _new_binop(name):
    def BINARY(self, bytecode, frame, space, arg, pc):
        w_right = frame.pop().deref()
        w_left = frame.pop().deref()
        frame.push(getattr(space, name)(w_left, w_right))
        return pc

    new_name = 'BINARY_' + name.upper()
    BINARY.func_name = new_name
    return new_name, BINARY

for _name in BINOP_LIST + BINOP_BITWISE + ['concat', 'instanceof',
                                           'lshift', 'rshift']:
    setattr(Interpreter, *_new_binop(_name))

unrolling_bc = unrolling_iterable(enumerate(BYTECODE_NAMES))
