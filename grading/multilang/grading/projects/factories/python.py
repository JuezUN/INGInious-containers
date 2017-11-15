import os.path
import tempfile

from grading.projects.factories.utils import CODE_WORKING_DIR
from grading.projects.project import ProjectFactory, LambdaProject


class PythonProjectFactory(ProjectFactory):
    """
    Implementation of ProjectFactory for Python.
    """

    def __init__(self, sandbox_runner, main_file_name='main.py', python_binary='python', additional_flags=None):
        """
        Initializes an instance of PythonProjectFactory with the given options.

        Arguments:
        main_file_name -- The name of the file to run. If running a code, this will also be the name
            of the file where the code will be stored.
        """

        self._sandbox_runner = sandbox_runner
        self._main_file_name = main_file_name
        self._python_binary = python_binary
        self._additional_flags = additional_flags if additional_flags is not None else []

    def create_from_code(self, code):
        project_directory = tempfile.mkdtemp(dir=CODE_WORKING_DIR)

        with open(os.path.join(project_directory, self._main_file_name), 'w') as main_file:
            main_file.write(code)

        return self.create_from_directory(project_directory)

    def create_from_directory(self, directory):
        def run(input_file):
            command = [self._python_binary, self._main_file_name] + self._additional_flags

            return self._sandbox_runner.run_command(command, stdin=input_file, cwd=directory)

        return LambdaProject(run_function=run)

