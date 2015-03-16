from hippy.builtin import wrap, Optional, wrap_method, ThisUnwrapper
from hippy.objects.base import W_Root as W_PHP_Root
from hippy.objects.instanceobject import W_InstanceObject
from hippy.objects.strobject import W_StringObject
from hippy.objects.arrayobject import W_ArrayObject
from hippy.module.pypy_bridge.scopes import PHP_Scope, Py_Scope
from hippy.module.pypy_bridge.util import _raise_php_bridgeexception
from hippy.module.pypy_bridge.py_adapters import (
        new_embedded_py_func, k_BridgeException, W_PyFuncGlobalAdapter,
        W_PyMethodFuncAdapter, W_PyFuncAdapter)
from hippy.builtin_klass import k_Exception, W_ExceptionObject
from hippy.error import PHPException, VisibilityError

from pypy.module.sys.version import CPYTHON_VERSION, PYPY_VERSION
from pypy.config.pypyoption import get_pypy_config
from pypy.tool.option import make_objspace, make_config
from pypy.interpreter.module import Module
from pypy.interpreter.error import OperationError
from pypy.interpreter.typedef import TypeDef
from pypy.interpreter.gateway import interp2app, unwrap_spec
from pypy.interpreter.baseobjspace import W_Root as Wpy_Root
from pypy.interpreter.function import Function as Py_Function
from pypy.interpreter.argument import Arguments
from pypy.module.__builtin__ import compiling as py_compiling

from rpython.rlib import jit

@wrap(['interp', str, str], name='embed_py_mod')
def embed_py_mod(interp, mod_name, mod_source):
    php_space = interp.space

    # create a new Python module in which to inject code
    w_py_mod_name = interp.py_space.wrap(mod_name)
    w_py_module = Module(interp.py_space, w_py_mod_name)

    # Register it in sys.modules
    w_py_sys_modules = interp.py_space.sys.get('modules')
    interp.py_space.setitem(w_py_sys_modules, w_py_mod_name, w_py_module)

    # Inject code into the fresh module
    # Get php file name in place of XXX
    pycompiler = interp.py_space.createcompiler() # XXX use just one
    code = pycompiler.compile(mod_source, 'XXX', 'exec', 0)
    code.exec_code(interp.py_space, w_py_module.w_dict,w_py_module.w_dict)

    return w_py_module.to_php(interp)

class PyCodeCacheVersion(object): pass

class PyCodeCache(object):

    _immutable_fields_ = ["cache"]

    def __init__(self):
        # maps: func_source -> pycode
        self.cache = {}
        self.version = PyCodeCacheVersion()

    @jit.elidable_promote()
    def _read(self, func_source, version):
        return self.cache.get(func_source, None)

    def read(self, func_source):
        return self._read(func_source, self.version)

    def update(self, func_source, pycode):
        self.cache[func_source] = pycode
        self.version = PyCodeCacheVersion()

PYCODE_CACHE = PyCodeCache()

def _compile_py_func_from_string_cached(interp, func_source):
    py_space = interp.py_space

    w_py_code = PYCODE_CACHE.read(func_source)
    if w_py_code is None:
        try:
            w_py_code = py_compiling.compile(
                    py_space, py_space.wrap(func_source), "<string>", "exec")
        except OperationError as e:
            e.normalize_exception(py_space)
            _raise_php_bridgeexception(interp,
                                       "Failed to compile Python code: %s" %
                                       e.errorstr(py_space))

        PYCODE_CACHE.update(func_source, w_py_code)

    return w_py_code

def _compile_py_func_from_string(
        interp, func_source, parent_php_scope):
    """ compiles a string returning a <name, func> pair """

    py_space = interp.py_space

    w_py_code = _compile_py_func_from_string_cached(interp, func_source)

    # Eval it into a dict
    w_py_fake_locals = py_space.newdict()
    py_compiling.eval(py_space, w_py_code, py_space.newdict(), w_py_fake_locals)

    # Extract the users function from the dict
    w_py_keys = w_py_fake_locals.descr_keys(py_space)
    w_py_vals = w_py_fake_locals.descr_values(py_space)

    w_py_zero = py_space.wrap(0)
    w_py_func_name = py_space.getitem(w_py_keys, w_py_zero)
    w_py_func = py_space.getitem(w_py_vals, w_py_zero)

    # The user should have defined one function.
    if py_space.int_w(py_space.len(w_py_keys)) != 1 or \
            not isinstance(w_py_func, Py_Function):
        _raise_php_bridgeexception(interp,
                "embed_py_func: Python source must define exactly one function")

    # inject parent scope (which may well be None)
    w_py_func.php_scope = PHP_Scope(interp, parent_php_scope)

    return w_py_func_name, w_py_func

