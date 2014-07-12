import sys

from rpython.rtyper.lltypesystem import lltype, rffi

from hippy import consts
from hippy.builtin import wrap_method, Optional, ThisUnwrapper
from hippy.builtin import StringArg
from hippy.builtin import LongArg
from hippy.builtin import InstanceUnwrapper, handle_as_exception
from hippy.klass import def_class
from hippy.objspace import getspace

from hippy.module.date import timelib
from hippy.module.date import W_DateTimeZone, W_DateTime
from hippy.module.date import common




@wrap_method(['interp', ThisUnwrapper(W_DateTimeZone), StringArg()],
             name='DateTimeZone::__construct', error_handler=handle_as_exception)
def construct(interp, this, timezone_name):
    common.initialize_timezone(interp, "DateTimeZone::__construct", this, timezone_name)


@wrap_method(['space', ThisUnwrapper(W_DateTimeZone)],
             name='DateTimeZone::getName', error=False)
def get_name(space, this):
    return space.wrap(this.timezone_info.get_name())


@wrap_method(['interp', ThisUnwrapper(W_DateTimeZone),
              InstanceUnwrapper(W_DateTime, 'DateTime', null=False)],
             name='DateTimeZone::getOffset', error=False)
def get_offset(interp, this, w_datetime):
    return common.timezone_offset_get(interp, this, w_datetime)


def _abbreviations_list(space):
    res = timelib.timezone_abbreviations_list()
    results = []
    for k, v in res.items():
        i = 0
        w_arr_x = []
        for t, o, f in v:
            w_arr_x.append((
                space.wrap(i),
                space.new_array_from_pairs([
                    (space.wrap("dst"), space.newbool(t)),
                    (space.wrap("offset"), space.wrap(int(o))),
                    (space.wrap("timezone_id"), space.wrap(f))
                ])
            ))
            i += 1
        results.append((space.wrap(k), space.new_array_from_pairs(w_arr_x)))
    return space.new_array_from_pairs(results)


@wrap_method(['space'], name='DateTimeZone::listAbbreviations',
             flags=consts.ACC_STATIC)
def list_abbreviations(space):
    return _abbreviations_list(space)


@wrap_method(['space', Optional(LongArg(None)), Optional(StringArg(None))],
             name='DateTimeZone::listIdentifiers', flags=consts.ACC_STATIC)
def identifiers_list(space, what=2047, country=None):
    return common.timezone_identifiers_list(space, what, country)


@wrap_method(['interp', ThisUnwrapper(W_DateTimeZone), Optional(int), Optional(int)],
             name='DateTimeZone::getTransitions', error=False)
def get_transition(interp, this,
                   timestamp_begin=-sys.maxint - 1,
                   timestamp_end=sys.maxint):

    return common.timezone_transitions_get(
        interp, this, timestamp_begin, timestamp_end)

@wrap_method(['interp', ThisUnwrapper(W_DateTimeZone)],
             name='DateTimeZone::getLocation')
def get_location(interp, this):
    return common.timezone_location_get(interp, this)


space = getspace()

k_DateTimeZone = def_class(
    'DateTimeZone',

    [construct,
     get_name,
     get_offset,
     list_abbreviations,
     identifiers_list,
     get_transition,
     get_location],

    [],

    [('AFRICA', space.wrap(common.AFRICA)),
     ('AMERICA', space.wrap(common.AMERICA)),
     ('ANTARCTICA', space.wrap(common.ANTARCTICA)),
     ('ARCTIC', space.wrap(common.ARCTIC)),
     ('ASIA', space.wrap(common.ASIA)),
     ('ATLANTIC', space.wrap(common.ATLANTIC)),
     ('AUSTRALIA', space.wrap(common.AUSTRALIA)),
     ('EUROPE', space.wrap(common.EUROPE)),
     ('INDIAN', space.wrap(common.INDIAN)),
     ('PACIFIC', space.wrap(common.PACIFIC)),
     ('UTC', space.wrap(common.UTC)),
     ('ALL', space.wrap(common.ALL)),
     ('ALL_WITH_BC', space.wrap(common.ALL_WITH_BC)),
     ('PER_COUNTRY', space.wrap(common.PER_COUNTRY))],

    instance_class=W_DateTimeZone
)
