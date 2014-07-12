
""" this imports timelib and specifically parse_date from php's timelib
"""

import py
import time
import subprocess

from rpython.rlib.rarithmetic import intmask
from rpython.translator.tool.cbuild import ExternalCompilationInfo
from rpython.rtyper.tool import rffi_platform as platform
from rpython.rtyper.lltypesystem import lltype, rffi
from hippy.tool.platform import get_gmake


ZONETYPE_ID = 3
ZONETYPE_ABBR = 2
ZONETYPE_OFFSET = 1


LIBDIR = py.path.local(__file__).join('..', 'lib/')
subprocess.check_call([get_gmake(), '-C', str(LIBDIR)])

eci = ExternalCompilationInfo(includes=['timelib.h', 'sys/time.h', 'time.h'],
                              include_dirs=[LIBDIR],
                              libraries=['timelib1'],
                              testonly_libraries=['timelib'],
                              library_dirs=[str(LIBDIR)])


def external(*args):
    return rffi.llexternal(*args, compilation_info=eci, releasegil=False)

timelib_error_message = rffi.CStruct('timelib_error_message',
                                     ('position', rffi.INT),
                                     ('character', lltype.Char),
                                     ('message', rffi.CCHARP))


class CConfig(object):
    ttinfo = platform.Struct('ttinfo', [
        ('offset', rffi.INT),
        ('isdst', rffi.INT),
        ('abbr_idx', lltype.Unsigned),
        ('isstdcnt', lltype.Unsigned),
        ('isgmtcnt', lltype.Unsigned),
    ])

    tm = platform.Struct("struct tm", [
        ("tm_sec", rffi.INT),
        ("tm_min", rffi.INT),
        ("tm_hour", rffi.INT),
        ("tm_mday", rffi.INT),
        ("tm_mon", rffi.INT),
        ("tm_year", rffi.INT),
        ("tm_wday", rffi.INT),
        ("tm_yday", rffi.INT),
        ("tm_isdst", rffi.INT),
        ("tm_gmtoff", rffi.LONG),
        ("tm_zone", rffi.CCHARP)])

    timeval = platform.Struct("struct timeval", [
        ("tv_sec", rffi.INT),
        ("tv_usec", rffi.INT)
    ])

    _compilation_info_ = eci

conf = platform.configure(CConfig)

tzinfo = rffi.CArrayPtr(conf['ttinfo'])
tm = conf['tm']
tmP = lltype.Ptr(tm)
timeval = conf['timeval']
timevalP = lltype.Ptr(timeval)

c_strftime = external('strftime',
                      [rffi.CCHARP, rffi.SIZE_T, rffi.CCHARP, tmP],
                      rffi.SIZE_T)

c_gettimeofday = external('gettimeofday', [timevalP, rffi.VOIDP], rffi.INT)

class CConfig(object):
    timelib_special = platform.Struct('timelib_special', [
        ('type', lltype.Unsigned),
        ('amount', lltype.Signed),
    ])

    tlocinfo = platform.Struct('tlocinfo', [
        ('country_code', lltype.FixedSizeArray(lltype.Char, 3)),
        ('latitude', lltype.Float),
        ('longitude', lltype.Float),
        ('comments', rffi.CCHARP),
    ])

    _compilation_info_ = eci

conf = platform.configure(CConfig)

tlocinfo = conf['tlocinfo']
timelib_special = conf['timelib_special']
timelib_specialP = lltype.Ptr(timelib_special)

class CConfig(object):
    timelib_tzinfo = platform.Struct('timelib_tzinfo', [
        ('name', rffi.CCHARP),

        ('ttisgmtcnt', lltype.Unsigned),
        ('ttisstdcnt', lltype.Unsigned),
        ('leapcnt', lltype.Unsigned),
        ('timecnt', lltype.Unsigned),
        ('typecnt', lltype.Unsigned),
        ('charcnt', lltype.Unsigned),

        ('trans', rffi.CArrayPtr(rffi.INT)),
        ('trans_idx', rffi.CArrayPtr(rffi.UCHAR)),

        ('type', tzinfo),
        ('timezone_abbr', rffi.CCHARP),

        # tlinfo  *leap_times;
        ('bc', lltype.Unsigned),
        ('location', tlocinfo)
    ])
    timelib_rel_time = platform.Struct('timelib_rel_time', [
        ('y', lltype.Signed),
        ('m', lltype.Signed),
        ('d', lltype.Signed),
        ('h', lltype.Signed),
        ('i', lltype.Signed),
        ('s', lltype.Signed),

        ('invert', rffi.INT),
        ('days', lltype.Signed),

        ('weekday', lltype.Signed),
        ('weekday_behavior', lltype.Signed),

        ('first_last_day_of', lltype.Signed),

        ("special", timelib_special),

        ("have_weekday_relative", lltype.Unsigned),
        ("have_special_relative", lltype.Unsigned),
    ])

    timelib_tzdb_index_entry = platform.Struct('timelib_tzdb_index_entry', [
        ('id', rffi.CCHARP),
        ('pos', lltype.Unsigned),
    ])

    _compilation_info_ = eci

