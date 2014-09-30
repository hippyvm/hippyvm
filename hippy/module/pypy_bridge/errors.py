from pypy.interpreter.error import OperationError

def raise_python_bridge_error(interp, msg):
    """ Raises BridgeError in Python """
    py_space = interp.py_space
    wpy_bridge_error = py_space.builtin.get("BridgeError")
    raise OperationError(wpy_bridge_error, py_space.wrap(msg))
