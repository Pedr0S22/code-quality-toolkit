"""Custom exception types for the toolkit core."""


class ToolkitError(Exception):
    """Base class for toolkit-specific exceptions."""


class PluginLoadError(ToolkitError):
    """Raised when a plugin fails to load or import."""


class PluginValidationError(ToolkitError):
    """Raised when a plugin does not comply with the contract."""


class ConfigurationError(ToolkitError):
    """Raised when configuration files are invalid."""


class AnalysisExecutionError(ToolkitError):
    """Raised for runtime errors during analysis."""
