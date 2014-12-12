from hippy.builtin import wrap, Optional, wrap_method, ThisUnwrapper
from hippy.objects.base import W_Root as Wph_Root
from hippy.objects.instanceobject import W_InstanceObject
from hippy.module.pypy_bridge.scopes import PHP_Scope
from hippy.module.pypy_bridge.util import _raise_php_bridgeexception
from hippy.module.pypy_bridge.py_adapters import (
        new_embedded_py_func, k_BridgeException, W_PyFuncGlobalAdapter,
        W_PyMethodFuncAdapter)
from hippy.builtin_klass import k_Exception, W_ExceptionObject
from hippy.error import PHPException

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

def _compile_py_func_from_string(
        interp, func_source, parent_php_scope=None):
    """ compiles a string returning a <name, func> pair """

    py_space = interp.py_space

    # compile the user's code
    w_py_code = py_compiling.compile(
            py_space, py_space.wrap(func_source), "<string>", "exec")

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
            _compile_py_func_from_string(interp, func_source)

    # Masquerade it as a PHP function in the global function cache
    w_php_func = W_PyFuncGlobalAdapter(w_py_func)
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
    w_php_func = W_PyMethodFuncAdapter(w_py_func)

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
