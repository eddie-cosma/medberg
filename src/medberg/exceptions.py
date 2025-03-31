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
