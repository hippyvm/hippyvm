import time
import math

from rpython.rlib import jit
from rpython.rtyper.lltypesystem import lltype, rffi
from rpython.rlib.rstring import StringBuilder

from hippy.error import PHPException
from hippy.builtin_klass import k_Exception
from hippy.module.date import timelib
from hippy.module.date.dateinterval_klass import W_DateInterval, k_DateInterval


class TimeZoneWrapper(object):

    def __init__(self, timelib_timezone, zone_type, zone_offset=None):
        self.timelib_timezone = timelib_timezone
        self.zone_type = zone_type
        self.zone_offset = zone_offset

    def get_name(self):
        if self.zone_offset:
            return self.zone_offset

        return rffi.charp2str(self.timelib_timezone.c_name)

    def get_offset(self, timelib_time):
        if self.zone_type == timelib.ZONETYPE_ABBR:
            dst = rffi.cast(lltype.Signed, timelib_time.c_dst) * 3600
            return int(timelib_time.c_z) * -60 + dst

        if self.zone_type == timelib.ZONETYPE_OFFSET:
            offset = (60 * rffi.cast(lltype.Signed, timelib_time.c_dst) * -60)
            return int(timelib_time.c_z) * -60 - offset

        return timelib.timelib_get_current_offset(timelib_time)


def initialize_date(interp, func_name, this, time_string=None, w_datetimezone=None):
    from hippy.module.date.datetimezone_klass import W_DateTimeZone, k_DateTimeZone

    this.timelib_time, error = timelib.timelib_time_from_string(time_string)
    this.timelib_time.c_zone_type, this.timelib_time.c_tz_info
    zone_type = rffi.cast(lltype.Signed, this.timelib_time.c_zone_type)

    timezone_offset = None

    if w_datetimezone:
        timelib_timezone = w_datetimezone.timelib_timezone
    elif zone_type == timelib.ZONETYPE_ID:
        timelib_timezone = this.timelib_time.c_tz_info
    elif zone_type == timelib.ZONETYPE_ABBR:
        timelib_timezone = timelib.timelib_parse_tzfile(
            this.timelib_time.c_tz_abbr,
            timelib.timelib_builtin_db()
        )

        if not timelib_timezone:
            timelib_timezone = interp.get_default_timezone(func_name).timelib_timezone

    elif zone_type == timelib.ZONETYPE_OFFSET:
        timelib_timezone = lltype.nullptr(timelib.timelib_tzinfo.TO)

        offset = timelib.timelib_get_current_offset(this.timelib_time) / 36
        mark = '+' if offset >= 0 else ''
        h, m = offset / 100, offset % 100
        "%s%s:%s" % (mark, timelib.format_to(2, h), timelib.format_to(2, m))

        timezone_offset = "%s%s:%s" % (
            mark, timelib.format_to(2, h),
            timelib.format_to(2, m)
        )

    else:
        timelib_timezone = interp.get_default_timezone(func_name).timelib_timezone

    if timelib_timezone:
        now = timelib.timelib_time_ctor()
        now.c_zone_type = timelib.TIMELIB_ZONETYPE_ID
        now.c_tz_info = timelib_timezone

        timelib.timelib_unixtime2local(now, int(time.time()))
        timelib.timelib_fill_holes(this.timelib_time, now, timelib.TIMELIB_NO_CLONE)
        timelib.timelib_update_ts(this.timelib_time, timelib_timezone)
        timelib.timelib_time_dtor(now)

        this.timelib_time.c_have_relative = rffi.cast(
            timelib.timelib_time.TO.c_have_relative, 1
        )

    this.w_datetimezone = W_DateTimeZone(k_DateTimeZone, [])

    this.w_datetimezone.timezone_info = TimeZoneWrapper(
        timelib_timezone, zone_type, timezone_offset
    )

    return error