conf = platform.configure(CConfig)
timelib_tzinfo = lltype.Ptr(conf['timelib_tzinfo'])
timelib_rel_time = conf['timelib_rel_time']
timelib_rel_timeP = lltype.Ptr(timelib_rel_time)
timelib_tzdb_index_entry = conf['timelib_tzdb_index_entry']
timelib_tzdb_index_entryP = rffi.CArrayPtr(timelib_tzdb_index_entry)


class CConfig(object):
    timelib_tzdb = platform.Struct('timelib_tzdb', ([
        ('version', rffi.CCHARP),
        ('index_size', rffi.INT),
        ('index', timelib_tzdb_index_entryP),
        ('data', rffi.CArrayPtr(rffi.UCHAR)),
    ]))
    timelib_error_container = platform.Struct('timelib_error_container',
       [('error_count', lltype.Signed),
        ('error_messages', rffi.CArrayPtr(timelib_error_message)),
        ('warning_count', lltype.Signed)])
    timelib_time = platform.Struct('timelib_time', ([
        ('y', lltype.Signed),
        ('m', lltype.Signed),
        ('d', lltype.Signed),
        ('h', lltype.Signed),
        ('i', lltype.Signed),
        ('s', lltype.Signed),
        ('f', lltype.Float),
        ('z', lltype.Signed),

        ('tz_abbr', rffi.CCHARP),
        ('tz_info', timelib_tzinfo),

        ('dst', lltype.Signed),
        ('relative', timelib_rel_timeP.TO),

        ('sse', lltype.Signed),

        ('have_time', lltype.Unsigned),
        ('have_date', lltype.Unsigned),
        ('have_relative', lltype.Unsigned),
        ('have_weeknr_day', lltype.Unsigned),

        ('sse_uptodate', lltype.Unsigned),
        ('tim_uptodate', lltype.Unsigned),
        ('zone_type', lltype.Signed),
        ('is_localtime', lltype.Signed),

        ]))
    timelib_time_offset = platform.Struct('timelib_time_offset', [
        ('offset', lltype.Signed),
        ('leap_secs', rffi.UINT),
        ('is_dst', rffi.UINT),
        ('abbr', rffi.CCHARP),
        ('transistion_time', lltype.Signed)
        ])

    timelib_tz_lookup_table = platform.Struct('timelib_tz_lookup_table', [
        ('name', rffi.CCHARP),
        ('type', lltype.Signed),
        ('gmtoffset', lltype.SingleFloat),
        ('full_tz_name', rffi.CCHARP),
    ])

    timelib_tz_lookup_table = platform.Struct('timelib_tz_lookup_table', [
        ('name', rffi.CCHARP),
        ('type', lltype.Signed),
        ('gmtoffset', lltype.SingleFloat),
        ('full_tz_name', rffi.CCHARP),
    ])

    TIMELIB_NO_CLONE = platform.DefinedConstantInteger(
        'TIMELIB_NO_CLONE')

    TIMELIB_ZONETYPE_ID = platform.DefinedConstantInteger(
        'TIMELIB_ZONETYPE_ID')
    TIMELIB_ZONETYPE_ABBR = platform.DefinedConstantInteger(
        'TIMELIB_ZONETYPE_ABBR')
    TIMELIB_ZONETYPE_OFFSET = platform.DefinedConstantInteger(
        'TIMELIB_ZONETYPE_OFFSET')


    _compilation_info_ = eci

conf = platform.configure(CConfig)
timelib_tzdb = lltype.Ptr(conf['timelib_tzdb'])
timelib_error_container = lltype.Ptr(conf['timelib_error_container'])
timelib_error_containerP = rffi.CArrayPtr(timelib_error_container)

timelib_time = lltype.Ptr(conf['timelib_time'])
timelib_time_offset = lltype.Ptr(conf['timelib_time_offset'])

timelib_tz_lookup_table = conf['timelib_tz_lookup_table']
timelib_tz_lookup_tableP = rffi.CArrayPtr(timelib_tz_lookup_table)

TIMELIB_NO_CLONE = conf['TIMELIB_NO_CLONE']
TIMELIB_ZONETYPE_ID = rffi.cast(rffi.UINT, conf['TIMELIB_ZONETYPE_ID'])
TIMELIB_ZONETYPE_ABBR = rffi.cast(rffi.UINT, conf['TIMELIB_ZONETYPE_ABBR'])
TIMELIB_ZONETYPE_OFFSET = rffi.cast(rffi.UINT, conf['TIMELIB_ZONETYPE_OFFSET'])

