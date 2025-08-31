import ctypes.util


def load_library(name: str):
    path = ctypes.util.find_library(name)
    if not path:
        raise Exception("Unable to load " + name)

    return ctypes.cdll.LoadLibrary(path)