def initialize_date_from_format(interp, func_name, w_date,
                                format_string, time_string, w_datetimezone):

    if not w_datetimezone:
        w_date.timezone = interp.get_default_timezone(func_name)
    else:
        w_date.timezone = w_datetimezone

    w_date.timelib_time, error = timelib.timelib_time_from_format(
        format_string, time_string
    )

    now = timelib.timelib_time_ctor()
    now.c_zone_type = timelib.TIMELIB_ZONETYPE_ID
    now.c_tz_info = w_date.timezone.timelib_timezone
    zone_type = rffi.cast(lltype.Signed, w_date.timelib_time.c_zone_type)

    if zone_type == timelib.ZONETYPE_ID:
        pass
    elif zone_type == timelib.ZONETYPE_ABBR:
        pass
    elif zone_type == timelib.ZONETYPE_OFFSET:
        pass

    timelib.timelib_unixtime2local(now, int(time.time()))
    timelib.timelib_fill_holes(w_date.timelib_time, now, timelib.TIMELIB_NO_CLONE)
    timelib.timelib_update_ts(w_date.timelib_time, w_date.timezone.timelib_timezone)
    timelib.timelib_time_dtor(now)

    w_date.timelib_time.c_have_relative = rffi.cast(
        timelib.timelib_time.TO.c_have_relative, 1
    )

    return error


def initialize_timezone(interp, func_name, this, name, warning=False):

    this.timelib_timezone = timelib.timelib_parse_tzfile(
        rffi.str2charp(name),
        timelib.timelib_builtin_db()
    )

    if this.timelib_timezone == lltype.nullptr(timelib.timelib_tzinfo.TO):
        message = "%s(): Unknown or bad timezone (%s)" % (func_name, name)
        if warning:
            interp.space.ec.warn(message)
        else:
            raise PHPException(k_Exception.call_args(
                interp, [interp.space.wrap(message)]
            ))
        return False

    this.timezone_info = TimeZoneWrapper(this.timelib_timezone, 3)

    return True


def date_diff(interp, w_datetime_1, w_datetime_2, absolute):

    null_ptr = lltype.nullptr(timelib.timelib_tzinfo.TO)
    timelib.timelib_update_ts(w_datetime_1.timelib_time, null_ptr)
    timelib.timelib_update_ts(w_datetime_2.timelib_time, null_ptr)

    interval = W_DateInterval(k_DateInterval, [])
    interval.time_diff = timelib.timelib_diff(
        w_datetime_1.timelib_time,
        w_datetime_2.timelib_time
    )

    if absolute:
        interval.time_diff.c_invert = rffi.cast(rffi.INT, 0)

    return interval


def date_addsub(interp, this, datetime_interval, sign):

    if rffi.cast(lltype.Signed, datetime_interval.time_diff.c_invert):
        sign *= -1

    this.timelib_time.c_relative.c_y += datetime_interval.time_diff.c_y * sign
    this.timelib_time.c_relative.c_m += datetime_interval.time_diff.c_m * sign
    this.timelib_time.c_relative.c_d += datetime_interval.time_diff.c_d * sign
    this.timelib_time.c_relative.c_h += datetime_interval.time_diff.c_h * sign
    this.timelib_time.c_relative.c_i += datetime_interval.time_diff.c_i * sign
    this.timelib_time.c_relative.c_s += datetime_interval.time_diff.c_s * sign

    this.timelib_time.c_have_relative = rffi.cast(
        timelib.timelib_time.TO.c_have_relative, 1
    )

    this.timelib_time.c_sse_uptodate = rffi.cast(
        timelib.timelib_time.TO.c_sse_uptodate, 0
    )

    timelib.timelib_update_ts(this.timelib_time, lltype.nullptr(timelib.timelib_tzinfo.TO))
    timelib.timelib_update_from_sse(this.timelib_time)

    this.timelib_time.c_have_relative = rffi.cast(
        timelib.timelib_time.TO.c_have_relative, 0
    )

    this.timelib_time.c_relative.c_y = 0
    this.timelib_time.c_relative.c_m = 0
    this.timelib_time.c_relative.c_d = 0
    this.timelib_time.c_relative.c_h = 0
    this.timelib_time.c_relative.c_i = 0
    this.timelib_time.c_relative.c_s = 0


SUNFUNCS_RET_TIMESTAMP = 0
SUNFUNCS_RET_STRING    = 1
SUNFUNCS_RET_DOUBLE    = 2