timelib_builtin_db = external('timelib_builtin_db', [], timelib_tzdb)

timelib_error_container_dtor = external('timelib_error_container_dtor',
                                        [timelib_error_container], lltype.Void)

timelib_update_ts = external('timelib_update_ts',
                             [timelib_time, timelib_tzinfo],
                             lltype.Void)

timelib_update_from_sse = external(
    'timelib_update_from_sse', [timelib_time], lltype.Void)

INTP = rffi.CArrayPtr(lltype.Signed)
timelib_date_to_int = external('timelib_date_to_int',
                               [timelib_time, INTP],
                               lltype.Signed)

timelib_tz_get_wrapper = rffi.CCallback([rffi.CCHARP, timelib_tzdb],
                                        timelib_tzinfo)

timelib_strtotime = external('timelib_strtotime',
                             [rffi.CCHARP, lltype.Signed,
                              timelib_error_containerP,
                              timelib_tzdb, timelib_tz_get_wrapper],
                             timelib_time)

timelib_diff = external(
    'timelib_diff', [timelib_time, timelib_time],
    timelib_rel_timeP
)

timelib_time_clone = external('timelib_time_clone', [timelib_time],
                              timelib_time)
timelib_tzinfo_clone = external('timelib_tzinfo_clone', [timelib_tzinfo],
                                timelib_tzinfo)

timelib_parse_from_format = external('timelib_parse_from_format',
                                     [rffi.CCHARP, rffi.CCHARP, lltype.Signed,
                                      timelib_error_containerP, timelib_tzdb,
                                      timelib_tz_get_wrapper],
                                     timelib_time)

timelib_time_dtor = external('timelib_time_dtor',
                             [timelib_time], lltype.Void)
timelib_time_ctor = external('timelib_time_ctor',
                             [], timelib_time)

timelib_tzinfo_ctor = external('timelib_tzinfo_ctor',
                               [rffi.CCHARP],
                               timelib_tzinfo)

timelib_rel_time_ctor = external('timelib_rel_time_ctor', [],
                                 timelib_rel_timeP)

timelib_fill_holes = external('timelib_fill_holes',
                              [timelib_time, timelib_time, rffi.INT],
                              lltype.Void)

timelib_unixtime2local = external('timelib_unixtime2local',
                                  [timelib_time, rffi.LONGLONG],
                                  lltype.Void)

timelib_unixtime2gmt = external('timelib_unixtime2gmt',
                                [timelib_time, rffi.LONGLONG],
                                lltype.Void)

timelib_parse_tzfile = external('timelib_parse_tzfile',
                                [rffi.CCHARP, timelib_tzdb],
                                timelib_tzinfo)

timelib_day_of_week = external('timelib_day_of_week',
                               [lltype.Signed, lltype.Signed, lltype.Signed],
                               lltype.Signed)

timelib_iso_day_of_week = external('timelib_iso_day_of_week',
                                   [lltype.Signed, lltype.Signed,
                                    lltype.Signed],
                                   lltype.Signed)

timelib_day_of_year = external('timelib_day_of_year',
                               [lltype.Signed, lltype.Signed, lltype.Signed],
                               lltype.Signed)

timelib_valid_date = external('timelib_valid_date',
                              [lltype.Signed, lltype.Signed, lltype.Signed],
                              lltype.Signed)

timelib_days_in_month = external('timelib_days_in_month', [lltype.Signed] * 2,
                                 lltype.Signed)

timelib_get_time_zone_info = external('timelib_get_time_zone_info',
                                      [lltype.Signed, timelib_tzinfo],
                                      timelib_time_offset)

timelib_time_offset_dtor = external('timelib_time_offset_dtor',
                                    [timelib_time_offset], lltype.Void)

timelib_isoweek_from_date = external('timelib_isoweek_from_date',
                                     [rffi.LONGLONG, rffi.LONGLONG,
                                      rffi.LONGLONG,
                                      rffi.CArrayPtr(rffi.LONGLONG),
                                      rffi.CArrayPtr(rffi.LONGLONG)],
                                     lltype.Void)

timelib_get_current_offset = external('timelib_get_current_offset',
                                      [timelib_time],
                                      lltype.Signed)

timelib_set_timezone = external('timelib_set_timezone',
                                [timelib_time,
                                 timelib_tzinfo],
                                lltype.Void)

timelib_time_offset_ctor = external('timelib_time_offset_ctor', [],
                                    timelib_time_offset)

timelib_timezone_abbreviations_list = external(
    'timelib_timezone_abbreviations_list',
    [], timelib_tz_lookup_tableP)

