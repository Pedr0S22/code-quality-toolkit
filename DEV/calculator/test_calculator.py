# test_calculator.py
# NOTE: this is a unit test of the calculator function, not the individual operations.
# - Therefore it can also be understood as an integration test of each individual operation.
# - We shall be using this as the integration test in the  'Automation'  tutorial

import subprocess # to run 'calculator.py' as a subprocess so that we can check its usage with command line arguments


def test_calculator_add():
    # Run calculator.py as if from the command line with add inputs ok
    result = subprocess.run(['python3', 'calculator.py', '+', '2', '3'], capture_output=True, text=True)

    # Assert the expected output
    assert '5' in result.stdout
#    assert '2' in result.stdout (only needed if you have more return arguments)

def test_wrong_operation():
    # Run calculator.py with an operation that was not yet implemented
    result = subprocess.run(['python3', 'calculator.py', '%', '2', '3'], capture_output=True, text=True)

    # Assert the expected output
    assert 'Invalid operation: %' in result.stdout


def test_wrong_nr_inputs():
    # Run calculator.py with a wrong number of inputs
    result = subprocess.run(['python3', 'calculator.py', '-', ], capture_output=True, text=True)

    # Assert the expected output
    assert 'Number of arguments must be exactly three' in result.stdout

