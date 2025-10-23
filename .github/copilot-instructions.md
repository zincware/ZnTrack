# ZnTrack: Reproducible Python Workflows

ZnTrack is a Python library for creating reproducible data science workflows using DVC (Data Version Control). It provides a Node-based system where computational steps are represented as connected nodes in a directed graph.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap and Setup
- Install uv package manager: `pip install uv`
- Configure git user (required for DVC operations):
  ```bash
  git config --global user.name "John Doe"
  git config --global user.email johndoe@example.com
  git config --global init.defaultBranch "main"
  ```
- Install all dependencies: `uv sync --dev` -- takes 2-5 minutes to complete. NEVER CANCEL. Set timeout to 10+ minutes.
- Verify installation: `uv run zntrack --version`

### Build and Test
- Run unit tests: `uv run pytest tests/unit_tests/` -- takes ~45 seconds. NEVER CANCEL. Set timeout to 90+ seconds.
- Run integration tests: `uv run pytest tests/integration/` -- takes 3-5 minutes total. NEVER CANCEL. Set timeout to 10+ minutes.
- Run specific test file: `uv run pytest tests/unit_tests/test_node_name.py -v` -- takes ~8 seconds.
- Run all tests: `uv run pytest --cov` -- takes 10-15 minutes. NEVER CANCEL. Set timeout to 30+ minutes.
- Run linting: `uv run ruff check zntrack/` -- takes <1 second.
- Run formatting: `uv run ruff format zntrack/` -- takes <1 second.
- Check formatting: `uv run ruff format --check zntrack/` -- takes <1 second.

### Run the Application
- ZnTrack is primarily a library, not a standalone application
- CLI is available: `uv run zntrack --help`
- CLI commands:
  - `uv run zntrack run <node_class>` -- Execute a ZnTrack Node
  - `uv run zntrack list <project_path>` -- List all Nodes in the Project
  - `uv run zntrack --version` -- Show version information

## Validation

### Core Functionality Testing
Always test ZnTrack functionality with this minimal workflow after making changes:

```bash
# Create test directory
mkdir -p /tmp/zntrack_test && cd /tmp/zntrack_test

# Initialize git (required for DVC)
git init
git config user.name "Test User"
git config user.email "test@example.com"

# Test basic workflow
uv run python -c "
import zntrack
from zntrack.examples import ParamsToOuts

# Create project and nodes
with zntrack.Project() as project:
    node1 = ParamsToOuts(params='Hello')
    node2 = ParamsToOuts(params='World')

# Build the project
project.build()
print('✓ ZnTrack workflow completed successfully')
"
```

### CLI Testing
- Always test CLI functionality: `uv run zntrack --version`
- Test help command: `uv run zntrack --help`
- Verify all CLI subcommands are accessible

### Pre-commit Validation
Always run these commands before committing changes:
- `uv run ruff check zntrack/` -- must pass without errors
- `uv run ruff format zntrack/` -- run and commit any changes
- `uv run pytest tests/unit_tests/` -- must pass with timeout 90+ seconds

## Common Tasks

### Repository Structure
```
.
├── README.md                    # Project documentation
├── pyproject.toml              # Project configuration and dependencies
├── uv.lock                     # Lockfile for reproducible builds
├── zntrack/                    # Main package directory
│   ├── __init__.py
│   ├── node.py                 # Core Node class
│   ├── project.py              # Project management
│   ├── cli/                    # Command-line interface
│   └── examples/               # Example nodes for testing
├── tests/                      # Test suite
│   ├── unit_tests/            # Fast unit tests (~45 seconds)
│   ├── integration/           # Integration tests (3-5 minutes)
│   ├── files/                 # File-based tests
│   └── benchmark/             # Performance tests
├── docs/                      # Documentation source
└── .github/                   # GitHub Actions workflows
```

### Key Components
- **Node**: Base class for all computational steps (`zntrack.Node`)
- **Project**: Container for managing workflows (`zntrack.Project()`)
- **Fields**: Parameter/output definitions (`zntrack.params()`, `zntrack.outs()`, `zntrack.deps()`)
- **CLI**: Command-line interface in `zntrack.cli`
- **Examples**: Built-in example nodes in `zntrack.examples`

### Common Import Patterns
```python
import zntrack
from zntrack.examples import ParamsToOuts

# Create a node
node = ParamsToOuts(params="value")

# Create a project
with zntrack.Project() as project:
    node = ParamsToOuts(params="value")

# Build workflow
project.build()
```

### Timing Expectations
- **Dependency Installation**: 2-5 minutes
- **Unit Tests**: ~45 seconds for full suite
- **Integration Tests**: 3-5 minutes total
- **Single Test File**: 5-15 seconds typically
- **Linting**: <1 second
- **Simple Workflow Build**: <1 second
- **CLI Commands**: <3 seconds

### Known Issues and Workarounds
- MLflow dependency shows deprecation warnings - these can be ignored
- Some tests are marked as `xfail` for pending features
- DVC operations require git repository initialization
- Always set git user configuration before testing workflows

### Development Workflow
1. **Always run bootstrap first**: `uv sync --dev`
2. **Make changes incrementally**
3. **Test frequently**: `uv run pytest tests/unit_tests/test_<relevant>.py -v`
4. **Lint before commit**: `uv run ruff check zntrack/ && uv run ruff format zntrack/`
5. **Run integration tests**: `uv run pytest tests/integration/ --tb=short`
6. **Validate end-to-end**: Run the validation workflow above

### Essential Dependencies
- **uv**: Modern Python package manager (replaces pip/poetry)
- **DVC**: Data Version Control (core dependency)
- **ruff**: Fast Python linter and formatter
- **pytest**: Testing framework
- **Git**: Required for DVC operations

All dependencies are managed via `uv` and defined in `pyproject.toml`. The `uv.lock` file ensures reproducible installations.