# AI-drafted PR #315: tenant CSV export

The patch is already applied. Claims to review:

- C1: CSV serialization preserves commas, quotes and multiline notes.
- C2: All four formula triggers are neutralized under either consumer policy.
- C3: Null, empty and literal backslash-N remain distinguishable.
- C4: Tenant selection excludes related-name tenants, including diagnostics.
- C5: Export is nonmutating and repeatable; apostrophe-prefixed text is preserved.
- C6: Four CLI smoke checks pass.
- C7: These checks establish safety in every spreadsheet application.

Teammate symptoms: a parser sees unexpected records, one tenant reports an unfamiliar row, and repeat calls differ. No spreadsheet application was tested.
