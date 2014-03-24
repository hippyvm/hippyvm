from rpython.rtyper.lltypesystem import lltype, rffi

from hippy import consts
from hippy.error import PHPException
from hippy.objspace import getspace
from hippy.builtin import (
    wrap_method, Optional, ThisUnwrapper, StringArg,
    LongArg, BoolArg, InstanceUnwrapper, handle_as_exception
)
from hippy.klass import def_class
from hippy.builtin_klass import GetterSetterWrapper, k_Exception

from hippy.module.date import timelib
from hippy.module.date import W_DateTime, W_DateTimeZone
from hippy.module.date.dateinterval_klass import W_DateInterval, k_DateInterval
from hippy.module.date import common


@wrap_method(['interp', ThisUnwrapper(W_DateTime), Optional(StringArg()),
              Optional(InstanceUnwrapper(W_DateTimeZone, 'DateTimeZone'))],
             name='DateTime::__construct', error_handler=handle_as_exception)
def construct(interp, this, format_string=None, w_datetimezone=None):
    error = common.initialize_date(interp, 'DateTime::__construct',
                            this, format_string, w_datetimezone)
    if error:
        raise PHPException(k_Exception.call_args(
            interp, [interp.space.wrap("%s(): %s" % ('DateTime::__construct', error))]
        ))


@wrap_method(['interp', Optional(StringArg(None)), Optional(StringArg(None)),
              Optional(InstanceUnwrapper(W_DateTimeZone, 'DateTimeZone'))],
             name='DateTime::createFromFormat', flags=consts.ACC_STATIC)
def create_from_format(interp, format_string, time_string, w_datetimezone):

    date = W_DateTime(k_DateTime, [])
    func_name = "DateTime::createFromFormat"

    if w_datetimezone:
        date.timelib_timezone = w_datetimezone.timelib_timezone
    else:
        date.timelib_timezone = interp.get_default_timezone(func_name)

    date.timelib_time = timelib.timelib_time_from_format(
        format_string, time_string, date.timelib_timezone
    )

    return date


@wrap_method(['space', ThisUnwrapper(W_DateTime), StringArg(False)],
             name="DateTime::format", error=False)
def format(space, this, str_time):
    return space.wrap(timelib.date_format(str_time, this.timelib_time))


@wrap_method(['interp', ThisUnwrapper(W_DateTime), StringArg(False)],
             name="DateTime::modify", error=False)
def modify(interp, this, string_modifier):

    this.timelib_time = timelib.timelib_time_modify(
        this.timelib_time, string_modifier, this.timezone.timelib_timezone
    )

    return this


@wrap_method(['interp', ThisUnwrapper(W_DateTime)],
             name="DateTime::getTimestamp")
def get_timestamp(interp, this):
    return common.date_timestamp_get(interp, this)

@wrap_method(['interp', ThisUnwrapper(W_DateTime), LongArg(None)],
             name='DateTime::setTimestamp')
def set_timestamp(interp, this, timestamp):

    timelib.timelib_unixtime2local(this.timelib_time, timestamp)
    timelib.timelib_update_ts(this.timelib_time, lltype.nullptr(timelib.timelib_tzinfo.TO))

    return this


@wrap_method(['space', ThisUnwrapper(W_DateTime)],
             name='DateTime::getTimezone')
def get_timezone(space, this):
    return this.timezone


@wrap_method(['interp', ThisUnwrapper(W_DateTime),
              InstanceUnwrapper(W_DateTimeZone, 'DateTimeZone')],
             name='DateTime::setTimezone', error=False)
def set_timezone(interp, this, w_datetimezone):
    this.timezone = w_datetimezone

    timelib.timelib_set_timezone(this.timelib_time, this.timezone.timelib_timezone)
    timelib.timelib_unixtime2local(this.timelib_time, this.timelib_time.c_sse)

    return this


@wrap_method(['interp', ThisUnwrapper(W_DateTime),
              LongArg(), LongArg(), LongArg()],
             name='DateTime::setDate', error=False)
def set_date(interp, this, year, month, day):

    this.timelib_time.c_y = year
    this.timelib_time.c_m = month
    this.timelib_time.c_d = day

    timelib.timelib_update_ts(
        this.timelib_time,
        lltype.nullptr(timelib.timelib_tzinfo.TO)
    )

    return this


@wrap_method(['interp', ThisUnwrapper(W_DateTime),
              LongArg(), LongArg(), Optional(LongArg())],
             name='DateTime::setISODate', error=False)
def set_iso_date(interp, this, year, week, day=1):

    this.timelib_time.c_y = year
    this.timelib_time.c_m = 1
    this.timelib_time.c_d = 1

    this.timelib_time.c_relative.c_d = timelib.timelib_daynr_from_weeknr(year, week, day)
    this.timelib_time.c_have_relative = rffi.cast(
        timelib.timelib_time.TO.c_have_relative, 1
    )

    timelib.timelib_update_ts(
        this.timelib_time,
        lltype.nullptr(timelib.timelib_tzinfo.TO)
    )

    return this


@wrap_method(['interp', ThisUnwrapper(W_DateTime),
              LongArg(), LongArg(), Optional(LongArg())],
             name='DateTime::setTime', error=False)
