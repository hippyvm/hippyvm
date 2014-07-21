def get_from_pymodule(pyspace, module, name):
    w_module = pyspace.getbuiltinmodule(module)
    return pyspace.getattr(w_module, pyspace.wrap(name))
