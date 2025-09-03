# Development Notes

## Package Management
This project uses [UV](https://docs.astral.sh/uv/) for Python package management.

### Common Commands:
- `uv sync` - Install dependencies from pyproject.toml
- `uv sync --dev` - Install with development dependencies  
- `uv run <command>` - Run commands in the project environment
- `uv add <package>` - Add a new dependency
- `uv add --dev <package>` - Add a development dependency
- `uv remove <package>` - Remove a dependency

### Running the Application:
- Development: `uv run uvicorn src.main:app --reload`
- Production: `uv run uvicorn src.main:app --host 0.0.0.0 --port 8000`

### Running Tests:
- `uv run pytest tests/`

### Database Initialization:
- `uv run python3 -c "from src.services.session_service import SessionService; import asyncio; asyncio.run(SessionService().create_tables())"`