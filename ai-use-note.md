# AI-use note

## Tools
- **ChatGPT**, during the work: to understand the requirements, explain the starter code, identify bugs, draft regression tests, suggest improvements to the exporter and review the result against P1–P6.
- **Claude Code (Anthropic)**, at the end (2026-11-12): first a read-only review of the whole submission, then the final changes at my request (details below). I reviewed its diff before committing. Claude Code did not commit or push anything.

## What Claude Code did

### 1. Read-only review (no files changed)
- Read the README, the export policy, the PR claims, the fixtures, every file in the repository and all 10 commits.
- Compared the supplied files with the original exercise zip. They were byte-identical, so no fixture, patch or claim had been edited.
- Ran the README commands: help, the test suite, both fixtures, malformed and missing input.
- Re-ran my pre-fix tests (commit `a7c1ff6`) against the original starter. 15 of 20 failed, which confirmed the failing-first order. The 7 P1 validation tests also passed on the starter, so they are controls.
- Captured the starter's real output on `primary.json` as evidence for the review:
  - 11 parsed records instead of 9;
  - X01 in the CSV and in the audit;
  - summary 9 exported / 1 foreign / 2 neutralized;
  - input mutated by repeat calls.
- Ran edge cases and a 5,000-row randomized round-trip on my fix (0 mismatches) and found one gap: deeply nested JSON crashed the CLI.
- Reported a prioritized list of problems:
  - the AI-use note and walkthrough were not pushed;
  - 8 placeholders were unfilled;
  - the review had no evidence;
  - the second-fixture reconciliation was not exact;
  - there was trailing whitespace.

### 2. Changes made at my request
- **`app.py`:** added `RecursionError` to the fatal-error handler (exit 2 instead of a traceback). Also removed trailing whitespace and extra blank lines and sorted the imports. The `export_rows` logic is unchanged.
- **Tests (27 → 32):**
  - the nested-JSON test, written and run before the fix;
  - the checker's foreign-content check fixed and extended;
  - literal README self-check values;
  - an exact 3-cell reconciliation of the second fixture;
  - a tamper test for the checker;
  - the optional generated-cell test.
- **Documentation:**
  - evidence added to `review.md`;
  - `run-guide.md` and `walkthrough.md` rewritten from executed output;
  - `work-log.md` restructured, with every placeholder filled;
  - this note updated.
- **Verification after the changes:**
  - 32/32 tests pass;
  - every run-guide command works as written;
  - `git diff --check` is clean;
  - the supplied files are unchanged.

## Concrete example: accepted, and how I checked it
**Output (Claude Code):** a valid JSON input nested 100,000 levels deep made the CLI crash with a Python traceback and exit code 1. P1 requires fatal errors to exit 2 with readable stderr and no stdout.

**How I checked it before accepting:**
1. I added `test_cli_rejects_excessively_nested_json` first and ran it against the unchanged code. It failed with `AssertionError: 1 != 2` (`work-log.md`, Appendix B.3).
2. The fix is one change: `RecursionError` was added to the fatal-error handler in `main()`.
3. I re-ran the full suite (32 tests, OK) and both fixtures. Their output is byte-for-byte unchanged.

## Other examples
- **Corrected (Claude Code):** its first draft of the work log said all the new checker tests fail on the original starter. The test output showed that the tamper test passes there, as designed, so the sentence was corrected before committing.
- **Accepted (ChatGPT):** use the standard library's `csv.writer` instead of joining strings with commas. I checked it against the exact P5 configuration with tests for commas, quotes, multiline cells and CRLF record endings, parsing the output back with `csv.reader`.
- **Accepted (ChatGPT):** for `trim-space-tab`, check the formula character after `value.lstrip(" \t")`, not after `strip()`. P4 allows skipping only leading ASCII spaces and tabs, so a leading newline must still block a trigger. I checked it with `test_trim_space_tab_policy_skips_only_spaces_and_tabs` and `test_trim_policy_does_not_skip_newlines_or_existing_apostrophes`.

## How AI output was checked
AI suggestions were treated as proposals, not as finished answers. Each one was checked against `inputs/export-policy.md`, the fixture rows and executed tests. Every number in the final documents comes from a command that was actually run; the commands are in `run-guide.md`.
