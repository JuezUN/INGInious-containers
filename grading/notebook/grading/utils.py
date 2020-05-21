import json
import subprocess

import graders_utils as gutils
from graders_utils import html_to_rst as html2rst
from results import GraderResult


def _run_command(command, **additional_flags):
    completed_process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **additional_flags)
    stdout = completed_process.stdout.decode()
    stderr = completed_process.stderr.decode()
    return_code = completed_process.returncode
    return return_code, stdout, stderr


def _feedback_str_for_internal_error():
    return "**{}**: There was an error while running your notebook. Please submit again.\n\n".format(
        GraderResult.INTERNAL_ERROR.name)


def _generate_feedback_info_internal_error(debug_info):
    feedback_info = {'global': {}, 'custom': {}}
    feedback_str = _feedback_str_for_internal_error()
    feedback_info['custom']['additional_info'] = json.dumps(debug_info)
    feedback_info['custom']['traceback'] = debug_info
    feedback_info['global']['result'] = "failed"
    feedback_info['grade'] = 0.0
    feedback_info['global']['feedback'] = feedback_str
    return feedback_info


def _generate_feedback_info(grader_results, debug_info, weights, tests):
    """
    This method generates a dictionary containing the information for the feedback
    setting function (check 'feedback_tools.py')

    Args:
        - results (list): Containing the results for executing student's source code (check 'results.py')
        - debug_info (dict): Dictionary containing the debugging info for the execution
        of the test cases.
        - weights (list): List of integers containing the importance of the nth-test
        - tests (list of tuples): A list containing a tuples with three values. The test's name, test's
        filename and amount of test_cases.
    """

    if weights is None:
        weights = [1] * len(tests)
    results = [grader_result["result"] for grader_result in grader_results]
    grades = [grader_result["total"] for grader_result in grader_results]
    feedback_info = {'global': {}, 'custom': {}}

    passing = sum(1 for result in grader_results if result["result"] == GraderResult.ACCEPTED)
    score = sum(grades)
    total_sum = sum(weights)

    summary_result = gutils.compute_summary_result(results)

    internal_errors = []
    for test_feedback in debug_info["files_feedback"].values():
        cases_errors = ["\t- Case {}: {}".format(i, case["error"]) for i, case in test_feedback["cases_info"].items() if
                        "is_grading_error" in case]
        if cases_errors:
            internal_error = [test_feedback["test_name"]] + cases_errors
            internal_errors.append("\n".join(internal_error))

    feedback_info['custom']['additional_info'] = json.dumps(debug_info)
    feedback_info['custom']['summary_result'] = summary_result.name
    feedback_info['custom']['internal_error'] = "\n".join(internal_errors)
    feedback_info['global']['result'] = "success" if passing == len(tests) else "failed"
    feedback_info['grade'] = score * 100.0 / total_sum

    return feedback_info


def _result_to_html(test_id, test_result, weight, show_debug_info):
    cases_debug_info = test_result["cases"]

    template_info = {
        "test_id": test_id + 1,
        "test_name": test_result["name"],
        "result_name": test_result["result"].name,
        "panel_id": "collapseDebug" + str(test_id),
        "block_id": "debugBlock" + str(test_id),
        "weight": weight,
        "total": "%.2f" % test_result["total"],
    }
    test_name_template_html = [
        """<ul class="list_disc" style="font-size:12px;"><li>
        <strong style="font-size:15px"> {test_name}: </strong><i>{result_name} - {total} / {weight} </i>""",
        "</li></ul>"
    ]
    test_results_template_html = [
        """<a class="btn btn-default btn-link btn-xs" role="button"
        data-toggle="collapse" href="#{panel_id}" aria-expanded="false" aria-controls="{panel_id}">
        Expand test results
        </a><div class="collapse" id="{panel_id}">""",
        "</div>"
    ]

    test_case_error_template_html = """<strong>Error:</strong><br><pre>{case_error}</pre>"""
    test_case_wrong_answer_template_html = """
                                        <br><strong>Output difference:</strong><pre>{case_output_diff}</pre><br>"""
    test_case_debug_info_template_html = """<ul class="list_disc" style="font-size:12px; list-style-type: square;"><li>
        <strong>Case {case_id}:</strong><a class="btn btn-default btn-link btn-xs" role="button" data-toggle="collapse" 
        href="#{case_panel_id}" aria-expanded="false"aria-controls="{case_panel_id}">Show debug info</a>
        <div class="collapse" id="{case_panel_id}">{debug_info}</div></li></ul>
        """
    test_case_executed_code = '<strong>Executed code:</strong><pre class="language-python"><code ' \
                              'class="language-python" data-language="python">{case_code}</code></pre>' \
                              '<script>highlight_code();</script>'

    result_html = [test_name_template_html[0]]
    if cases_debug_info and show_debug_info:
        result_html.append(test_results_template_html[0])
        for i, case_debug_info in cases_debug_info.items():
            debug_info = []
            if case_debug_info["is_runtime_error"]:
                debug_info.append(test_case_error_template_html.format(case_error=case_debug_info["error"]))
            if "case_code" in case_debug_info:
                debug_info.append(test_case_executed_code.format(
                    case_code=case_debug_info["case_code"].replace("{", "{{").replace("}", "}}")))
            if not case_debug_info["is_runtime_error"]:
                case_output_diff = case_debug_info["case_output_diff"].replace("/n", "<br>").replace("<", "&lt;")
                debug_info.append(test_case_wrong_answer_template_html.format(case_output_diff=case_output_diff))
            case_data = {
                "case_id": i,
                "case_panel_id": "collapse_debug_test_%s_case_%s" % (str(test_id), str(i)),
                "debug_info": ''.join(debug_info)
            }
            result_html.append(test_case_debug_info_template_html.format(**case_data))
        result_html.append(test_results_template_html[1])

    result_html.append(test_name_template_html[1])
    result_html = ''.join(result_html).format(**template_info)

    return html2rst(result_html)
