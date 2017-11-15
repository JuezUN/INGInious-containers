

class BuildError(Exception):
    def __init__(self, compilation_output):
        self.compilation_output = compilation_output


class ProjectNotBuiltError(Exception):
    pass
