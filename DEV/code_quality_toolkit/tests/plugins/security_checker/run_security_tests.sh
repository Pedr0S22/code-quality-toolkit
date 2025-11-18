#!/bin/bash

# Simple test runner for Security Checker

set -e

if ! command -v pytest &> /dev/null; then
    echo "Error: pytest not installed"
    echo "Install: pip install pytest"
    exit 1
fi

pytest test_plugin_security.py "$@"