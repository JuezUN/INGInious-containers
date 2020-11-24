"""
This module contains the util functions for the grader and feedback_tools modules.
"""
import rst
from sys import getsizeof


def html_to_rst(html):
    """ Generates an RST HTML block from the given HTML """
    return '\n\n.. raw:: html\n\n' + rst.indent_block(1, html) + '\n'


def feedback_str_for_compilation_error(compilation_output):
    return "**Compilation error**:\n\n" + html_to_rst("<pre>%s</pre>" % (compilation_output,))


def compute_summary_result(results):
    return min(results)


def check_output(actual_output, expected_output):
    """
    Compares the output of a program against an expected output. Returns true if the actual and the
    expected output match.
    """

    return actual_output == expected_output


def reduce_text(text, max_size, additional_text=""):
    if getsizeof(text) <= max_size:
        return text
    else:
        split_text = text.splitlines()
        new_text = []
        for s in split_text:
            new_text.append(s)
            if getsizeof(new_text) >= max_size:
                break
        new_text.append(additional_text)

        return '\n'.join(new_text)
