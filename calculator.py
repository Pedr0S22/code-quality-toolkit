#!/usr/bin/env python3
"""
Wrapper to run DEV/calculator/calculator.py from repository root.
"""
import sys
import os

# Add DEV/calculator to sys.path so imports work
calculator_dir = os.path.join(os.path.dirname(__file__), 'DEV', 'calculator')
sys.path.insert(0, calculator_dir)

# Change working directory to DEV/calculator for relative imports
original_cwd = os.getcwd()
os.chdir(calculator_dir)

try:
    # Import and run the calculator main
    from calculator import main
    main()
finally:
    os.chdir(original_cwd)
