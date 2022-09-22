from abc import abstractmethod, ABCMeta
from glob import glob
import os
import tempfile
import subprocess
from results import GraderResult, parse_non_zero_return_code

CODE_WORKING_DIR = '/task/student/'


def _run_in_sandbox(command, **subprocess_options):
    """
    Runs the given command with the given options and returns a tuple of
    (return_code, stdout, stderr). It is provided as a helper method for implementations of
    Project. The subprocess_options are sent directly to subprocess.run().

    Arguments:
    command -- A list specifying the program and the arguments to be run.
    subprocess_options -- Additional options sent to subprocess.run.
    """
    try:
        command_to_run = ["run_student"] + command
        completed_process = subprocess.run(command_to_run, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, **subprocess_options)

        stdout = completed_process.stdout.decode()
        stderr = completed_process.stderr.decode()
        return_code = completed_process.returncode

        return return_code, stdout, stderr
    except Exception as a:
        return GraderResult.INTERNAL_ERROR, "", str(a)


def _get_compilation_message_from_return_code(return_code):
    if return_code == 0:
        return ""

    result = parse_non_zero_return_code(return_code)

    if result == GraderResult.MEMORY_LIMIT_EXCEEDED:
        return _("The memory limit was exceeded during compilation.")
    elif result == GraderResult.TIME_LIMIT_EXCEEDED:
        return _("The time limit was exceeded during compilation.")
    elif result in [GraderResult.INTERNAL_ERROR, GraderResult.RUNTIME_ERROR]:
        return _("Compilation failed.")
    else:
        raise AssertionError(_("Unhandled grader result: ") + str(result))


class BuildError(Exception):
    def __init__(self, compilation_output):
        self.compilation_output = compilation_output


class ProjectNotBuiltError(Exception):
    pass


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
    def run(self, input_file, **run_student_flags):
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
        run_student_flags: several flags passed to the run_student container like --time, --hard-time and --memory
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

    def run(self, input_file, **run_student_flags):
        super().run(input_file, **run_student_flags)

        return self._run(input_file, **run_student_flags)


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


class PythonProjectFactory(ProjectFactory):
    """
    Implementation of ProjectFactory for Python.
    """

    def __init__(self, main_file_name='main.py', python_binary='python', additional_flags=None):
        """
        Initializes an instance of PythonProjectFactory with the given options.

        Arguments:
        main_file_name -- The name of the file to run. If running a code, this will also be the name
            of the file where the code will be stored.
        """

        self._main_file_name = main_file_name
        self._python_binary = python_binary
        self._additional_flags = additional_flags if additional_flags is not None else []

    def create_from_code(self, code):
        project_directory = tempfile.mkdtemp(dir=CODE_WORKING_DIR)

        with open(os.path.join(project_directory, self._main_file_name), 'w') as main_file:
            main_file.write(code)

        return self.create_from_directory(project_directory)

    def create_from_directory(self, directory):
        def run(input_file, **run_student_flags):
            sandbox_flags = _parse_run_student_args(**run_student_flags)
            command = sandbox_flags + [self._python_binary, self._main_file_name] + self._additional_flags

            return _run_in_sandbox(command, stdin=input_file, cwd=directory)

        return LambdaProject(run_function=run)


class JavaProjectFactory(ProjectFactory):
    """
    Implementation of ProjectFactory for Java.
    """

    def __init__(self, main_class='Main', source_version='1.8', sourcepath="src", classpath="lib",
                 bootclasspath=None):
        """
        Initializes an instance of JavaProjectFactory with the given options.

        Arguments:
        main_file_name -- The name of the file to run. If running a code, this will also be the name
            of the file where the code will be stored.
        """

        self._main_class = main_class
        self._main_file_name = self._main_class + ".java"
        self._source_version = source_version
        self._sourcepath = sourcepath
        self._classpath = classpath
        self._bootclasspath = bootclasspath

    def create_from_code(self, code):
        project_directory = tempfile.mkdtemp(dir=CODE_WORKING_DIR)
        source_directory = os.path.join(project_directory, self._sourcepath)
        os.makedirs(source_directory)

        with open(os.path.join(source_directory, self._main_file_name), 'w') as main_file:
            main_file.write(code)

        return self.create_from_directory(project_directory)

    def create_from_directory(self, directory):
        build_directory = os.path.join(directory, "build")
        if not os.path.exists(build_directory):
            os.makedirs(build_directory)

        def build():
            source_files = glob(os.path.join(os.path.abspath(directory), "**/*.java"), recursive=True)

            javac_command = ["javac", "-source", self._source_version, "-d", "build",
                             "-cp", self._classpath + "/*",
                             "-sourcepath", self._sourcepath]

            if self._bootclasspath is not None:
                javac_command.extend(["-bootclasspath", self._bootclasspath])

            javac_command.extend(source_files)

            return_code, stdout, stderr = _run_in_sandbox(javac_command, cwd=directory)
            if return_code != 0:
                raise BuildError(_get_compilation_message_from_return_code(return_code) + "\n" + stderr)

        def run(input_file, **run_student_flags):
            classpath_entries = ["build", self._classpath, self._classpath + "/*"]
            sandbox_flags = _parse_run_student_args(**run_student_flags)
            java_command = sandbox_flags + ["java", "-cp", os.pathsep.join(classpath_entries), self._main_class]
            return _run_in_sandbox(java_command, stdin=input_file, cwd=directory)

        return LambdaProject(run_function=run, build_function=build)