@wrap(['interp', str], name='embed_py_func')
def embed_py_func(interp, func_source):
    """Embeds a python function returning a callable PHP instance.
    Lexical scope *is* associated"""
    php_space, py_space = interp.space, interp.py_space

    # Compile
    php_frame = interp.get_frame()
    w_py_func_name, w_py_func = _compile_py_func_from_string(
            interp, func_source, php_frame)

    # make a callable instance a bit like a closure
    return new_embedded_py_func(interp, w_py_func)

@wrap(['interp', str], name='embed_py_func_global')
def embed_py_func_global(interp, func_source):
    """Puts a python function into the global function cache.
    no lexical scope is associated, thus mimicking the behaviour of
    a standard php function. to embed a python function with scope,
    use instead embed_py_func()"""

    php_space, py_space = interp.space, interp.py_space

    # Compile (note *no* parent PHP frame passed)
    w_py_func_name, w_py_func = \
            _compile_py_func_from_string(interp,
                                         func_source, interp.global_frame)

    # Masquerade it as a PHP function in the global function cache
    w_php_func = W_PyFuncGlobalAdapter(interp, w_py_func)
    php_space.global_function_cache.declare_new(py_space.str_w(w_py_func_name), w_php_func)

from hippy.builtin import Optional
@wrap(['interp', str, str], name='embed_py_meth')
def embed_py_meth(interp, class_name, func_source):
    """Inject a Python method into a PHP class.
    Here a Python method is a function accepting self as the first arg.
    """
    php_space, py_space = interp.space, interp.py_space

    php_frame = interp.get_frame()
    w_py_func_name, w_py_func = \
            _compile_py_func_from_string(interp, func_source, php_frame)
    w_php_func = W_PyMethodFuncAdapter(interp, w_py_func)

    w_php_class = interp.lookup_class_or_intf(class_name, autoload=True)
    if w_php_class is None:
        assert False # XXX

    w_php_class.embed_py_meth(py_space.str_w(w_py_func_name), w_php_func)

@wrap(['interp', str], name='import_py_mod')
def import_py_mod(interp, modname):
    py_space = interp.py_space

    assert not py_space.config.objspace.honor__builtins__

    w_import = py_space.builtin.getdictvalue(py_space, '__import__')
    if w_import is None:
        raise OperationError(py_space.w_ImportError,
                             py_space.wrap("__import__ not found"))

    w_modname = py_space.wrap(modname)
    try:
        w_obj = py_space.call_function(w_import, w_modname, py_space.w_None,
                py_space.w_None, py_space.wrap(modname.split(".")[-1]))
    except OperationError as e: # import failed, pass exn up to PHP
        e.normalize_exception(py_space)
        w_py_exn = e.get_w_value(py_space)
        w_php_exn = w_py_exn.to_php(interp)
        from hippy.error import Throw
        raise Throw(w_php_exn)

    return w_obj.to_php(interp)

def _find_static_py_meth(interp, class_name, meth_name):
    # first look in PHP scope for a class of this name
    kls = interp.lookup_class_or_intf(class_name)
    if kls is not None:
        ctx_kls = interp.get_contextclass()
        meth = kls.locate_static_method(meth_name, ctx_kls, True)
        if meth is None or not isinstance(meth.method_func, W_PyMethodFuncAdapter):
            return None
        else:
            return meth.method_func.get_wrapped_py_obj()
    else:
        # otherwise we have to search lexical scopes upwards for the class
        py_scope = interp.get_current_bytecode().py_scope
        if py_scope is not None:
            from pypy.objspace.std.typeobject import W_TypeObject
            kls = py_scope.py_lookup(class_name)
            if kls is None:
                return None
            elif isinstance(kls, W_TypeObject):
                meth = kls.lookup(meth_name)
                from pypy.interpreter.function import StaticMethod
                if isinstance(meth, StaticMethod):
                    w_py_func = meth.w_function
                    assert isinstance(w_py_func, Py_Function)
                    return w_py_func
                else:
                    return None
            else:
                # should not be reachable.
                # If there was a PHP class we would have found it in the
                # first case.
                assert False

