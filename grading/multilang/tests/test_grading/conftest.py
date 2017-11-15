import pytest
import subprocess
from grading.projects.factories import initialize_factories
from grading.projects.factories.utils import SandboxRunner


@pytest.fixture
def fake_sandbox():
    class FakeSandboxRunner(SandboxRunner):
        def run_command(self, command, **subprocess_options):
            completed_process = subprocess.run(command, stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE, **subprocess_options)

            stdout = completed_process.stdout.decode()
            stderr = completed_process.stderr.decode()
            return_code = completed_process.returncode

            return return_code, stdout, stderr

    initialize_factories(FakeSandboxRunner())
    yield None
    initialize_factories()
