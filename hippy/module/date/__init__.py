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
        w_res = W_InstanceObject.clone(self, interp, contextclass)
        w_res.timelib_timezone = timelib.timelib_tzinfo_clone(
            self.timelib_timezone)

        return w_res


class W_DateTime(W_InstanceObject):
    timestamp = -1
    timezone = None

    def clone(self, interp, contextclass):
        w_res = W_InstanceObject.clone(self, interp, contextclass)
        w_res.timelib_time = timelib.timelib_time_clone(self.timelib_time)

        return w_res
