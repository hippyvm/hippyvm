from testing.test_interpreter import BaseTestInterpreter
from hippy.hippyoption import (is_optional_extension_enabled, OPTIONAL_EXTS,
    enable_all_optional_extensions)

class TestOptionalExtensions(object):
    """ Test optional extensions mechanisms """

    def test_all_enabled(self):
        # for tests, all extensions should be enabled
        for ext in OPTIONAL_EXTS:
            assert is_optional_extension_enabled(ext)
