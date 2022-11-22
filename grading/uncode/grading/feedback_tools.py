"""
This module contains the tools for presenting the feedback to the student.

Tools:
    - Diff
    - Feedback Manager/Handler/

TO DO:
    - Charts: Donut, Bars
"""

import difflib
import itertools
import sys

from graders_utils import reduce_text, html_to_rst as html2rst
from inginious import feedback
from results import GraderResult


class Diff:
    """
    This class contains the toolbox (methods) for the creation
    of a diff feedback

    Attributes:
        - diff_max_lines (int): The maximum number of lines that the diff tool should show
        - diff_context_lines (int): The diff tool context lines to use. # TODO Better Resume
        - output_diff_for (set): Group of str containing the test cases for which the diff
        tool is going to be used.
        - testcase_template (str): Containing the html code for presenting the diff of
        an specific test case
    """

    def __init__(self, options):
        """
        Initialize the object with the attributes found on the options
        dictionary. 

        Note: This dictionary is given on the run file, given by the task creator

        Args:
            options (dict): Dictionary that contains the options given on the run file    
        """
        self.diff_max_lines = options.get("diff_max_lines", 100)
        self.diff_context_lines = options.get("diff_context_lines", 3)
        self.output_diff_for = set(options.get("output_diff_for", []))
        self.custom_feedback = options.get("custom_feedback", {})
        self.show_input = options.get('show_input', False)

        self.toggle_debug_info_template = ["""<ul><li><strong>Test {test_id}: {result_name} </strong>
                                    <a class="btn btn-default btn-link btn-xs" role="button" data-toggle="collapse" 
                                    href="#{panel_id}" aria-expanded="false" aria-controls="{panel_id}">""" +
                                           _("Toggle diff") + """</a> <div class="collapse" id="{panel_id}">""",
                                           """</div></li></ul>"""]
        self.toggle_debug_info_template_for_staff = ["""<ul><li><strong>Test {test_id}: {result_name} </strong>
                                    <a class="btn btn-default btn-link btn-xs" role="button" data-toggle="collapse" 
                                    href="#{panel_id}" aria-expanded="false" aria-controls="{panel_id}">""" +
                                           _("Toggle diff (only for staff)") + """</a> <div class="collapse" id="{panel_id}">""",
                                           """</div></li></ul>"""]
        self.input_template = _("""<p>Input preview: {title_input}</p>
                                  <pre class="input-area" id="{block_id}-input">{input_text}</pre>
                                  <div id="{title_input}_download_link"></div>
                                  <script>createDownloadLink("{title_input}");</script>
                                  """)
        self.diff_template = """<pre id="{block_id}"></pre>
                                <script>updateDiffBlock("{block_id}", `{diff_result}`);</script>"""
        self.custom_feedback_template = _("""<p>Custom feedback</p><pre>{custom_feedback}</pre><br>""")
        self.runtime_error_template = """<p>Error: </p><br><pre>{stderr}</pre>"""

        self.not_debug_info_template = """<ul><li><strong>Test {0}: {1} </strong></li></ul>"""

    def compute(self, current_output, expected_output):
        """
        Computes a diff between the program output and the expected output.
        This function will strip the diff to diff_max_lines, and provide a context of diff_context_lines
        for each difference found.

        Args:
            - actual_output (str): First text given for the diff tool.
            - expected_output (str): Second text given for the diff tool.
        """
        #  800 KBs will be the max length of stdout and expected output to calculate diff
        _max_length = (2 ** 10) * 800
        expected_output = reduce_text(expected_output, _max_length)
        expected_output_lines = expected_output.splitlines()
        # In case the expected output has an end of line at the end, add it to the split lines.
        if expected_output and expected_output[-1] == '\n':
            expected_output_lines.append("\n")

        actual_output = reduce_text(current_output, _max_length)
        actual_output_lines = actual_output.splitlines()
        # In case the actual output has an end of line at the end, add it to the split lines.
        if actual_output and actual_output[-1] == '\n':
            actual_output_lines.append("\n")

        diff_generator = difflib.unified_diff(expected_output_lines, actual_output_lines, n=self.diff_context_lines,
                                              fromfile="expected_output",
                                              tofile="your_output")

        # Remove file names (legend will be added in the frontend)
        start = 2
        diff_output = '\n'.join(itertools.islice(diff_generator, start,
                                                 start + self.diff_max_lines if
                                                 self.diff_max_lines is not None else sys.maxsize))

        end_of_diff_reached = next(diff_generator, None) is None

        if not end_of_diff_reached:
            diff_output += "\n..."

        if diff_output == "":
            diff_output = _("\n@@ Diff is too big and was clipped. The error might be in last lines.\n")

        return diff_output
    
    def get_options_dict(self):
        """
        This method creates a dictionary containing the information of the options required for the feedback

        """
        options = {
            "diff_max_lines":self.diff_max_lines,
            "diff_context_lines":self.diff_context_lines,
            "output_diff_for":list(self.output_diff_for),
            "custom_feedback":self.custom_feedback,
            "show_input":self.show_input,
        }
        return options

    def to_html_block(self, test_id, result, test_case, debug_info, is_staff=False):
        """
        This method creates a html block (rst embedding html) for a single test case.

        Args:
            - test_id (int):
            - result: Represents the results for the feedback (check 'results.py')
            - test_case (tuple): A pair of names. The input filename and the expected output filename
            - debug_info (dict): Debugging information about the execution of the source code.

        Returns:
            An string representing the html block to be presented in the feedback about 
            a single test case.
        """
        input_filename = test_case[0]
        if result in [GraderResult.ACCEPTED, GraderResult.INTERNAL_ERROR] or input_filename not in self.output_diff_for and not is_staff:
            text = self.not_debug_info_template.format(
                test_id + 1, result.name)
            return html2rst(text)

        diff_result = debug_info.get("files_feedback", {}).get(input_filename, {}).get("diff", None)
        stderr = debug_info.get("files_feedback", {}).get(input_filename, {}).get("stderr", "")
        diff_available = diff_result is not None
        input_text = get_input_sample(test_case)
        template_info = {
            "test_id": test_id + 1,
            "result_name": result.name,
            "panel_id": "collapseDiff" + str(test_id),
            "block_id": "diffBlock" + str(test_id),
            "input_text_id": "input_text_" + str(test_id),
            "input_text": input_text,
            "title_input": test_case[0]
        }
        template = [self.toggle_debug_info_template[0]] if not is_staff else [self.toggle_debug_info_template_for_staff[0]]


        if input_filename in self.custom_feedback:
            template_info["custom_feedback"] = self.custom_feedback[input_filename]
            template.append(self.custom_feedback_template)

        if self.show_input:
            template.append(self.input_template)

        if diff_available:
            template_info["diff_result"] = escape_text(diff_result)
            template.append(self.diff_template)

        if GraderResult.RUNTIME_ERROR == result:
            template_info["stderr"] = stderr
            template.append(self.runtime_error_template)

        template.append(self.toggle_debug_info_template[1])
        diff_html = "".join(template).format(**template_info)

        return html2rst(diff_html)


def get_input_sample(test_case):
    """ This method reads and gets an small sample of input that will be shown to students."""
    max_lines = 15
    max_length = 2 ** 10
    with open(test_case[0], 'r') as input_file:
        input_text = input_file.readlines()
        if len(input_text) > max_lines:
            input_sample = "".join(input_text[:max_lines] + ['...\n'])
        else:
            input_sample = "".join(input_text)

        if len(input_sample) > max_length:
            return input_sample[:max_length] + '...\n'
        else:
            return input_sample


def set_feedback(results):
    """
    Sets all the feedback variables using the dict results.

    Args:
        - results (dict): Contains all the information necessary for
        returning the feedback information. i.e global_result, global_feedback,
        grade, and all the custom values.
    """
    for key in results['custom']:
        feedback.set_custom_value("custom_" + key, results['custom'][key])

    # Set global values
    feedback.set_global_result(results['global']['result'])
    feedback.set_grade(results['grade'])
    feedback.set_global_feedback(results['global']['feedback'])


def escape_text(text):
    return text.replace('\\', "\\\\").replace('`', "\\`").replace('\n', "\\n").replace("$", "\\$").replace('\t', "\\t")
