from hippy.klass import def_class
from hippy.builtin_klass import k_Exception, W_ExceptionObject


k_ReflectionException = def_class(
    'ReflectionException',
    [],
    extends=k_Exception,
    instance_class=W_ExceptionObject
)
