from hippy.klass import def_class
from hippy.builtin_klass import k_Exception

k_LogicException = def_class('LogicException', [], extends=k_Exception)
k_BadFunctionCallException = def_class('BadFunctionCallException', [],
                                       extends=k_LogicException)
k_BadMethodCallException = def_class('BadMethodCallException', [],
                                     extends=k_BadFunctionCallException)
