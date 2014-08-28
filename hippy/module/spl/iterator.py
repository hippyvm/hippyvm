from hippy.klass import def_class
from hippy.builtin import ExitFunctionWithError, wrap_method
from hippy.module.spl.interface import k_OuterIterator


@wrap_method(['interp', 'this'], name='IteratorIterator::current')
def ii_current(interp, this):
    raise ExitFunctionWithError('Not yet implemented in hippy')

@wrap_method(['interp', 'this'], name='IteratorIterator::getInnerIterator')
def ii_getInnerIterator(interp, this):
    raise ExitFunctionWithError('Not yet implemented in hippy')

@wrap_method(['interp', 'this'], name='IteratorIterator::key')
def ii_key(interp, this):
    raise ExitFunctionWithError('Not yet implemented in hippy')

@wrap_method(['interp', 'this'], name='IteratorIterator::next')
def ii_next(interp, this):
    raise ExitFunctionWithError('Not yet implemented in hippy')

@wrap_method(['interp', 'this'], name='IteratorIterator::rewind')
def ii_rewind(interp, this):
    raise ExitFunctionWithError('Not yet implemented in hippy')

@wrap_method(['interp', 'this'], name='IteratorIterator::valid')
def ii_valid(interp, this):
    raise ExitFunctionWithError('Not yet implemented in hippy')

k_IteratorIterator = def_class(
    'IteratorIterator',
    [ii_current, ii_getInnerIterator, ii_key, ii_next, ii_rewind, ii_valid],
    implements=[k_OuterIterator])
