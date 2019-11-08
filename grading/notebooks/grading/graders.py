"""
This module contains the Multi-language Grader and the method for grading 
the submission requests.

This module works with the help of the libraries on its base container (uncode).
"""

from abc import ABC, abstractmethod
from inginious import input, feedback
import json
import subprocess
import html
import tempfile
import projects
from results import GraderResult, parse_non_zero_return_code
from zipfile import ZipFile
from base_grader import BaseGrader
from feedback_tools import Diff, set_feedback
import graders_utils as gutils
from submission_requests import SubmissionRequest

from .notebook_project import get_notebook_factory


class NotebookGrader(BaseGrader):
    """
    This is the basic grader used by the multilang container.

    Attributes:
        - submission_request (obj): Contains the student's submission request object
        - diff_tool (obj): Instance of the class Diff. Containing the diff tool with some
        specific 'options'.
        - generate_diff (bool): Value signaling that is necessary to generate the diff feedback.
    """

    def __init__(self, submission_request, options):
        super(NotebookGrader, self).__init__(submission_request)
        self.filename = options.get("filename", "file.ipynb")
        # self.generate_diff = options.get("compute_diff", True)
        # self.treat_non_zero_as_runtime_error = options.get("treat_non_zero_as_runtime_error", True)
        # options['show_input'] = True
        # self.diff_tool = Diff(options)
        # self.check_output = options.get('check_output', gutils.check_output)

    def create_project(self):
        """
        This method constructs a project (an abstraction of runnable code) for the grading of the student's code.

        Returns:
            Project: An abstraction of runnable code that contains the student's code
            and can be given specific test cases for the grading of the source code
        """
        request = self.submission_request
        project_factory = get_notebook_factory()

        # TODO: Change the problem type
        if request.problem_type == 'code_file_multiple_languages':
            path = self.filename
            with open(path, "wb") as project_file:
                project_file.write(request.code)

            # Extract the python code.
            subprocess.run(["jupyter", "nbconvert", "--to", "script", "*.ipynb"])
            project = project_factory.create_from_directory('./')
            return project

    def grade(self, test_cases, weights=None):
        """
        This method grades the student's source code against some specific test cases

        Args:
            test_cases (list of tuples): A list containing a tuples with a pair of string. The name
            of the input file and name of the expected output file of each test case.
            weights (list): List of integers describing the importance of each test case
        """
        project = self.create_project()
        results, totals, debug_info = self._run_code_against_all_test_cases(project, test_cases)

        # Check for errors in run
        if GraderResult.COMPILATION_ERROR in results:
            compilation_output = debug_info.get("compilation_output", "")
            feedback_str = gutils.feedback_str_for_compilation_error(compilation_output)
        else:
            # Generate feedback string for tests
            feedbacklist = []
            for i, result in enumerate(results):
                                    feedbacklist.append(self._result_to_html(i, result))
            feedback_str = '\n\n'.join(feedbacklist)

        feedback_info = self._generate_feedback_info(results, debug_info, weights, test_cases, totals)
        feedback_info['global']['feedback'] = feedback_str

        set_feedback(feedback_info)

    def _result_to_html(self, test_id, result):
        return '- **Test %d: %s**' % (test_id + 1, result.name)

    def _run_code_against_all_test_cases(self, project, test_cases):
        """
        This method runs the code against all the test cases and returns a list containing
        the results and dictionary containing information for debugging.

        Args:
            project (obj): An instance of Project (an abstraction of runnable code)
            test_cases (list): A list containing the pairs input filename and expected output filename as tuples.            


        Returns:
            - grader_results (list): A list containing the grading result of each test case
            (i.e output equals to expected output)
            - debug_info (dict): A dictionary containing the information about debugging, the keys are the
            input filenames.
        """
        grader_results = []
        debug_info = {}
        totals = []

        try:
            project.build()

            debug_info["files_feedback"] = {}
            for test_name, test_filename in test_cases:
                grader_result, total, test_case_debug_info = self._run_code_against_test_case(project, test_filename, test_name)

                debug_info["files_feedback"][test_filename] = test_case_debug_info
                grader_results.append(grader_result)
                totals.append(total)

        except projects.BuildError as e:
            debug_info["compilation_output"] = e.compilation_output

            grader_results = [GraderResult.COMPILATION_ERROR for _ in test_cases]

        return grader_results, totals, debug_info

    def _run_code_against_test_case(self, project, test_filename, test_name):
        """
        This method computes the results and debug information of an specific
        run of the source code against one single test case.

        Args:
            project (obj): Instance of project, an abstraction of runnable code
            test_filename (str): Name of the test file in the test case.
            expected_output_filename (str): Name of the output file in the test case.

        Returns:
            The result of the execution of the student's source code, (ACCEPTED or WRONG_ANSWER in the case
            of zero return code. Check 'results.py')
            And the debug information in the execution.
        """
        project.run(test_filename)
        return_code, stdout, stderr = project.run(test_filename)
        total = self._parse_test_results(test_name, stdout)

        if return_code == 0 and total != 0.0:
            # output_matches = self.check_output(stdout, expected_output)
            # TODO: PARSE THE OUTPUT
            result = GraderResult.ACCEPTED
        else:
            result = GraderResult.WRONG_ANSWER

        debug_info = {
            "test_filename": test_filename,
            "test_name": test_name,
            "stdout": html.escape(stdout),
            "stderr": html.escape(stderr),
            "return_code": return_code
        }

        # debug_info = {"stderr": stderr, "code": return_code, "stdout": stdout}
        return result, total, debug_info

    def _parse_test_results(self, test_name, stdout):
        # TODO: Take the test_name to get more infor from output
        stdout = stdout.split('\n')
        point_breakdown_str = "Point breakdown"
        score_str = "Score:"
        score_index = stdout.index(score_str)
        total = float(stdout[score_index + 1].strip().split(' ')[1])

        return total

    def _generate_feedback_info(self, results, debug_info, weights, test_cases, totals):
        """
        This method generates a dictionary containing the information for the feedback
        setting function (check 'feedback_tools.py')

        Args:
            - results (list): Containing the results for executing student's source code (check 'results.py')
            - debug_info (dict): Dictionary containing the debugging info for the execution
            of the test cases.
            - weights (list): List of integers containing the importance of the nth-test
            - test_cases (list): List of pairs of filenames. i.e (input_filename, expected_output_filename)
        """

        if weights is None:
            weights = [1] * len(test_cases)

        feedback_info = {'global': {}, 'custom': {}}

        passing = sum(1 for result in results if result == GraderResult.ACCEPTED)
        score = sum(weights[i] * total for i, total in enumerate(totals))
        total_sum = sum(weights)

        summary_result = gutils.compute_summary_result(results)

        feedback_info['custom']['additional_info'] = json.dumps(debug_info)
        feedback_info['custom']['summary_result'] = summary_result.name
        feedback_info['global']['result'] = "success" if passing == len(test_cases) else "failed"
        feedback_info['grade'] = score * 100.0 / total_sum

        return feedback_info

    def _construct_compilation_error_feedback_info(self, error):
        """
        Returns a dictionary with the feedback information, in case of a 
        compilation error.

        Args:
            error (obj): An instance of class BuildError (check 'projects.py')

        Returns:
            A dictionary with the information for the feedback setting.
        """
        feedback_info = {'global': {}, 'custom': {}}
        compilation_output = error.compilation_output
        feedback_info['global']['feedback'] = gutils.feedback_str_for_compilation_error(compilation_output)
        feedback_info['global']['result'] = GraderResult.COMPILATION_ERROR

        return feedback_info


# Problem Handler TODO: Change in future versions


def handle_problem_action(problem_id, test_cases, options={}, weights=None, language_name=None):
    """
    Decides whether to grade the given problem against the test cases, or run it against a
    user-provided custom input according to the task action. If language_name is None, it will be
    automatically inferred from the problem with the given id (assuming it's a
    "code multiple language" problem).
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
    # sub_req.action == "submit":
    simple_grader.grade(test_cases, weights)
