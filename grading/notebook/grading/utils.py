import json

import graders_utils as gutils
from graders_utils import html_to_rst as html2rst
from results import GraderResult


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

    feedback_info['custom']['additional_info'] = json.dumps(debug_info)
    feedback_info['custom']['summary_result'] = summary_result.name
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
        "total": test_result["total"],
    }
    test_name_template_html = [
        """<ul><li><strong>{test_name}: {result_name} - {total} / {weight} </strong>""",
        "</li></ul>"
    ]
    test_results_template_html = [
        """<a class="btn btn-default btn-link btn-xs" role="button"
        data-toggle="collapse" href="#{panel_id}" aria-expanded="false" aria-controls="{panel_id}">
        Expand test results
        </a><div class="collapse" id="{panel_id}">""",
        "</div>"
    ]
    test_case_error_template_html = """- <strong>Case {case_id}:</strong> {case_error} <br>"""
    test_case_wrong_answer_template_html = """- <strong>Case {case_id}:</strong> 
        <a class="btn btn-default btn-link btn-xs" role="button" data-toggle="collapse" href="#{case_panel_id}" 
        aria-expanded="false"aria-controls="{case_panel_id}">Show debug info</a>
        <div class="collapse" id="{case_panel_id}"><div class="row"><strong>Executed code:</strong><pre>{case_code}</pre></div>
        <br><div class="row"><strong>Output difference</strong><pre>{case_output_diff}</pre></div></div><br>"""

    result_html = test_name_template_html[0].format(**template_info)
    test_result_name = test_result["result"].name
    if test_result_name in ["RUNTIME_ERROR", "WRONG_ANSWER"] and cases_debug_info and show_debug_info:
        result_html += test_results_template_html[0].format(**template_info)
        for i, case_debug_info in cases_debug_info.items():
            if case_debug_info["is_runtime_error"]:
                result_html += test_case_error_template_html.format(case_id=i, case_error=case_debug_info["error"])
            else:
                case_data = {
                    "case_id": i,
                    "case_panel_id": "collapseDebugCase" + str(i),
                    "case_code": case_debug_info["case_code"].replace("/n", "<br>"),
                    "case_output_diff": case_debug_info["case_output_diff"].replace("/n", "<br>")
                }
                result_html += test_case_wrong_answer_template_html.format(**case_data)
        result_html += test_results_template_html[1]
    result_html += test_name_template_html[1]

    return html2rst(result_html)
