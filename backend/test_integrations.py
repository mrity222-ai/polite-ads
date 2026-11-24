"""Compatibility entrypoint. Historical assertions are archived in docs/archived-tests.
Runs the maintained isolated regression suite, not a separate 35/11/10-check audit.
"""
if __name__ == '__main__':
    import unittest
    import test_regressions
    unittest.main(module=test_regressions, verbosity=2)
