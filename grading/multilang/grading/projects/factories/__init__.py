from .utils import InginiousSandboxRunner
from .c import CProjectFactory
from .cpp import CppProjectFactory
from .java import JavaProjectFactory
from .python import PythonProjectFactory

_ALL_FACTORIES = {}


def initialize_factories(sandbox_runner=InginiousSandboxRunner()):
    global _ALL_FACTORIES
    _ALL_FACTORIES = {
        "python2": PythonProjectFactory(sandbox_runner),
        "python3": PythonProjectFactory(sandbox_runner, python_binary='python3'),
        "java7": JavaProjectFactory(sandbox_runner, source_version="1.7",
                                    bootclasspath="/usr/lib/jvm/java-1.7.0-openjdk/jre/lib/rt.jar"),
        "java8": JavaProjectFactory(sandbox_runner),
        "cpp": CppProjectFactory(sandbox_runner, additional_flags=["-O2"]),
        "cpp11": CppProjectFactory(sandbox_runner, additional_flags=["-std=c++11", "-O2"]),
        "c": CProjectFactory(sandbox_runner, additional_flags=["-O2"]),
        "c11": CProjectFactory(sandbox_runner, additional_flags=["-std=c11", "-O2"])
    }


def factory_exists(name):
    return name in _ALL_FACTORIES


def get_factory_from_name(name):
    """
    Returns a ProjectFactory instance associated to the given name.
    Raises ValueError if no instance is associated to that name.
    """

    if not factory_exists(name):
        raise ValueError("Factory does not exist: " + name)

    return _ALL_FACTORIES[name]


initialize_factories()
