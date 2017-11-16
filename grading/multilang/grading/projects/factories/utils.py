import subprocess
import time
import psutil
import os
from grading.results import GraderResult, parse_non_zero_return_code
from grading.projects.project import RunResult
from abc import ABCMeta, abstractmethod

CODE_WORKING_DIR = '/task/student/'


class ProcessProfiler(object):
    def profile(self, *subprocess_args, poll_interval=0.1, **subprocess_kwargs):
        initial_time = time.perf_counter()
        process = psutil.Popen(*subprocess_args, **subprocess_kwargs)
        max_memory_usage = 0

        while process.poll() is None:
            memory_usage = self._poll_memory_usage(process)
            max_memory_usage = max(max_memory_usage, memory_usage)
            time.sleep(poll_interval)

        execution_time = time.perf_counter() - initial_time

        return process, execution_time, max_memory_usage

    def _poll_memory_usage(self, process):
        related_processes = process.children(recursive=True) + [process]

        memory_usage = 0
        for related_process in related_processes:
            try:
                memory_info = related_process.memory_full_info()
                memory_usage += memory_info.uss

            except psutil.NoSuchProcess:
                # This is an expected race condition.
                pass

        return memory_usage




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
        profiler = ProcessProfiler()
        process, execution_time, max_memory_usage = profiler.profile(
            ["run_student"] + command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **subprocess_options)

        stdout = process.stdout.read().decode()
        stderr = process.stderr.read().decode()
        return_code = process.returncode

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
