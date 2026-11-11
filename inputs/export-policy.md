# FernExport export policy (authoritative)

P1. Envelope: nonempty string tenant, policy `direct` or `trim-space-tab`, rows array. Each row requires unique nonempty string row_id, nonempty string tenant, present title/note each string or null. Validate all rows before selection. Fatal errors: exit 2, readable stderr without cell values, no stdout. Empty arrays valid; extra keys ignored.

P2. Select case-sensitive exact tenant equality. Preserve input order. Columns/header: row_id,title,note. Foreign content/IDs never enter CSV, audit or errors; summary may count exclusions. Error messages may identify one-based row position only.

P3. Encode null as two characters `\N`; double every backslash in strings. Thus null, literal backslash-N and empty string differ. Preserve other characters, including newlines and apostrophes.

P4. Check each original non-null exported string. direct checks character zero; trim-space-tab skips only leading ASCII space/tab. If the checked character is `=`, `+`, `-` or `@`, prefix exactly one ASCII apostrophe to the encoded full string, preserving whitespace. Apostrophe-prefixed input does not trigger. Never reprocess encoded cells or mutate input.

P5. Use stdlib csv.writer: comma delimiter, double quote quotechar, doublequote true, QUOTE_MINIMAL, CRLF record endings, no BOM. JSON stdout keys: csv, neutralized_cells (row_id/column objects, row then column order), summary. Summary keys: input_rows,exported_rows,foreign_rows,neutralized_cells,redacted_cells. Redacted_cells is zero; no content redaction occurs.

P6. Round-trip means csv.reader yields the policy-transformed cells, including exact header/order/count, not original raw strings. For reverse interpretation, remove added apostrophes using the audit, recognize exact `\N` as null, otherwise decode paired backslashes. Identical calls produce identical output. This synthetic policy proves no universal spreadsheet safety guarantee.
