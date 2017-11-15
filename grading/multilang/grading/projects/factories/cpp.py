import os.path
import tempfile

from grading.projects.errors import BuildError
from grading.projects.factories.utils import CODE_WORKING_DIR, _get_compilation_message_from_return_code
from grading.projects.project import LambdaProject
from .makefile import MakefileProjectFactory


class CppProjectFactory(MakefileProjectFactory):
    """
    Implementation of ProjectFactory for C++.
    """

    def __init__(self, sandbox_runner, additional_flags=None):
        """
        Initializes an instance of CppProjectFactory with the given options.
        """

        super().__init__(sandbox_runner)
        if additional_flags is None:
            additional_flags = []

        self._additional_flags = additional_flags

    def create_from_code(self, code):
        project_directory = tempfile.mkdtemp(dir=CODE_WORKING_DIR)
        with open(os.path.join(project_directory, "main.cpp"), 'w') as main_file:
            main_file.write(code)

        def build():
            compilation_command = ["g++", "main.cpp", "-o", "main"] + self._additional_flags
            return_code, stdout, stderr = self._sandbox_runner.run_command(compilation_command, cwd=project_directory)
            if return_code != 0:
                raise BuildError(_get_compilation_message_from_return_code(return_code) + "\n" + stderr)

        def run(input_file):
            run_command = ["./main"]
            return self._sandbox_runner.run_command(run_command, stdin=input_file, cwd=project_directory)

        return LambdaProject(run_function=run, build_function=build)