timelib_timezone_builtin_identifiers_list = external(
    'timelib_timezone_builtin_identifiers_list',
    [INTP], timelib_tzdb_index_entryP)

timelib_timezone_id_from_abbr = external(
    'timelib_timezone_id_from_abbr',
    [rffi.CCHARP, lltype.SignedLongLong, lltype.Signed],
    rffi.CCHARP
)

timelib_daynr_from_weeknr = external(
    'timelib_daynr_from_weeknr',
    [lltype.Signed, lltype.Signed, lltype.Signed],
    lltype.Signed
)

timelib_astro_rise_set_altitude = external(
    'timelib_astro_rise_set_altitude',
    [timelib_time, lltype.Float, lltype.Float, lltype.Float, lltype.Signed,
     rffi.CArrayPtr(lltype.Float), rffi.CArrayPtr(lltype.Float),
     rffi.CArrayPtr(rffi.LONGLONG),
     rffi.CArrayPtr(rffi.LONGLONG), rffi.CArrayPtr(rffi.LONGLONG)],
    lltype.Signed
)


DEBUG = True


def tzinfo_callback(arg1, arg2):
    return timelib_parse_tzfile(arg1, arg2)


def timelib_timezone(name):
    with rffi.scoped_str2charp(name) as ll_s:
        return timelib_parse_tzfile(ll_s, timelib_builtin_db())


def timelib_time_modify(timelib_time, modifier, tzi):
    error = ''

    ll_s = rffi.str2charp(modifier)
    error_c = lltype.malloc(timelib_error_containerP.TO, 1, flavor='raw')

    tmp_timelib_time = timelib_strtotime(
        ll_s, len(modifier), error_c, timelib_builtin_db(), tzinfo_callback
    )

    error_count = rffi.cast(lltype.Signed, error_c[0].c_error_count)

    if error_count:
        position = int(error_c[0].c_error_messages[0].c_position)
        message = rffi.charp2str(error_c[0].c_error_messages[0].c_message)
        char = error_c[0].c_error_messages[0].c_character

        error = "Failed to parse time string (%s) at position %s (%s): %s" % (
            modifier, position, char, message
        )

    lltype.free(error_c, flavor='raw')

    rffi.c_memcpy(
        rffi.cast(rffi.VOIDP, timelib_time.c_relative),
        rffi.cast(rffi.VOIDP, tmp_timelib_time.c_relative),
        rffi.sizeof(timelib_rel_time)
    )

    timelib_time.c_have_relative = tmp_timelib_time.c_have_relative
    timelib_time.c_sse_uptodate = rffi.cast(rffi.UINT, 0)

    if intmask(tmp_timelib_time.c_y) != -99999:
        timelib_time.c_y = tmp_timelib_time.c_y

    if intmask(tmp_timelib_time.c_m) != -99999:
        timelib_time.c_m = tmp_timelib_time.c_m

    if intmask(tmp_timelib_time.c_d) != -99999:
        timelib_time.c_d = tmp_timelib_time.c_d

    if intmask(tmp_timelib_time.c_h) != -99999:
        timelib_time.c_h = tmp_timelib_time.c_h

        if intmask(tmp_timelib_time.c_i) != -99999:
            timelib_time.c_i = tmp_timelib_time.c_i

            if intmask(tmp_timelib_time.c_s) != -99999:
                timelib_time.c_s = tmp_timelib_time.c_s
            else:
                timelib_time.c_s = rffi.cast(lltype.Signed, 0)
        else:
            timelib_time.c_i = rffi.cast(lltype.Signed, 0)
            timelib_time.c_s = rffi.cast(lltype.Signed, 0)

    timelib_time_dtor(tmp_timelib_time)

    timelib_update_ts(timelib_time, lltype.nullptr(timelib_tzinfo.TO))
    timelib_update_from_sse(timelib_time)
    timelib_time.c_have_relative = rffi.cast(rffi.UINT, 0)

    return timelib_time, error


def timelib_time_from_timestamp(timestamp, timelib_timezone):
    timelib_time = timelib_time_ctor()
    timelib_time.c_tz_info = timelib_timezone
    timelib_time.c_zone_type = TIMELIB_ZONETYPE_ID
    timelib_unixtime2local(timelib_time, timestamp)

    return timelib_time


def timelib_time_from_format(time_format_string, time_string):
    time_string = time_string or 'now'
    error = ''

    ll_s = rffi.str2charp(time_string)
    ll_format = rffi.str2charp(time_format_string)
    error_c = lltype.malloc(timelib_error_containerP.TO, 1, flavor='raw')

    ll_res = timelib_parse_from_format(
        ll_format, ll_s, len(time_string), error_c,
        timelib_builtin_db(), tzinfo_callback
    )

    error_count = rffi.cast(lltype.Signed, error_c[0].c_error_count)

    if error_count:
        position = int(error_c[0].c_error_messages[0].c_position)
        message = rffi.charp2str(error_c[0].c_error_messages[0].c_message)
        char = error_c[0].c_error_messages[0].c_character

        error = "Failed to parse time string (%s) at position %s (%s): %s" % (
            time_string, position, char, message
        )

    lltype.free(error_c, flavor='raw')

    return ll_res, error


