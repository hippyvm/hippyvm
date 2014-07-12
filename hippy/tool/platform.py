import os, sys

def get_gmake():
    """ Locate GNU make """
    try:
        GMAKE = os.environ["MAKE"]
    except KeyError:
        if "bsd" in sys.platform:
            GMAKE = "gmake"
        else:
            GMAKE = "make"
    return GMAKE
