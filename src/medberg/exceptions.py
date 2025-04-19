"""Custom exceptions for the medberg package."""


class LoginException(Exception):
    """Raised when login fails."""

    def __init__(self):
        message = "The username or password provided is incorrect. A connection to the secure site could not be established."
        super().__init__(message)


class InvalidFileException(Exception):
    """Raised when an invalid file is requested."""

    def __init__(self):
        message = "The specified file was not found on the secure site."
        super().__init__(message)


class FileDownloadFailureException(Exception):
    """Raised when a file download fails."""

    def __init__(self):
        message = "The specified file failed to download. This sometimes occurs because of rate limiting on the secure site."


class InvalidFilterException(Exception):
    """Raised when an invalid filter is applied to a list of Files."""

    def __init__(self):
        message = "The specified filter is invalid. Please ensure the filter value is a string, integer, callable, or valid iterable (list, tuple)."
        super().__init__(message)


class MissingRowPatternException(Exception):
    """Raised when attempting to parse a file without a row pattern."""

    def __init__(self):
        message = "A row pattern must be specified before attempting to parse a file. A pattern could not be automatically determined. Set one manually to continue."


class EmptyBufferException(Exception):
    """Raised when attempting to dump am empty buffer to disk."""

    def __init__(self):
        message = "There was an error loading the saved file. To prevent data loss, no changes to the file have been made."
        super().__init__(message)
