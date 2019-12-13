import json

import graders_utils as gutils
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


def _result_to_html(test_id, result, total, weight):
    return '- **Test %d: %s** - %0.2f / %0.2f' % (test_id + 1, result.name, total, weight)
