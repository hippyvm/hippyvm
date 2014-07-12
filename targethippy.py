take_options = True

def get_additional_config_options():
    from hippy.hippyoption import hippy_optiondescription
    return hippy_optiondescription

def target(driver, args):
    driver.exe_name = 'hippy-c'
    config = driver.config

    from rpython.config.config import to_optparse, SUPPRESS_USAGE
    parser = to_optparse(config, parserkwargs={'usage': SUPPRESS_USAGE })
    parser.parse_args(args)

    from hippy.hippyoption import set_options
    set_options(config)

    from hippy.main import entry_point
    return entry_point, None

def jitpolicy(driver):
    from rpython.jit.codewriter.policy import JitPolicy
    return JitPolicy()
