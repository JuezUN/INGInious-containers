import os
import tempfile
import subprocess
from projects import ProjectFactory, LambdaProject, CODE_WORKING_DIR


def _run_in_sandbox(command, **subprocess_options):
    """
    Runs the given command with the given options and returns a tuple of
    (return_code, stdout, stderr). It is provided as a helper method for implementations of
    Project. The subprocess_options are sent directly to subprocess.run().

    Arguments:
    command -- A list specifying the program and the arguments to be run.
    subprocess_options -- Additional options sent to subprocess.run.
    """

    completed_process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **subprocess_options)

    stdout = completed_process.stdout.decode()
    stderr = completed_process.stderr.decode()
    return_code = completed_process.returncode

    return return_code, stdout, stderr


class NotebookProjectFactory(ProjectFactory):
    """
    Implementation of ProjectFactory for Notebooks.
    """

    def __init__(self, main_file_name='main.py', python_binary='python3', additional_flags=None):
        """
        Initializes an instance of NotebookProjectFactory with the given options.

        Arguments:
        main_file_name -- The name of the file to run. If running a code, this will also be the name
            of the file where the code will be stored.
        """

        # self._main_file_name = main_file_name
        # self._python_binary = python_binary
        self._additional_flags = additional_flags if additional_flags is not None else []

    # This method does not apply for notebooks.
    def create_from_code(self, code=None):
        return

    def create_from_directory(self, directory=None):
        def run(input_file):
            command = ["ok", "--local", "--score"] + ["-q", input_file] + self._additional_flags

            return _run_in_sandbox(command)

        return LambdaProject(run_function=run)


def get_notebook_factory():
    return NotebookProjectFactory(additional_flags=["--timeout", "20"])
