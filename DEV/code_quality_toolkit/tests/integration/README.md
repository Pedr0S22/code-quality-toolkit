# CLI Failure Modes – Technical Documentation
## Component Name
cli_failure_modes_tests

## Version
0.1.0

## Authors
Alfonso Pintado Gracia            2025175710        @alfooonsoo17
Carlos Lomelín Valdés             2025154763        @carloslomelinv
Miguel Pedro Rodrigues Carvalho   2023216436        @parzival3301
Samuel Gomes Esteban              2025178876        @samuugomes
Mathias Gustavo Welz              2025167903        @mathiasgwelz

## ---USER GUIDE---
## What These Tests Verify
The CLI failure-mode tests ensure that the Code Quality Toolkit behaves safely and predictably when things go wrong.
They validate that the CLI:
- Does not crash even if the engine crashes internally
- Handles plugin load errors cleanly
- Produces a valid report even when a plugin crashes at runtime
- Applies severity-based exit codes correctly
These tests guarantee CLI resilience from the user perspective.

## How These Tests Work
1. Each test creates a temporary project directory.
2. The CLI is executed through main([...]).
3. Internal components such as load_plugins and run_analysis are mocked to simulate failures.
4. The returned exit code and output files are validated.

## What You’ll See When Running Them
- No Python traceback unless the error is unmanaged
- Predictable exit codes:
  - 0: success
  - 1: plugin load error
  - 2: unexpected engine crash
  - 3: severity threshold triggered

## Example Failure Behaviors
- A plugin failing to load prints a clean error message and exits with code 1
- A plugin crashing during analyze() still generates report.json
- A synthetic "PLUGIN_ERROR" entry appears when a plugin crashes
- Passing --fail-on-severity high produces exit code 3 when a plugin triggers a high-severity issue
Each test ensures that the system reacts gracefully and remains usable.

## How to Interpret Failures
If any of these tests fail, it usually indicates:
- An exception is escaping the CLI (bug)
- The wrong exit code is being returned
- The CLI generated no report when it should
- Plugin errors are not being captured properly
Fixes often involve adding or adjusting try/except blocks inside the CLI engine.

## Summary
These tests exist to guarantee that the CLI cannot be taken down by a misbehaving plugin or engine component.
They enforce high reliability and user-facing stability.

## ---TECHNICAL DOCUMENTATION---
## Description
This module defines integration tests for the Code Quality Toolkit CLI, focusing on failure modes, error handling, and exit-code correctness.

It validates the system’s ability to:
- Catch internal engine crashes
- Manage plugin load errors
- Record plugin runtime failures in output reports
- Enforce severity-based exit gating
The goal is to ensure that no exception from any part of the system can crash the CLI.

## 1. Purpose
The purpose of this test suite is to ensure that the CLI maintains:
- Fault isolation between components
- Deterministic exit codes
- Stable behavior under plugin failures
- Valid output reports even in error conditions
These tests shield end-users from internal errors.

## 2. How It Works
The tests simulate four critical failure modes:
- 1 Engine crash simulation
  - run_analysis is patched to raise Exception("Core Meltdown")
  - Expected exit code: 2
- 2 Plugin load failure
  - load_plugins is patched to raise PluginLoadError
  - Expected behaviors:
    - exit code 1
    - error message printed to stderr
- 3 Plugin runtime crash
  - A mock plugin raises RuntimeError inside analyze()
  - Expected behaviors:
    - CLI does not crash
    - report.json is generated
    - global status = "failed"
    - plugin summary = "failed"
    - synthetic "PLUGIN_ERROR" issue included
- 4 Severity-based exit code
  - With --fail-on-severity high, a crashing plugin triggers exit code 3
  - Ensures severity filters apply even during plugin errors
All tests use tmp_path for isolation and unittest.mock.patch to inject controlled failures.

## 3. Main Component: Crashing Plugin Stub
# Attributes
The stub plugin defines minimal metadata:
  "name": "CrashingPlugin"
  "version": "0.0.1"
  "description": "Always crashes"
# Important Methods
  get_metadata(): supplies plugin identification
  analyze(source_code, file_path): intentionally raises RuntimeError
  Used to test the engine’s error-capture behavior
This plugin always fails, making it ideal for resilience testing.

## 4. Output Format (When Plugin Crashes)
The CLI writes a report.json containing:
{
  "analysis_metadata": {
    "status": "failed"
  },
  "details": [
    {
      "plugins": [
        {
          "plugin": "CrashingPlugin",
          "summary": { "status": "failed" },
          "results": [
            {
              "code": "PLUGIN_ERROR",
              "message": "...plugin exception..."
            }
          ]
        }
      ]
    }
  ]
}
This structure proves that the error was caught, recorded, and reported.

## 5. Expected Exit Codes
- EXIT_SUCCESS → 0
- EXIT_MANAGED_ERROR → 1
- EXIT_UNEXPECTED_ERROR → 2
- EXIT_SEVERITY_ERROR → 3
Each test checks that the correct code is returned.

## 6. Conclusion
This test suite is essential for validating the resilience and reliability of the CLI.
It ensures that plugin crashes, engine failures, or configuration issues never destabilize the system.
By enforcing strict exit-code and reporting behavior, it guarantees a robust experience for all users.