"""
This module contains the Notebook Grader and the method for grading
the submission requests.

This Notebook grader uses the its base container's modules (uncode container).
"""

import html
import json
import re
import traceback
from collections import OrderedDict

from results import GraderResult, parse_non_zero_return_code
from base_grader import BaseGrader
from feedback_tools import Diff, set_feedback
from submission_requests import SubmissionRequest

from .notebook_project import get_notebook_factory
from .utils import _generate_feedback_info, _result_to_html, _generate_feedback_info_internal_error


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
        self.test_time_limit = options.get("time_limit", 5)
        self.test_hard_time_limit = options.get("hard_time_limit", 10)
        self.test_memory_limit = options.get("memory_limit", 50)
        self.show_runtime_errors = options.get("treat_non_zero_as_runtime_error", True)
        self.show_debug_info_for = set(options.get("show_debug_info_for", []))
        self.custom_feedback = options.get("custom_feedback", {})
        self.diff_tool = Diff(options)
        self.response_type = options.get('response_type','json')
        self.dataset = options.get("dataset", {"url": '', 'filename': ''})

    def create_project(self):
        """
        This method constructs a project (an abstraction of runnable code) for the grading of the student's code.

        Returns:
            Project: An abstraction of runnable code that contains the student's code
            and can be given specific test cases for the grading of the source code
        """
        request = self.submission_request
        notebook_filepath = "{}.ipynb".format(self.filename)
        project_factory = get_notebook_factory()
        project_factory.filename = self.filename
        project_factory.notebook_path = notebook_filepath
        project_factory.dataset = self.dataset
        project_factory._additional_flags = ["--timeout", str(self.test_time_limit)]

        if request.problem_type == 'notebook_file':
            with open(notebook_filepath, "wb") as project_file:
                project_file.write(request.code)
            project = project_factory.create_from_directory()
            return project

        return None

    def grade(self, tests, weights=None):
        """
        This method grades the student's source code against some specific test cases

        Args:
            tests (list of tuples): A list containing a tuples with three values. The test's name, test's
            filename and amount of test_cases.
            weights (list): List of integers describing the importance of each test
        """

        try:
            project = self.create_project()
            project.build()

            tests_results, debug_info = self._run_all_tests(project, tests, weights)

            # Check for errors in run
            result_codes = [result.get("result", GraderResult.INTERNAL_ERROR) for result in tests_results if result]
            if GraderResult.INTERNAL_ERROR in result_codes:
                set_feedback(_generate_feedback_info_internal_error(debug_info,self.response_type))
            else:
                # Generate feedback string for tests
                res_type = self.response_type
                #Saving feedback as json
                if res_type == 'json':
                    feedback_list_json = []
                    for i, test_result in enumerate(tests_results):
                        if not test_result:
                            continue
                        show_debug_info = i in self.show_debug_info_for or self.submission_request.is_staff
                        test_custom_feedback = self.custom_feedback.get(i, "")
                        
                        feedback_obj = {
                            "i": i,
                            "test_result": test_result,
                            "weights": weights[i],
                            "show_debug_info": show_debug_info,
                            "test_custom_feedback": test_custom_feedback
                        }
                        feedback_list_json.append(feedback_obj)
                    options_for_feedback = self.diff_tool.get_options_dict()
                    options_for_feedback["container_type"] = "notebook"
                    options_for_feedback["is_staff"] = self.submission_request.is_staff
                    feedback_list_json.append(options_for_feedback)
                    feedback_list_json.append(debug_info)
                    feedback_str_json = json.dumps(feedback_list_json)
                    feedback_str = feedback_str_json
                #Saving feedback as rst
                elif res_type == 'rst':
                    feedback_list_rst = []
                    for i, test_result in enumerate(tests_results):
                        if not test_result:
                            continue

                        show_debug_info = i in self.show_debug_info_for or self.submission_request.is_staff
                        test_custom_feedback = self.custom_feedback.get(i, "")
                        feedback_list_rst.append(
                            _result_to_html(i, test_result, weights[i], show_debug_info, test_custom_feedback, self.submission_request.is_staff))
                    feedback_str = '\n\n'.join(feedback_list_rst)

                feedback_info = _generate_feedback_info(tests_results, debug_info, weights, tests)
                feedback_info['global']['feedback'] = feedback_str

                set_feedback(feedback_info)
        except Exception as e:
            debug_info = dict(internal_error_output=str(e))
            set_feedback(_generate_feedback_info_internal_error(debug_info, self.response_type))
            return

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
            debug_info["files_feedback"] = {}
            for i, test in enumerate(tests):
                if not test:
                    tests_results.append(None)
                    continue

                test_name, test_filename, total_cases = test
                (grader_result, test_total), test_debug_info = self._run_single_test(project, (
                    test_name, test_filename, weights[i], total_cases))

                debug_info["files_feedback"][test_name] = test_debug_info
                tests_results.append({"result": grader_result, "total": test_total, "name": test_name,
                                      "cases": test_debug_info["cases_info"]})

        except Exception as e:
            debug_info["internal_error_output"] = traceback.format_exc()
            debug_info["files_feedback"] = {}
            tests_results = [{
                "result": GraderResult.INTERNAL_ERROR,
                "total": 0.0,
                "name": test[0],
                "cases": OrderedDict()
            } for test in tests if test]

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
        time = self.test_time_limit
        hard_time = self.test_hard_time_limit
        memory = self.test_memory_limit
        sandbox_flags = {"time": time, "memory": memory, "hard-time": hard_time}
        return_code, stdout, stderr = project.run(test_filename, **sandbox_flags)
        if self._is_test_case_timeout(stdout):
            return_code, stdout, stderr = project.run(test_filename, **sandbox_flags)

        score = 0.0
        cases_info = {}

        if return_code == 0:
            if self._is_test_case_timeout(stdout):
                result = GraderResult.TIME_LIMIT_EXCEEDED
            else:
                score = self._get_total_score_test_case(stdout)
                cases_info = self._get_case_diff(stdout, test_name, total_cases)
                is_runtime_error, found_grading_runtime_exception, cases_info_exception = self._check_exception(stdout,
                                                                                                                test_name,
                                                                                                                total_cases)
                # Merge results
                for key, value in cases_info.items():
                    if key in cases_info_exception:
                        cases_info[key] = {**value, **cases_info_exception[key]}
                for key, value in cases_info_exception.items():
                    if key not in cases_info:
                        cases_info[key] = cases_info_exception[key]

                if is_runtime_error:
                    if found_grading_runtime_exception:
                        result = GraderResult.GRADING_RUNTIME_ERROR
                    else:
                        result = GraderResult.RUNTIME_ERROR
                elif score != weight:
                    result = GraderResult.WRONG_ANSWER
                else:
                    result = GraderResult.ACCEPTED
        else:
            result = parse_non_zero_return_code(return_code)

        # In case show_runtime_errors is not checked, show the other errors as WRONG_ANSWER
        if not self.show_runtime_errors and result not in [GraderResult.ACCEPTED, GraderResult.WRONG_ANSWER]:
            result = GraderResult.WRONG_ANSWER

        debug_info = {
            "test_filename": test_filename,
            "test_name": test_name,
            "stdout": html.escape(stdout.replace("<", "&lt;").replace(">", "&gt;")),
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
            case_code = []
            case_output_diff = ""
            case_wrong_answer_str = "# Error: expected"
            if case_wrong_answer_str not in case_lines:
                continue

            for line in case_lines:
                if line.startswith('>>> ') or line.startswith('... '):
                    case_code.append(line[4:])
                elif line.startswith("# "):
                    if line == case_wrong_answer_str:
                        case_output_diff += "Expected/n"
                    else:
                        case_output_diff += line[2:] + '/n'

            if len(case_code) > 1:
                case_code = case_code[1:]
            cases_info[str(case)] = {
                "is_runtime_error": False,
                "case_code": '\n'.join(case_code),
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
        found_grading_runtime_exception = False
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
            traceback_str = 'Traceback (most recent call last):'
            traceback_index = 0
            for index, line in enumerate(case_lines):
                error_pattern = re.compile("[a-zA-Z]*Error.*")
                if line.startswith(traceback_str):
                    is_runtime_error = True
                    found_student_code_exception = True
                    traceback_index = index
                elif error_pattern.match(line) or line == "Exception":
                    # Look for the error that caused the student exception
                    if found_student_code_exception:
                        code_error = []
                        try:
                            for error_index in range(index, traceback_index - 1, -1):
                                error_line = case_lines[error_index]
                                if "File" in error_line:
                                    if " in " in error_line:
                                        error_line = "in '{}'".format(error_line.split()[-1])
                                    break
                                code_error.append(error_line.replace('{', '{{').replace('}', '}}'))
                            if not code_error:
                                code_error.append(line.replace('{', '{{').replace('}', '}}'))
                        except:
                            code_error = [line]
                        error = "{}\n...\n{}\n".format(traceback_str, '\n'.join(reversed(code_error)))
                        cases_info[str(case)] = {"is_runtime_error": is_runtime_error, "error": error}
                    else:
                        is_runtime_error = True
                        found_grading_runtime_exception = True
                        cases_info[str(case)] = {"is_runtime_error": True, "is_grading_error": True, "error": line}
        return is_runtime_error, found_grading_runtime_exception, cases_info

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
    if sub_req.action == "submit":
        simple_grader.grade(tests, weights)
    elif sub_req.action == "customtest":
        custom_tests = [test[0] if test else None for test in sub_req.custom_input]
        weights = [test[1] if test else 0 for test in sub_req.custom_input]
        simple_grader.grade(custom_tests, weights)
