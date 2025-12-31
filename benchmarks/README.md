# Hatchway Performance Benchmarks

This directory contains performance benchmarks for the django-hatchway framework.

## Overview

The benchmarks are organized into two main categories:

### 1. API Performance (`test_api_performance.py`)

Tests the performance of actual API endpoints with realistic workloads:

- **List endpoints**: Testing pagination, filtering, and sorting with varying dataset sizes (10, 50, 200 items)
- **Detail endpoints**: Single record retrieval with different relationship depths
- **Create operations**: Simple and complex object creation, including bulk operations
- **Update operations**: Partial updates (PATCH)
- **Search operations**: Full-text search across different dataset sizes
- **Nested resources**: Comments under posts, testing relationship loading

### 2. Framework Internals (`test_framework_internals.py`)

Measures the performance of core framework components:

- **Parameter extraction**: Query params, body params, mixed sources
- **Schema serialization**: Simple objects, complex objects with relationships, lists
- **Type introspection**: Annotation parsing, signifier extraction
- **Request processing**: Measuring framework overhead
- **Validation**: Success and failure paths
- **Response formatting**: Different response types (dict, list, schema)

## Running Benchmarks

### Quick Start

```bash
# Install benchmark dependencies
uv sync --group bench

# Run all benchmarks
just bench

# Run only API benchmarks
just bench-api

# Run only framework internals benchmarks
just bench-internals
```

### Baseline Comparison

Track performance over time by saving baselines:

```bash
# Save current performance as baseline
just bench-save baseline

# Make changes to code...

# Compare against baseline
just bench-compare-to baseline
```

### Detailed Reports

```bash
# Verbose output with statistics
just bench-verbose

# Generate HTML report with histograms
just bench-html

# Quick benchmarks (fewer iterations, faster)
just bench-quick
```

## Understanding Results

Benchmark output shows several key metrics:

- **Min/Max**: Fastest and slowest execution times
- **Mean**: Average execution time
- **StdDev**: Standard deviation (lower is better - more consistent)
- **Median**: Middle value (less affected by outliers)
- **IQR**: Interquartile range (measure of statistical dispersion)
- **Outliers**: Number of outlier measurements
- **Rounds**: Number of benchmark iterations

### Example Output

```
------------------------------------------------------------------------------------------- benchmark: 8 tests -------------------------------------------------------------------------------------------
Name (time in ms)                          Min                 Max                Mean            StdDev              Median               IQR            Outliers     OPS            Rounds  Iterations
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_post_list_empty                     1.2841 (1.0)        2.1234 (1.0)        1.4523 (1.0)      0.1234 (1.0)        1.4234 (1.0)      0.0892 (1.0)          4;5  688.5234 (1.0)         100           1
test_post_detail                         2.5678 (2.0)        4.3421 (2.04)       2.8934 (1.99)     0.2456 (1.99)       2.8123 (1.98)     0.1567 (1.76)         3;4  345.6234 (0.50)         50           1
...
```

## Performance Targets

Current performance targets (these should be adjusted based on actual measurements):

### API Endpoints
- **List (50 items)**: < 10ms
- **Detail**: < 5ms
- **Create**: < 8ms
- **Update**: < 7ms
- **Search**: < 15ms

### Framework Overhead
- **Minimal view**: < 1ms
- **Simple validation**: < 2ms
- **Schema serialization**: < 5ms per object

## Factories

The `factories.py` module provides factory definitions using `factory-boy` and `faker`:

- `UserFactory`: Creates test users
- `PostFactory`: Creates blog posts with realistic data
- `CommentFactory`: Creates comments
- `create_posts(count, with_comments)`: Batch creation helper
- `create_large_dataset()`: Creates a large realistic dataset for stress testing

### Using Factories in Tests

```python
from benchmarks.factories import PostFactory, create_posts

# Create single post
post = PostFactory()

# Create batch with comments
posts = create_posts(count=100, with_comments=True)

# Create with custom data
post = PostFactory(title="Custom Title", published=True)
```

## Writing New Benchmarks

