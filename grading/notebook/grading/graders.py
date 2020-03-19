"""
This module contains the Notebook Grader and the method for grading
the submission requests.

This Notebook grader uses the its base container's modules (uncode container).
"""

import subprocess
import html
from collections import OrderedDict

import projects
import re
from results import GraderResult, parse_non_zero_return_code
from base_grader import BaseGrader
from feedback_tools import Diff, set_feedback
import graders_utils as gutils
from submission_requests import SubmissionRequest

from .notebook_project import get_notebook_factory
from .utils import _generate_feedback_info, _result_to_html


class NotebookGrader(BaseGrader):
    """
    This is the basic grader used by the notebook container.

    Attributes:
        - submission_request (obj): Contains the student's submission request object.
        - options (Dict): Options sent from INGInious.
    """

    def __init__(self, submission_request, options):
        super(NotebookGrader, self).__init__(submission_request)
        self.filename = options.get("filename", "notebook")
        self.show_runtime_errors = options.get("treat_non_zero_as_runtime_error", True)
        self.show_debug_info_for = set(options.get("show_debug_info_for", []))

    def create_project(self):
        """
        This method constructs a project (an abstraction of runnable code) for the grading of the student's code.

        Returns:
            Project: An abstraction of runnable code that contains the student's code
            and can be given specific test cases for the grading of the source code
        """
        request = self.submission_request
        project_factory = get_notebook_factory()

        if request.problem_type == 'notebook_file':
            notebook_filepath = "{}.ipynb".format(self.filename)
            with open(notebook_filepath, "wb") as project_file:
                project_file.write(request.code)

            self._convert_nb_to_python_script(notebook_filepath)
            files = subprocess.run(["ls"], cwd="/task/", stdout=subprocess.PIPE).stdout.decode("utf-8").split('\n')
            for file in files:
                if file and file not in ["run", "task.yaml", notebook_filepath, "student"]:
                    subprocess.run(["cp", "-r", file, "/task/student/"], cwd="/task/")
            print(subprocess.run(["ls"], cwd="/task/student/", stdout=subprocess.PIPE).stdout)
            project = project_factory.create_from_directory()
            return project

        return None

    def _convert_nb_to_python_script(self, notebook_path):
        # Extract the python code within the same folder where the code is located.
        subprocess.run(
            ["jupyter", "nbconvert", "--to", "python", notebook_path, "--TemplateExporter.exclude_markdown=True"])
        python_script_path = "{}.py".format(self.filename)
        accepted_lines = ["import subprocess\n"]
        get_ipython_pattern = r"get_ipython\(\)"
        install_module_pattern = r"get_ipython\(\)\.system\(\'(pip|conda) install .*\'\)"
        shell_command_pattern = r"get_ipython\(\)\.system\(\'(.+?)\'\)"
        comment_line_pattern = r"#.*"
        with open(python_script_path, "r") as python_script:
            lines = python_script.readlines()
            for line in lines:
                strip_line = line.strip()
                if re.match(shell_command_pattern, strip_line) and not re.match(install_module_pattern, strip_line):
                    try:
                        shell_command = re.search(shell_command_pattern, strip_line).group(1).split()
                        new_line = "call = subprocess.run({}, stdout=subprocess.PIPE)\n".format(shell_command)
                        accepted_lines.append(new_line)
                        new_line = "print(call.stdout.decode('utf-8'))\n"
                        accepted_lines.append(new_line)
                    except Exception:
                        pass
                    continue
                elif re.match(get_ipython_pattern, strip_line) or re.match(comment_line_pattern,
                                                                           strip_line) or not strip_line:
                    continue

                accepted_lines.append(line)

        with open(python_script_path, "w") as python_script:
            python_script.write(''.join(accepted_lines))

    def grade(self, tests, weights=None):
        """
        This method grades the student's source code against some specific test cases

        Args:
            tests (list of tuples): A list containing a tuples with three values. The test's name, test's
            filename and amount of test_cases.
            weights (list): List of integers describing the importance of each test
        """
        project = self.create_project()
        assert project is not None
        tests_results, debug_info = self._run_all_tests(project, tests, weights)

        # Check for errors in run
        if GraderResult.COMPILATION_ERROR in tests_results:
            compilation_output = debug_info.get("compilation_output", "")
            feedback_str = gutils.feedback_str_for_compilation_error(compilation_output)
        else:
            # Generate feedback string for tests
            feedbacklist = []
            for i, test_result in enumerate(tests_results):
                show_debug_info = i in self.show_debug_info_for
                feedbacklist.append(
                    _result_to_html(i, test_result, weights[i], show_debug_info))
            feedback_str = '\n\n'.join(feedbacklist)

        feedback_info = _generate_feedback_info(tests_results, debug_info, weights, tests)
        feedback_info['global']['feedback'] = feedback_str

        set_feedback(feedback_info)

    def _run_all_tests(self, project, tests, weights):
        """
        This method runs all the OK tests and returns a list of Dicts containing
        the results, total for each test and a dictionary containing debugging information.

        Args:
            project (obj): An instance of Project (an abstraction of runnable code)

        Returns:
            - tests_results (list): A list of Dicts containing the grading result of each test case (i.e. Accepted)
            and the total grade.
            - debug_info (dict): A dictionary containing the information about debugging.
        """
        tests_results = []
        debug_info = {}

        try:
            project.build()

            debug_info["files_feedback"] = {}
            for i, test in enumerate(tests):
                test_name, test_filename, total_cases = test
                (grader_result, test_total), test_debug_info = self._run_single_test(project, (
                    test_name, test_filename, weights[i], total_cases))

                debug_info["files_feedback"][test_name] = test_debug_info
                tests_results.append({"result": grader_result, "total": test_total, "name": test_name,
                                      "cases": test_debug_info["cases_info"]})

        except projects.BuildError as e:
            debug_info["compilation_output"] = e.compilation_output

            tests_results = [{
                "result": GraderResult.COMPILATION_ERROR,
                "total": 0.0,
                "name": test[0],
                "cases": OrderedDict()
            } for test in tests]

        return tests_results, debug_info

    def _run_single_test(self, project, test):
        """
        This method computes the results and debug information of a single test.

        Args:
            project (obj): Instance of project, an abstraction of runnable code
            test (tuple): Tuple with three values. The test's name, test's filename and amount of test cases.

        Returns:
            The result of the execution of the student's source code in the specific test (i.e. RUNTIME_ERROR) with
            the total grade for the test and the debug information in the execution.
        """
        test_name, test_filename, weight, total_cases = test

        return_code, stdout, stderr = project.run(test_filename)
        if self._is_test_case_timeout(stdout):
            return_code, stdout, stderr = project.run(test_filename)

        score = 0.0
        cases_info = {}
        if return_code == 0:
            if self._is_test_case_timeout(stdout):
                result = GraderResult.TIME_LIMIT_EXCEEDED
            else:
                score = self._get_total_score_test_case(stdout)
                is_runtime_error, found_professor_code_exception, cases_info = self._check_exception(stdout, test_name,
                                                                                                     total_cases)
                if self.show_runtime_errors and is_runtime_error:
                    if found_professor_code_exception:
                        result = GraderResult.INTERNAL_ERROR
                    else:
                        result = GraderResult.RUNTIME_ERROR
                elif self._is_test_case_compilation_error(stdout):
                    result = GraderResult.COMPILATION_ERROR
                elif score != weight:
                    result = GraderResult.WRONG_ANSWER
                    cases_info.update(self._get_case_diff(stdout, test_name, total_cases))
                else:
                    result = GraderResult.ACCEPTED
        else:
            result = parse_non_zero_return_code(return_code)

        debug_info = {
            "test_filename": test_filename,
            "test_name": test_name,
            "stdout": html.escape(stdout),
            "stderr": html.escape(stderr),
            "return_code": return_code,
            "cases_info": cases_info
        }
        return (result, score), debug_info

    def _get_case_diff(self, stdout, test_name, total_cases):
        """
        Parses the output from OK grader for each case, getting the final result for each case, the code and
        output diff
        :param stdout: Output from OK grader
        :param test_name:
        :param total_cases: Total test cases the test has
        :return: A Dict with the result, the executed code and the output diff
        """
        lines = stdout.split('\n')
        cases_info = OrderedDict()
        for case in range(1, total_cases + 1):
            case_error_str = "%s > Suite %d > Case 1" % (test_name, case)
            if case_error_str not in stdout:
                continue
            case_error_str_end = "---------------------------------------------------------------------"
            case_error_index_start = lines.index(case_error_str)
            case_error_index_end = lines.index(case_error_str_end, case_error_index_start, len(lines))
            case_lines = lines[case_error_index_start:case_error_index_end]
            case_code = ""
            case_output_diff = ""
            case_wrong_answer_str = "# Error: expected"
            if case_wrong_answer_str not in case_lines:
                continue

            student_code_import_str = "from %s import *" % self.filename
            for line in case_lines:

                if line.startswith('>>> ') and student_code_import_str != line[4:]:
                    case_code += line[4:] + '/n'
                elif line.startswith("# "):
                    if line == case_wrong_answer_str:
                        case_output_diff += "Expected/n"
                    else:
                        case_output_diff += line[2:] + '/n'

            cases_info[str(case)] = {
                "is_runtime_error": False,
                "case_code": case_code,
                "case_output_diff": case_output_diff
            }
        return cases_info

    def _check_exception(self, stdout, test_name, total_cases):
        """
        Check the stdout executed with exceptions. This also checks if the exception was thrown either on student's or
        professor's code for testing.
        In order to know whether the exception occurred in student's code, OK command separates each case with its
        corresponding exception, when its a student's code exception, the error starts with:
        `Traceback (most recent call last):` and following the next messages corresponding to the exception.
        When its a professor's code exception, the message is thrown exception, for example, NameError, corresponding
        to the python exceptions' name.
        """
        found_student_code_exception = False
        found_professor_code_exception = False
        is_runtime_error = False

        lines = stdout.split('\n')
        cases_info = OrderedDict()
        for case in range(1, total_cases + 1):
            case_error_str = "%s > Suite %d > Case 1" % (test_name, case)
            if case_error_str not in stdout:
                continue
            case_error_str_end = "---------------------------------------------------------------------"
            case_error_index_start = lines.index(case_error_str)
            case_error_index_end = lines.index(case_error_str_end, case_error_index_start, len(lines))
            case_lines = lines[case_error_index_start:case_error_index_end]
            found_student_code_exception = False
            for line in case_lines:
                error_pattern = re.compile("[a-zA-Z]*Error.*")
                if line.startswith('Traceback (most recent call last):'):
                    is_runtime_error = True
                    found_student_code_exception = True
                elif error_pattern.match(line) or line == "Exception":
                    # Look for the error that caused the student exception
                    if found_student_code_exception:
                        cases_info[str(case)] = {"is_runtime_error": is_runtime_error, "error": line}
                    else:
                        is_runtime_error = True
                        found_professor_code_exception = True
        return is_runtime_error, found_professor_code_exception, cases_info

    def _is_test_case_compilation_error(self, stdout):
        if "SyntaxError" in stdout:
            return True
        return False

    def _is_test_case_timeout(self, stdout):
        str_to_check = "# Error: evaluation exceeded"
        return str_to_check in stdout

    def _get_total_score_test_case(self, stdout):
        stdout_lines = stdout.split('\n')
        score_str = "Score:"
        try:
            score_index = stdout_lines.index(score_str)
            total = float(stdout_lines[score_index + 1].strip().split(' ')[1])
        except:
            total = 0.0

        return total


def handle_problem_action(problem_id, tests, options={}, weights=None, language_name=None):
    """
    problem_id: The id of the problem where the code (and optionally the language) will be extracted
        from.
    test_cases: Same as in grade().
    language_name: The name of the language that the code is written in. If None, it will be
        extracted from the problem with id problem_id.
    weights: grade().
    options: Diff class.
    """

    sub_req = SubmissionRequest(problem_id, language_name)
    simple_grader = NotebookGrader(sub_req, options)
    simple_grader.grade(tests, weights)
