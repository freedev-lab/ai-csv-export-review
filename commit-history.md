# Repository and commit history

- **Repository:** https://github.com/freedev-lab/ai-csv-export-review
- **All commits (live list):** https://github.com/freedev-lab/ai-csv-export-review/commits/main

The history is kept exactly as it happened, with no rebase, amend or squash, so the order of work can be checked commit by commit. All times are UTC.

## Timeline at a glance
- **2026-11-11 09:54:** exercise zip downloaded. The zip only becomes available after clicking Start, so the 24-hour window began at or shortly before this time.
- **2026-11-11 14:09:** first commit, the code review, before any code change.
- **2026-11-11 18:56:** the fix, committed after six commits of failing tests.
- **2026-11-12 06:48:** last commit in the table below, inside the 24-hour window.

## Every commit, with the test result at that commit

"Tests" is the result of `python3 -B -m unittest discover -s tests -p '*_test.py'` run on that exact commit. Failures before a fix are intentional, because the tests were written first.

| # | Time (UTC) | Commit | What it did | Tests at this commit |
|---|---|---|---|---|
| 1 | 2026-11-11 14:09 | [`7d69429`][c01] | Code review written first: six findings and C1–C7 verdicts | no tests yet |
| 2 | 2026-11-11 15:53 | [`4e0672d`][c02] | Imports the starter exactly as supplied (identical to the exercise zip) and adds the first failing test: tenant isolation (P2) | 5 run, 1 failing |
| 3 | 2026-11-11 16:05 | [`4e4f07f`][c03] | Failing tests: CSV serialization (P5) | 7 run, 3 failing |
| 4 | 2026-11-11 17:28 | [`f03fc07`][c04] | Failing tests: cell encoding (P3) | 9 run, 5 failing |
| 5 | 2026-11-11 17:35 | [`12bad56`][c05] | Failing tests and one control: formula neutralization (P4) | 12 run, 7 failing |
| 6 | 2026-11-11 18:14 | [`2a994a5`][c06] | Failing tests: no input mutation, repeatable output (P4, P6) | 14 run, 9 failing |
| 7 | 2026-11-11 18:28 | [`a7c1ff6`][c07] | Reusable round-trip checker and fixture tests (P6) | 20 run, 15 failing |
| 8 | 2026-11-11 18:56 | [`bcd472e`][c08] | **The fix:** `app.py` +89/−12 lines, plus a work-log entry | 20 run, all pass |
| 9 | 2026-11-11 22:37 | [`5ad5a32`][c09] | P1 validation controls (they pass before and after the fix) | 27 run, all pass |
| 10 | 2026-11-11 22:47 | [`2f50ea9`][c10] | Claim reasons, merge verdict, run guide | 27 run, all pass |
| 11 | 2026-11-12 06:42 | [`91f84af`][c11] | Failing test: deeply nested JSON must exit 2 (P1) | 28 run, 1 failing |
| 12 | 2026-11-12 06:43 | [`d7b1658`][c12] | **Second fix:** `RecursionError` handled, whitespace cleaned (`app.py` +4/−6 lines) | 28 run, all pass |
| 13 | 2026-11-12 06:43 | [`0faa734`][c13] | Literal README self-check, exact second-fixture reconciliation, checker tamper test, generated-cell test | 32 run, all pass |
| 14 | 2026-11-12 06:44 | [`5ccc129`][c14] | Review evidence, run guide, work log, walkthrough and AI-use note, all with executed results | 32 run, all pass |
| 15 | 2026-11-12 06:48 | [`b5a2200`][c15] | AI-use note: details of the Claude Code review | 32 run, all pass |

This file was added in the commit after `b5a2200`. The live list linked above always shows every commit.

## What the history shows
- **Review first.** The first commit is the review, before any test or code change.
- **Reproduce before repair.** Six commits add failing tests before the fix. The failure count grows from 1 to 15, and all 20 tests pass at the fix (`bcd472e`). The late nested-JSON change follows the same pattern: a failing test (`91f84af`), then the fix (`d7b1658`).
- **Small, reviewable fixes.** All code changes are in `app.py`: +89/−12 lines in `bcd472e` and +4/−6 lines in `d7b1658`.
- **Supplied files untouched.** `inputs/`, `README.md`, `.gitignore` and `tests/app_test.py` have not changed since `4e0672d`, which contains the starter exactly as supplied.

## Phases by commit time
- **2026-11-11, 14:09–18:56:** review, failing tests, checker, fix.
- **2026-11-11, 22:37–22:47:** P1 validation controls, claim table, run guide.
- **2026-11-12, 06:42–06:48:** final review pass with Claude Code (see `ai-use-note.md`): the nested-JSON test and fix, stronger checker tests, documentation filled with executed results.

## Check it yourself

```sh
git log --reverse --format='%h %ad %s' --date=iso                      # commits and times
git diff 4e0672d HEAD -- app.py                                          # the complete fix
git diff 4e0672d HEAD -- inputs README.md .gitignore tests/app_test.py   # prints nothing
```

To re-run the tests at any commit (for example `a7c1ff6`) without changing your checkout:

```sh
tmp=$(mktemp -d) && git archive a7c1ff6 | tar -x -C "$tmp"
(cd "$tmp" && python3 -B -m unittest discover -s tests -p '*_test.py')
```

[c01]: https://github.com/freedev-lab/ai-csv-export-review/commit/7d6942990f977f1d31dd329c435057201065008c
[c02]: https://github.com/freedev-lab/ai-csv-export-review/commit/4e0672dc145cb8a9d0861d4c360d164ee5a1fb95
[c03]: https://github.com/freedev-lab/ai-csv-export-review/commit/4e4f07f742b9a300e16da29673aa4e81361f005e
[c04]: https://github.com/freedev-lab/ai-csv-export-review/commit/f03fc072e4b4a50c74f52a816acb06614ecc5812
[c05]: https://github.com/freedev-lab/ai-csv-export-review/commit/12bad566838257f66d08fc9b4f168870a135471a
[c06]: https://github.com/freedev-lab/ai-csv-export-review/commit/2a994a58eb0e20b89b496f678fbed60da95bb007
[c07]: https://github.com/freedev-lab/ai-csv-export-review/commit/a7c1ff69999b3ab741185d1a2ec74d3cf7573385
[c08]: https://github.com/freedev-lab/ai-csv-export-review/commit/bcd472e46ef9ba2404871d5fa78387ec3a4947bd
[c09]: https://github.com/freedev-lab/ai-csv-export-review/commit/5ad5a324023e5c8e40685533f6faeac0356453be
[c10]: https://github.com/freedev-lab/ai-csv-export-review/commit/2f50ea9c94b99f22675b6bd8aa3d73e261326007
[c11]: https://github.com/freedev-lab/ai-csv-export-review/commit/91f84af4a5721573772eeca02b6879f6be1aaa0b
[c12]: https://github.com/freedev-lab/ai-csv-export-review/commit/d7b16586a7fb5cb156238355ca9e9341951fe3fd
[c13]: https://github.com/freedev-lab/ai-csv-export-review/commit/0faa734a073b1e7f29720f6966a9859f2bfcce16
[c14]: https://github.com/freedev-lab/ai-csv-export-review/commit/5ccc129fe62c872359bb620e11aa2228d1d2a519
[c15]: https://github.com/freedev-lab/ai-csv-export-review/commit/b5a220029a4ae43474ada15ee9025339e47c7074