### Basic Benchmark Structure

```python
import pytest

class TestMyFeature:
    @pytest.mark.django_db
    def test_my_benchmark(self, benchmark):
        """Description of what this benchmarks."""
        # Setup
        data = create_test_data()

        # Benchmark
        result = benchmark(function_to_test, *args)

        # Assertion
        assert result.status_code == 200
```

### Best Practices

1. **Use descriptive names**: `test_post_list_with_100_items` is better than `test_list`
2. **Isolate what you're testing**: Set up data before calling `benchmark()`
3. **Use realistic data**: Use factories to create data that matches production
4. **Test edge cases**: Empty datasets, large datasets, deep nesting
5. **Group related tests**: Use classes to organize benchmarks by feature
6. **Add docstrings**: Explain what each benchmark measures

### Fixtures

Common fixtures available:

- `request_factory`: Django RequestFactory for creating mock requests
- `sample_user`: A test user
- `sample_posts`: 50 posts with comments (pre-created)

## Continuous Integration

To track performance over time:

1. Run benchmarks on main branch and save baseline:
   ```bash
   git checkout main
   just bench-save main
   ```

2. Switch to your feature branch:
   ```bash
   git checkout feature-branch
   just bench-compare-to main
   ```

3. Review differences and investigate any significant regressions

## Tips for Performance Optimization

1. **Identify bottlenecks**: Use `--benchmark-verbose` to see detailed stats
2. **Profile code**: Use `cProfile` or `py-spy` for deep profiling
3. **Test incrementally**: Make small changes and benchmark frequently
4. **Consider N+1 queries**: Check database query counts with `django-debug-toolbar`
5. **Cache wisely**: Measure before and after adding caching
6. **Batch operations**: Test bulk vs individual operations

## Benchmark Results Storage

Results are stored in `.benchmarks/` directory:

```
.benchmarks/
├── Linux-CPython-3.14-64bit/
│   ├── 0001_baseline.json
│   ├── 0002_v0.5.2.json
│   ├── 0003_optimization.json
│   └── benchmark.html
```

### Managing Saved Benchmarks

```bash
# List all saved benchmarks
just bench-list

# Show storage location and size
just bench-where

# Delete specific benchmark
just bench-delete old-benchmark

# Keep only certain benchmarks
just bench-clean-except baseline,v0.5.2

# Delete all
just bench-clean
```

### Exporting Results

Export benchmarks for analysis or reporting:

```bash
# Export to CSV (for Excel/Google Sheets)
just bench-export-format baseline csv
# Creates: benchmark_results.csv

# Export to JSON (for scripts/analysis)
just bench-export-format baseline json
# Creates: benchmark_results.json

# Export to Markdown (for documentation)
just bench-export-format baseline markdown
# Creates: benchmark_results.md
```

You can also use the Python script directly:
```bash
python3 benchmarks/export_benchmarks.py baseline --format csv --output my_results.csv
```

### Version Control

The `.benchmarks/` directory is gitignored by default. Options for tracking:

1. **Don't commit** (default) - Clean slate for each developer
2. **Commit key baselines** - Track major version performance
   ```bash
   git add -f .benchmarks/Linux-*/0001_v0.5.2.json
   git commit -m "Add v0.5.2 performance baseline"
   ```
3. **Export and commit** - Commit CSV/Markdown exports instead of JSON
   ```bash
   just bench-export-format v0.5.2 markdown
   git add benchmark_results.md
   ```

## Interpreting Performance Changes

### Acceptable Changes
- **±5%**: Normal variation, within noise
- **±10%**: Noticeable but may be acceptable depending on trade-offs

### Investigate
- **+15% or more**: Potential regression, investigate before merging
- **-15% or more**: Significant improvement, document what changed

### Red Flags
- **+50% or more**: Serious regression
- **High StdDev increase**: Inconsistent performance, may indicate issues

## Related Commands

```bash
# Install dependencies
just install

# Run regular tests
just test

# Run tests with coverage
just test-coverage

# Clean benchmark results
just bench-clean
```