def timelib_time_from_string(time_string):
    time_string = time_string or 'now'
    error = ''

    ll_s = rffi.str2charp(time_string)
    error_c = lltype.malloc(timelib_error_containerP.TO, 1, flavor='raw')

    ll_res = timelib_strtotime(
        ll_s, len(time_string), error_c, timelib_builtin_db(), tzinfo_callback
    )

    error_count = rffi.cast(lltype.Signed, error_c[0].c_error_count)

    if error_count:
        position = int(error_c[0].c_error_messages[0].c_position)
        message = rffi.charp2str(error_c[0].c_error_messages[0].c_message)
        char = error_c[0].c_error_messages[0].c_character

        error = "Failed to parse time string (%s) at position %s (%s): %s" % (
            time_string, position, char, message
        )

    lltype.free(error_c, flavor='raw')

    return ll_res, error


def timelib_time_to_int(ll_res):
    error = lltype.malloc(INTP.TO, 1, flavor='raw', zero=True)
    res = timelib_date_to_int(ll_res, error)
    lltype.free(error, flavor='raw')


def strtotime(s, now, timelib_timezone):
    if len(s) == 0:
        return -1
    if now == -1:
        now = int(time.time())
    with rffi.scoped_str2charp(s) as ll_s:
        error_c = lltype.malloc(timelib_error_containerP.TO, 1, flavor='raw')
        ll_res = timelib_strtotime(ll_s,
                                   len(s), error_c, timelib_builtin_db(),
                                   tzinfo_callback)
        error_count = rffi.cast(lltype.Signed, error_c[0].c_error_count)
        error = error_c[0]
        lltype.free(error_c, flavor='raw')
        if error_count != 0:
            if DEBUG:
                print (rffi.charp2str(error.c_error_messages[0].c_message),
                       "at",
                       rffi.cast(lltype.Signed,
                                 error.c_error_messages[0].c_position))
            timelib_error_container_dtor(error)
            return -1
        if rffi.cast(lltype.Signed, error.c_warning_count) != 0:
            #return -1
            #raise Exception("warnings unimplemented, do something")
            pass
        timelib_error_container_dtor(error)
        ll_now = timelib_time_ctor()
        ll_now.c_tz_info = timelib_timezone
        ll_now.c_zone_type = TIMELIB_ZONETYPE_ID
        timelib_unixtime2local(ll_now, now)
        timelib_fill_holes(ll_res, ll_now, TIMELIB_NO_CLONE)
        timelib_update_ts(ll_res, timelib_timezone)
        timelib_time_dtor(ll_now)
        error = lltype.malloc(INTP.TO, 1, flavor='raw', zero=True)
        res = timelib_date_to_int(ll_res, error)
        err_val = error[0]
        lltype.free(error, flavor='raw')
        timelib_time_dtor(ll_res)
        if err_val:
            return -1
        return res


class IntervalToTimeException(Exception):
    pass


def str_interval_to_time(s):
    if len(s) == 0:
        raise IntervalToTimeException
    with rffi.scoped_str2charp(s) as ll_s:

        error_c = lltype.malloc(timelib_error_containerP.TO, 1, flavor='raw')

        ll_res = timelib_strtotime(
            ll_s, len(s), error_c, timelib_builtin_db(), tzinfo_callback
        )

        error_count = rffi.cast(lltype.Signed, error_c[0].c_error_count)
        error = error_c[0]

        lltype.free(error_c, flavor='raw')

        if error_count != 0:
            if DEBUG:
                print (rffi.charp2str(error.c_error_messages[0].c_message),
                       "at",
                       rffi.cast(lltype.Signed,
                                 error.c_error_messages[0].c_position))
            timelib_error_container_dtor(error)
            raise IntervalToTimeException
        if rffi.cast(lltype.Signed, error.c_warning_count) != 0:
            pass

        res = (
            ll_res.c_relative.c_y,
            ll_res.c_relative.c_m,
            ll_res.c_relative.c_d,
            ll_res.c_relative.c_h,
            ll_res.c_relative.c_i,
            ll_res.c_relative.c_s
        )

        timelib_error_container_dtor(error)
        timelib_time_dtor(ll_res)
        return res


