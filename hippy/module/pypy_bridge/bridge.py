from hippy.builtin import wrap, Optional, wrap_method, ThisUnwrapper
from hippy.objects.base import W_Root as Wph_Root
from hippy.objects.instanceobject import W_InstanceObject
from hippy.klass import def_class, Method
from hippy.module.pypy_bridge.scopes import PHP_Scope
from hippy.module.pypy_bridge.util import _raise_php_bridgeexception
from hippy.module.pypy_bridge.py_adapters import (
        new_embedded_py_func, k_BridgeException)
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

# XXX broken
# All bridge errors will raise a PyPyException back up to PHP
k_PyPyException = def_class('PyPyException',
        [], extends=k_Exception, instance_class=W_ExceptionObject)

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

def _compile_py_func_from_string(interp, func_source):
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

    ph_frame = interp.get_frame()
    w_py_func.php_scope = PHP_Scope(interp, ph_frame)

    return w_py_func_name, w_py_func

@wrap(['interp', str], name='embed_py_func')
def embed_py_func(interp, func_source):
    php_space, py_space = interp.space, interp.py_space

    # Compile
    w_py_func_name, w_py_func = _compile_py_func_from_string(interp, func_source)

    # Masquerade it as a PHP function.
    return new_embedded_py_func(interp, w_py_func)

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
