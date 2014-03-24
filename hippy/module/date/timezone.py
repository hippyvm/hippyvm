
from rpython.rtyper.lltypesystem import lltype, rffi
from hippy.module.date import timelib


class TimeZoneInfo(object):
    local_tzi = lltype.nullptr(timelib.timelib_tzinfo.TO)
    
    def __init__(self, is_empty):
        self.is_empty = is_empty

    def get_offset_s(self, timestamp):
        offset = timelib.timelib_get_time_zone_info(timestamp, self.local_tzi)
        res = offset.c_offset
        timelib.timelib_time_offset_dtor(offset)
        return rffi.cast(lltype.Signed, res)

    def is_dst(self, timestamp):
        offset = timelib.timelib_get_time_zone_info(timestamp, self.local_tzi)
        res = offset.c_is_dst
        timelib.timelib_time_offset_dtor(offset)
        return rffi.cast(lltype.Signed, res)

    def abbr(self, timestamp):
        offset = timelib.timelib_get_time_zone_info(timestamp, self.local_tzi)
        res = rffi.charp2str(offset.c_abbr)
        timelib.timelib_time_offset_dtor(offset)
        return res


def initialize_timezone_info(tz_name):
    tzi = TimeZoneInfo(tz_name is None)
    with rffi.scoped_str2charp("UTC") as ll_s:
        ll_tzi = timelib.timelib_parse_tzfile(
            ll_s, timelib.timelib_builtin_db())
    if not ll_tzi:
        raise Exception("failed to initialize timezone")
    tzi.timezone = tz_name
    tzi.utc_tzi = ll_tzi
    if tz_name is None:
        tzi.timezone = 'UTC'
        return tzi
    with rffi.scoped_str2charp(tz_name) as ll_s:
        ll_tzi = timelib.timelib_parse_tzfile(
            ll_s, timelib.timelib_builtin_db())
    if not ll_tzi:
        raise Exception("failed to initialize timezone")
    tzi.local_tzi = ll_tzi
    return tzi
