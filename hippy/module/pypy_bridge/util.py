from pypy.interpreter.error import OperationError

from hippy.module.pypy_bridge.php_wrappers import k_BridgeException

def _raise_py_bridgeerror(py_space, msg):
    w_bridgeerror = py_space.builtin.get("BridgeError")
    raise OperationError(w_bridgeerror, py_space.wrap(msg))

def _raise_php_bridgeexception(interp, msg):
    w_php_exn = k_BridgeException.call_args(interp, [interp.space.wrap(msg)])
    from hippy.error import Throw
    raise Throw(w_php_exn)
