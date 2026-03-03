# Counter-Training Convention Audit Criteria

Conventions that conflict with LLM training priors. During the workon audit step, check only lines introduced or modified by the current branch. Classify each convention as **mechanical** (auto-fix) or **judgment** (flag for user review at commit time).

## 1. Inline aggressively *(judgment)*

Single-use variables and functions should be inlined unless the name genuinely clarifies something non-obvious or inlining would create unreasonably long lines.

**Detection:** A variable assigned once and used once, or a function called from exactly one place.

```python
# before
result = get_tickets()
return result

# after
return get_tickets()
```

```python
# before
def build_filter(status):
    return {"status": status}

tickets = query(build_filter("ready"))

# after
tickets = query({"status": "ready"})
```

## 2. No decorative comments *(mechanical)*

No section dividers (`# ---`, `# ===`), no decorative formatting, no gratuitous docstrings. Comments should be rare, short, and factual. Plain `#` only.

**Detection:** Lines matching `# ---`, `# ===`, `# ***`, or similar repeating-character patterns. Docstrings on internal functions. Comments that restate what the code already says.

```python
# before
# ---- Helper Functions ----
def load_config():
    """Load the configuration file."""
    return read_yaml("config.yml")

# after
def load_config():
    return read_yaml("config.yml")
```

## 3. Full-word variable names *(mechanical)*

Always use full words: `result` not `res`, `command` not `cmd`, `environment` not `env` (as a variable — `env` as a keyword argument is fine). Exception: `i`, `k`, `v`, `e` in tight scopes.

**Detection:** Common abbreviations: `res`, `cmd`, `env`, `config` → `configuration` (only when used as a variable name, not a keyword argument), `msg`, `buf`, `ctx`, `req`, `resp`, `err`, `val`, `attr`, `elem`, `param`, `arg`, `dir` → `directory`, `temp` → `temporary`.

```python
# before
cmd = build_shell_command(env=settings)
res = run(cmd)

# after
command = build_shell_command(env=settings)
result = run(command)
```

## 4. No unnecessary abstractions *(judgment)*

Don't extract helper functions for one-time operations. Three similar lines of code are better than a premature abstraction. Don't design for hypothetical future requirements.

**Detection:** A function defined and called exactly once. A class with a single method. A utility module with one function. An abstraction layer that just delegates to another function.

```python
# before
def format_ticket_line(ticket):
    return f"- {ticket.id}: {ticket.title}"

output = "\n".join(format_ticket_line(t) for t in tickets)

# after
output = "\n".join(f"- {t.id}: {t.title}" for t in tickets)
```

## 5. Relative imports *(mechanical)*

Use `from .module import ...` for intra-package imports, not `from package.module import ...`.

**Detection:** An import statement using the full package name where a relative import would work (the imported module is in the same package).

```python
# before (inside scripts/src/scripts/build.py)
from scripts.utils import run_command

# after
from .utils import run_command
```

## 6. Use run_command / check_command *(mechanical)*

Use functions from `common.run_command` instead of raw `subprocess.run`. Use `check_command` (returns bool, no output) for idempotent operations where failure is expected — never `try: run_command(...); except CalledProcessError: pass`.

**Detection:** Bare `subprocess.run` calls. Try/except blocks wrapping `run_command` that catch `CalledProcessError` and pass.

```python
# before
try:
    run_command("firewall-cmd --add-zone=incus")
except CalledProcessError:
    pass

# after
check_command("firewall-cmd --add-zone=incus")
```
