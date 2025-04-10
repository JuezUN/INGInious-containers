"""
This module contains the Multi-language Grader and the method for grading 
the submission requests.

This module works with the help of the libraries on its base container (uncode).
"""
import os
import json
import html
import tempfile
import projects
from sys import getsizeof
import gc
import tarfile
from results import GraderResult, parse_non_zero_return_code, SandboxCodes
from zipfile import ZipFile, is_zipfile
from base_grader import BaseGrader
from feedback_tools import Diff, set_feedback, get_input_sample
import graders_utils as gutils
from submission_requests import SubmissionRequest
from .utils import remove_sockets_exception, cut_stderr, is_presentation_error


class SimpleGrader(BaseGrader):
    """
    This is the basic grader used by the multilang container.

    Attributes:
        - submission_request (obj): Contains the student's submission request object
        - diff_tool (obj): Instance of the class Diff. Containing the diff tool with some
        specific 'options'.
        - generate_diff (bool): Value signaling that is necessary to generate the diff feedback.
    """

    def __init__(self, submission_request, options):
        super(SimpleGrader, self).__init__(submission_request)
        self.generate_diff = options.get("compute_diff", True)
        self.treat_non_zero_as_runtime_error = options.get("treat_non_zero_as_runtime_error", True)
        options['show_input'] = True
        self.diff_tool = Diff(options)
        self.output_diff_for = set(options.get("output_diff_for", []))
        self.check_output = options.get('check_output', gutils.check_output)
        self.time_limit = options.get('time_limit', 2)
        self.hard_time_limit = options.get('hard_time_limit', self.time_limit)
        self.output_limit = options.get('output_limit', (2 ** 20) * 2)
        self.memory_limit = options.get('memory_limit', 50)
        self.response_type = options.get('response_type','json')
        self.ignore_presentation_error = options.get("ignore_presentation_error", False)

    def create_project(self):
        """
        This method constructs a project (an abstraction of runnable code) for the grading of the student's code.

        Returns:
            Project: An abstraction of runnable code that contains the student's code
            and can be given specific test cases for the grading of the source code
        """
        request = self.submission_request
        project_factory = projects.get_factory_from_name(request.language_name)
        if request.problem_type == 'code_multiple_languages':
            project = project_factory.create_from_code(request.code)
            return project
        if request.problem_type == 'code_file_multiple_languages':
            # Create project directory to add source code and unzip files
            project_directory = tempfile.mkdtemp(dir=projects.CODE_WORKING_DIR)
            
            # Source file path is project_directory path plus an extension
            # to write the file with the same name that the temporal project_directory
            file_path = project_directory + ".file"
            
            # We write the file next to the project directory, so the contents of
            # the extracted file is available in the temporal project_directory
            with open(file_path, "wb") as project_file:
                project_file.write(request.code)
            # Check if file is tar or zip file
            if tarfile.is_tarfile(file_path):
            # Unzip all the files on the project directory
                with tarfile.open(file_path) as project_file:
                    project_file.extractall(path=project_directory)
            elif is_zipfile(file_path):
             # Unzip all the files on the project directory
                with ZipFile(file_path) as project_file:
                    project_file.extractall(path=project_directory)
                    
            #We check if the extracted files are the project or a single directory with th real project
            files = [f for f in os.listdir(project_directory)]
            if len(files) == 1 and os.path.isdir(os.path.join(project_directory,files[0])):
                project_directory = os.path.join(project_directory,files[0])
            # Finally create the project
            project = project_factory.create_from_directory(project_directory)
            return project

    def grade(self, test_cases, weights=None, set_feedback=set_feedback):
        """
        This method grades the student's source code against some specific test cases

        Args:
            test_cases (list of tuples): A list containing a tuples with a pair of string. The name
            of the input file and name of the expected output file of each test case.
            weights (list): List of integers describing the importance of each test case
        """
        project = self.create_project()
        results, debug_info = self._run_code_against_all_test_cases(project, test_cases)

        # Check for errors in run
        if GraderResult.COMPILATION_ERROR in results:
            compilation_output = debug_info.get("compilation_output", "")
            feedback_str = gutils.feedback_str_for_compilation_error(compilation_output,"multilang",self.response_type)
        else:
            # Generate feedback string for tests format based with response type
            res_type = self.response_type
            # Saving feedback as json
            if res_type == 'json':
                feedback_list_json = []
                for i, result in enumerate(results):
                    test_case = test_cases[i]
                    #for each case we save the info for the html templates on the frontend
                    feedback_obj = {
                        "i": i,
                        "result": result,
                        "test_case": test_case,
                        "input_sample": get_input_sample(test_case)
                    }
                    feedback_list_json.append(feedback_obj)
                # We save the container's options required for the feedback
                options_for_feedback = self.diff_tool.get_options_dict()
                options_for_feedback["container_type"] = "multilang"
                options_for_feedback["is_staff"] = self.submission_request.is_staff
                feedback_list_json.append(options_for_feedback)
                # We also save the debug info for the feedback
                feedback_list_json.append(debug_info)
                # Converting the list to a json format string
                # The json object always have this structure on multilang
                # [ feedback_obj_test_case_1 , ... , feedback_obj_test_case_n , options_for_feedback , debug_info ]
                feedback_str_json = json.dumps(feedback_list_json)
                feedback_str = feedback_str_json
            #Saving feedback as rst
            elif res_type == 'rst':
                feedback_list_rst = []
            
                for i, result in enumerate(results):
                    test_case = test_cases[i]
                    feedback_list_rst.append(self.diff_tool.to_html_block(i, result, test_case, debug_info, self.submission_request.is_staff))
                    
                feedback_str_rst = '\n\n'.join(feedback_list_rst)
                feedback_str = feedback_str_rst
            
        # Create the feedback_info dict and assign the string depend on the response type
        feedback_info = self._generate_feedback_info(results, debug_info, weights, test_cases)
        feedback_info['global']['feedback'] = feedback_str

        set_feedback(feedback_info)

    def run_custom_input(self, set_feedback=set_feedback):
        """
        This function test the student's source code against the custom input of this student.
        """
        project = self.create_project()
        results = {}

        try:
            return_code, stdout, stderr = self._run_custom_input_project(project)
            results = self._generate_custom_input_feedback_info(return_code, stdout, stderr)
        except projects.BuildError as e:
            results = self._construct_compilation_error_feedback_info(e)

        # Return feedback
        set_feedback(results)

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

        try:
            project.build()

            debug_info["files_feedback"] = {}
            for input_filename, exp_output_filename in test_cases:
                grader_result, test_case_debug_info = self._run_code_against_test_case(project, input_filename,
                                                                                       exp_output_filename)

                debug_info["files_feedback"][input_filename] = test_case_debug_info
                grader_results.append(grader_result)

        except projects.BuildError as e:
            debug_info["compilation_output"] = e.compilation_output

            grader_results = [GraderResult.COMPILATION_ERROR for _ in test_cases]

        return grader_results, debug_info

    def _run_code_against_test_case(self, project, input_filename, expected_output_filename):
        """
        This method computes the results and debug information of an specific
        run of the source code against one single test case.

        Args:
            project (obj): Instance of project, an abstraction of runnable code
            input_filename (str): Name of the input file in the test case.
            expected_output_filename (str): Name of the output file in the test case.

        Returns:
            The result of the execution of the student's source code, (ACCEPTED or WRONG_ANSWER in the case
            of zero return code. Check 'results.py')
            And the debug information in the execution.
        """
        with open(input_filename, 'r') as input_file, open(expected_output_filename, 'r') as expected_output_file:
            time = self.time_limit
            hard_time = self.time_limit
            memory = self.memory_limit
            return_code, stdout, stderr = project.run(input_file,
                                                      **{"time": time, "memory": memory, "hard-time": hard_time})
            stderr = remove_sockets_exception(stderr)
            stderr = cut_stderr(stderr)
            expected_output = expected_output_file.read()
            # In case the stdout takes more memory than the output limit. It sets the stdout to free up memory
            # and avoid memory leaks.
            if getsizeof(stdout) > self.output_limit:
                stdout = ""
                # Call the garbage collector to reduce memory usage
                gc.collect()
                result = GraderResult.OUTPUT_LIMIT_EXCEEDED
            elif return_code == 0:
                output_matches = self.check_output(stdout, expected_output)
                if output_matches:
                    result = GraderResult.ACCEPTED
                elif is_presentation_error(stdout, expected_output):
                    result = GraderResult.ACCEPTED if self.ignore_presentation_error else \
                        GraderResult.PRESENTATION_ERROR
                else:
                    result = GraderResult.WRONG_ANSWER
            elif self.treat_non_zero_as_runtime_error:
                result = parse_non_zero_return_code(return_code)
            else:
                result = GraderResult.WRONG_ANSWER

            debug_info = {}
            if result != GraderResult.ACCEPTED:
                diff = None
                if self.generate_diff and (result == GraderResult.WRONG_ANSWER or
                                           result == GraderResult.PRESENTATION_ERROR) and \
                        (input_filename in self.output_diff_for or self.submission_request.is_staff):
                    diff = html.escape(self.diff_tool.compute(stdout, expected_output))

                # As output might be very long, store string of max 50 KBs.
                _stdout_max_length = (2 ** 10) * 50
                stdout = gutils.reduce_text(stdout, _stdout_max_length)
                debug_info.update({
                    "input_file": input_filename,
                    "stdout": html.escape(stdout),
                    "stderr": html.escape(stderr),
                    "return_code": return_code,
                    "diff": diff,
                })
                gc.collect()

            return result, debug_info

    def _generate_feedback_info(self, results, debug_info, weights, test_cases):
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
        score = sum(weights[i] for i, result in enumerate(results) if result == GraderResult.ACCEPTED)
        total_sum = sum(weights)

        summary_result = gutils.compute_summary_result(results)

        feedback_info['custom']['additional_info'] = json.dumps(debug_info)
        feedback_info['custom']['summary_result'] = summary_result.name
        feedback_info['global']['result'] = "success" if passing == len(test_cases) else "failed"
        feedback_info['grade'] = (score * 100.0 / total_sum) if total_sum > 0 else 100.0

        return feedback_info

    def _run_custom_input_project(self, project):
        """
        This method runs the student's source code against a custom input that
        the student defines on the task submission section.

        Args:
            - project (obj): An instance of Project. An abstraction of runnable code
            (check 'projects.py').

        Returns:
            The return code, standard output and standard error files.
        """
        # Create a file with the custom input
        custom_input_filename = 'custom_input.txt'
        with open(custom_input_filename, 'w') as input_file:
            input_file.write(self.submission_request.custom_input)
        with open(custom_input_filename, 'r') as input_file:
            try:
                project.build()
                time = self.time_limit
                hard_time = self.time_limit
                memory = self.memory_limit
                return_code, stdout, stderr = project.run(input_file,
                                                          **{"time": time, "memory": memory, "hard-time": hard_time})
                return return_code, stdout, stderr
            except projects.BuildError as e:
                raise

    def _generate_custom_input_feedback_info(self, return_code, stdout, stderr):
        """
        This method generates a dictionary with the information for setting the 
        feedback information (check 'feedback_tools.py').

        Args:
            - return_code (int): The return code after running a project (abstraction of code)
            - stdout (str): The contents of the standard output after running a project.
            - stderr (str): The contents of the standard error after running a project.

        Returns:
            A dictionary containing the information for the feedback.
        """

        feedback_info = {'global': {}, 'custom': {}}
        # In case the stdout takes more memory than the output limit. It sets the stdout to free up memory
        # and avoid memory leaks.
        if getsizeof(stdout) > self.output_limit:
            stdout = ""
            # Call the garbage collector to reduce memory usage
            gc.collect()
            feedback_info['global']['return'] = GraderResult.OUTPUT_LIMIT_EXCEEDED
            feedback_info['global']['feedback'] = gutils.html_to_rst(
                _("Your code exceeded the output limit") + ": <strong>%s</strong>" % feedback_info['global'][
                    'return'].name)
        elif return_code == 0:
            feedback_info['global']['return'] = GraderResult.ACCEPTED
            feedback_info['global']['feedback'] = gutils.html_to_rst(
                _("Your code finished successfully. Check your output below\n."))
        else:
            feedback_info['global']['return'] = parse_non_zero_return_code(return_code)
            feedback_info['global']['feedback'] = gutils.html_to_rst(
                _("Your code did not run successfully") + ": <strong>%s</strong>" % (
                    feedback_info['global']['return'].name,))
        # Output length will be 80 KBs at most.
        _stdout_max_length = (2 ** 10) * 80
        feedback_info['custom']['stdout'] = gutils.reduce_text(stdout,
                                                               _stdout_max_length, _("Long output, it was reduced."))
        feedback_info['custom']['stderr'] = remove_sockets_exception(stderr)

        feedback_info['global']['result'] = "success" if feedback_info['global'][
                                                             'return'] == GraderResult.ACCEPTED else "failed"
        feedback_info['grade'] = 100.0 if feedback_info['global']['return'] == GraderResult.ACCEPTED else 0.0

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
        feedback_info['global']['return'] = GraderResult.COMPILATION_ERROR
        feedback_info['global']['feedback'] = gutils.html_to_rst(
            _("Your code did not run successfully: <strong>%s</strong>, check the error below.") %
            feedback_info['global']['return'].name)
        feedback_info['global']['result'] = "failed"
        feedback_info['grade'] = 0.0
        feedback_info['custom']['stdout'] = ""
        feedback_info['custom']['stderr'] = compilation_output

        return feedback_info


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
    simple_grader = SimpleGrader(sub_req, options)
    if sub_req.action == "submit":
        simple_grader.grade(test_cases, weights)
    elif sub_req.action == "customtest":
        simple_grader.run_custom_input()
