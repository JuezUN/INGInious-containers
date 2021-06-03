import re


def remove_sockets_exception(stderr):
    if not stderr:
        return stderr
    stderr = stderr.split('\n')
    start_exception_regex = r"Exception ignored in: <bound method Socket\.__del__ of <zmq\.sugar\.socket\.Socket.*"
    start_exception_index = len(stderr)
    for i, line in enumerate(stderr):
        if re.match(start_exception_regex, line):
            start_exception_index = i
            break

    return "\n".join([line for i, line in enumerate(stderr) if i < start_exception_index])


def cut_stderr(stderr):
    """This cut the stderr in case it is too long just showing the first and last lines"""

    if not stderr:
        return stderr

    max_lines = 20
    stderr_lines = stderr.split('\n')
    if len(stderr_lines) <= max_lines:
        return stderr

    stderr_lines = stderr_lines[:max_lines // 2] + ['\t\t...'] + stderr_lines[-(max_lines // 2):]
    return "\n".join(stderr_lines)


def is_presentation_error(stdout, expected_output):
    """

    Tokenize the texts by splitting the texts with multiple delimiters: space, \r, \t, and \n. Resulting empty strings
    are ignored. That way, the comparison of the two generated lists is done only with the actual answers.

    A presentation error is considered when the data in the output is correct, but it is not correctly formatted.
    Therefore, both outputs, the `stdout` and `expected_output`, must have the same tokens.

    The `stdout` is not considered presentation error in two cases:
        1. The length of tokens is different to the total tokens from the expected output. This is probably a wrong
            answer.
        2. A token is different from the expected output.
    :param stdout: the test case's output after running the code.
    :param expected_output: expected output of the corresponding test case.
    :return: Boolean value indicating if there is presentation error or not.
    """
    tokens_stdout = [token for token in re.split("[ \r\t\n]", stdout) if token]
    tokens_expected_output = [token for token in re.split("[ \r\t\n]", expected_output) if token]

    if len(tokens_stdout) != len(tokens_expected_output):
        return False

    idx_token_expected_output = 0
    for token_stdout in tokens_stdout:
        token_expected_output = tokens_expected_output[idx_token_expected_output]

        if token_stdout != token_expected_output:
            return False

        idx_token_expected_output += 1

    return True
