class InvalidFileException(Exception):
    def __init__(self):
        message = "The specified file was not found on the secure site."
        super().__init__(message)