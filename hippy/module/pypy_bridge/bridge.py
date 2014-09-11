from hippy.builtin import wrap, Optional, wrap_method, ThisUnwrapper
from hippy.objects.base import W_Root as Wph_Root
from hippy.objects.instanceobject import W_InstanceObject
from hippy.klass import def_class, Method
from hippy.module.pypy_bridge.scopes import PHP_Scope
from hippy.module.pypy_bridge.php_wrappers import (
        W_EmbeddedPyFunc, new_embedded_py_func_lexical)
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
from pypy.objspace.std import StdObjSpace
from pypy.interpreter.argument import Arguments
from pypy.module.__builtin__ import compiling as py_compiling

from rpython.rlib import jit

# XXX broken
# All bridge errors will raise a PyPyException back up to PHP
k_PyPyException = def_class('PyPyException',
        [], extends=k_Exception, instance_class=W_ExceptionObject)

@wrap(['interp', str, str], name='embed_py_mod')
def embed_py_mod(interp, mod_name, mod_source):
    phspace = interp.space

    # create a new Python module in which to inject code
    wpy_mod_name = interp.pyspace.wrap(mod_name)
    wpy_module = Module(interp.pyspace, wpy_mod_name)

    # Register it in sys.modules
    wpy_sys_modules = interp.pyspace.sys.get('modules')
    interp.pyspace.setitem(wpy_sys_modules, wpy_mod_name, wpy_module)

    # Inject code into the fresh module
    # Get php file name in place of XXX
    pycompiler = interp.pyspace.createcompiler() # XXX use just one
    code = pycompiler.compile(mod_source, 'XXX', 'exec', 0)
    code.exec_code(interp.pyspace, wpy_module.w_dict,wpy_module.w_dict)

    return wpy_module.to_php(interp)

def _compile_py_func_from_string(interp, func_source):
    """ compiles a string returning a <name, func> pair """

    pyspace = interp.pyspace

    # compile the user's code
    wpy_code = py_compiling.compile(
            pyspace, pyspace.wrap(func_source), "<string>", "exec")

    # Eval it into a dict
    wpy_fake_locals = pyspace.newdict()
    py_compiling.eval(pyspace, wpy_code, pyspace.newdict(), wpy_fake_locals)

    # Extract the users function from the dict
    wpy_keys = wpy_fake_locals.descr_keys(pyspace)
    wpy_vals = wpy_fake_locals.descr_values(pyspace)

    wpy_zero = pyspace.wrap(0)
    wpy_func_name = pyspace.getitem(wpy_keys, wpy_zero)
    wpy_func = pyspace.getitem(wpy_vals, wpy_zero)

    # The user should have defined one function.
    assert pyspace.int_w(pyspace.len(wpy_keys)) == 1
    assert isinstance(wpy_func, Py_Function)

    ph_frame = interp.get_frame()
    wpy_func.php_scope = PHP_Scope(interp, ph_frame)

    return wpy_func_name, wpy_func

@wrap(['interp', str], name='embed_py_func')
def embed_py_func(interp, func_source):
    phspace, pyspace = interp.space, interp.pyspace

    # Compile
    wpy_func_name, wpy_func = _compile_py_func_from_string( interp, func_source)

    # Masquerade it as a PHP function.
    func_name = pyspace.str_w(wpy_func_name)
    ph_func = W_EmbeddedPyFunc(interp, wpy_func)
    phspace.global_function_cache.declare_new(func_name, ph_func)

@wrap(['interp', str], name='embed_py_func_lexical')
def embed_py_func_lexical(interp, func_source):
    phspace, pyspace = interp.space, interp.pyspace

    # Compile
    wpy_func_name, wpy_func = _compile_py_func_from_string(interp, func_source)

    # Masquerade it as a PHP function.
    #func_name = pyspace.str_w(wpy_func_name)
    #ph_func = W_EmbeddedPyFunc(interp, wpy_func)
    #phspace.global_function_cache.declare_new(func_name, ph_func)
    return new_embedded_py_func_lexical(interp, wpy_func)

@wrap(['interp', str], name='import_py_mod')
def import_py_mod(interp, modname):
    pyspace = interp.pyspace

    assert not pyspace.config.objspace.honor__builtins__

    w_import = pyspace.builtin.getdictvalue(pyspace, '__import__')
    if w_import is None:
        raise OperationError(pyspace.w_ImportError,
                             pyspace.wrap("__import__ not found"))

    w_modname = pyspace.wrap(modname)
    w_obj = pyspace.call_function(w_import, w_modname, pyspace.w_None,
                                  pyspace.w_None, pyspace.wrap(modname.split(".")[-1]))

    return w_obj.to_php(interp)
