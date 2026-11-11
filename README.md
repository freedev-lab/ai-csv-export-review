# Review and repair an AI CSV exporter

This is one Software Engineer Intern assessment with a **24-hour** window. Your recruiter assigns one exercise from the bank. Your 24 hours start when you click **Start** on the link in your invitation email; the exercise zip becomes available at that moment. Send your submission back within 24 hours of clicking Start. You are not expected to work for the full 24 hours: organize your own working time and breaks within the window. There are no surprise messages or overnight availability requirements, and hours worked are not scored. Follow-through and verification matter more than hours or volume.

The fictional FernExport team has an AI-drafted CSV export pull request already applied. A teammate reports unexpected parsed records, an unfamiliar tenant row, and different results on repeat calls. Review the claims before repairing the exporter. The useful outcome is a small, reviewable fix and a reusable check that another teammate can trust on a changed consumer policy.

All companies, tenants, assets and product behavior here are **fictional assessment facts**. The supplied fixtures are the authoritative universe. Outside research is optional and cannot affect marks. Do not contact real systems, send real messages, publish, or use production credentials.

## Supplied inputs and setup

You need basic Python, JSON, CLI use, tests, diffs, tenant isolation and CSV parsing. Python **3.10 or later**, its standard library, and any local editor are sufficient; no packages, accounts, paid tools, web access or company framework are needed.

- [Starter module](app.py): deliberate defects in an already applied AI patch; review beyond the diff.
- [Patch](inputs/change.diff) and [PR description](inputs/pr-description.md): code changes, C1–C7 claims and reported symptoms.
- [Export policy](inputs/export-policy.md): authoritative P1–P6, including exact serialization and both consumer modes.
- [Primary fixture](inputs/primary.json): ten rows with text, nulls and different tenants.
- [Second fixture](inputs/secondary.json): the same schema and row identities, a revised note and a stricter consumer mode.
- [Malformed input](inputs/malformed-input.txt): truncated JSON for fatal-error handling.
- [Smoke checks](tests/app_test.py): four infrastructure checks, **not feature acceptance tests**.

From the exported `candidate/` directory:

```sh
python3 --version
python3 -B app.py --help
python3 -B -m unittest discover -s tests -p '*_test.py' -v
python3 -B app.py --input inputs/primary.json
python3 -B app.py --input inputs/secondary.json
```

The four smoke checks pass. Both fixture commands currently exit **0**, printing JSON with an unverified `csv` string, audit and summary. The fourth smoke check replaces the usual exit-3 placeholder assertion for this flawed starter. Help exits 0; missing files or malformed JSON exit 2 with readable stderr and no stdout. Keep those contracts and the smoke checks; document any test refinement.

## Core task and observable acceptance criteria

1. **Review first.** Write comments with an `app.py` line or diff location, severity on your own scale, evidence, consequence and proposed fix. Disposition every C1–C7 claim as confirmed, false or not verifiable, with a reason and a merge verdict.
2. **Reproduce before repair.** Add a failing test for each reported defect and legitimate controls. Retain failing-first output. Test parsed cell contents rather than visually judging the JSON string.
3. **Repair** `export_rows` to P1–P6 with a small reviewable change. Use stdlib `csv` for serialization. Preserve input order and exact tenant selection, distinct null/empty/literal-backslash representations, policy-specific neutralization and nonmutation. Validate all rows before selection; fatal diagnostics must not echo cells.
4. **Build a reusable round-trip checker** accepting a payload and result. Assert header, parsed cells, column/row counts, order, audit/counts and absence of foreign content. Include empty input, a constructed boundary and two calls on the same object. Round-trip is transport of the policy-transformed cells; it is not raw-string identity after neutralization.
5. **Apply that checker unchanged** to the second fixture. Reconcile changed and unchanged cells, record any code refinement and rerun primary. Describe the guarantee actually demonstrated and the limits of the PR's spreadsheet claim.

Self-check after repair: each fixture has 10 input rows, 8 exported rows in R01–R08 order, 2 excluded foreign rows and 0 redacted cells. Primary neutralizes 4 cells; secondary 6. Each parses as one header plus 8 data records, including the multiline note. The second fixture must change at least one parsed cell while preserving others. Do not edit the source fixtures, patch or claim description to make tests pass.

Add meaningful automated checks that test results and errors, not just that code runs. Include at least one boundary case you construct, and one failing case you fix or a validation that causes a refinement. A clear, tested core earns full marks. Optional stretch: add a small deterministic generated-cell test; not needed for full marks. A web service, full framework, database, public deployment, or large architecture is outside the core scope.

## Time and AI use

Plan your own time within the 24-hour window. Prioritize the core contract and leave time for verification instead of adding features.

**AI is allowed and encouraged** for coding, explanation, test generation, critique and optional research. Tool choice is not graded. No AI tool is provided; you may use any AI tool you already have, and no purchase is required. Free/offline tools and completing the exercise without AI are supported. Check AI output against the rules, input rows and executed tests. Submit a short AI-use note with one concrete accepted, corrected or rejected output and how you checked it; if you did not use AI, state that. Do not invent an AI failure or share complete prompt histories, private account access, or secrets.

## Submission

Submit an archive or repository containing runnable source, tests, the supplied inputs, and:

1. The written review, claim check and verdict.
2. A short run guide with exact commands for both fixtures and meaningful checks; include representative outputs or assertions with row IDs and policy IDs.
3. A concise decision/work log: priorities and what you deferred; one obstacle and response; one validation/refinement; known limits and next step.
4. The AI-use note described above.
5. A 3–5 minute walkthrough recording **or equivalent accessible text** explaining the most serious defect, one edge case, and evidence of execution.

You do not need a public repository, deployment, PDF or proprietary tools. Document incomplete behavior honestly. Do not submit only a report: the review with the runnable fix and reproducible tests are the primary deliverables.

Published scoring: **usable result 40, accuracy/verification 25, prioritization 20, communication/handoff 15**. Full marks are available on the core alone. Tool choice, AI-detector judgments, prose polish, hours worked and sheer output volume are not scored.
