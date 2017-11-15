from grading.projects.project import ProjectFactory, LambdaProject
from grading.projects.errors import BuildError
from abc import ABCMeta


class MakefileProjectFactory(ProjectFactory, metaclass=ABCMeta):
    """
    Implementation of ProjectFactory for Makefile based projects.
    """

    def __init__(self, sandbox_runner):
        self._sandbox_runner = sandbox_runner

    def create_from_directory(self, directory):
        def build():
            compilation_command = ["make"]
            return_code, stdout, stderr = self._sandbox_runner.run_command(compilation_command, cwd=directory)
            if return_code != 0:
                raise BuildError(stderr)

        def run(input_file):
            run_command = ["make", "run"]
            return self._sandbox_runner.run_command(run_command, stdin=input_file, cwd=directory)

        return LambdaProject(run_function=run, build_function=build)

