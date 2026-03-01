# Testing Conventions

## Framework

pytest, run via `uv run pytest` from the repo root.

## File placement

Tests live alongside the code they test:
- `docker/api/tests/` for API service tests
- `docker/localizer/tests/` for localizer tests
- `scripts/tests/` for scripts package tests

Mirror the source structure. If the module is `scripts/src/scripts/tickets.py`, the test is `scripts/tests/test_tickets.py`.

## Naming

- **Test functions**: `test_should_<expected>_when_<condition>` — describes the behavior, not the implementation.
  - `test_should_return_empty_list_when_no_tickets_have_frontmatter`
  - `test_should_raise_value_error_when_ticket_id_not_found`
  - `test_should_group_tickets_by_status_in_column_order`
- **Test classes**: `Test<Unit>` — groups related tests for a single function or class.
  - `TestParseFrontmatter`, `TestLoadTickets`, `TestUpdateTicketStatus`
- **Fixtures**: lowercase, descriptive nouns. `sample_ticket`, `ticket_directory`, `frontmatter_text`.

## Pattern

Arrange-Act-Assert (AAA). One logical assertion per test.

```python
def test_should_parse_status_when_valid_frontmatter():
    # Arrange
    text = "---\nid: T1\ntitle: Test\nstatus: ready\ndepends_on: []\n---\n# Body"

    # Act
    metadata, body = parse_frontmatter(text)

    # Assert
    assert metadata["status"] == "ready"
```

The comments (`# Arrange`, `# Act`, `# Assert`) are optional — use them when the phases aren't visually obvious. Omit them for trivial tests where the structure is self-evident.

## Mocking

Mock only at system boundaries:
- **External APIs** — HTTP calls to third-party services
- **Databases** — SQL queries, connection objects
- **Filesystem** — use `tmp_path` fixture instead of mocking; for read-only tests, use real fixture files
- **Time** — `freezegun` or `time_machine` when tests depend on wall clock
- **Randomness** — seed the RNG or mock `random`

Never mock internal collaborators. If `function_a` calls `function_b`, test them together — don't mock `function_b` inside `function_a`'s test. Use dependency injection to make boundaries explicit.

## Fixtures

Prefer factory functions over complex fixture chains:

```python
def make_ticket(id: str = "T1", status: str = "ready", **overrides: Any) -> Ticket:
    defaults = {"id": id, "title": "Test ticket", "status": status, "depends_on": [], "body": "", "file_path": Path("t1-test.md")}
    defaults.update(overrides)
    return Ticket(**defaults)
```

Use `@pytest.fixture` for shared setup that requires teardown (temp directories, database connections, server processes). Don't use fixtures just to avoid repeating a constructor call — a factory function is simpler.

## Parametrize

Use `@pytest.mark.parametrize` for data-driven tests:

```python
@pytest.mark.parametrize("status", ["blocked", "design-needed", "plan-needed", "ready", "done"])
def test_should_accept_valid_status(status: str):
    ticket = make_ticket(status=status)
    assert ticket.status == status
```

Don't copy-paste five test functions that differ only in input data.

## Coverage

No numeric coverage target. Tests encode acceptance criteria, not line coverage. A ticket's "Done when" criteria should map to test cases. Additional tests for edge cases and error handling are expected but not measured by a percentage.

## What not to test

- Auto-generated code (`packages/generated/`)
- Third-party library internals
- Pure configuration files
- Trivial property access with no logic
