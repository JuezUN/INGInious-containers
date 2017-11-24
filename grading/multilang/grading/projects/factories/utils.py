import subprocess
import json
from grading.results import GraderResult, parse_non_zero_return_code
from grading.projects.project import RunResult
from abc import ABCMeta, abstractmethod

CODE_WORKING_DIR = '/task/student/'

class SandboxRunner(metaclass=ABCMeta):
    @abstractmethod
    def run_command(self, command, **subprocess_options):
        """
        Runs the given command with the given options in a sandbox and returns an instance of RunResult.
        The subprocess_options are sent directly to subprocess.run().

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
        execution_info_file = "/task/execution_info.json"
        completed_process = subprocess.run(
            ["run_student", "--execution-info-file", execution_info_file] + command, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, **subprocess_options)

        stdout = completed_process.stdout.decode()
        stderr = completed_process.stderr.decode()
        return_code = completed_process.returncode

        execution_time = None
        max_memory_usage = None

        try:
            with open(execution_info_file, "r") as f:
                execution_info = json.loads(f.read())
                execution_time = execution_info["execution_time"]
                max_memory_usage = execution_info["max_memory_usage"]
        except IOError as e:
            # If the file is not available, just ignore it. This might happen because the run_student process
            # was killed before it finished.
            print("Execution information could not be retrieved:", e)
            pass

        return RunResult(return_code=return_code, stdout=stdout, stderr=stderr, execution_time=execution_time,
                         memory_usage=max_memory_usage)


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
