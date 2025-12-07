# Contributing to ABC Emergency for Home Assistant

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

Please be respectful and constructive in all interactions. We welcome contributors of all skill levels.

## Ways to Contribute

### Reporting Issues

We use GitHub issue templates to help you provide the right information. Choose the template that best fits your issue:

| Template | Use When |
|----------|----------|
| [Bug Report](https://github.com/troykelly/homeassistant-abcemergency/issues/new?template=1_bug_report.yml) | Something isn't working as expected |
| [Feature Request](https://github.com/troykelly/homeassistant-abcemergency/issues/new?template=2_feature_request.yml) | Suggesting new functionality |
| [Help/Question](https://github.com/troykelly/homeassistant-abcemergency/issues/new?template=4_help_question.yml) | Need assistance or clarification |

**Before submitting:**
1. Check [existing issues](https://github.com/troykelly/homeassistant-abcemergency/issues) for duplicates
2. Gather required information (versions, logs, etc.)

### Improving Documentation

- Fix typos or unclear instructions
- Add examples
- Improve troubleshooting guides

### Code Contributions

## Development Setup

### Prerequisites

- Python 3.12+
- Home Assistant development environment
- Git

### Clone and Install

```bash
git clone https://github.com/troykelly/homeassistant-abcemergency.git
cd homeassistant-abcemergency

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements_test.txt
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=custom_components.abcemergency --cov-report=term-missing

# Run specific test file
pytest tests/test_api.py -v

# Run specific test
pytest tests/test_api.py::test_fetch_incidents -v
```

### Type Checking

```bash
mypy custom_components/abcemergency/
```

### Linting

```bash
ruff check custom_components/abcemergency/
ruff format custom_components/abcemergency/
```

## Development Guidelines

### Test-Driven Development (TDD)

This project follows strict TDD:

1. **Write a failing test first**
2. **Write minimal code to pass the test**
3. **Refactor while keeping tests green**

No code without a test. No exceptions.

### Type Safety

- **Never use `Any` type** (except `**kwargs: Any` when required by HA overrides)
- Use `TypedDict` for API responses
- Use `dataclasses` for internal models
- Modern syntax: `str | None` not `Optional[str]`

### Code Style

- Use `from __future__ import annotations`
- Explicit return types on all functions
- Type all class attributes
- Use `_attr_*` pattern for entity attributes
- Never do I/O in properties

### Research Before Implementing

If your implementation fails twice:

1. Stop coding
2. Read official documentation
3. Examine working implementations in HA core
4. Understand before trying again

## Issue-Driven Development

**All work must be linked to a GitHub Issue.** This is enforced - PRs without linked issues will be rejected.

### Workflow

1. Check the [project board](https://github.com/users/troykelly/projects/6) for issues
2. Create an issue if one doesn't exist for your work
3. Create a branch: `issue-{N}-{short-description}`
4. Commit with issue reference: `type(scope): message (#N)`
5. Create PR with `Fixes #N` in the body

### Branch Naming

```
issue-42-fix-api-timeout
issue-123-add-flood-sensor
```

## Pull Request Process

1. **Find or create an issue** for your work
2. **Fork the repository**
3. **Create a feature branch**: `git checkout -b issue-{N}-description`
4. **Make your changes**
5. **Run the full test suite**: `pytest tests/ --cov`
6. **Run type checking**: `mypy custom_components/abcemergency/`
7. **Run linting**: `ruff check . && ruff format --check .`
8. **Commit with issue reference**: `fix(scope): message (#N)`
9. **Push to your fork**
10. **Open a Pull Request** with `Fixes #N` in the body

### PR Requirements

- [ ] All tests pass
- [ ] 100% test coverage maintained
- [ ] Type checking passes
- [ ] Linting passes
- [ ] Documentation updated if needed
- [ ] Commit messages are clear

### Commit Message Format

```
type(scope): short description (#issue)

Longer description if needed.
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`

**Scopes:** `api`, `sensor`, `binary-sensor`, `geo-location`, `config-flow`, `coordinator`

**Examples:**
```
fix(api): handle API timeout gracefully (#42)
feat(sensor): add bushfire count sensor (#123)
test(coordinator): add update interval tests (#7)
```

## Project Structure

```
custom_components/abcemergency/
├── __init__.py           # Integration setup
├── manifest.json         # Integration metadata
├── config_flow.py        # UI configuration
├── const.py              # Constants, TypedDicts
├── coordinator.py        # DataUpdateCoordinator
├── entity.py             # Base entity class
├── api.py                # ABC Emergency API client
├── models.py             # Dataclasses
├── sensor.py             # Incident count sensors
├── binary_sensor.py      # Alert state sensors
├── geo_location.py       # Map markers
├── helpers.py            # Geolocation calculations
├── exceptions.py         # Custom exceptions
└── diagnostics.py        # Diagnostic download

tests/
├── conftest.py           # Pytest fixtures
├── test_*.py             # Test files
```

## Getting Help

- Open a [discussion](https://github.com/troykelly/homeassistant-abcemergency/discussions)
- Ask in your PR if you're stuck
- Review existing code for patterns

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
