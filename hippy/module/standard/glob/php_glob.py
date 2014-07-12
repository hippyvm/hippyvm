from hippy.builtin import wrap, Optional
from hippy.module.standard.glob.cglob import _glob
from hippy.module.standard.file.funcs import _valid_fname


@wrap(['interp', str, Optional(int)])
def glob(interp, pattern, flags=0):
    if not _valid_fname(pattern):
        interp.space.ec.warn(
            "glob() expects parameter 1 to be a valid path, string given")
        return interp.space.w_Null
    r, files = _glob(pattern, flags)
    if r != 0 and files != []:
        return interp.space.w_False
    res_list = []
    for i in files:
        res_list.append(interp.space.newstr(i))
    return interp.space.new_array_from_list(res_list)
