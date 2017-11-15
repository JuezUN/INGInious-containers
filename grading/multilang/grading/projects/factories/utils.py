import subprocess
from grading.results import GraderResult, parse_non_zero_return_code
from abc import ABCMeta, abstractmethod

CODE_WORKING_DIR = '/task/student/'


class SandboxRunner(metaclass=ABCMeta):
    @abstractmethod
    def run_command(self, command, **subprocess_options):
        """
        Runs the given command with the given options in a sandbox and returns a tuple of
        (return_code, stdout, stderr).  The subprocess_options are sent directly to subprocess.run().

        Arguments:
        command -- A list specifying the program and the arguments to be run.
        subprocess_options -- Additional options sent to subprocess.run.
        """
        pass


class InginiousSandboxRunner(SandboxRunner):
    """
    Implementation of SandboxRunner that uses run_student as a sandbox.
    """
    def run_command(self, command, **subprocess_options):
        completed_process = subprocess.run(["run_student"] + command, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, **subprocess_options)

        stdout = completed_process.stdout.decode()
        stderr = completed_process.stderr.decode()
        return_code = completed_process.returncode

        return return_code, stdout, stderr


def _get_compilation_message_from_return_code(return_code):
    if return_code == 0:
        return ""

    result = parse_non_zero_return_code(return_code)

    if result == GraderResult.MEMORY_LIMIT_EXCEEDED:
        return "The memory limit was exceeded during compilation."
    elif result == GraderResult.TIME_LIMIT_EXCEEDED:
        return "The time limit was exceeded during compilation."
    elif result in [GraderResult.INTERNAL_ERROR, GraderResult.RUNTIME_ERROR]:
        return "Compilation failed."
    else:
        raise AssertionError("Unhandled grader result: " + str(result))
