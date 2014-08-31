"""Interfaces defined by the SPL extension"""

from hippy import consts
from hippy.klass import def_class
from hippy.builtin_klass import new_abstract_method, k_Iterator

k_SeekableIterator = def_class('SeekableIterator',
    [new_abstract_method(["interp"], name="SeekableIterator::seek")],
    flags=consts.ACC_INTERFACE | consts.ACC_ABSTRACT, extends=k_Iterator)


k_RecursiveIterator = def_class('RecursiveIterator',
    [new_abstract_method(["interp"], name="RecursiveIterator::hasChildren"),
     new_abstract_method(["interp"], name="RecursiveIterator::getChildren")],
    flags=consts.ACC_INTERFACE | consts.ACC_ABSTRACT, extends=k_Iterator)


def_class('Countable',
    [new_abstract_method(["interp"], name="Countable::count")],
    flags=consts.ACC_INTERFACE | consts.ACC_ABSTRACT)
