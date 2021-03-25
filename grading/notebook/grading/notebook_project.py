import re
import ast
import requests

from projects import ProjectFactory, LambdaProject, CODE_WORKING_DIR, _run_in_sandbox, _parse_run_student_args, \
    BuildError
from .utils import _run_command


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

        self._additional_flags = additional_flags if additional_flags is not None else []
        self.filename = None
        self.notebook_path = None
        self.dataset = None

    # This method does not apply for notebooks.
    def create_from_code(self, code=None):
        return

    def create_from_directory(self, directory=None):
        def build():
            _download_dataset(self.dataset["url"], self.dataset["filename"])
            _convert_nb_to_python_script(self.notebook_path, self.filename)
            _copy_files_to_student_dir(self.notebook_path)

        def run(input_file, **run_student_flags):
            sandbox_flags = _parse_run_student_args(**run_student_flags)
            ok_py_command = ["ok", "--local", "--score", "-q", input_file]
            command = sandbox_flags + ok_py_command + self._additional_flags

            return _run_in_sandbox(command, cwd="student/")

        return LambdaProject(run_function=run, build_function=build)


def _download_dataset(url, filename):
    try:
        if url and filename:
            result = requests.get(url, allow_redirects=True)

            with open(filename, 'wb') as file:
                file.write(result.content)
    except Exception as e:
        raise BuildError("Failed downloading dataset, make sure the container has access to Internet.")


def _copy_files_to_student_dir(notebook_filepath):
    return_code, stdout, stderr = _run_command(["ls"], cwd="/task/")
    files = stdout.split('\n')
    no_copy_files = ["run", "task.yaml", notebook_filepath, "student"]
    for file in files:
        if file and file not in no_copy_files:
            _run_command(["cp", "-r", file, "/task/student/"], cwd="/task/")


def _convert_nb_to_python_script(notebook_path, filename):
    try:
        remove_cells_regex = [
            "'%s'" % r"\s*#\s*TEST_CELL\s*",
            "'%s'" % r"\s*#\s*IGNORE_CELL\s*",
        ]  # Matches cells with the comment '#TEST_CELL' and '#IGNORE_CELL' which also accepts several whitespaces.
        remove_cells = ','.join(remove_cells_regex)

        # Extract the python code within the same folder where the code is located.
        command = ["jupyter", "nbconvert", "--to", "python", notebook_path, "--TemplateExporter.exclude_markdown=True",
                   "--RegexRemovePreprocessor.patterns=[{}]".format(remove_cells)]
        _run_command(command)

        python_script_path = "{}.py".format(filename)
        processed_code = _preprocess_code(python_script_path)
        with open(python_script_path, "w") as python_script:
            python_script.write(processed_code)
    except Exception as e:
        raise BuildError("Unexpected error while parsing the notebook. Check that your notebook runs correctly and try again.")


def _preprocess_code(python_script_path):
    with open(python_script_path, "r") as python_script:
        lines = python_script.readlines()
    code = _remove_unwanted_lines(lines)
    return _enclose_code_with_try(code)


def _remove_unwanted_lines(lines):
    # code to block stdout from student's code.
    stdout_code = """
import sys
class DummyFile(object):
    def write(self, x): pass
save_stdout = sys.stdout
sys.stdout = DummyFile()
"""
    result = ["import subprocess"] + stdout_code.split('\n')
    get_ipython_pattern = r"get_ipython\(\)"
    install_module_pattern = r"get_ipython\(\)\.system\(\'(pip|conda) install .*\'\)"
    shell_command_pattern = r"(\s*?)get_ipython\(\)\.system\(\'(.+?)\'\)(\s*)"
    comment_line_pattern = r"#.*"
    for line in lines:
        strip_line = line.strip()
        if re.match(shell_command_pattern, line) and not re.match(install_module_pattern, strip_line):
            try:
                whitespace_line = re.search(shell_command_pattern, line).group(1)
                shell_command = re.search(shell_command_pattern, line).group(2).split()
                new_line = "{}call = subprocess.run({}, stdout=subprocess.PIPE)".format(whitespace_line, shell_command)
                result.append(new_line)
                new_line = "{}call.stdout.decode('utf-8')".format(whitespace_line)
                result.append(new_line)
            except Exception as e:
                pass
            continue
        elif re.match(get_ipython_pattern, strip_line) \
                or re.match(comment_line_pattern, strip_line) \
                or not strip_line:
            continue
        result.append(line)

    # Restore the stdout value to do not affect grading code.
    result.append("sys.stdout = save_stdout")
    return '\n'.join(result)


def _enclose_code_with_try(code):
    try:
        parser = ast.parse(code)
    except SyntaxError as e:
        return code
    main_lines = [child_node.lineno - 1 for child_node in parser.body]
    code_lines = [line for line in code.split('\n')]
    total_lines = len(code_lines)
    total_main_lines = len(main_lines)
    result = []
    i = 0
    while i < total_main_lines:
        result.append("try:")
        right_limit = total_lines
        if i + 1 < total_main_lines:
            right_limit = main_lines[i + 1]
        for j in range(main_lines[i], right_limit):
            if code_lines[j]:
                result.append("\t{}".format(code_lines[j]))
        result.append("except:\n\tpass")
        i += 1
    return '\n'.join(result)


def get_notebook_factory():
    return NotebookProjectFactory()
