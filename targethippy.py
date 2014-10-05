take_options = True

from hippy.main import mk_entry_point
from pypy.tool.ann_override import PyPyAnnotatorPolicy
from rpython.config.config import Config

from pypy.config.pypyoption import get_pypy_config

def get_additional_config_options():
    from hippy.hippyoption import hippy_optiondescription
    return hippy_optiondescription

class ConfigMergeError(Exception): pass

# 'translation.secondaryentrypoints' is 'main' in 'Hippy'
#     but 'cpyext,main' in 'PyPy'
# 'translation.withsmallfuncsets' is '5' in 'Hippy' but '0' in 'PyPy'
MERGE_RESOLUTIONS = {
    'translation.secondaryentrypoints' : 'cpyext,main', # PyPy
    'translation.withsmallfuncsets' : 5,                # Hippy
}

def _pstr(path_list):
    """ path list to string """
    return ".".join(path_list)

def get_merge_resolution(path_elems):
    try:
        return MERGE_RESOLUTIONS[_pstr(path_elems)]
    except KeyError:
        return None

def check_no_resolution(path_elems):
    res = get_merge_resolution(path_elems)
    if res is not None:
        raise ConfigMergeError(
                "Redundent merge resolution: '%s'" % _pstr(path_elems))

def merge_configs(c1, c2, c1_who="config1", c2_who="config2", path=[]):
    from rpython.config.config import Config

    for child in c2._cfgimpl_descr._children:
        name = child._name
        try:
            c1_sub = getattr(c1, name)
            found = True
        except AttributeError:
            found = False

        if found:
            # Both configs have this configuration key, merge.
            c2_sub = getattr(c2, child._name)
            assert type(c1_sub) == type(c2_sub)

            if type(c1_sub) == Config:
                # Recurse lower
                check_no_resolution(path + [name])
                merge_configs(c1_sub, c2_sub, c1_who, c2_who, path + [name])
            else:
                # A leaf, check the values are the same
                if c1_sub != c2_sub:
                    resolution = get_merge_resolution(path + [name])
                    if resolution is None:
                        # Merge conflict with no resolution. Barf.
                        raise ConfigMergeError(
                                "'%s' is '%s' in '%s' but '%s' in '%s'" % (
                                _pstr(path + [name]),
                                c1_sub, c1_who, c2_sub, c2_who))
                    else:
                        # use the resolved value
                        setattr(c1, name, resolution)
                else:
                    # If we get here, it was a leaf with no conflict, do nothing
                    check_no_resolution(path + [name])
        else:
            # c1 does not have this whole subtree, so just copy it in
            value = getattr(c2, child._name)
            c1._cfgimpl_values[child._name] = value

# Stashed from handle_config
TRANSLATECONFIG = [None]

def target(driver, args):
    driver.exe_name = 'hippy-c'
    config = driver.config
    translateconfig = TRANSLATECONFIG[0]

    # Parse hippy options
    from rpython.config.config import to_optparse, SUPPRESS_USAGE
    parser = to_optparse(config, parserkwargs={'usage': SUPPRESS_USAGE })
    parser.parse_args(args)


    from hippy.hippyoption import (
        OPTIONAL_EXTS, is_optional_extension_enabled, HippyOptionError)

    from hippy.hippyoption import set_options
    set_options(config)

    for ext in OPTIONAL_EXTS:
        asked = getattr(config.optexts, ext)
        if asked and not is_optional_extension_enabled(ext):
            raise HippyOptionError("%s extension sources are missing!" % ext)

    # We need to merge a PyPy configurtaion into the hippy config
    pypy_config = get_pypy_config(translating=True)

    from pypy.config.pypyoption import enable_allworkingmodules
    from pypy.config.pypyoption import enable_translationmodules
    enable_allworkingmodules(pypy_config)
    enable_translationmodules(pypy_config)

    # ensures pypy_hooks has a .space
    pypy_config.objspace.usemodules.pypyjit = True

    #config.translation.check_str_without_nul = True

    # Makes C errors, e.g.: XXX
    # implement_18.c: In function
    #    'pypy_g_ccall_XML_ParserCreateNS__arrayPtr_Char':
    # implement_18.c:25541:2: error:
    #    'pypy_g_array1_24' undeclared (first use in this function)
    # pypy_g_array1_24[0] = l_a1_140;
    pypy_config.objspace.usemodules.pyexpat = False

    # And stuff for the non-goal-specific config
    if (not translateconfig.help and
        translateconfig._cfgimpl_value_owners['opt'] == 'default'):
        raise Exception("You have to specify the --opt level.\n"
                "Try --opt=2 or --opt=jit, or equivalently -O2 or -Ojit .")

    # set up the objspace optimizations based on the --opt argument
    from pypy.config.pypyoption import set_pypy_opt_level
    set_pypy_opt_level(pypy_config, translateconfig.opt)

    # JIT/GC enablement should mirror from hippy
    # (just to prevent merge conflicts)
    pypy_config.translation.jit = config.translation.jit
    pypy_config.translation.gc = config.translation.gc

    from pypy.objspace.std import multimethod
    if pypy_config.objspace.std.multimethods == 'mrd':
        assert multimethod.InstallerVersion1.instance_counter == 0,\
               'The wrong Installer version has already been instatiated'
        multimethod.Installer = multimethod.InstallerVersion2
    elif pypy_config.objspace.std.multimethods == 'doubledispatch':
        # don't rely on the default, set again here
        assert multimethod.InstallerVersion2.instance_counter == 0,\
               'The wrong Installer version has already been instatiated'
        multimethod.Installer = multimethod.InstallerVersion1

    merge_configs(config, pypy_config, "Hippy", "PyPy")

    # XXX Turn continuations on. Or we get:
    # AssertionError: stacklet: you have to translate with --continuation
    # Should be fixed properly someday.
    config.translation.continuation = True

    # PyPy needs threads
    config.translation.thread = True

    # XXX hack to make this translate on OpenBSD with LibreSSL
    pypy_config.objspace.usemodules._ssl = False

    # Python objectspace ctor is not Rpython so create it here and
    # encapsulate it inside the entry point with a closure.
    from pypy.objspace.std import StdObjSpace as PyStdObjSpace
    py_space = PyStdObjSpace(config)

    return mk_entry_point(py_space), None, PyPyAnnotatorPolicy()

def handle_config(config, translateconfig):
    TRANSLATECONFIG[0] = translateconfig # XXX better way to get at this?

def jitpolicy(driver):
    from pypy.module.pypyjit.policy import PyPyJitPolicy, pypy_hooks
    return PyPyJitPolicy(pypy_hooks)
