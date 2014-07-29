from pypy.interpreter.error import OperationError

def raise_python_bridge_error(interp, msg):
    """ Raises BridgeError in Python """
    pyspace = interp.pyspace
    wpy_bridge_error = pyspace.builtin.get("BridgeError")
    raise OperationError(wpy_bridge_error, pyspace.wrap(msg))
