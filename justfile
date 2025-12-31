# justfile for django-hatchway
# Run `just` to see available commands

# List available commands
default:
    @just --list

# ============================================================================
# Testing
# ============================================================================

# Run all tests
test:
    uv run pytest

# Run tests with verbose output
test-verbose:
    uv run pytest -v

# Run tests with coverage
test-coverage:
    uv run pytest --cov=hatchway --cov-report=term-missing

# Run a specific test file
test-file FILE:
    uv run pytest {{FILE}}

# Run a specific test function
test-func FUNC:
    uv run pytest -k {{FUNC}}

# ============================================================================
# Code Quality
# ============================================================================

# Run all pre-commit hooks
lint:
    pre-commit run --all-files

# Format code with black
format:
    uv run black hatchway tests

# Sort imports with isort
sort-imports:
    uv run isort hatchway tests

# Run type checking with mypy
typecheck:
    uv run mypy hatchway

# Run flake8 linting
flake:
    uv run flake8 hatchway tests

# Run all code quality checks
check: format sort-imports lint typecheck

# ============================================================================
# Demo Project
# ============================================================================

# Run the demo server
demo-serve PORT="8000":
    cd demo && uv run python manage.py runserver {{PORT}}

# Create and apply demo migrations
demo-migrate:
    cd demo && uv run python manage.py makemigrations
    cd demo && uv run python manage.py migrate

# Create a superuser for demo
demo-superuser:
    cd demo && uv run python manage.py createsuperuser

# Reset demo database
demo-reset:
    rm -f demo/db.sqlite3
    rm -rf demo/media
    cd demo && uv run python manage.py migrate
    @echo "Database reset complete. Run 'just demo-superuser' to create an admin user."

# Load demo data
demo-data:
    cd demo && uv run python manage.py shell -c "from django.contrib.auth.models import User; from api.models import Post, Comment; user = User.objects.create_user('demo', 'demo@example.com', 'demo'); post = Post.objects.create(title='Hello Hatchway', content='This is a demo post', author=user, published=True, tags=['demo', 'django']); Comment.objects.create(post=post, author_name='Demo User', content='Great framework!', rating=5)"
    @echo "Demo data loaded. Login with username: demo, password: demo"

# Setup complete demo environment
demo-setup: demo-reset demo-superuser demo-data

# Open Django shell for demo project
demo-shell:
    cd demo && uv run python manage.py shell

# Open API documentation in browser
demo-docs:
    @echo "Opening API documentation at http://localhost:8000/api/docs/"
    @echo "Make sure the server is running with: just demo-serve"
    xdg-open http://localhost:8000/api/docs/ 2>/dev/null || open http://localhost:8000/api/docs/ 2>/dev/null || echo "Please open http://localhost:8000/api/docs/ in your browser"

# ============================================================================
# Package Management
# ============================================================================

# Install dependencies
install:
    uv sync

# Install pre-commit hooks
install-hooks:
    pre-commit install

# Update dependencies
update:
    uv lock --upgrade

# ============================================================================
# Building and Publishing
# ============================================================================

# Build the package
build:
    uv build

# Clean build artifacts
clean:
    rm -rf dist/
    rm -rf build/
    rm -rf *.egg-info
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete

# Build and check package
build-check: clean build
    twine check dist/*

# Publish to PyPI (requires credentials)
publish: build-check
    twine upload dist/*

# Publish to TestPyPI
publish-test: build-check
    twine upload --repository testpypi dist/*

# ============================================================================
# Development Utilities
# ============================================================================

# Show project structure
tree:
    tree -I '.venv|__pycache__|*.pyc|.git|node_modules|*.egg-info|.pytest_cache' -L 3

# Count lines of code
loc:
    find hatchway tests -name "*.py" | xargs wc -l

# Check for security issues with bandit
security:
    uv run bandit -r hatchway

# ============================================================================
# Git Helpers
# ============================================================================

# Show current git status
status:
    git status

# Create a new release (updates version and creates tag)
release VERSION:
    @echo "Creating release {{VERSION}}"
    # Update version in pyproject.toml and __init__.py
    sed -i 's/version = "[^"]*"/version = "{{VERSION}}"/' pyproject.toml
    sed -i 's/__version__ = "[^"]*"/__version__ = "{{VERSION}}"/' hatchway/__init__.py
    git add pyproject.toml hatchway/__init__.py
    git commit -m "Releasing {{VERSION}}"
    git tag -a "v{{VERSION}}" -m "Release {{VERSION}}"
    @echo "Release {{VERSION}} created. Push with: git push && git push --tags"
