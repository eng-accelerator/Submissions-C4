# Contributing to Astraeus

Thank you for your interest in contributing to Astraeus.

## Getting Started

1. Fork this repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Make your changes
4. Run the test suite: `pytest tests/ -v`
5. Commit with conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
6. Push and open a Pull Request

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your OPENROUTER_API_KEY to .env
```

## Project Structure

See [ARCHITECTURE.md](ARCHITECTURE.md) for system design and [AGENTS.md](AGENTS.md) for agent specifications.

## Code Style

- Python 3.10+ with type hints
- Docstrings on public functions
- Tests in `tests/` using pytest

## Agent Skills

Each agent has a corresponding skill definition in `skills/<skill-name>/SKILL.md` following the [Agent Skills standard](https://agentskills.io). When modifying agent behavior, update the corresponding SKILL.md.

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_agents.py -v
pytest tests/test_cli.py -v
pytest tests/test_skills.py -v
```