def date_sunrise_sunset(func_name, interp, num_args, timestamp, return_format,
                        latitude, longitude, zenith, gmt_offset):

    sunrise = False
    if func_name == "date_sunrise":
        sunrise = True

    if return_format not in [SUNFUNCS_RET_TIMESTAMP,
                             SUNFUNCS_RET_STRING,
                             SUNFUNCS_RET_DOUBLE]:
        interp.space.ec.warn(
            "%s(): Wrong return format given, pick one of "
            "SUNFUNCS_RET_TIMESTAMP, SUNFUNCS_RET_STRING or SUNFUNCS_RET_DOUBLE"
            % func_name)
        return interp.space.w_False

    altitude = 90 - zenith

    timelib_time = timelib.timelib_time_ctor()
    timelib_timezone = interp.get_default_timezone("date").timelib_timezone
    timelib_time.c_tz_info = timelib_timezone
    timelib_time.c_zone_type = timelib.TIMELIB_ZONETYPE_ID

    timelib.timelib_unixtime2local(timelib_time, timestamp)

    c_h_rise = lltype.malloc(rffi.CArrayPtr(lltype.Float).TO, 1, flavor='raw')
    c_h_set = lltype.malloc(rffi.CArrayPtr(lltype.Float).TO, 1, flavor='raw')
    c_rise = lltype.malloc(rffi.CArrayPtr(rffi.LONGLONG).TO, 1, flavor='raw')
    c_set = lltype.malloc(rffi.CArrayPtr(rffi.LONGLONG).TO, 1, flavor='raw')
    c_transit = lltype.malloc(rffi.CArrayPtr(rffi.LONGLONG).TO, 1, flavor='raw')

    rs = timelib.timelib_astro_rise_set_altitude(
        timelib_time, longitude, latitude, altitude, 1,
        c_h_rise, c_h_set, c_rise, c_set, c_transit
    )

    if num_args <= 5:
        gmt_offset = float(timelib.timelib_get_current_offset(timelib_time) / 3600)

    timelib.timelib_time_dtor(timelib_time)

    if rs != 0:
        return interp.space.w_False

    if return_format == 0:
        return interp.space.wrap(c_rise[0] if sunrise else c_set[0])

    N = (c_h_rise[0] if sunrise else c_h_set[0]) + gmt_offset

    if N > 24 or N < 0:
        N -= math.floor(N / 24) * 24

    if return_format == 1:
        return interp.space.wrap("%s:%s" % (
            timelib.format_to(2, int(math.floor(N))),
            timelib.format_to(2, int(math.floor(60 * (N - int(N)))))
        ))

    elif return_format == 2:
        return interp.space.wrap(N)


AFRICA = 1
AMERICA = 2
ANTARCTICA = 4
ARCTIC = 8
ASIA = 16
ATLANTIC = 32
AUSTRALIA = 64
EUROPE = 128
INDIAN = 256
PACIFIC = 512
UTC = 1024
ALL = 2047
ALL_WITH_BC = 4095
PER_COUNTRY = 4096


def _check_id_allowed(entry, what):
    if what & AFRICA and entry.startswith("Africa/"):
        return True
    if what & AMERICA and entry.startswith("America/"):
        return True
    if what & ANTARCTICA and entry.startswith("Antarctica/"):
        return True
    if what & ARCTIC and entry.startswith("Arctic/"):
        return True
    if what & ASIA and entry.startswith("Asia/"):
        return True
    if what & ATLANTIC and entry.startswith("Atlantic/"):
        return True
    if what & AUSTRALIA and entry.startswith("Australia/"):
        return True
    if what & EUROPE and entry.startswith("Europe/"):
        return True
    if what & INDIAN and entry.startswith("Indian/"):
        return True
    if what & PACIFIC and entry.startswith("Pacific/"):
        return True
    if what & UTC and entry.startswith("UTC"):
        return True
    return False


def timezone_identifiers_list(space, what, country):
    result = []
    entry_list = timelib.build_db()
    i = 0
    for entry in entry_list:
        if what == PER_COUNTRY:
            if entry.ccode == country:
                result.append((space.wrap(i), space.wrap(entry.name)))
            i += 1
        elif what == ALL_WITH_BC or _check_id_allowed(entry.name, what) \
             and rffi.cast(lltype.Signed, entry.schar) == 1:
            result.append((space.wrap(i), space.wrap(entry.name)))
            i += 1

    return space.new_array_from_pairs(result)


