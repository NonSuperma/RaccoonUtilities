class MissingInputError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class DirectoryError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class FfmpegGeneralError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class FfmpegConcadError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
