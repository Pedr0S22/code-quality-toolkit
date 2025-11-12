"""Plugin discovery and loading utilities."""

from __future__ import annotations

import importlib.util
import inspect
import sys
from collections.abc import Iterable
from pathlib import Path
from types import ModuleType

from . import logging
from .contracts import PluginMetadata, PluginProtocol
from .errors import PluginLoadError, PluginValidationError

# Define a variable that contains the absolute file system path to the
# application's plugins directory, assuming a specific project structure relative
# to the file where this line of code resides:
#
# '__file__' is a built-in variable in Python that holds the path (string) to the
# current module file.
# 'resolve()' converts the path to its absolute form, and resolves any relative
# components like src/toolkit/plugins/<plugin_name_folder>/plugin.py
# 'parent' gets the directory (folder) containing the current file
# The '/' operator is used here for path joining, and appends the string "plugins"
# as a new segment to the plugins path being calculated
PLUGIN_ROOT = Path(__file__).resolve().parent.parent / "plugins"


def _iter_plugin_modules() -> Iterable[tuple[str, Path]]:
    """
    This is a generator that scans the predefined plugin root directory,
    identifies valid plugin modules, and returns their names and file paths.
    It provides the exact file locations to the load_plugins function.

    Returns an Iterable of tuples. Each tuple contains a plugin's name (str)
    and its file path (Path).
    """

    for (
        plugin_dir
    ) in PLUGIN_ROOT.iterdir():  # .iterdir() is a pathlib method that iterates over
        # all files and subdirectories immediately within PLUGIN_ROOT.
        if (
            not plugin_dir.is_dir()
        ):  # checks if the current item found (plugin_dir) is actually a directory.
            continue  # in which case it skips the item and moves to the next one.
            # This ensures that only plugin directories are processed.
        # == Locating the Plugin File ==
        # Uses the path joining operator (/) to construct the expected path to the
        # primary plugin entry file. This enforces a project convention:
        # *Every plugin must be contained in a file named plugin.py inside
        # its directory*.
        module_file = plugin_dir / "plugin.py"
        if module_file.exists():
            """
            Yield Result: If the file exists, the generator yields a tuple
            containing:
            - plugin_dir.name: The name of the directory, which is used as the
                plugin's unique package name.
            - module_file: The full pathlib.Path object pointing to the
            plugin.py file.
            """
            yield (plugin_dir.name, module_file)


def _import_module_from_path(name: str, path: Path) -> ModuleType:
    """
    This function is a low-level utility responsible for programmatically loading
    and executing a Python module (the plugin file) directly from a file path.
    This is crucial in the dynamic plugin loading process,
    allowing the main application to use code that isn't part of its initial imports.

    It relies on the importlib module (part of the standard Python library), which
    provides the tools for custom import mechanisms.
    """

    # == Creation of the module specification (spec)
    """
    This is the core step: it creates an ModuleSpec object (spec), which is a
    blueprint for the module.
    - The first argument, f"toolkit.plugins.{name}.plugin", defines the fully
        qualified name under which the module will be known in the system.
        This hierarchical naming helps avoid naming collisions.
    - path: The second argument tells the system where to find the module file
        (plugin.py).
    """
    spec = importlib.util.spec_from_file_location(
        f"toolkit.plugins.{name}.plugin", path
    )
    # Check if the specification or its loader component could not be created.
    # If that is the case, raise a PluginLoadError, signaling an environment or
    # path issue.
    if spec is None or spec.loader is None:
        raise PluginLoadError(f"Unable to create spec for plugin {name}")

    # otherwise, keep calm and move on ;)

    # == Creating the Module Object ==

    # Create the actual module object (module) in memory, based on the blueprint
    # established by spec. At this point the module exists but its code hasn't
    # been executed yet.
    module = importlib.util.module_from_spec(spec)

    # Register the newly created module object in Python's global dictionary of
    # loaded modules (sys.modules). This ensures that if the application tries
    # to import this module again, it will retrieve this exact object instead of
    # attempting to load it again.
    sys.modules[spec.name] = module

    # == Executing the Module Code ==
    # This is the step that executes the plugin.py code.
    # using a try block to catch any error that occurs during the execution of
    # the plugin's code.
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001 - propagate as PluginLoadError
        # this is a linter instruction to do not flag such broad exception
        # Any execution error is caught and explicitly re-raised as a
        # specific PluginLoadError, thus clearly indicating which plugin failed
        # to import and preserving the original exception context.
        raise PluginLoadError(f"Failed to import plugin {name}: {exc}") from exc

    # The successfully initialized and executed module object is returned.
    # This object can then be inspected to find the actual plugin
    # class for instantiation.
    return module


