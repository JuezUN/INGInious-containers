from abc import abstractmethod
from glob import glob
import os
import tempfile
import subprocess

CODE_WORKING_DIR = 'student/'

def _run_in_sandbox(command, **subprocess_options):
    """
    Runs the given command with the given options and returns a tuple of
    (return_code, stdout, stderr). It is provided as a helper method for implementations of
    Project. The subprocess_options are sent directly to subprocess.run().

    Arguments:
    command -- A list specifying the program and the arguments to be run.
    subprocess_options -- Additional options sent to subprocess.run.
    """

    completed_process = subprocess.run(["run_student"] + command, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, **subprocess_options)

    stdout = completed_process.stdout.decode()
    stderr = completed_process.stderr.decode()
    return_code = completed_process.returncode

    return (return_code, stdout, stderr)

class CompilationError(Exception):
    def __init__(self, compilation_output):
        self.compilation_output = compilation_output


class Project(object):
    """
    Represents a runnable code project. Subclasses must take care of running the code using the
    run_student command.
    """

    @abstractmethod
    def run(self, input_file):
        """
        Executes this project with the given input file and returns a tuple of
        (return_code, stdout, stderr), where return_code is the status code the process finished
        with, and stdout and stderr are strings with the standard and the error output of the
        program.

        Implementations of this method may raise CompilationError if the project has compilation
        errors.

        Arguments:
        input_file -- a file-like object to be sent as stdin to the code process.
        """

        pass

class LambdaProject(Project):
    """
    A Project implementation that takes the run method as a parameter.
    """

    def __init__(self, run_function):
        assert run_function is not None

        self._run = run_function

    def run(self, input_file):
        return self._run(input_file)

class ProjectFactory(object):
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
        def run(input_file):
            command = [self._python_binary, self._main_file_name] + self._additional_flags

            return _run_in_sandbox(command, stdin=input_file, cwd=directory)

        return LambdaProject(run_function=run)


class JavaProjectFactory(ProjectFactory):
    """
    Implementation of ProjectFactory for Java.
    """

    def __init__(self, main_class='Main', source_version='1.8', sourcepath="src", classpath="lib"):
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

        def run(input_file):
            source_files = glob(os.path.join(os.path.abspath(directory), "**/*.java"), recursive=True)

            javac_command = ["javac", "-source", self._source_version, "-d", "build", "-cp", self._classpath + "/*",
                    "-sourcepath", self._sourcepath] + source_files
            return_code, stdout, stderr = _run_in_sandbox(javac_command, stdin=input_file, cwd=directory)
            if return_code != 0:
                raise CompilationError(stderr)

            classpath_entries = ["build", self._classpath, self._classpath + "/*"]
            java_command = ["java", "-cp" , os.pathsep.join(classpath_entries), self._main_class]
            return _run_in_sandbox(java_command, stdin=input_file, cwd=directory)

        return LambdaProject(run_function=run)


_ALL_FACTORIES = {
    "python2": PythonProjectFactory(),
    "python3": PythonProjectFactory(python_binary='python3'),
    "java7": JavaProjectFactory(source_version="1.7"),
    "java8": JavaProjectFactory()
}

def factory_exists(name):
    return name in _ALL_FACTORIES

def get_factory_from_name(name):
    """
    Returns a ProjectFactory instance associated to the given name.
    Raises ValueError if no instance is associated to that name.
    """

    if not factory_exists(name):
        raise ValueError("Factory does not exist: " + name)

    return _ALL_FACTORIES[name]