def getdate(timestamp, timelib_timezone):
    t = timelib_time_ctor()
    t.c_tz_info = timelib_timezone
    t.c_zone_type = TIMELIB_ZONETYPE_ID
    timelib_unixtime2local(t, timestamp)
    dow = timelib_day_of_week(t.c_y, t.c_m, t.c_d)
    res = (t.c_y, t.c_m, t.c_d, t.c_h, t.c_i, t.c_s, t.c_f, dow,
           rffi.cast(lltype.Signed, t.c_zone_type))
    timelib_time_dtor(t)
    return res


_short_day_name = [
    "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"
]


def short_day_name(y, m, d):
    return _short_day_name[timelib_day_of_week(y, m, d)]


_full_day_name = [
    "Sunday", "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday"
]


def full_day_name(y, m, d):
    return _full_day_name[timelib_day_of_week(y, m, d)]

full_month_names = [
    "January", "February", "March", "April",
    "May", "June", "July", "August",
    "September", "October", "November", "December"
]

short_month_names = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]


def english_suffix(number):
    if number >= 10 and number <= 19:
        return "th"
    if number % 10 == 1:
        return "st"
    elif number % 10 == 2:
        return "nd"
    elif number % 10 == 3:
        return "rd"
    return "th"


def format_to(num, i, c="0"):
    out = str(abs(i))
    if len(out) < num:
        return "%s%s" % ('-' if i < 0 else "", c * (num - len(out)) + out)
    return str(i)


def format_str_to(num, out, c="0"):
    if len(out) < num:
        return c * (len(out) - num) + out
    return out


