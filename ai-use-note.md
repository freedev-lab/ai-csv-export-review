# AI-use note

## Tools
- **ChatGPT**, during the work: to understand the requirements, explain the starter code, identify bugs, draft regression tests, suggest improvements to the exporter and review the result against P1–P6.
- **Claude Code (Anthropic)**, at the end: a read-only review of the whole submission and its git history against the README. At my request it then made the final changes, and I reviewed the diff before committing. Those changes were:
  - filling the placeholder results with executed output;
  - adding evidence to the review;
  - the nested-JSON fix and its test;
  - stronger checker tests.

## Concrete example: accepted, and how I checked it
**Output (Claude Code):** a valid JSON input nested 100,000 levels deep made the CLI crash with a Python traceback and exit code 1. P1 requires fatal errors to exit 2 with readable stderr and no stdout.

**How I checked it before accepting:**
1. I added `test_cli_rejects_excessively_nested_json` first and ran it against the unchanged code. It failed with `AssertionError: 1 != 2` (`work-log.md`, Appendix B.3).
2. The fix is one change: `RecursionError` was added to the fatal-error handler in `main()`.
3. I re-ran the full suite (32 tests, OK) and both fixtures. Their output is byte-for-byte unchanged.

## Earlier examples (ChatGPT)
- **Accepted:** use the standard library's `csv.writer` instead of joining strings with commas. I checked it against the exact P5 configuration with tests for commas, quotes, multiline cells and CRLF record endings, parsing the output back with `csv.reader`.
- **Accepted:** for `trim-space-tab`, check the formula character after `value.lstrip(" \t")`, not after `strip()`. P4 allows skipping only leading ASCII spaces and tabs, so a leading newline must still block a trigger. I checked it with `test_trim_space_tab_policy_skips_only_spaces_and_tabs` and `test_trim_policy_does_not_skip_newlines_or_existing_apostrophes`.

## How AI output was checked
AI suggestions were treated as proposals, not as finished answers. Each one was checked against `inputs/export-policy.md`, the fixture rows and executed tests. Every number in the final documents comes from a command that was actually run; the commands are in `run-guide.md`.
