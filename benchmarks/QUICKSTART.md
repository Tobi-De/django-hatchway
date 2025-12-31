# Benchmark Quick Start

## Installation

```bash
# Install benchmark dependencies
uv sync --group bench
```

## Running Benchmarks

### Basic Usage

```bash
# Run all benchmarks
just bench

# Quick benchmarks (fewer iterations, faster)
just bench-quick
```

### Focused Benchmarks

```bash
# Run only API endpoint benchmarks
just bench-api

# Run only framework internals benchmarks
just bench-internals
```

### Saving & Comparing Results

```bash
# Save current performance as baseline
just bench-save baseline

# Save with a descriptive name
just bench-save before-optimization
just bench-save v0.5.2
just bench-save main-branch

# List all saved benchmarks
just bench-list

# See where benchmarks are stored
just bench-where

# Make your changes to the code...

# Compare against baseline
just bench-compare-to baseline

# Compare two specific saved benchmarks
just bench-diff baseline before-optimization

# Delete a specific benchmark
just bench-delete old-benchmark
```

### Detailed Analysis

```bash
# Verbose output with full statistics
just bench-verbose

# Generate HTML report with graphs
just bench-html
# Then open .benchmarks/*/benchmark.html in your browser
```

## Understanding Output

```
Name (time in ms)          Min      Max     Mean   StdDev   Median      IQR   Outliers  OPS
test_post_list_small     1.234    2.456    1.567    0.123    1.534    0.089     4;5     637.8
```

- **Mean**: Average time (lower is better)
- **Median**: Middle value (less affected by outliers)
- **StdDev**: Consistency (lower is more consistent)
- **OPS**: Operations per second (higher is better)

## Workflow for Performance Changes

1. **Before making changes:**
   ```bash
   git checkout main
   just bench-save main
   ```

2. **Make your changes**

3. **Compare results:**
   ```bash
   just bench-compare-to main
   ```

4. **Interpret:**
   - **Green** (faster): Good! Document what improved
   - **Red** (slower): Investigate if the slowdown is acceptable
   - **±5%**: Normal variation
   - **>15%**: Significant change, needs attention

## Common Scenarios

### "I want to see if my optimization worked"

```bash
# Before optimization
just bench-save before

# After making changes
just bench-compare-to before
```

### "I want to track long-term trends"

```bash
# Periodically save benchmarks with version tags
just bench-save v0.5.2
just bench-save v0.6.0

# Compare versions
just bench-compare-to v0.5.2
```

### "I only care about one specific area"

```bash
# Run specific test file
uv run --group bench pytest benchmarks/test_api_performance.py::TestListEndpointPerformance --benchmark-only

# Run specific test
uv run --group bench pytest benchmarks/test_api_performance.py::TestListEndpointPerformance::test_post_list_large --benchmark-only
```

## Tips

1. **Close other applications** when running benchmarks for consistent results
2. **Run multiple times** - first run may be slower due to cold cache
3. **Use `bench-quick`** during development, full benchmarks for final comparison
4. **Commit baselines** to track project performance over time
5. **Check CPU load** - high system load affects results

## What Gets Benchmarked?

### API Benchmarks
- List endpoints with various dataset sizes (10, 50, 200 items)
- Detail endpoints with different relationship depths
- Create/update/delete operations
- Bulk operations
- Search functionality
- Nested resources

### Framework Internals
- Parameter extraction from different sources
- Validation (success and failure paths)
- Schema serialization (simple, complex, lists)
- Type introspection
- Response formatting

## Performance Targets

Current informal targets (adjust based on your needs):

- **List endpoint (50 items)**: < 10ms
- **Detail endpoint**: < 5ms
- **Create operation**: < 8ms
- **Framework overhead**: < 1ms

## Exporting Results

```bash
# Export benchmark to CSV (for Excel, etc.)
just bench-export-format baseline csv

# Export to JSON (for programmatic analysis)
just bench-export-format baseline json

# Export to Markdown (for documentation)
just bench-export-format baseline markdown
```

The exported files include:
- **CSV**: `benchmark_results.csv` - spreadsheet-friendly format
- **JSON**: `benchmark_results.json` - for scripts/tools
- **Markdown**: `benchmark_results.md` - for documentation/reports

## Managing Saved Benchmarks

```bash
# Keep only important benchmarks
just bench-clean-except baseline,v0.5.2,main

# Remove all saved benchmarks
just bench-clean
```

Benchmarks are stored in `.benchmarks/` directory (gitignored by default).

## Next Steps

- Read full guide: `benchmarks/README.md`
- View benchmark code: `benchmarks/test_*.py`
- Customize factories: `benchmarks/factories.py`
