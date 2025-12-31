#!/usr/bin/env python3
"""
Export benchmark results to various formats.

Usage:
    python benchmarks/export_benchmarks.py <benchmark_name> [--format csv|json|markdown]
"""

import argparse
import csv
import json
import sys
from pathlib import Path


def find_benchmark_file(name):
    """Find the benchmark JSON file by name."""
    benchmark_dir = Path(".benchmarks")
    if not benchmark_dir.exists():
        print("Error: No .benchmarks directory found", file=sys.stderr)
        sys.exit(1)

    # Search for the benchmark file
    files = list(benchmark_dir.rglob(f"*{name}.json"))
    if not files:
        print(f"Error: Benchmark '{name}' not found", file=sys.stderr)
        available = list(benchmark_dir.rglob("*.json"))
        if available:
            print("\nAvailable benchmarks:", file=sys.stderr)
            for f in available:
                print(f"  - {f.stem}", file=sys.stderr)
        sys.exit(1)

    return files[0]


def export_to_csv(data, output_file):
    """Export benchmark data to CSV."""
    benchmarks = data["benchmarks"]

    with open(output_file, "w", newline="") as f:
        fieldnames = [
            "name",
            "min",
            "max",
            "mean",
            "stddev",
            "median",
            "iqr",
            "ops",
            "rounds",
            "iterations",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for b in benchmarks:
            writer.writerow(
                {
                    "name": b["name"],
                    "min": b["stats"]["min"],
                    "max": b["stats"]["max"],
                    "mean": b["stats"]["mean"],
                    "stddev": b["stats"]["stddev"],
                    "median": b["stats"]["median"],
                    "iqr": b["stats"]["iqr"],
                    "ops": b["stats"]["ops"],
                    "rounds": b["stats"]["rounds"],
                    "iterations": b["stats"]["iterations"],
                }
            )

    print(f"Exported to {output_file}")


def export_to_json(data, output_file):
    """Export benchmark data to JSON (simplified)."""
    benchmarks = data["benchmarks"]

    simplified = {
        "metadata": data.get("metadata", {}),
        "benchmarks": [
            {
                "name": b["name"],
                "stats": b["stats"],
                "params": b.get("params", {}),
            }
            for b in benchmarks
        ],
    }

    with open(output_file, "w") as f:
        json.dump(simplified, f, indent=2)

    print(f"Exported to {output_file}")


def export_to_markdown(data, output_file):
    """Export benchmark data to Markdown table."""
    benchmarks = data["benchmarks"]
    metadata = data.get("metadata", {})

    with open(output_file, "w") as f:
        # Header
        f.write("# Benchmark Results\n\n")

        # Metadata
        if metadata:
            f.write("## Metadata\n\n")
            for key, value in metadata.items():
                f.write(f"- **{key}**: {value}\n")
            f.write("\n")

        # Results table
        f.write("## Results\n\n")
        f.write("| Name | Min (µs) | Max (µs) | Mean (µs) | Median (µs) | StdDev | OPS |\n")
        f.write("|------|----------|----------|-----------|-------------|--------|-----|\n")

        for b in benchmarks:
            stats = b["stats"]
            # Convert to microseconds for readability
            min_us = stats["min"] * 1_000_000
            max_us = stats["max"] * 1_000_000
            mean_us = stats["mean"] * 1_000_000
            median_us = stats["median"] * 1_000_000
            stddev_us = stats["stddev"] * 1_000_000

            f.write(
                f"| {b['name']} | {min_us:.2f} | {max_us:.2f} | {mean_us:.2f} | "
                f"{median_us:.2f} | {stddev_us:.2f} | {stats['ops']:.0f} |\n"
            )

    print(f"Exported to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Export benchmark results")
    parser.add_argument("name", help="Benchmark name to export")
    parser.add_argument(
        "--format",
        "-f",
        choices=["csv", "json", "markdown", "md"],
        default="csv",
        help="Output format (default: csv)",
    )
    parser.add_argument(
        "--output", "-o", help="Output file (default: benchmark_results.<format>)"
    )

    args = parser.parse_args()

    # Find benchmark file
    benchmark_file = find_benchmark_file(args.name)
    print(f"Found benchmark: {benchmark_file}")

    # Load data
    with open(benchmark_file) as f:
        data = json.load(f)

    # Determine output file
    format_ext = "md" if args.format == "markdown" else args.format
    output_file = args.output or f"benchmark_results.{format_ext}"

    # Export
    if args.format == "csv":
        export_to_csv(data, output_file)
    elif args.format == "json":
        export_to_json(data, output_file)
    elif args.format in ("markdown", "md"):
        export_to_markdown(data, output_file)


if __name__ == "__main__":
    main()
