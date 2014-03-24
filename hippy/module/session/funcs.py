from hippy.builtin import wrap
from hippy.builtin import Optional
from hippy.builtin import BoolArg
from hippy.objects.base import W_Root
from collections import OrderedDict

PHP_WHITESPACE = '\x0b\0'


@wrap(['interp', Optional(W_Root)])
def session_cache_expire(interp, w_new=None):
    """Return current cache expire"""
    act = interp.session.cache_expire
    space = interp.space
    if not w_new:
        return space.newint(act)

    w_num = space.as_number(w_new)
    interp.config.set_ini_w('session.cache_expire', w_num)
    n = space.int_w(w_num)
    interp.session.cache_expire = n
    return space.newint(act)


@wrap(['interp', Optional(str)])
def session_cache_limiter(interp, limiter=None):
    """Get and/or set the current cache limiter"""
    act = interp.session.cache_limiter
    space = interp.space
    if limiter is None:
        return space.newstr(act)

    if not limiter:
        limiter = ""
    interp.config.set_ini_w('session.cache_limiter', space.wrap(limiter))
    interp.session.cache_limiter = limiter
    return space.newstr(act)


@wrap(['space', 'interp', str])
def session_decode(space, interp, data):
    """Decodes session data from a session encoded string"""
    if interp.session.is_active():
        w_session = interp.session.get_session_var(interp)
        d = interp.session.unserialize(interp, data)
        if not d:
            return space.w_True
        w_session.store(interp.space.new_array_from_rdict(d))
        return space.w_True
    return space.w_False


@wrap(['interp'])
def session_destroy(interp):
    """Destroys all data registered to a session"""
    if not interp.session.is_active():
        interp.warn("session_destroy(): Trying to destroy "
                      "uninitialized session")
        return interp.space.w_False
    interp.session.destroy(interp)
    return interp.space.w_True


@wrap(['interp'])
def session_encode(interp):
    """Encodes the current session data as a session encoded string"""
    ses = interp.session
    if ses.is_active():
        res = ses.serialize(interp, ses.get_session_var(interp))
        if res == "":
            return interp.space.w_False
        return interp.space.wrap(res)
    interp.warn("session_encode(): Cannot encode non-existent session")
    return interp.space.w_False


@wrap(['interp'])
def session_get_cookie_params(interp):
    """Get the session cookie parameters"""
    space = interp.space
    rdict_w = OrderedDict()
    for item in ['lifetime', 'path', 'domain']:
        rdict_w[item] = interp.config.get_ini_w('session.cookie_' + item)
    for item in ['secure', 'httponly']:
        rdict_w[item] = space.wrap(bool(space.int_w(
            interp.config.get_ini_w('session.cookie_' + item))))
    return space.new_array_from_rdict(rdict_w)


def clean_name(name):
    res = ""
    for c in name:
        if c in PHP_WHITESPACE:
            continue
        res += c
    return res


@wrap(['space', Optional(str)])
def session_id(space, _session_id=None):
    """Get and/or set the current session id"""
    act = space.ec.interpreter.session.session_id
    if _session_id is None:
        return space.newstr(act)

    if not _session_id:
        _session_id = ""
    space.ec.interpreter.session.session_id = clean_name(_session_id)
    return space.wrap(act)


def session_is_registered():
    """Find out whether a global variable is registered in a session"""
    pass


@wrap(['space', Optional(str)])
def session_module_name(space, module_name=None):
    """Get and/or set the current session module
       what this function does is mistery"""
    act = space.ec.interpreter.session.module_name
    if module_name is not None:
        if module_name == "\0":
            module_name = ""
        space.ec.interpreter.session.module_name = module_name
    return space.wrap(act)


def _contains_letter(_str):
    for c in _str:
        if (c > 'a' and c < 'z') or\
           (c > 'A' and c < 'Z') or c == '\t' or c == "\0":
            return True
    return False


