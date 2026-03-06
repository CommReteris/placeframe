# Commit Message Style Guide

- **Subject line**: Concise but specific (under 72 chars). Prefix with `[prose]` or `[code]` to indicate whether the commit contains documentation (markdown, text, skill files, research) or code (Python, configs, .gitignore, pyproject.toml). Name the actual things that changed — don't hide details behind vague catch-alls like "update config" or "fix scripts".
- **Body**: Use a bulleted list (`-`) of short phrases. State *what* changed, not *why*. No full sentences, no parenthetical justifications.
- **Brevity**: Err heavily on the side of terse. "Fix label_type/link_type to NOT NULL" not "Fix label_type and link_type columns in nodes table to be NOT NULL (were incorrectly nullable)".
- **Accuracy**: Name the specific things that changed. Don't hide bug fixes under vague phrasing.
- **Structure**: Subject line summarizes the theme; body bullets cover specifics that wouldn't fit in the subject. Omit the body entirely for trivial changes where the subject says it all.
- **Separate prose and code**: Never mix documentation files (markdown, text, skill files, research notes) with code files (Python, configs, .gitignore, pyproject.toml) in the same commit. They require different review modes. If a change touches both, split into separate commits.
- **No trailers**: Do NOT add Co-Authored-By or other trailers.

## Examples

**Bad** → **Good**:

- `Update config files` → `[code] Fix label_type/link_type to NOT NULL`
  (Name what changed, don't hide behind "update")

- `[code] Refactor board scanning to support nested directories and improve overall code quality` → `[code] Make board ticket scanning recurse into subdirectories`
  (State the change, not the aspirations)

- `[prose] Add new skill files and update ticket statuses for multiple items` → `[prose] Trivial skill prose fixes: T28, T36, T37, T41, T42, T48`
  (Be specific — list the tickets or changes)
