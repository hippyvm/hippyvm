from hippy.klass import def_class
from hippy.builtin_klass import k_Exception

k_LogicException = def_class('LogicException', [], extends=k_Exception)
k_BadFunctionCallException = def_class('BadFunctionCallException', [],
                                       extends=k_LogicException)
k_BadMethodCallException = def_class('BadMethodCallException', [],
                                     extends=k_BadFunctionCallException)
k_InvalidArgumentException = def_class('InvalidArgumentException', [],
                                       extends=k_BadFunctionCallException)
k_DomainException = def_class('DomainException', [], extends=k_LogicException)
k_RuntimeException = def_class('RuntimeException', [], extends=k_Exception)
k_UnexpectedValueException = def_class('UnexpectedValueException', [],
                                       extends=k_RuntimeException)