def _charp2str_to_null(cp, index):
    index = rffi.cast(lltype.Signed, index)
    string = StringBuilder()
    while cp[index] != '\x00':
        string.append(cp[index])
        index += 1
    return string.build()


def timezone_transitions_get(interp, w_datetimezone, timestamp_begin, timestamp_end):
    space = interp.space
    timezone = w_datetimezone.timelib_timezone
    results = []

    space.new_array_from_pairs([
       (space.wrap('ts'), space.wrap(timestamp_begin)),
       (space.wrap('time'), space.wrap('')),
       (space.wrap('offset'), space.wrap(
           int(timezone.c_type[0].c_offset))),
       (space.wrap('isdst'), space.wrap(
           bool(int(timezone.c_type[0].c_isdst)))),
       (space.wrap('abbr'), space.wrap(
           _charp2str_to_null(timezone.c_timezone_abbr,
                              timezone.c_type[0].c_abbr_idx))),
    ])

    for i in range(timezone.c_timecnt):
        trans = int(timezone.c_trans[i])

        if timestamp_begin < trans and trans < timestamp_end:
            results.append(space.new_array_from_pairs([
                (space.wrap('ts'), space.wrap(trans)),
                (space.wrap('time'), space.wrap('')),
                (space.wrap('offset'), space.wrap(
                    int(timezone.c_type[
                        timezone.c_trans_idx[i]
                    ].c_offset))),
                (space.wrap('isdst'), space.wrap(
                    bool(int(timezone.c_type[
                        timezone.c_trans_idx[i]
                    ].c_isdst)))),
                (space.wrap('abbr'), space.wrap(_charp2str_to_null(
                    timezone.c_timezone_abbr,
                    timezone.c_type[
                        timezone.c_trans_idx[i]
                    ].c_abbr_idx
                )))
            ]))

    return space.new_array_from_list(results)


def date_timestamp_get(interp, w_datetime):
    error = lltype.malloc(
        rffi.CArrayPtr(lltype.Signed).TO, 1, flavor='raw', zero=True
    )

    timestamp = timelib.timelib_date_to_int(w_datetime.timelib_time, error)

    lltype.free(error, flavor='raw')
    return interp.space.wrap(timestamp)


def date_offset_get(interp, w_date):
    zone_type = rffi.cast(lltype.Signed, w_date.timelib_time.c_zone_type)

    if zone_type == timelib.ZONETYPE_ID:
        offset = timelib.timelib_get_time_zone_info(
            w_date.timelib_time.c_sse, w_date.timelib_time.c_tz_info)
        value = int(offset.c_offset)
        timelib.timelib_time_offset_dtor(offset)
        return interp.space.wrap(value)

    if zone_type == timelib.ZONETYPE_ABBR:
        dst = rffi.cast(lltype.Signed, w_date.timelib_time.c_dst) * 3600
        return interp.space.wrap(int(w_date.timelib_time.c_z) * -60 + dst)

    if zone_type == timelib.ZONETYPE_OFFSET:
        return interp.space.wrap(
            int(w_date.timelib_time.c_z) - (60 *
                rffi.cast(lltype.Signed, w_date.timelib_time.c_dst)) * -60)

    return w_date


def timezone_offset_get(interp, w_datetimezone, w_datetime):
    offset = timelib.timelib_get_time_zone_info(
        w_datetime.timelib_time.c_sse,
        w_datetimezone.timezone_info.timelib_timezone
    )
    res = offset.c_offset
    timelib.timelib_time_offset_dtor(offset)

    return interp.space.wrap(rffi.cast(lltype.Signed, res))

@jit.dont_look_inside
def timezone_location_get(interp, w_datetimezone):
    space = interp.space

    c_location = w_datetimezone.timelib_timezone.c_location

    country_code = "%s%s" % (
        c_location.c_country_code[0],
        c_location.c_country_code[1]
    )
    latitude = c_location.c_latitude
    longitude = c_location.c_longitude
    comments = rffi.charp2str(c_location.c_comments)

    return space.new_array_from_pairs([
        (space.wrap("country_code"), space.wrap(country_code)),
        (space.wrap("latitude"), space.wrap(latitude)),
        (space.wrap("longitude"), space.wrap(longitude)),
        (space.wrap("comments"), space.wrap(comments))
    ])
