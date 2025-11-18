# Duplicate Code Checker Plugin

This plugin identifies repeated blocks of code by scanning
the source with a sliding-window approach.

It compares consecutive normalized lines (excluding comments
and empty lines) to detect structural duplication.

## Configuration

The checker uses a **window size** to determine how many
consecutive lines form a block.  The default window is
**3**, but it can be adjusted when calling the checker
directly:

```python
dc.check(source_code, window=4)
```

A larger window reduces false positives by requiring longer
repeated sequences. A smaller window increases sensitivity
but may flag shorter patterns.

## Results

The plugin produces a report containing:

- A results list with entries describing each duplicate block:
    - severity: always "medium"
    - code: "DUPLICATED_CODE"
    - message: includes a block signature
    - line: starting line of the duplicate block
    - hint: suggestion to refactor repeated logic
- A summary section reporting:
    - total issues detected
    - analysis status
