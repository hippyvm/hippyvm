
from hippy.main import entry_point
from rpython.jit.codewriter.policy import JitPolicy


def target(driver, args):
    driver.exe_name = 'hippy-c'
    return entry_point, None


def jitpolicy(driver):
    return JitPolicy()