def date_format(format_string, t):
    week_year_set = False

    isoweek = lltype.malloc(rffi.CArrayPtr(rffi.LONGLONG).TO, 1, flavor='raw')
    isoyear = lltype.malloc(rffi.CArrayPtr(rffi.LONGLONG).TO, 1, flavor='raw')

    offset = lltype.nullptr(timelib_time_offset.TO)
    zone_type = rffi.cast(lltype.Signed, t.c_zone_type)

    if zone_type == ZONETYPE_ABBR:
        z = rffi.cast(lltype.Signed, t.c_z)

        offset = timelib_time_offset_ctor()
        offset.c_offset = rffi.cast(rffi.INT,
                                    (z - (rffi.cast(lltype.Signed, t.c_dst) *
                                          60)) * -60)
        offset.c_leap_secs = rffi.cast(rffi.UINT, 0)
        offset.c_is_dst = rffi.cast(rffi.UINT, t.c_dst)
    elif zone_type == ZONETYPE_OFFSET:
        z = rffi.cast(lltype.Signed, t.c_z)

        offset = timelib_time_offset_ctor()
        offset.c_offset = rffi.cast(rffi.INT, z * -60)
        offset.c_leap_secs = rffi.cast(rffi.UINT, 0)
        offset.c_is_dst = rffi.cast(rffi.UINT, 0)
        offset.c_abbr = rffi.str2charp("GMT+2000")  # not really

    else:
        offset = timelib_get_time_zone_info(
            t.c_sse, t.c_tz_info
        )

    date_string = []
    i = 0

    d = rffi.cast(lltype.Signed, t.c_d)
    i_offset = rffi.cast(lltype.Signed, offset.c_offset)

    while i < len(format_string):
        element = format_string[i]

        i += 1

        if element == 'd':
            date_string.append(format_to(2, d))

        elif element == 'D':
            date_string.append(short_day_name(t.c_y, t.c_m, d))

        elif element == 'j':
            date_string.append("%d" % d)

        elif element == 'l':
            date_string.append(full_day_name(t.c_y, t.c_m, d))

        elif element == 'S':
            date_string.append(english_suffix(d))

        elif element == 'w':
            date_string.append("%d" % timelib_day_of_week(t.c_y, t.c_m, d))

        elif element == 'N':
            date_string.append("%d" % timelib_iso_day_of_week(t.c_y, t.c_m, d))

        elif element == 'z':
            date_string.append("%d" % timelib_day_of_year(t.c_y, t.c_m, d))

        elif element == 'W':
            if not week_year_set:
                timelib_isoweek_from_date(t.c_y, t.c_m, t.c_d,
                                          isoweek, isoyear)
                week_year_set = True
            date_string.append(format_to(2,
                                         rffi.cast(lltype.Signed, isoweek[0])))
        elif element == 'o':
            if not week_year_set:
                timelib_isoweek_from_date(t.c_y, t.c_m, t.c_d,
                                          isoweek, isoyear)
                week_year_set = True
            date_string.append("%d" % rffi.cast(lltype.Signed, isoyear[0]))

        elif element == 'F':
            date_string.append(full_month_names[t.c_m - 1])

        elif element == 'm':
            date_string.append(format_to(2, t.c_m))

        elif element == 'M':
            date_string.append(short_month_names[t.c_m - 1])

        elif element == 'n':
            date_string.append("%d" % t.c_m)

        elif element == 't':
            date_string.append("%d" % timelib_days_in_month(t.c_y, t.c_m))

        elif element == 'L':
            date_string.append("%d" % is_leap(t.c_y))

        elif element == 'Y':
            date_string.append(format_to(4, t.c_y))

        elif element == 'y':
            y = '%d' % t.c_y
            stop = len(y) - 2
            if stop < 0:
                stop = 0
            date_string.append(y[stop:])

        elif element == 'a':
            date_string.append("pm" if t.c_h >= 12 else "am")

        elif element == 'A':
            date_string.append("PM" if t.c_h >= 12 else "AM")

        elif element == 'B':
            retval = ((((t.c_sse)-((t.c_sse) - (((t.c_sse) % 86400) + 3600))) * 10) / 864)
            while retval < 0:
                retval += 1000

            retval = retval % 1000
            date_string.append(format_to(3, retval))

        elif element == 'g':
            if t.c_h % 12:
                date_string.append("%d" % (t.c_h % 12))
            else:
                date_string.append("12")

        elif element == 'h':
            if t.c_h % 12:
                date_string.append(format_to(2, t.c_h % 12))
            else:
                date_string.append("12")

        elif element == 'G':
            date_string.append("%d" % t.c_h)

        elif element == 'H':
            date_string.append(format_to(2, t.c_h))

        elif element == 'i':
            date_string.append(format_to(2, t.c_i))

        elif element == 's':
            date_string.append(format_to(2, t.c_s))

        elif element == 'u':
            date_string.append(element)
            # raise NotImplementedError(element)

        elif element == 'I':
            date_string.append("%d" % rffi.cast(lltype.Signed,
                                                offset.c_is_dst))

        elif element == 'P':
            date_string.append("%s%s:%s" % (
                ('-' if i_offset < 0 else '+'),
                format_to(2, abs(i_offset / 3600)),
                format_to(2, abs(i_offset % 3600) / 60)
            ))

        elif element == 'O':
            date_string.append("%s%s%s" % (
                ('-' if i_offset < 0 else '+'),
                format_to(2, abs(i_offset / 3600)),
                format_to(2, abs(i_offset % 3600) / 60)
            ))

        elif element == 'T':
            if t.c_tz_abbr:
                date_string.append(rffi.charp2str(t.c_tz_abbr))

        elif element == 'e':
            if zone_type == ZONETYPE_ID:
                date_string.append(rffi.charp2str(t.c_tz_info.c_name))
            elif zone_type == ZONETYPE_ABBR:
                date_string.append(rffi.charp2str(offset.c_abbr))
            elif zone_type == ZONETYPE_OFFSET:
                date_string.append("%s%s:%s" % (
                    '-' if i_offset < 0 else '+',
                    format_to(2, abs(i_offset / 3600)),
                    format_to(2, abs((i_offset % 3600) / 60)))
                )

        elif element == 'Z':
            date_string.append("%d" % rffi.cast(lltype.Signed, i_offset))

        elif element == 'c':
            date_string.append("%s-%s-%sT%s:%s:%s%s%s:%s" % (
                format_to(4, rffi.cast(lltype.Signed, t.c_y)),
                format_to(2, rffi.cast(lltype.Signed, t.c_m)),
                format_to(2, t.c_d),
                format_to(2, rffi.cast(lltype.Signed, t.c_h)),
                format_to(2, rffi.cast(lltype.Signed, t.c_i)),
                format_to(2, rffi.cast(lltype.Signed, t.c_s)),
                "-" if i_offset < 0 else "+",
                format_to(2, abs(i_offset / 3600)),
                format_to(2, abs(i_offset % 3600) / 60))
            )

        elif element == 'r':
            i_offset = rffi.cast(lltype.Signed, offset.c_offset)
            date_string.append(
                "%s, %s %s %s %s:%s:%s %s%s%s" % (
                    format_str_to(3, short_day_name(t.c_y, t.c_m, d), " "),
                    format_to(2, d),
                    format_str_to(3, short_month_names[t.c_m - 1], " "),
                    format_to(4, t.c_y),
                    format_to(2, t.c_h),
                    format_to(2, t.c_i),
                    format_to(2, t.c_s),
                    '-' if i_offset < 0 else '+',
                    format_to(2, abs(i_offset / 3600)),
                    format_to(2, abs(i_offset % 3600)),
                )
            )

        elif element == 'U':
            date_string.append("%d" % t.c_sse)

        elif element == '\\':
            if i < len(format_string):
                date_string.append(format_string[i])
                i += 1

        else:
            date_string.append(element)

    lltype.free(isoyear, flavor='raw')
    lltype.free(isoweek, flavor='raw')
    return "".join(date_string)