class MakefileProjectFactory(ProjectFactory):
    """
    Implementation of ProjectFactory for Makefile based projects.
    """

    def create_from_directory(self, directory):
        def build():
            compilation_command = ["make"]
            return_code, stdout, stderr = _run_in_sandbox(compilation_command, cwd=directory)
            if return_code != 0:
                raise BuildError(stderr)

        def run(input_file, **run_student_flags):
            sandbox_flags = _parse_run_student_args(**run_student_flags)
            run_command = sandbox_flags + ["make", "run"]
            return _run_in_sandbox(run_command, stdin=input_file, cwd=directory)

        return LambdaProject(run_function=run, build_function=build)


class CppProjectFactory(MakefileProjectFactory):
    """
    Implementation of ProjectFactory for C++.
    """

    def __init__(self, additional_flags=None):
        """
        Initializes an instance of CppProjectFactory with the given options.
        """
        if additional_flags is None:
            additional_flags = []

        self._additional_flags = additional_flags

    def create_from_code(self, code):
        project_directory = tempfile.mkdtemp(dir=CODE_WORKING_DIR)
        with open(os.path.join(project_directory, "main.cpp"), 'w') as main_file:
            main_file.write(code)

        def build():
            compilation_command = ["g++", "main.cpp", "-o", "main"] + self._additional_flags
            return_code, stdout, stderr = _run_in_sandbox(compilation_command, cwd=project_directory)
            if return_code != 0:
                raise BuildError(_get_compilation_message_from_return_code(return_code) + "\n" + stderr)

        def run(input_file, **run_student_flags):
            sandbox_flags = _parse_run_student_args(**run_student_flags)
            run_command = sandbox_flags + ["./main"]
            return _run_in_sandbox(run_command, stdin=input_file, cwd=project_directory)

        return LambdaProject(run_function=run, build_function=build)


class CProjectFactory(MakefileProjectFactory):
    """
    Implementation of ProjectFactory for C.
    """

    def __init__(self, additional_flags=None):
        """
        Initializes an instance of CProjectFactory with the given options.
        """
        if additional_flags is None:
            additional_flags = []

        self._additional_flags = additional_flags

    def create_from_code(self, code):
        project_directory = tempfile.mkdtemp(dir=CODE_WORKING_DIR)
        with open(os.path.join(project_directory, "main.c"), 'w') as main_file:
            main_file.write(code)

        def build():
            compilation_command = ["gcc", "main.c", "-o", "main"] + self._additional_flags
            return_code, stdout, stderr = _run_in_sandbox(compilation_command, cwd=project_directory)
            if return_code != 0:
                raise BuildError(_get_compilation_message_from_return_code(return_code) + "\n" + stderr)

        def run(input_file, **run_student_flags):
            sandbox_flags = _parse_run_student_args(**run_student_flags)
            run_command = sandbox_flags + ["./main"]
            return _run_in_sandbox(run_command, stdin=input_file, cwd=project_directory)

        return LambdaProject(run_function=run, build_function=build)


class VerilogProjectFactory(ProjectFactory):
    """
    Implementation of project for verilog code
    """

    def __init__(self, additional_flags=None):
        """
        Initializes an instance of VerilogProjectFactory with the given options.
        """
        self._additional_flags = additional_flags if additional_flags is not None else []

    def create_from_code(self, code):
        pass

    def create_from_directory(self, directory, file_names):
        def build():
            golden_file = os.path.join(os.path.abspath(directory), file_names["teachers_code"] + ".v")
            testbench_file = os.path.join(os.path.abspath(directory), file_names["testbench"] + ".v")
            design_file = os.path.join(os.path.abspath(directory), file_names["students_code"] + ".v")

            # Compile the testbench using the golden model
            compilation_golden = ["iverilog", "-o", "golden.out", testbench_file, golden_file] + self._additional_flags
            return_code, stdout, stderr = _run_in_sandbox(compilation_golden, cwd=directory)
            if return_code != 0:
                raise BuildError(_get_compilation_message_from_return_code(return_code) + "\n" + stderr)

            # Compile the testbench using the student's code
            compilation_code = ["iverilog", "-o", "code.out", testbench_file, design_file] + self._additional_flags
            return_code, stdout, stderr = _run_in_sandbox(compilation_code, cwd=directory)
            if return_code != 0:
                raise BuildError(_get_compilation_message_from_return_code(return_code) + "\n" + stderr)

        def run(input_file=None, **run_student_flags):
            # Simulate using Icarus Verilog the testbench using the golden model
            run_command = ["vvp", "golden.out"]
            return_code_golden, stdout_golden, stderr_golden = _run_in_sandbox(run_command, cwd=directory)

            # Simulate using Icarus Verilog the testbench using the student's code
            run_command = ["vvp", "code.out"]
            # Return the stdout of the simulation of the golden model and the run in sandbox of the simulation of the
            # code in evaluation
            return stdout_golden, _run_in_sandbox(run_command, cwd=directory)

        return LambdaProject(run_function=run, build_function=build)