def _instantiate_plugin(module: ModuleType, package_name: str) -> PluginProtocol:
    """
    This function finalizes the plugin loading process by taking a dynamically
    imported module and creating a runnable instance of the plugin, while enforcing
    strict structural validation to ensure the plugin adheres to the required
    application protocol.

    It receives two arguments: the dynamically loaded module object
    (from '_import_module_from_path') and its package_name (e.g., "stylechecker").
    It returns an object conforming to the PluginProtocol.
    """

    # == Locating the Plugin Class/Object ==

    # This code mandates a convention: every valid plugin module must define
    # an attribute named Plugin. If it's missing, a PluginValidationError is raised.
    if not hasattr(module, "Plugin"):
        raise PluginValidationError(
            f"Plugin module {package_name} missing 'Plugin' attribute"
        )

    # getattr retrieves this attribute. At this point, plugin_cls could be the
    # plugin class itself or an previously (already-) instantiated object
    # (a singleton).
    plugin_cls = module.Plugin

    # == Instantiation vs. Direct Use ==

    if inspect.isclass(plugin_cls):
        # If it is a class, the code instantiates it by calling it (plugin_cls()).
        # This is the standard way to handle object-oriented plugins.
        instance = plugin_cls()  # type: ignore[call-arg]

    else:
        # If it is not a class (which means that the plugin developer defined
        # and assigned an already-instantiated object to the Plugin attribute),
        # the code uses it directly. This accommodates singleton patterns where
        # the plugin initialization happens immediately upon module execution.
        instance = plugin_cls

    # Note: The variable 'instance:' now holds the final, runnable plugin object.

    # == Protocol Enforcement ==

    # This is the protocol validation step: it ensures that the plugin object
    # adheres to the expected interface (PluginProtocol):
    # - get_metadata: A method used to retrieve the plugin's name, version,
    #   and other details.
    # - analyze: The main method that contains the actual code inspection logic.
    # If either is missing, a PluginValidationError is raised, indicating the
    # plugin is structurally unusable.
    if not hasattr(instance, "get_metadata") or not hasattr(instance, "analyze"):
        raise PluginValidationError(
            f"Plugin {package_name} does not implement required methods"
        )

    # == Metadata Validation ==

    metadata = instance.get_metadata()

    # deeper checks on the metadata contents
    _validate_metadata(metadata, package_name)

    # The fully validated and instantiated plugin object is returned, ready for
    # use in the analysis.
    return instance  # type: ignore[return-value]


def _validate_metadata(metadata: PluginMetadata, package_name: str) -> None:
    """
    This function enforces the mandatory content requirements for a plugin's
    metadata dictionary. It ensures that every loaded plugin provides essential
    identification and descriptive fields.
    → "name", "version", "description"

    It acts as a gatekeeper, guaranteeing that every dynamically loaded plugin
    is properly labeled and described before it is allowed to participate in the
    code analysis.

    It takes the plugin's metadata (a dictionary-like object of type PluginMetadata)
    and the plugin's package_name (e.g., "stylechecker") for use in error messages.
    It returns None if the validation passes successfully.
    """

    # Iterate over a tuple of required keys: "name", "version", and "description".
    # These are the minimum fields needed to identify and describe any plugin.

    for key in ("name", "version", "description"):
        # If a key is missing, raises an exception indicating that the plugin
        # package is incomplete.
        if key not in metadata:
            raise PluginValidationError(
                f"Plugin {package_name} metadata missing '{key}'"
            )

        # If the key exists, check its value for being "falsy" (evaluating to
        # False in a boolean context).
        # It prevents plugins from passing the first check (key exists) but
        # providing useless, empty data.
        # If the value is empty an exception is raised to force the plugin
        # developer to provide meaningful content for the required field.
        if not metadata[key]:
            raise PluginValidationError(
                f"Plugin {package_name} metadata field '{key}' is empty"
            )


def load_plugins(requested: Iterable[str] | None = None) -> dict[str, PluginProtocol]:
    """Load plugins filtered by requested metadata names.

    Accepts an optional iterable of plugin names ('requested') and is type-hinted
    to return a dictionary where keys are plugin names (strings) and values are
    plugin objects (PluginProtocol).
    """

    # == Initialization ==
    plugin_instances: dict[str, PluginProtocol] = (
        {}
    )  # empty dictionary initialized to store the successfully instantiated plugins.

    # The input list of requested plugin names is converted into a set, which makes
    # membership checks (lookup) much faster than using a list. If requested is None,
    # this is also set to None.
    requested_set = {name for name in requested} if requested is not None else None

    # == Iterating, Importing, and Filtering Plugins ==

    # === Iterating ===
    for (
        package_name,
        module_file,
    ) in _iter_plugin_modules():  # Scan the plugin root directory and get
        # the name and path for each found plugin module file.

        # === Importing ===
        module = _import_module_from_path(
            package_name, module_file
        )  # dynamically imports the file as a Python 'module' object.
        plugin = _instantiate_plugin(
            module, package_name
        )  # finds the main plugin class within the imported module
        # and creates an instance of it (plugin).
        metadata = (
            plugin.get_metadata()
        )  # retrieves necessary information about the plugin, namely its unique name.

        # === Filtering ===
        # Check if a filter was applied (requested_set is not None) and if the
        # plugin's name is not in the requested set. If both are true, the plugin
        # is logged as skipped and the loop continues to the next module.
        if requested_set is not None and metadata["name"] not in requested_set:
            logging.log("plugin.skipped", plugin=metadata["name"], reason="filtered")
            continue

        # Check if a plugin with the same name has already been loaded. If so, it
        # raises a PluginValidationError, preventing configuration conflicts from
        # having two plugins with the same identifier.
        if metadata["name"] in plugin_instances:
            raise PluginValidationError(
                f"Duplicate plugin name detected: {metadata['name']}"
            )
        # otherwise, it is added to the plugin_instances dictionary using its
        # metadata name as the key. Success is logged with the plugin's name and
        # the module file path.
        plugin_instances[metadata["name"]] = plugin
        logging.log("plugin.loaded", plugin=metadata["name"], module=str(module_file))

    # == end of Iterating ==

    # == Missing Plugins Check ==
    if requested_set is not None:
        missing = sorted(
            requested_set - set(plugin_instances)
        )   # set containing all names that were requested but not successfully
            # added to plugin_instances.
        if missing:
            # a PluginLoadError is raised, detailing exactly which requested
            # plugins could not be loaded.
            raise PluginLoadError(f"Requested plugins not found: {', '.join(missing)}")
        # otherwise...

    # ...the dictionary of validated and loaded plugin instances is returned.
    return plugin_instances


def discover_plugins() -> list[str]:
    """Return plugin package names discovered on disk."""

    return sorted(name for name, _ in _iter_plugin_modules())
