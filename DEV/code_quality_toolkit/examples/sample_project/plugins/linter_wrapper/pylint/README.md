# Test Data Generation Summary
This directory contains generated Python files to validate the LINTER_WRAPPER plugin. The files are categorized by severity levels mapped to Pylint message types:

- **L1 (Low / Convention & Refactor):** Tests style issues, naming conventions (C0103), missing docstrings (C0114), and code complexity (R0913).
- **L2 (Medium / Warning):** Tests potential bugs, unused imports (W0611), dangerous defaults (W0102), and unreachable code (W0101).
- **L3 (High / Error & Fatal):** Tests build-breaking errors, syntax issues, undefined variables (E0602), and import errors (E0401).

**Mixed Sets:**
- Combinations (L1+L2, L1+L3, L2+L3) to test severity aggregation logic.
- **Kitchen Sink:** A stress-test file containing violations of all severity levels simultaneously to verify full reporting capabilities.
```

### Option 2: Detailed Inventory (Best for the specific test script header)

This lists the exact files created and the specific Pylint codes they trigger.

```text
Test Suite Inventory:
---------------------------------------------------------
1. L1_Low (Convention/Refactor):
   - low_1_naming.py    : Invalid Naming (C0103)
   - low_2_docstring.py : Missing Docstring (C0114)
   - low_3_else.py      : Unnecessary Else (R1705)
   - low_4_lines.py     : Line Too Long (C0301)
   - low_5_args.py      : Too Many Arguments (R0913)

2. L2_Medium (Warning):
   - med_1_import.py    : Unused Import (W0611)
   - med_2_unused.py    : Unused Variable (W0612)
   - med_3_dangerous.py : Dangerous Default Arg [] (W0102)
   - med_4_unreach.py   : Unreachable Code (W0101)
   - med_5_eval.py      : Use of Eval (W0123)

3. L3_High (Error):
   - high_1_undef.py    : Undefined Variable (E0602)
   - high_2_member.py   : Member Not Found (E1101)
   - high_3_importerr.py: Import Error (E0401)
   - high_4_args.py     : No Value For Argument (E1120)
   - high_5_redef.py    : Function Redefined (E0102)

4. Mixed Scenarios:
   - Mix_L1_L2          : Style issues + Warnings
   - Mix_L1_L3          : Style issues + Errors
   - Mix_L2_L3          : Warnings + Errors
   - Mix_All            : All severity levels combined
   
5. Stress Test:
   - kitchen_sink_nightmare.py : A single file triggering violations 
     across all categories (L1, L2, L3) to ensure robust parsing.