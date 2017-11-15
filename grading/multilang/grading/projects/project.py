from abc import abstractmethod, ABCMeta
from .errors import ProjectNotBuiltError


class Project(object, metaclass=ABCMeta):
    """
    Represents a runnable code project. Subclasses must take care of running the code using the
    run_student command.
    """

    def __init__(self):
        self._is_built = False

    def build(self):
        """
        Builds this project. A BuildError is thrown if the project cannot be built.

        A call to this method is mandatory before a call to the run method.
        Subclasses should override _do_build() instead of this method.
        """

        self._do_build()
        self._is_built = True

    @abstractmethod
    def _do_build(self):
        """
        Subclasses should override this method to perform the actual build logic.
        A BuildError should be thrown if the project cannot be built (the build process
        is assumed to be successful if no error is thrown).
        """
        pass

    @abstractmethod
    def run(self, input_file):
        """
        Executes this project with the given input file and returns a tuple of
        (return_code, stdout, stderr), where return_code is the status code the process finished
        with, and stdout and stderr are strings with the standard and the error output of the
        program.

        The project must be built before any call to this method, or a ProjectNotBuiltError will
        be thrown.

        Subclasses must call this implementation before any custom logic, to properly validate that
        the project was built.

        Arguments:
        input_file -- a file-like object to be sent as stdin to the code process.
        """

        if not self._is_built:
            raise ProjectNotBuiltError()


class LambdaProject(Project):
    """
    A Project implementation that takes the run and _do_build functions as parameters.
    """

    def __init__(self, run_function, build_function=None):
        super().__init__()

        assert run_function is not None

        if build_function is None:
            build_function = lambda: None

        self._run = run_function
        self._build = build_function

    def _do_build(self):
        self._build()

    def run(self, input_file):
        super().run(input_file)

        return self._run(input_file)


class ProjectFactory(object, metaclass=ABCMeta):
    """
    Represents a factory of code projects.
    """

    @abstractmethod
    def create_from_code(self, code):
        """
        Creates a Project instance from the given code.

        Arguments:
        code -- a string with the code of the project.
        """
        pass

    @abstractmethod
    def create_from_directory(self, directory):
        """
        Creates a Project from the given directory.

        Arguments:
        directory -- the root directory of the project.
        """

        pass
