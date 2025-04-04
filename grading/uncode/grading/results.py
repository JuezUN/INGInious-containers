from enum import IntEnum


class GraderResult(IntEnum):
    """
    Represents a result of the grader. Results are ordered by precedence (lower values override
    higher values when computing a summary result).
    """
    COMPILATION_ERROR = 10
    TIME_LIMIT_EXCEEDED = 20
    MEMORY_LIMIT_EXCEEDED = 30
    RUNTIME_ERROR = 40
    OUTPUT_LIMIT_EXCEEDED = 50
    GRADING_RUNTIME_ERROR = 60
    INTERNAL_ERROR = 70
    PRESENTATION_ERROR = 80
    WRONG_ANSWER = 90
    ACCEPTED = 100


class SandboxCodes(IntEnum):
    MEMORY_LIMIT = 252
    TIME_LIMIT = 253
    INTERNAL_ERROR = 254


def parse_non_zero_return_code(return_code):
    assert return_code != 0

    if return_code == SandboxCodes.MEMORY_LIMIT:
        return GraderResult.MEMORY_LIMIT_EXCEEDED
    elif return_code == SandboxCodes.TIME_LIMIT:
        return GraderResult.TIME_LIMIT_EXCEEDED
    elif return_code == SandboxCodes.INTERNAL_ERROR:
        return GraderResult.INTERNAL_ERROR
    else:
        return GraderResult.RUNTIME_ERROR
