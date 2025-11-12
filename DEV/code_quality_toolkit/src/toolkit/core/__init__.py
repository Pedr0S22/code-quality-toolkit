"""Core infrastructure for the Code Quality Toolkit."""


import typing as _t
if _t.TYPE_CHECKING:
    from . import cli as _cli  # for type checkers only # noqa: F401

def __getattr__(name):
    if name == "cli":
        from . import cli as _cli
        return _cli
    raise AttributeError(name)
