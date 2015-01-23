from collections import OrderedDict
from hippy.objects.instanceobject import W_InstanceObject
from hippy.module.date import timelib


def default_timezone(interp, name='UTC'):
    from hippy.module.date.datetimezone_klass import k_DateTimeZone
    w_datetimezone = W_DateTimeZone(k_DateTimeZone, [])
    w_datetimezone.timelib_timezone = timelib.timelib_timezone(name)
    return w_datetimezone


class W_DateTimeZone(W_InstanceObject):
    tzname = None

    def clone(self, interp, contextclass):
        from hippy.module.date.common import TimeZoneWrapper

        w_res = W_InstanceObject.clone(self, interp, contextclass)
        assert isinstance(w_res, W_DateTimeZone)

        w_res.timelib_timezone = timelib.timelib_tzinfo_clone(
            self.timelib_timezone
        )
        w_res.timezone_info = TimeZoneWrapper(w_res.timelib_timezone, 3)

        return w_res


class W_DateTime(W_InstanceObject):
    timestamp = -1
    timezone = None
    w_datetimezone = None

    def compare(self, w_obj, objspace, strict):

        offset_1 = self.w_datetimezone.timezone_info.get_offset(
            self.timelib_time
        )

        assert isinstance(w_obj, self.__class__)

        offset_2 = w_obj.w_datetimezone.timezone_info.get_offset(
            w_obj.timelib_time
        )

        if self.timelib_time.c_sse == w_obj.timelib_time.c_sse and offset_1 == offset_2:
            return [], [], [], 0
        return [], [], [], 1

    def clone(self, interp, contextclass):
        from hippy.module.date.common import TimeZoneWrapper

        w_res = W_InstanceObject.clone(self, interp, contextclass)
        w_datetimezone = W_InstanceObject.clone(self.w_datetimezone, interp, contextclass)

        assert isinstance(w_res, W_DateTime)
        assert isinstance(w_datetimezone, W_DateTimeZone)


        w_datetimezone.timelib_timezone = timelib.timelib_tzinfo_clone(
            self.w_datetimezone.timezone_info.timelib_timezone
        )
        w_datetimezone.timezone_info = TimeZoneWrapper(w_datetimezone.timelib_timezone, 3)

        w_res.w_datetimezone = w_datetimezone
        w_res.timelib_time = timelib.timelib_time_clone(self.timelib_time)

        return w_res
