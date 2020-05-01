from inginious import input, feedback
import json
import os
import difflib
import html
import tempfile
from glob import glob

import projects
from results import GraderResult, parse_non_zero_return_code
from zipfile import ZipFile
from base_grader import BaseGrader
from graders_utils import html_to_rst as html2rst
from feedback_tools import Diff, set_feedback
import graders_utils as gutils
from submission_requests import SubmissionRequest
from shutil import copyfile


class HDLGrader(BaseGrader):
    def __init__(self, submission_request, options):
        super(HDLGrader, self).__init__(submission_request)
        self.generate_diff = options.get("compute_diff", True)
        self.treat_non_zero_as_runtime_error = options.get("treat_non_zero_as_runtime_error", True)
        self.diff_tool = DiffWaveDrom(options)
        self.check_output = options.get('check_output', gutils.check_output)
        self.entity_name = options.get('entity_name', 'testbench')        

    def create_project(self, testbench_file_name, golden_file_name):
        """
        Creates a project (VHDL or Verilog) to test the code
        """
        # Create factory project
        language_name = self.submission_request.language_name
        project_factory = projects.get_factory_from_name(language_name)

        # Create directory
        project_directory = tempfile.mkdtemp(dir=projects.CODE_WORKING_DIR)

        if self.submission_request.problem_type == 'code_multiple_languages':            
            if language_name == 'verilog':
                code_file_name = tempfile.mkstemp(suffix="D.v", dir=project_directory)[1]
                testbench_temp_name = tempfile.mkstemp(suffix="T.v", dir=project_directory)[1]
                golden_temp_name = tempfile.mkstemp(suffix="G.v", dir=project_directory)[1]
            elif language_name == 'vhdl':
                code_file_name = tempfile.mkstemp(suffix="D.vhd", dir=project_directory)[1]
                testbench_temp_name = os.path.join(project_directory, testbench_file_name)

            with open(code_file_name, "w+") as code_file:
                code_file.write(self.submission_request.code)
                copyfile(testbench_file_name, testbench_temp_name)
                copyfile(golden_file_name, golden_temp_name)

            if language_name == 'verilog':
                return project_factory.create_from_directory(project_directory)
            elif language_name == 'vhdl':                
                return project_factory.create_from_directory(project_directory, testbench_temp_name[1], self.entity_name)

        if self.submission_request.problem_type == 'code_file_multiple_languages':
            project_directory = tempfile.mkdtemp(dir=projects.CODE_WORKING_DIR)

            # Add source code to zip file
            with open(project_directory + ".zip", "wb") as project_file:
                project_file.write(self.submission_request.code)

            # Unzip all the files on the project directory
            with ZipFile(project_directory + ".zip") as project_file:
                project_file.extractall(path=project_directory)

            if language_name == 'verilog':
                # Add the testbench
                testbench_temp_name = tempfile.mkstemp(suffix=".v", dir=project_directory)[1]
                copyfile(testbench_file_name, testbench_temp_name)
                return project_factory.create_from_directory(project_directory)         
            elif language_name == 'vhdl':
                testbench_temp_name = os.path.join(project_directory, testbench_file_name)
                copyfile(testbench_file_name, testbench_temp_name)
                return project_factory.create_from_directory(project_directory, testbench_temp_name[1], self.entity_name)

    def grade(self, testbench_file_name, expected_output_name):
        """
        Creates, Runs ands Test the code from the user. Finally setting the feedback
        variables.
        """

        debug_info = {'files_feedback': {}}
        # Create the project
        project = self.create_project(testbench_file_name, expected_output_name)
        # Run the project
        try:
            project.build()
        except projects.BuildError as e:
            debug_info["compilation_output"] = e.compilation_output

        if "compilation_output" in debug_info:
            feedback_info = {'global': {}, 'custom': {}}
            feedback_info['global']['result'] = "failed"
            feedback_info['grade'] = 0.0
            compilation_output = debug_info.get("compilation_output", "")
            feedback_str = gutils.feedback_str_for_compilation_error(compilation_output)
        else:
            results = project.run(None)

            result, debug_info['files_feedback'][testbench_file_name], feedback_info = self._construct_feedback(results)
            test_cases = (testbench_file_name, expected_output_name)
            feedback_str = self.diff_tool.hdl_to_html_block(0, result, test_cases, debug_info)

        feedback_info['global']['feedback'] = feedback_str
        set_feedback(feedback_info)
        # Return the grade and feedback of the code

    def _construct_feedback(self, results):
        #results contains the std ouput of the simulation of the golden model which is the expected output, and the return_code, stdout and stderr of the simulation of the code in evaluation
        stdout_golden, result_evaluation = results
        return_code, stdout, stderr = result_evaluation

        feedback_info = {'global': {}, 'custom': {}}
        result = GraderResult.WRONG_ANSWER
        if return_code == 0:
            expected_output = stdout_golden
            correct = self.check_output(stdout, expected_output)
            feedback_info['global']['result'] = "success" if correct else "failed"
            feedback_info['grade'] = 100.0 if correct else 0.0
            if correct:
                result = GraderResult.ACCEPTED

        debug_info = {}

        if result != GraderResult.ACCEPTED:
            diff = None
            if self.generate_diff:
                diff = self.diff_tool.compute(stdout, expected_output)

            debug_info.update({
                "input_file": "",
                "stdout": html.escape(stdout),
                "stderr": html.escape(stderr),
                "return_code": return_code,
                "diff": None if diff is None else html.escape(diff),
            })
        return result, debug_info, feedback_info


def handle_problem_action(problem_id, testbench, output, options=None):
    sub_req = SubmissionRequest(problem_id)
    grader = HDLGrader(sub_req, options)
    grader.grade(testbench, output)


class DiffWaveDrom(Diff):
    def hdl_to_html_block(self, test_id, result, test_case, debug_info):
        html_block = self.to_html_block(test_id, result, test_case, debug_info)
        if html_block.find("updateDiffBlock") != -1:
            html_block = html_block.replace("updateDiffBlock", "updateWaveDromBlock")
        return html_block
