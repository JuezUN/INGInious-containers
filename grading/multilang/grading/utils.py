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
