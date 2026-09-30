"""Internal build and validation tooling for the curious-signals repository."""


class ToolError(RuntimeError):
    """A tooling step failed in a way the command line reports without a traceback."""