@wrap(['interp', Optional(W_Root)])
def session_name(interp, w_name=None):
    """Get and/or set the current session name"""
    space = interp.space
    act = interp.session.name
    if w_name is None:
        return space.wrap(act)
    name = space.str_w(space.as_string(w_name))

    if w_name.tp == space.tp_int or\
       w_name.tp == space.tp_float or\
       w_name.tp == space.tp_bool or\
       w_name.tp == space.tp_null:
        interp.warn("session_name(): session.name "
                      "cannot be a numeric or empty '%s'" % name)
        return space.wrap(act)

    if space.is_resource(w_name):
        interp.warn("session_name() expects "
                      "parameter 1 to be string, resource given")
        return space.w_Null
    if name == '':
        interp.warn("session_name(): session.name "
                      "cannot be a numeric or empty '%s'" % name)
        return space.wrap(act)

    if name != '\0':
        interp.session.name = name
        interp.config.set_ini_w('session.name', space.wrap(name))

    return space.wrap(act)


@wrap(['space', Optional(BoolArg(None))])
def session_regenerate_id(space, delete_old_session=False):
    """Update the current session id with a newly generated one"""
    if space.ec.interpreter.session.is_active():
        space.ec.interpreter.session.create_id()
        return space.w_True
    return space.w_False


def session_register_shutdown():
    """Session shutdown function"""
    pass


# removed in 5.4
def session_register():
    """Register one or more global variables with the current session"""


@wrap(['interp', Optional(str)])
def session_save_path(interp, path=None):
    """Get and/or set the current session save path"""
    w_act = interp.config.get_ini_w('session.save_path')
    if not path:
        path = ""
        interp.session.save_path = path
    else:
        interp.config.set_ini_w('session.save_path', interp.space.wrap(path))
    return w_act


@wrap(['interp', W_Root, Optional(str),
       Optional(str), Optional(BoolArg(None)),
       Optional(BoolArg(None))])
def session_set_cookie_params(interp, w_lifetime, path=None, domain=None,
                              secure=False, httponly=False):
    """Set the session cookie parameters"""
    space = interp.space
    if space.is_resource(w_lifetime):
        return space.w_Null
    lifetime = space.str_w(w_lifetime)
    ses = interp.session
    try:
        lt = int(lifetime)
        ses.cookie_lifetime = lt
        interp.config.set_ini_w('session.cookie_lifetime', w_lifetime)
    except ValueError:
        pass
    interp.config.set_ini_w('session.cookie_secure', space.wrap(int(secure)))
    ses.cookie_secure = secure
    interp.config.set_ini_w('session.cookie_httponly',
                            space.wrap(int(httponly)))
    ses.cookie_httponly = httponly
    if path:
        interp.config.set_ini_w('session.cookie_path', space.wrap(path))
        ses.cookie_path = path
    if domain:
        interp.config.set_ini_w('session.cookie_domain', space.wrap(domain))
        ses.cookie_domain = domain
    return space.w_Null


def session_set_save_handler():
    """Sets user-level session storage functions"""
    pass


@wrap(['interp', 'args_w'])
def session_start(interp, args_w):
    """Start new or resume existing session"""
    if interp.session.is_active():
        interp.notice("A session had already been "
                        "started - ignoring session_start()")
        return interp.space.w_True
    res = interp.session.start(interp)
    return interp.space.newbool(res)


@wrap(['space'])
def session_status(space):
    """Returns the current session status"""
    return space.wrap(space.ec.interpreter.session.status)


# removed in 5.4
def session_unregister():
    """Unregister a global variable from the current session"""


@wrap(['interp', 'args_w'])
def session_unset(interp, args_w):
    """Free all session variables"""
    if len(args_w) != 0:
        return interp.space.w_False
    if interp.session.is_active():
        interp.session.unset(interp)
        return interp.space.w_Null
    return interp.space.w_False


@wrap(['interp', 'args_w'], aliases=['session_commit'])
def session_write_close(interp, args_w=None):
    """Write session data and end session"""
    interp.session.write_close(interp)
