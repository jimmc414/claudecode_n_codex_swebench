# SWE-bench Unified Tool Usage Guide

## Quick Start

The `swe_bench.py` tool combines all benchmark functionality into one command and supports both Claude Code and Codex backends.

### Common Commands

```bash
# Run full benchmark (300 instances) - DEFAULT
python swe_bench.py

# Quick test (10 instances with evaluation)
python swe_bench.py quick

# Check all scores and statistics
python swe_bench.py check

# Evaluate your previous test interactively
python swe_bench.py eval --interactive
```

## All Commands

### Running New Benchmarks

```bash
# Quick test (10 instances)
python swe_bench.py run --quick

# Standard test (50 instances)
python swe_bench.py run --standard  

# Full test (300 instances)
python swe_bench.py run --full

# Custom number
python swe_bench.py run --limit 25

# With specific model (September 2025)
python swe_bench.py run --model opus-4.1 --quick
python swe_bench.py run --model sonnet-3.7 --limit 20
python swe_bench.py run --model claude-opus-4-1-20250805 --full

# Skip evaluation (generation only)
python swe_bench.py run --quick --no-eval

# More parallel Docker workers
python swe_bench.py run --limit 20 --max-workers 4
# Use Codex backend
python swe_bench.py run --quick --backend codex
```

### Model Selection

```bash
# List available models (Claude by default)
python swe_bench.py list-models
# Codex models
python swe_bench.py list-models --backend codex

# Use aliases for convenience
python swe_bench.py run --model opus-4.1 --quick    # Latest Opus
python swe_bench.py run --model sonnet-3.7 --quick  # Latest Sonnet 3.x
python swe_bench.py run --model best --quick        # Best performance
python swe_bench.py run --model fast --quick        # Fastest/cheapest

# Or use full model names
python swe_bench.py run --model claude-opus-4-1-20250805 --quick

# Any model accepted by Claude's /model command works
python swe_bench.py run --model custom-model-name --quick
# With Codex backend
python swe_bench.py run --model codex-4.2 --backend codex --limit 5
```

### Evaluating Past Predictions

```bash
# Interactive selection (shows list, you choose)
python swe_bench.py eval --interactive

# Specific file (use actual filename from predictions/)
python swe_bench.py eval --file predictions_YYYYMMDD_HHMMSS.jsonl

# All from specific date
python swe_bench.py eval --date 2025-09-02

# Last N predictions
python swe_bench.py eval --last 5

# Date range
python swe_bench.py eval --date-range 2025-09-01 2025-09-03

# Pattern matching
python swe_bench.py eval --pattern "*_163*"

# Dry run (preview only)
python swe_bench.py eval --last 3 --dry-run
```

### Viewing Scores

```bash
# Basic view
python swe_bench.py scores

# With statistics
python swe_bench.py scores --stats

# Show trends
python swe_bench.py scores --trends

# Show pending evaluations
python swe_bench.py scores --pending

# Filter to evaluated only
python swe_bench.py scores --filter evaluated

# Export to CSV
python swe_bench.py scores --export results.csv

# Last N entries
python swe_bench.py scores --last 10
```

## Shortcuts

These shortcuts make common tasks easier:

```bash
# Quick test (same as: run --limit 10)
python swe_bench.py quick

# Full benchmark (same as: run --limit 300)
python swe_bench.py full

# Check scores (same as: scores --stats --pending)
python swe_bench.py check
```

## Understanding Scores

- **Generation Score**: % of issues where patches were created (misleading)
- **Evaluation Score**: % of issues actually fixed (real score)

Example output:
```
Generation Score: 100.0% (patches created)
Evaluation Score: 33.3% (issues fixed) ← REAL SCORE
```

## Time Estimates

| Test Size | Generation Time | Evaluation Time | Total Time |
|-----------|----------------|-----------------|------------|
| Quick (10) | ~20-30 min | ~30-50 min | ~1-2 hours |
| Standard (50) | ~2-3 hours | ~3-5 hours | ~5-8 hours |
| Full (300) | ~12-15 hours | ~20-30 hours | ~35-45 hours |

## Tips

1. **Start small**: Use `quick` for testing
2. **Check before eval**: Use `check` to see pending evaluations
3. **Batch evaluate**: Use `eval --last 5` to evaluate multiple at once
4. **Monitor progress**: The tool shows real-time progress
5. **Save time**: Use `--no-eval` when just testing generation

## Your Typical Workflow

```bash
# 1. Run a quick test
python swe_bench.py quick

# 2. Check the scores
python swe_bench.py check

# 3. If you skipped eval, run it later
python swe_bench.py eval --last 1

# 4. Export results for analysis
python swe_bench.py scores --export my_results.csv
```