# XXX call_py_func isn't optimised, and isn't currently traceable.
@wrap(['interp', W_PHP_Root, W_PHP_Root, W_PHP_Root], name='call_py_func')
def call_py_func(interp, w_func_or_w_name, w_args, w_kwargs):
    """Calls a Python function with kwargs.

    call_py_func($target, $args, $kwargs);

    Where:
    $target -- what to call
    $args -- positional args
    $kwargs -- keyword args

    Interface is similar to call_user_func in PHP, so the following are all valid:
    call_py_func("myfunc", ...)
    call_py_func($my_callable, ...)
    call_py_func("MyClass::my_static_meth", ...)
    call_py_func(["MyClass", "my_static_meth"], ...)
    call_py_func([$my_inst, "my_meth"], ...)
    """
    py_space, php_space = interp.py_space, interp.space
    w_self = []
    w_py_func = None

    if isinstance(w_func_or_w_name, W_StringObject):
        # either a function or static method
        name = php_space.str_w(w_func_or_w_name)
        if "::" in name:
            # static method call
            class_name, meth_name = name.split("::")
            w_py_func = _find_static_py_meth(interp, class_name, meth_name)
        else:
            # named (global) function call
            w_php_func = interp.locate_function(php_space.str_w(w_func_or_w_name))
            if not isinstance(w_php_func, W_PyFuncGlobalAdapter):
                w_py_func = None
            else:
                w_py_func = w_php_func.get_wrapped_py_obj()
    elif isinstance(w_func_or_w_name, W_ArrayObject):
        # static or dynamic method call
        if w_func_or_w_name.arraylen() != 2:
            _raise_php_bridgeexception(interp,
                "When passing an array to call_py_func, len must be 2")
        elems = w_func_or_w_name.as_list_w()
        w_class_name_or_inst, w_meth_name = elems[0], elems[1]
        if not isinstance(w_meth_name, W_StringObject):
            _raise_php_bridgeexception(interp, "method name should be a string")
        meth_name = php_space.str_w(w_meth_name)
        if isinstance(w_class_name_or_inst, W_StringObject):
            # static method call
            class_name = php_space.str_w(w_class_name_or_inst)
            w_py_func = _find_static_py_meth(interp, class_name, meth_name)
        else:
            # dynamic method call
            ctx_kls = interp.get_contextclass()
            try:
                w_py_meth = w_class_name_or_inst.getmeth(php_space, meth_name, ctx_kls)
            except VisibilityError:
                w_py_meth = None

            if w_py_meth is None:
                w_py_func = None
            else:
                from hippy.klass import W_BoundMethod
                assert isinstance(w_py_meth, W_BoundMethod)
                w_method_func = w_py_meth.method_func
                assert isinstance(w_method_func, W_PyMethodFuncAdapter)
                w_py_func = w_method_func.get_wrapped_py_obj()
                w_self = [w_class_name_or_inst.to_py(interp)]
    elif isinstance(w_func_or_w_name, W_PyFuncAdapter):
        # a callable python instance object
        w_py_func = w_func_or_w_name.w_py_func
    else:
        _raise_php_bridgeexception(interp, "Invalid argument to call_py_func")

    assert w_py_func is None or isinstance(w_py_func, Py_Function)
    if w_py_func is None:
        _raise_php_bridgeexception(interp, "Failed to find Python function or method")
    else:
        # we now have something callable, next perform the call
        w_py_args = w_self + [x.to_py(interp) for x in w_args.as_list_w()]

        w_kw_pairs = w_kwargs.as_pair_list(php_space)
        w_py_keywords = []
        w_py_keywords_w = []
        for pair in w_kw_pairs:
            w_k, w_v = pair
            if not isinstance(w_k, W_StringObject):
                _raise_php_bridgeexception(interp, "Python kwargs must have string keys")
            w_py_keywords.append(php_space.str_w(w_k))
            w_py_keywords_w.append(w_v.to_py(interp))

        args = Arguments(py_space, w_py_args, keywords=w_py_keywords, keywords_w=w_py_keywords_w)
        w_py_rv = w_py_func.call_args(args)
        return w_py_rv.to_php(interp)
