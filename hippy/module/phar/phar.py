from hippy.module.spl.spl import W_RecursiveDirectoryIterator

class W_Phar(W_RecursiveDirectoryIterator):
    pass

PharClass = def_class(
    'Phar',
    [],     # Methods
    implements=['Countable', 'ArrayAccess'],
    instance_class=W_Phar,
    extends='RecursiveDirectoryIterator',)
