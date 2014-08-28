from rpython.config.config import OptionDescription, BoolOption, Config
from rpython.rlib.objectmodel import specialize

class HippyOptionError(Exception): pass

OPTIONAL_EXTS = ["mysql", "hash", "fastcgi", "xml", "mcrypt"]

optexts_descriptions = [
        BoolOption("allexts", "Enable all extensions",
           default=False,
           cmdline="--allexts",
           requires=[("optexts.%s" % e, True) for e in OPTIONAL_EXTS]
        )] + [
            BoolOption(extname, "Enable %s extension" % extname,
            default=False,
            cmdline="--withext-%s" % extname
        ) for extname in OPTIONAL_EXTS]

hippy_optiondescription = OptionDescription("optexts",
    "Optional extensions", optexts_descriptions)

# You need this top-level container when calling Config ctor directly.
# You don't need this is the target because the opt parser does this part.
top_hippy_optiondescription = \
        OptionDescription("hippy", "all options", [
            BoolOption("translating", "Are we translating?", default=False),
            hippy_optiondescription])


OPTIONS = Config(top_hippy_optiondescription) # default config


def set_options(config):
    import sys
    thismod = sys.modules[__name__]
    setattr(thismod, "OPTIONS", config)


def enable_all_optional_extensions():
    for extname in OPTIONAL_EXTS:
        setattr(OPTIONS.optexts, extname, True)


@specialize.memo()
def is_optional_extension_enabled(extname):
    try:
        __import__('ext_module.%s' % extname)
        on_import_path = True
    except ImportError:
        on_import_path = False

    try:
        return getattr(OPTIONS.optexts, extname) and on_import_path
    except AttributeError:
        raise HippyOptionError("No optional extension named '%s'" % extname)