def set_time(interp, this, hour, minute, second=0):
    this.timelib_time.c_h = hour
    this.timelib_time.c_i = minute
    this.timelib_time.c_s = second

    timelib.timelib_update_ts(
        this.timelib_time,
        lltype.nullptr(timelib.timelib_tzinfo.TO)
    )

    return this


@wrap_method(['interp', ThisUnwrapper(W_DateTime),
              InstanceUnwrapper(W_DateInterval, 'DateInterval')],
             name='DateTime::sub')
def sub(interp, this, datetime_interval):
    common.date_addsub(interp, this, datetime_interval, -1)
    return this


@wrap_method(['interp', ThisUnwrapper(W_DateTime),
              Optional(InstanceUnwrapper(W_DateInterval, 'DateInterval'))],
             name='DateTime::add')
def add(interp, this, datetime_interval=None):
    common.date_addsub(interp, this, datetime_interval, 1)
    return this


@wrap_method(['interp', ThisUnwrapper(W_DateTime),
              InstanceUnwrapper(W_DateTime, 'DateTime'), Optional(BoolArg(None))],
             name='DateTime::diff')
def diff(interp, this, w_datetime, absolute=False):

    null_ptr = lltype.nullptr(timelib.timelib_tzinfo.TO)
    timelib.timelib_update_ts(this.timelib_time, null_ptr)
    timelib.timelib_update_ts(w_datetime.timelib_time, null_ptr)

    interval = W_DateInterval(k_DateInterval, [])
    interval.time_diff = timelib.timelib_diff(this.timelib_time, w_datetime.timelib_time)

    if absolute:
        interval.time_diff.c_invert = rffi.cast(rffi.INT, 0)

    return interval


@wrap_method(['interp', ThisUnwrapper(W_DateTime)],
             name='DateTime::getOffset', error=False)
def get_offset(interp, this):

    zone_type = rffi.cast(lltype.Signed, this.timelib_time.c_zone_type)
    if zone_type == timelib.ZONETYPE_ID:
        offset = timelib.timelib_get_time_zone_info(
            this.timelib_time.c_sse, this.timelib_time.c_tz_info)
        value = int(offset.c_offset)
        timelib.timelib_time_offset_dtor(offset)
        return interp.space.wrap(value)

    if zone_type == timelib.ZONETYPE_ABBR:
        return interp.space.wrap(int(this.timelib_time.c_z) * -60)

    if zone_type == timelib.ZONETYPE_OFFSET:
        return interp.space.wrap(
            int(this.timelib_time.c_z) - (60 *
                rffi.cast(lltype.Signed, this.timelib_time.c_dst)) * -60)

    return this


@wrap_method(['space', ThisUnwrapper(W_DateTime)],
             name='DateTime::getLastErrors')
def get_last_errors(space, this):
    raise NotImplementedError


# properties

def _get_date(interp, this):
    return interp.space.wrap(timelib.date_format('Y-m-d H:i:s', this.timelib_time))

def _set_date(interp, this, w_value):
    raise NotImplementedError()

def _get_timezone(interp, this):
    zone_type = rffi.cast(lltype.Signed, this.timelib_time.c_zone_type)

    if zone_type == timelib.ZONETYPE_ID:
        return interp.space.wrap(
            rffi.charp2str(this.timezone.timelib_timezone.c_name)
        )
    elif zone_type == timelib.ZONETYPE_ABBR:
        return interp.space.wrap(
            rffi.charp2str(this.timelib_time.c_tz_abbr)
        )
    elif zone_type == timelib.ZONETYPE_OFFSET:
        pass


def _set_timezone(interp, this, w_value):
    raise NotImplementedError()

def _get_timezone_type(interp, this):
    return interp.space.wrap(rffi.cast(lltype.Signed, this.timelib_time.c_zone_type))

def _set_timezone_type(interp, this, w_value):
    raise NotImplementedError()


space = getspace()

k_DateTime = def_class(
    'DateTime',

    [construct,
     format,
     modify,
     get_timestamp,
     set_timestamp,
     get_timezone,
     set_date,
     set_iso_date,
     set_time,
     set_timezone,
     # create_from_format,
     get_last_errors,
     sub,
     add,
     diff,
     get_offset],

    [GetterSetterWrapper(_get_date, _set_date, "date", consts.ACC_PUBLIC),
     GetterSetterWrapper(_get_timezone_type, _set_timezone_type, "timezone_type", consts.ACC_PUBLIC),
     GetterSetterWrapper(_get_timezone, _set_timezone, "timezone", consts.ACC_PUBLIC)],

    [('ATOM', space.wrap("Y-m-d\TH:i:sP")),
     ('COOKIE', space.wrap("l, d-M-y H:i:s T")),
     ('ISO8601', space.wrap("Y-m-d\TH:i:sO")),
     ('RFC822', space.wrap("D, d M y H:i:s O")),
     ('RFC850', space.wrap("l, d-M-y H:i:s T")),
     ('RFC1036', space.wrap("D, d M y H:i:s O")),
     ('RFC1123', space.wrap("D, d M Y H:i:s O")),
     ('RFC2822', space.wrap("D, d M Y H:i:s O")),
     ('RFC3339', space.wrap("Y-m-d\TH:i:sP")),
     ('RSS', space.wrap("D, d M Y H:i:s O")),
     ('W3C', space.wrap("Y-m-d\TH:i:sP"))],

    instance_class=W_DateTime
)