def mktime(hour, minute, second, month, day, year, dst, gmt, tzi):
    t = timelib_time_ctor()
    if gmt:
        timelib_unixtime2gmt(t, int(time.time()))
    else:
        t.c_tz_info = tzi
        t.c_zone_type = TIMELIB_ZONETYPE_ID
        timelib_unixtime2local(t, int(time.time()))

    if year >= 0 and year < 70:
        year += 2000
    elif year >= 70 and year <= 100:
        year += 1900
    t.c_y = year
    t.c_m = month
    t.c_d = day
    t.c_h = hour
    t.c_i = minute
    t.c_s = second
    if gmt:
        timelib_update_ts(t, lltype.nullptr(timelib_tzinfo.TO))
    else:
        timelib_update_ts(t, tzi.local_tzi)

    adjust = 0
    res = t.c_sse
    if dst != -1:
        if gmt:
            if dst == 1:
                adjust = -3600
        else:
            if dst == 1 and not tzi.is_dst(res):
                adjust = -3600
            if dst == 0 and tzi.is_dst(res):
                adjust = 3600

    res += adjust
    timelib_time_dtor(t)
    return res


def isoweek_from_date(year, month, day):
    iw = lltype.malloc(rffi.CArrayPtr(rffi.LONGLONG).TO, 1, flavor='raw')
    iy = lltype.malloc(rffi.CArrayPtr(rffi.LONGLONG).TO, 1, flavor='raw')
    timelib_isoweek_from_date(year, month, day, iw, iy)
    week = iw[0]
    lltype.free(iw, flavor='raw')
    lltype.free(iy, flavor='raw')
    return week


def is_leap(year):
    # (y) % 4 == 0 && ((y) % 100 != 0 || (y) % 400 == 0)
    if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
        return True
    return False


class TzAbbrEntry(object):
    def __init__(self, name, _type, offset, fullname):
        self.name = name
        self._type = _type
        self.offset = offset
        self.fullname = fullname


def _unpack_fields(entry):
    if not entry.c_name:
        return None
    name = rffi.charp2str(entry.c_name)
    _type = int(entry.c_type)
    offset = float(entry.c_gmtoffset)
    fullname = ""
    if entry.c_full_tz_name:
        fullname = rffi.charp2str(entry.c_full_tz_name)
    return TzAbbrEntry(name, _type, offset, fullname)


def timezone_abbreviations_list():
    ll_arr = timelib_timezone_abbreviations_list()
    res = {}
    i = 0
    entry = _unpack_fields(ll_arr[0])
    while entry:
        i += 1
        if entry.name in res:
            res[entry.name].append((entry._type, entry.offset, entry.fullname))
        else:
            res[entry.name] = [(entry._type, entry.offset, entry.fullname)]
        entry = _unpack_fields(ll_arr[i])
    return res


if __name__ == '__main__':
    print strtotime('1970-01-01')


def timezone_builtin_identifiers_list():
    count = lltype.malloc(INTP.TO, 1, flavor='raw', zero=True)
    ll_arr = timelib_timezone_builtin_identifiers_list(count)
    res = []
    for i in range(count[0]):
        res.append((ll_arr[i].c_pos, rffi.charp2str(ll_arr[i].c_id)))
    return res


def timezone_id_from_abbr(abbr, offset, isdst):
    with rffi.scoped_str2charp(abbr) as ll_abbr:
        ll_res = timelib_timezone_id_from_abbr(ll_abbr, offset, isdst)
        if ll_res:
            return rffi.charp2str(ll_res)
    return ""


class TZEntry(object):
    def __init__(self, name, ccode, schar):
        self.name = name
        self.ccode = ccode
        self.schar = schar


def build_db():
    res = []
    ll_res = timelib_builtin_db()
    c = ll_res.c_index_size
    for i in range(c):
        name = rffi.charp2str(ll_res.c_index[i].c_id)
        pos = rffi.cast(lltype.Signed, ll_res.c_index[i].c_pos)
        ccode = chr(ll_res.c_data[pos + 5]) + chr(ll_res.c_data[pos + 6])
        schar = ll_res.c_data[pos + 4]
        res.append(TZEntry(name, ccode, schar))
    return res


def get_offset(c_time, c_timezone):

    zone_type = rffi.cast(lltype.Signed, c_time.c_zone_type)
    if zone_type == ZONETYPE_ID:
        offset = timelib_get_time_zone_info(
            c_time.c_sse, c_time.c_tz_info)
        value = int(offset.c_offset)
        timelib_time_offset_dtor(offset)

        return value

    if zone_type == ZONETYPE_ABBR:
        return int(c_time.c_z * -60)

    if zone_type == ZONETYPE_OFFSET:
        return int(c_time.c_z - (60 * c_time.c_dst)) * -60


def timezone_name(timelib_timezone):
    return rffi.charp2str(timelib_timezone.c_name)
