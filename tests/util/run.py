#!/usr/bin/env python3
try:
    import coverage as cvrg
    coverage = cvrg.Coverage(include='evernotebot/*')
    coverage.start()
except ImportError:
    coverage = None

import importlib.util
import os
import sys
import unittest
from os.path import dirname


def coverage_report(coverage):
    coverage.stop()
    coverage.save()
    try:
        coverage.report()
    except cvrg.misc.CoverageException:
        pass


def import_module_by_path(path):
    spec = importlib.util.spec_from_file_location('test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_test_modules(pattern):
    test_modules = []
    if pattern.endswith('.py') and os.path.sep in pattern and os.path.exists(pattern):
        module = import_module_by_path(pattern)
        return [module]
    current_dir = os.path.dirname(os.path.realpath(__file__))
    for dirpath, _, filenames in os.walk(current_dir):
        for name in filenames:
            if name.startswith('test') and name.endswith('.py') and pattern in name.lower():
                path = os.path.join(dirpath, name)
                module = import_module_by_path(path)
                test_modules.append(module)
    return test_modules


if __name__ == '__main__':
    os.environ['EVERNOTEBOT_HOSTNAME'] = 'localhost'
    os.environ['TELEGRAM_BOT_NAME'] = 'test'
    os.environ['TELEGRAM_API_TOKEN'] = 'secret'  # nosec
    os.environ['EVERNOTE_READONLY_KEY'] = 'secret'  # nosec
    os.environ['EVERNOTE_READONLY_SECRET'] = 'secret'  # nosec
    os.environ['EVERNOTE_READWRITE_KEY'] = 'secret'  # nosec
    os.environ['EVERNOTE_READWRITE_SECRET'] = 'secret'  # nosec

    project_dir = dirname(dirname(os.path.realpath(__file__)))
    sys.path.insert(0, project_dir)
    pattern = sys.argv[1].lower() if len(sys.argv) > 1 else ''
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for module in get_test_modules(pattern):
        suite.addTests(loader.loadTestsFromModule(module))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.failures or result.errors:
        sys.exit(1)
    elif coverage:
        coverage_report(coverage)
