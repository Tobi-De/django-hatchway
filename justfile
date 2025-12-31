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

# Watch tests (re-run on file changes)
test-watch:
    uv run pytest-watch

# ============================================================================
# Benchmarking
# ============================================================================

# Run all benchmarks
bench:
    DJANGO_SETTINGS_MODULE=demo.settings uv run --group bench pytest benchmarks/ --benchmark-only --benchmark-sort=mean --ds=demo.settings

# Run benchmarks with comparison to previous results
bench-compare:
    DJANGO_SETTINGS_MODULE=demo.settings uv run --group bench pytest benchmarks/ --benchmark-only --benchmark-compare --benchmark-sort=mean --ds=demo.settings

# Run benchmarks and save baseline
bench-save NAME="baseline":
    DJANGO_SETTINGS_MODULE=demo.settings uv run --group bench pytest benchmarks/ --benchmark-only --benchmark-save={{NAME}} --benchmark-sort=mean --ds=demo.settings

# Compare benchmarks against a saved baseline
bench-compare-to NAME="baseline":
    DJANGO_SETTINGS_MODULE=demo.settings uv run --group bench pytest benchmarks/ --benchmark-only --benchmark-compare={{NAME}} --benchmark-sort=mean --ds=demo.settings

# Run API benchmarks only
bench-api:
    DJANGO_SETTINGS_MODULE=demo.settings uv run --group bench pytest benchmarks/test_api_performance.py --benchmark-only --benchmark-sort=mean --ds=demo.settings

# Run framework internals benchmarks only
bench-internals:
    DJANGO_SETTINGS_MODULE=demo.settings uv run --group bench pytest benchmarks/test_framework_internals.py --benchmark-only --benchmark-sort=mean --ds=demo.settings

# Run benchmarks with verbose output
bench-verbose:
    DJANGO_SETTINGS_MODULE=demo.settings uv run --group bench pytest benchmarks/ --benchmark-only --benchmark-verbose --benchmark-sort=mean --ds=demo.settings

# Run quick benchmarks (fewer iterations)
bench-quick:
    DJANGO_SETTINGS_MODULE=demo.settings uv run --group bench pytest benchmarks/ --benchmark-only --benchmark-min-rounds=3 --benchmark-sort=mean --ds=demo.settings

# Generate HTML benchmark report
bench-html:
    DJANGO_SETTINGS_MODULE=demo.settings uv run --group bench pytest benchmarks/ --benchmark-only --benchmark-autosave --benchmark-histogram --ds=demo.settings
    @echo "Open .benchmarks/*/benchmark.html in your browser"

# List all saved benchmarks
bench-list:
    @echo "Saved benchmarks in .benchmarks/:"
    @find .benchmarks -name "*.json" -type f 2>/dev/null | sort | sed 's/.*\//  - /' | sed 's/.json//' || echo "  (no saved benchmarks yet)"

# Show benchmark storage location
bench-where:
    @echo "Benchmarks are stored in: .benchmarks/"
    @du -sh .benchmarks 2>/dev/null | awk '{print "Current size:", $$1}' || echo "Current size: 0"
    @echo ""
    @just bench-list

# Delete a specific saved benchmark
bench-delete NAME:
    @echo "Deleting benchmark: {{NAME}}"
    find .benchmarks -name "*{{NAME}}.json" -delete
    @echo "Deleted. Remaining benchmarks:"
    @just bench-list

# Export benchmark results to CSV
bench-export NAME OUTPUT="benchmark_results.csv":
    @echo "Exporting benchmark '{{NAME}}' to {{OUTPUT}}"
    @python3 -c "import json, csv, sys; \
    data = json.load(open([f for f in __import__('pathlib').Path('.benchmarks').rglob('*{{NAME}}.json')][0])); \
    benchmarks = data['benchmarks']; \
    with open('{{OUTPUT}}', 'w', newline='') as f: \
        writer = csv.DictWriter(f, fieldnames=['name', 'min', 'max', 'mean', 'stddev', 'median', 'iqr', 'ops']); \
        writer.writeheader(); \
        [writer.writerow({'name': b['name'], 'min': b['stats']['min'], 'max': b['stats']['max'], \
                          'mean': b['stats']['mean'], 'stddev': b['stats']['stddev'], \
                          'median': b['stats']['median'], 'iqr': b['stats']['iqr'], \
                          'ops': b['stats']['ops']}) for b in benchmarks]" 2>/dev/null || echo "Error: Benchmark '{{NAME}}' not found"
    @echo "Exported to {{OUTPUT}}"

# Compare two saved benchmarks
bench-diff BASELINE CURRENT:
    @echo "Comparing {{BASELINE}} vs {{CURRENT}}:"
    DJANGO_SETTINGS_MODULE=demo.settings uv run --group bench pytest benchmarks/ --benchmark-only --benchmark-compare={{BASELINE}} --benchmark-compare-fail=mean:10% --ds=demo.settings 2>&1 | grep -A 100 "Comparing"

# Export benchmark to CSV/JSON/Markdown
bench-export-format NAME FORMAT="csv":
    python3 benchmarks/export_benchmarks.py {{NAME}} --format {{FORMAT}}

# Clean benchmark results
bench-clean:
    rm -rf .benchmarks/

# Clean all except specific saved benchmarks (comma-separated)
bench-clean-except KEEP:
    @echo "Keeping: {{KEEP}}"
    @for name in $$(echo "{{KEEP}}" | tr ',' ' '); do \
        find .benchmarks -name "*$$name.json" -type f | while read file; do \
            echo "Keeping: $$file"; \
        done; \
    done
    @find .benchmarks -name "*.json" -type f | while read file; do \
        keep=false; \
        for name in $$(echo "{{KEEP}}" | tr ',' ' '); do \
            if echo "$$file" | grep -q "$$name"; then \
                keep=true; \
                break; \
            fi; \
        done; \
        if [ "$$keep" = "false" ]; then \
            echo "Deleting: $$file"; \
            rm "$$file"; \
        fi; \
    done

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
