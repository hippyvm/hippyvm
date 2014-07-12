from rpython.rlib.rstring import StringBuilder
from rpython.rlib import rmd5
from rpython.rlib import rpath
from rpython.rlib.objectmodel import we_are_translated
from hippy.module.serialize import SerializerMemo, unserialize_returning_dict
from rpython.rlib.rstring import assert_str0
from collections import OrderedDict
import time
import os

PHP_SESSION_DISABLED = 0
PHP_SESSION_NONE = 1
PHP_SESSION_ACTIVE = 2

SERIALIZE_HANDLERS = ('php',)


def serialize_hash(w_obj, var_hash):
    if w_obj in var_hash:
        var_no = var_hash[w_obj]
        return var_no, var_hash
    else:
        var_no = len(var_hash) + 1
        var_hash[w_obj] = var_no
        return var_no, var_hash


class Session(object):

    def __init__(self, interp):
        self.status = PHP_SESSION_NONE
        self.session_id = ""
        self.init_settings(interp)
        if self.auto_start:
            self.start(interp)

    def start(self, interp):
        if self.status == PHP_SESSION_NONE:
            if not self.serialize_handler in SERIALIZE_HANDLERS:
                interp.warn("session_start(): Cannot find "
                                   "serialization handler '%s' "
                                   "- session startup failed"
                                   % self.serialize_handler)
                return False
            if not self.session_id:
                self.create_id()
            self.init_settings(interp)
            self.status = PHP_SESSION_ACTIVE
            self.read_session_file(interp)
            return True
        return True

    def read_session_file(self, interp):
        space = interp.space
        cookie_path = interp.space.str_w(
            interp.config.get_ini_w('session.cookie_path'))
        w_cookie = self.get_cookie_var(interp).deref()
        w_cookie_id = space.getitem(w_cookie, space.wrap(self.name))
        if space.is_null(w_cookie_id):
            interp.header('Set-Cookie: %s=%s; path=%s' % (self.name,
                                                          self.session_id,
                                                          cookie_path), True,
                                                          False)
        else:
            cookie_id = space.str_w(w_cookie_id)
            self.session_id = cookie_id
        path = interp.space.str_w(interp.config.get_ini_w('session.save_path'))
        fname = self.name + "-" + self.session_id
        dest = rpath.join(path, [fname])
        try:
            f = open(dest)
            data = f.read(-1)
            f.close()
        except OSError:
            dct = None
        except IOError:
            dct = None
        else:
            dct = self.unserialize(interp, data)
        w_ses = self.get_session_var(interp)
        if dct is None:
            w_ses.store(space.new_array_from_rdict(OrderedDict()))
        else:
            d = OrderedDict()
            for k, w_v in dct.iteritems():
                d[k] = w_v
            w_ses.store(space.new_array_from_rdict(d))

    def create_session_file(self, interp, val):
        if self.status != PHP_SESSION_ACTIVE:
            return
        space = interp.space
        path = space.str_w(interp.config.get_ini_w('session.save_path'))
        fname = self.name + "-" + self.session_id
        dest = rpath.join(path, [fname])
        try:
            f = open(dest, "w")
            f.write(val)
            f.close()
        except OSError:
            interp.warn(
                "session_start(): open(%s, O_RDWR) failed")
            return
        except IOError, e:
            if not we_are_translated():
                interp.warn(
                    "session_start(): open(%s, O_RDWR) "
                    "failed: %s (%d)" % (dest, e.strerror, e.errno))
            return

    def create_id(self):
        d = rmd5.RMD5(str(time.time()))
        self.session_id = d.hexdigest()

    def destroy(self, interp):
        if self.status == PHP_SESSION_ACTIVE:
            path = interp.space.str_w(interp.config.get_ini_w('session.save_path'))
            fname = self.name + "-" + self.session_id
            dest = rpath.join(path, [fname])
            try:
                assert dest is not None
                dest = assert_str0(dest)
                os.remove(dest)
            except:
                pass
            self.session_id = ""
            self.status = PHP_SESSION_NONE

    def deactivate(self):
        if self.status == PHP_SESSION_ACTIVE:
            self.status = PHP_SESSION_NONE

    def init_settings(self, interp):
        config = interp.config
        space = interp.space
        self.name = space.str_w(config.get_ini_w('session.name'))
        self.auto_start = bool(space.int_w(config.get_ini_w(
            'session.auto_start')))
        self.cookie_lifetime = space.int_w(config.get_ini_w(
            'session.cookie_lifetime'))
        self.cookie_path = space.str_w(config.get_ini_w('session.cookie_path'))
        self.cookie_domain = space.str_w(config.get_ini_w(
            'session.cookie_domain'))
        self.cookie_secure = space.int_w(config.get_ini_w(
            'session.cookie_secure'))
        self.cookie_httponly = space.int_w(config.get_ini_w(
            'session.cookie_httponly'))
        self.cache_expire = space.int_w(config.get_ini_w(
            'session.cache_expire'))
        self.cache_limiter = space.str_w(config.get_ini_w(
            'session.cache_limiter'))
        self.save_path = space.str_w(config.get_ini_w('session.save_path'))
        w_module_name = config.get_ini_w('session.module_name')
        if w_module_name is None:
            self.module_name = None
        else:
            self.module_name = space.str_w(w_module_name)
        self.serialize_handler = space.str_w(config.get_ini_w(
            'session.serialize_handler'))

    def is_active(self):
        return self.status == PHP_SESSION_ACTIVE

    def write_close(self, interp):
        session_var = self.get_session_var(interp)
        serialize_val = self.serialize(interp, session_var)
        self.create_session_file(interp, serialize_val)
        self.deactivate()
        return serialize_val

    def get_session_var(self, interp):
        return interp.globals.get_var(interp.space, '_SESSION')

    def get_cookie_var(self, interp):
        return interp.globals.get_var(interp.space, '_COOKIE')

    def serialize(self, interp, w_ses):
        space = interp.space
        if not w_ses:
            return ""
        res = StringBuilder()
        memo = SerializerMemo()
        w_ses = w_ses.deref()
        with space.iter(w_ses.deref()) as itr:
            while not itr.done():
                w_key, w_value = itr.next_item(space)
                if space.is_integer(w_key):
                    num = space.int_w(w_key.as_number(space))
                    interp.notice("session_encode(): "
                                         "Skipping numeric key %d" % num)
                    continue
                key = space.str_w(w_key)

                if key.find('!') > 0:
                    continue
                res.append(key)
                res.append('|')
                w_value.serialize(space, res, memo)
        return res.build()

    def unserialize(self, interp, data):
        return unserialize_returning_dict(interp.space, data)

    def unset(self, interp):
        w_sess = self.get_session_var(interp)
        w_sess.store(interp.space.new_array_from_pairs([]))
