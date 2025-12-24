# Contributing to xStage

Thank you for your interest in contributing to xStage!

## Code of Conduct

Be excellent to each other.

## How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Run tests: `pytest tests/`
6. Format code: `black src/`
7. Commit changes (`git commit -m 'Add amazing feature'`)
8. Push to branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## Development Setup
```bash
git clone https://github.com/xstage-pipeline/xstage
cd xstage
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

## Coding Standards

- Black for formatting (100 char line length)
- Pylint for linting
- Type hints encouraged
- Docstrings in Google style

## Questions?

Open an issue or join our Discord!