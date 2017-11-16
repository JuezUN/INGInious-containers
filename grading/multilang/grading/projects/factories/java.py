import os.path
import tempfile
from glob import glob

from grading.projects.errors import BuildError
from grading.projects.factories.utils import CODE_WORKING_DIR, _get_compilation_message_from_return_code
from grading.projects.project import LambdaProject, ProjectFactory


class JavaProjectFactory(ProjectFactory):
    """
    Implementation of ProjectFactory for Java.
    """

    def __init__(self, sandbox_runner, main_class='Main', source_version='1.8', sourcepath="src", classpath="lib",
                 bootclasspath=None):
        """
        Initializes an instance of JavaProjectFactory with the given options.

        Arguments:
        main_file_name -- The name of the file to run. If running a code, this will also be the name
            of the file where the code will be stored.
        """

        self._sandbox_runner = sandbox_runner
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

            compilation_result = self._sandbox_runner.run_command(javac_command, cwd=directory)
            if compilation_result.return_code != 0:
                raise BuildError(_get_compilation_message_from_return_code(compilation_result.return_code) + "\n" +
                                 compilation_result.stderr)

        def run(input_file):
            classpath_entries = ["build", self._classpath, self._classpath + "/*"]
            java_command = ["java", "-cp", os.pathsep.join(classpath_entries), self._main_class]
            return self._sandbox_runner.run_command(java_command, stdin=input_file, cwd=directory)

        return LambdaProject(run_function=run, build_function=build)