class VHDLProjectFactory(ProjectFactory):
    def __init__(self, additional_flags=None):
        """
        Initializes an instance of VHDLProjectFactory with the given options.
        """
        self._additional_flags = additional_flags if additional_flags is not None else []

    def create_from_code(self, code):
        pass

    def create_from_directory(self, directory, entity_name, file_names):
        def build():
            testbench_file = os.path.join(os.path.abspath(directory), file_names["testbench"] + ".vhd")
            design_file = os.path.join(os.path.abspath(directory), file_names["students_code"] + ".vhd")

            # Analyze the testbench using the student's code
            compilation_code = ["ghdl", "-a", testbench_file, design_file] + self._additional_flags
            return_code, stdout, stderr = _run_in_sandbox(compilation_code, cwd=directory)
            if return_code != 0:
                raise BuildError(_get_compilation_message_from_return_code(return_code) + "\n" + stderr)

        def run(input_file=None, **run_student_flags):
            golden_file = os.path.join(os.path.abspath(directory), file_names["teachers_code"] + ".vhd")
            testbench_file = os.path.join(os.path.abspath(directory), file_names["testbench"] + ".vhd")
            design_file = os.path.join(os.path.abspath(directory), file_names["students_code"] + ".vhd")

            # Simulate using GHDL the testbench using the golden model
            run_command = ["ghdl", "-c", golden_file, testbench_file, "-r", entity_name]
            return_code_golden, stdout_golden, stderr_golden = _run_in_sandbox(run_command, cwd=directory)
            if return_code_golden != 0:
                raise BuildError(_get_compilation_message_from_return_code(return_code_golden) + "\n" + stderr_golden)

            # Simulate using GHDL the testbench using the student's code
            run_command = ["ghdl", "-c", design_file, testbench_file, "-r", entity_name]
            return_code_student, stdout_student, stderr_student = _run_in_sandbox(run_command, cwd=directory)

            # GHDL output format is (always will have more than 6 fields split by ":"):
            #   filename:#line:#column:time:kind_of_note:report_output
            # It is only needed the report_output part (to have a similar stdout than in VerilogProjectFactory)
            # so it is take from the 6 column to the end of line because report_output could contain ":"
            stdout_golden = "\n".join([":".join(x.split(":")[5:]) for x in stdout_golden.split("\n")])

            # For the student code only it's needed the report_output like in stdout_golden
            stdout_student = "\n".join([":".join(x.split(":")[5:]) for x in stdout_student.split("\n")])
            # Return the stdout of the simulation of the golden model
            # and the run in sandbox of the simulation of the code in evaluation
            return stdout_golden, (return_code_student, stdout_student, stderr_student)

        return LambdaProject(run_function=run, build_function=build)


_ALL_FACTORIES = {
    "python3": PythonProjectFactory(python_binary='python3'),
    "java7": JavaProjectFactory(source_version="1.7",
                                bootclasspath="/usr/lib/jvm/java-1.7.0-openjdk/jre/lib/rt.jar"),
    "java8": JavaProjectFactory(),
    "cpp": CppProjectFactory(["-O2"]),
    "cpp11": CppProjectFactory(additional_flags=["-std=c++11", "-O2"]),
    "c": CProjectFactory(["-O2"]),
    "c11": CProjectFactory(additional_flags=["-std=c11", "-O2"]),
    "verilog": VerilogProjectFactory(),
    "vhdl": VHDLProjectFactory()
}


def factory_exists(name):
    return name in _ALL_FACTORIES


def get_factory_from_name(name):
    """
    Returns a ProjectFactory instance associated to the given name.
    Raises ValueError if no instance is associated to that name.
    """

    if not factory_exists(name):
        raise ValueError(_("Factory does not exist: ") + name)

    return _ALL_FACTORIES[name]


def _parse_run_student_args(**kwargs):
    flags = [["--%s" % key.replace("_", '-'), "%s" % str(value)] for key, value in kwargs.items()]
    return ['--share-network'] + [value for flag in flags for value in flag]
