# SWE-bench Code Model File Structure

## ESSENTIAL FILES (Must Keep)

```
claudecode_swe_bench/
│
├── swe_bench.py                 # Main unified tool - ESSENTIAL
├── code_swe_agent.py          # Core agent that runs Claude Code or Codex - ESSENTIAL
├── run_benchmark_with_eval.py   # Benchmark runner - ESSENTIAL (imported by swe_bench.py)
├── evaluate_predictions.py      # Evaluation handler - ESSENTIAL (imported by swe_bench.py)
├── show_scores.py               # Score viewer - ESSENTIAL (imported by swe_bench.py)
│
├── README.md                    # Main documentation - ESSENTIAL
├── USAGE.md                     # Command reference - KEEP
├── requirements.txt             # Python dependencies - ESSENTIAL
├── benchmark_scores.log         # Results tracking - KEEP (your data)
│
├── utils/                       # ESSENTIAL - Core utilities
│   ├── __init__.py
│   ├── claude_interface.py     # Claude CLI interface
│   ├── model_registry.py       # Model definitions
│   ├── patch_extractor.py      # Extract patches from Claude output
│   └── prompt_formatter.py     # Format prompts for Claude
│
├── prompts/                     # KEEP - Prompt templates
│   ├── swe_bench_prompt.txt    # Default prompt
│   ├── chain_of_thought_prompt.txt
│   └── react_style_prompt.txt
│
├── SWE-bench/                   # ESSENTIAL - SWE-bench is pip installed from here
│   ├── [SWE-bench source files]
│   └── ...
│
├── predictions/                 # KEEP - Your generated patches
│   ├── predictions_*.jsonl     # Your test results
│   └── ...
│
├── results/                     # KEEP - Claude outputs for debugging
│   ├── instance_*.json
│   └── ...
│
├── evaluation_results/          # KEEP - Docker evaluation results
│   ├── [timestamp]/
│   └── ...
│
└── logs/                        # KEEP - Runtime logs
    └── run_evaluation/
        └── [evaluation logs]
```


## TEMPORARY FILES (Can Delete)

```
__pycache__/                    # Python cache - regenerates automatically
.claude/                        # Claude CLI settings - optional
*.pyc                          # Python compiled files - regenerates
```

## Summary

### Must Keep (Core Functionality):
- All 5 Python files in root directory
- `utils/` directory (all files)
- `SWE-bench/` directory (swebench installed from here)
- `README.md`, `requirements.txt`

### Should Keep (Your Data):
- `predictions/` - Your test results
- `evaluation_results/` - Docker test results  
- `logs/` - Debugging information
- `results/` - Claude outputs
- `benchmark_scores.log` - Score history
- `prompts/` - Prompt templates

### Can Delete:
- `__pycache__/`
- `.claude/` (unless you have custom settings)
- Any `.pyc` files

## Minimal Working Installation

If starting fresh, you only need:
1. The 5 Python files in root
2. The `utils/` directory  
3. The `prompts/` directory
4. `README.md` and `requirements.txt`
5. Install SWE-bench: `pip install swebench`

Everything else (predictions, results, logs) will be created as you run tests.