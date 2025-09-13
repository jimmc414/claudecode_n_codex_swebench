#!/usr/bin/env python3
"""
Unified SWE-bench Command Line Tool
Combines all benchmark, evaluation, and scoring functionality
"""

import argparse
import sys
import os
from pathlib import Path

# Import the existing functionality
sys.path.insert(0, str(Path(__file__).parent))

# Check for swebench installation when needed for evaluation
def check_swebench_installed():
    """Check if swebench is installed, provide helpful message if not."""
    try:
        import swebench
        return True
    except ImportError:
        print("\n⚠️  SWE-bench module not found!")
        print("To install SWE-bench for evaluation, run:")
        print("  pip install swebench")
        print("Or install from source:")
        print("  git clone https://github.com/princeton-nlp/SWE-bench.git")
        print("  cd SWE-bench && pip install -e .")
        print("\nNote: You can still generate patches without swebench,")
        print("but evaluation requires it to test if patches actually work.")
        return False

from run_benchmark_with_eval import EnhancedBenchmarkRunner
from evaluate_predictions import PredictionEvaluator
from show_scores import ScoreViewer
from utils.model_registry import list_models, get_model_name
from code_swe_agent import DEFAULT_BACKEND

def run_command(args):
    """Handle 'run' subcommand - run new benchmarks"""
    runner = EnhancedBenchmarkRunner(
        model=args.model if hasattr(args, 'model') else None,
        backend=args.backend if hasattr(args, 'backend') and args.backend else DEFAULT_BACKEND,
    )
    
    # Set default limit if not specified
    if not args.limit:
        if args.quick:
            args.limit = 10
        elif args.standard:
            args.limit = 50
        elif args.full:
            args.limit = 300
        else:
            args.limit = 300  # Default to full test
    
    # Import datetime for logging
    from datetime import datetime
    import time
    
    print("="*60)
    print("SWE-bench Benchmark Runner")
    print("="*60)
    print(f"Dataset: {args.dataset}")
    print(f"Instances: {args.limit}")
    if hasattr(args, 'model') and args.model:
        model_name = get_model_name(args.model, runner.backend) if args.model else None
        print(f"Model: {args.model} -> {model_name}")
    print(f"Backend: {runner.backend}")
    print(f"Evaluation: {'DISABLED' if args.no_eval else 'ENABLED'}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run inference
    print(f"\nPhase 1: Generating patches with {runner.backend.title()} Code...")
    start_time = time.time()
    prediction_file, generation_time = runner.run_inference(args.dataset, args.limit)
    
    if not prediction_file:
        print("❌ Failed to generate predictions")
        runner.log_result(
            args.dataset, args.limit, 0.0, None, generation_time, 0,
            None, f"Failed to generate predictions. {args.notes}", "failed"
        )
        return 1
    
    # Calculate generation score
    generation_score, total_instances = runner.calculate_generation_score(prediction_file)
    print(f"\n📈 Generation Score: {generation_score:.2f}% ({int(generation_score * total_instances / 100)}/{total_instances} patches generated)")
    
    # Run evaluation unless disabled
    evaluation_score = None
    evaluation_time = 0
    evaluation_status = "skipped" if args.no_eval else "pending"
    
    if not args.no_eval:
        # Check if swebench is installed for evaluation
        if not check_swebench_installed():
            print("\n⚠️  Skipping evaluation due to missing swebench module")
            evaluation_status = "skipped"
            evaluation_score = None
            evaluation_time = 0
        else:
            print("\nPhase 2: Evaluating patches with Docker...")
            evaluation_score, evaluation_time = runner.run_evaluation(
                prediction_file, args.dataset, args.max_workers
            )
            
            if evaluation_score is not None:
                evaluation_status = "completed"
            else:
                evaluation_status = "failed"
                evaluation_score = 0.0
    
    total_time = time.time() - start_time
    
    # Log results
    runner.log_result(
        args.dataset, total_instances, generation_score,
        evaluation_score, generation_time, evaluation_time,
        prediction_file, args.notes, evaluation_status
    )
    
    # Display summary
    print("\n" + "="*60)
    print("BENCHMARK SUMMARY")
    print("="*60)
    print(f"Dataset: {args.dataset}")
    print(f"Instances tested: {total_instances}")
    print(f"Generation Score: {generation_score:.2f}% (patches created)")
    
    if evaluation_status == "completed":
        print(f"Evaluation Score: {evaluation_score:.2f}% (issues fixed) ← REAL SCORE")
    elif evaluation_status == "skipped":
        print("Evaluation: SKIPPED (use without --no-eval for real scores)")
    else:
        print("Evaluation: FAILED")
    
    print(f"\nTotal time: {total_time:.1f} seconds")
    print(f"Results logged to: {runner.log_file}")
    
    return 0

def eval_command(args):
    """Handle 'eval' subcommand - evaluate past predictions"""
    # Check if swebench is installed for evaluation
    if not check_swebench_installed():
        return 1
    
    evaluator = PredictionEvaluator()
    
    # Get all prediction files
    all_files = evaluator.get_prediction_files()
    
    if not all_files:
        print("No prediction files found in predictions/")
        return 1
    
    # Filter based on selection mode
    selected_files = []
    
    if args.file:
        # Specific file
        file_path = Path(args.file)
        if not file_path.exists():
            file_path = evaluator.predictions_dir / args.file
        
        if file_path.exists():
            for f, t, c in all_files:
                if f == file_path or f.name == args.file:
                    selected_files = [(f, t, c)]
                    break
        
        if not selected_files:
            print(f"File not found: {args.file}")
            return 1
            
    elif args.date:
        selected_files = evaluator.filter_by_date(all_files, args.date)
        
    elif args.date_range:
        selected_files = evaluator.filter_by_date_range(
            all_files, args.date_range[0], args.date_range[1]
        )
        
    elif args.last:
        selected_files = all_files[:args.last]
        
    elif args.pattern:
        selected_files = evaluator.filter_by_pattern(all_files, args.pattern)
        
    else:
        # Interactive mode (default)
        selected_files = evaluator.interactive_selection(all_files)
    
    if not selected_files:
        print("No files selected for evaluation.")
        return 1
    
    # Show selection summary
    print(f"\n{'='*70}")
    print(f"Selected {len(selected_files)} file(s) for evaluation")
    print(f"{'='*70}")
    
    total_instances = 0
    for f, timestamp, count in selected_files:
        status = evaluator.check_evaluation_status(f)
        status_marker = "✓" if status == "completed" else "○"
        print(f"  {status_marker} {timestamp.strftime('%Y-%m-%d %H:%M:%S')} - "
              f"{count} instances - {f.name}")
        total_instances += count
    
    print(f"\nTotal instances to evaluate: {total_instances}")
    
    if args.dry_run:
        print("\n[DRY RUN] Would evaluate the above files.")
        return 0
    
    # Confirm if multiple files
    if len(selected_files) > 1 and not args.force:
        try:
            response = input("\nProceed with evaluation? (y/n): ").strip().lower()
        except EOFError:
            response = 'n'
        if response != 'y':
            return 0
    
    # Evaluate each file
    results = []
    for i, (pred_file, timestamp, count) in enumerate(selected_files, 1):
        print(f"\n[{i}/{len(selected_files)}] Processing {pred_file.name}")
        
        score, eval_time = evaluator.evaluate_file(
            pred_file,
            args.dataset,
            args.max_workers,
            update_log=not args.no_update_log,
            force=args.force
        )
        
        if score is not None:
            results.append((pred_file.name, count, score, eval_time))
    
    # Summary
    if results:
        print(f"\n{'='*70}")
        print("EVALUATION SUMMARY")
        print(f"{'='*70}")
        
        for filename, instances, score, eval_time in results:
            print(f"  {filename}: {score:.2f}% ({instances} instances, {eval_time:.1f}s)")
        
        if len(results) > 1:
            avg_score = sum(r[2] for r in results) / len(results)
            total_time = sum(r[3] for r in results)
            print(f"\nAverage score: {avg_score:.2f}%")
            print(f"Total evaluation time: {total_time:.1f}s")
    
    return 0

def scores_command(args):
    """Handle 'scores' subcommand - view and analyze scores"""
    viewer = ScoreViewer()
    scores = viewer.load_scores()
    
    if not scores:
        print("No benchmark scores found.")
        print("Run benchmarks first with:")
        print("  python swe_bench.py run --quick")
        return 1
    
    # Apply last N filter if specified
    if args.last:
        scores = scores[-args.last:]
    
    # Main display
    print("\n" + "="*60)
    print("SWE-BENCH BENCHMARK SCORES")
    print("="*60)
    
    viewer.display_scores(scores, args.filter)
    
    # Additional displays based on flags
    if args.stats:
        viewer.show_statistics(scores)
    
    if args.trends:
        viewer.show_trends(scores)
    
    if args.pending:
        viewer.show_pending_evaluations(scores)
    
    # Export if requested
    if args.export:
        viewer.export_to_csv(scores, args.export)
    
    # Quick summary
    evaluated = len([s for s in scores if s.get("evaluation_status") == "completed"])
    pending = len([s for s in scores if s.get("evaluation_status") != "completed"])
    
    print(f"\nSummary: {len(scores)} total runs, {evaluated} evaluated, {pending} pending")
    
    if pending > 0 and not args.pending:
        print(f"\n💡 Tip: You have {pending} runs pending evaluation.")
        print(f"   Run: python swe_bench.py eval --interactive")
    
    return 0

def quick_command(args):
    """Shortcut for quick test"""
    args.limit = 10
    args.no_eval = False
    return run_command(args)

def full_command(args):
    """Shortcut for full test"""
    args.limit = 300
    args.no_eval = False
    return run_command(args)

def check_command(args):
    """Shortcut for checking scores"""
    args.stats = True
    args.pending = True
    args.trends = False
    args.filter = "all"
    args.export = None
    args.last = None
    return scores_command(args)

def list_models_command(args):
    """List available models"""
    backend = args.backend if hasattr(args, 'backend') and args.backend else DEFAULT_BACKEND
    print()
    print(list_models(backend))
    print()
    return 0

def main():
    parser = argparse.ArgumentParser(
        description="Unified SWE-bench Command Line Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full benchmark (default)
  python swe_bench.py
  
  # Quick test with evaluation
  python swe_bench.py quick
  
  # Standard test without evaluation  
  python swe_bench.py run --standard --no-eval
  
  # Evaluate specific prediction
  python swe_bench.py eval --file predictions_20250902_163415.jsonl
  
  # Check all scores
  python swe_bench.py check
  
  # Run with specific model
  python swe_bench.py run --model opus-4.1 --quick
  python swe_bench.py run --model sonnet-3.7 --limit 20
        """
    )
    
    # Create subparsers
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # RUN command
    run_parser = subparsers.add_parser('run', help='Run new benchmark')
    run_parser.add_argument('--limit', type=int, help='Number of instances')
    run_parser.add_argument('--quick', action='store_true', help='Quick test (10 instances)')
    run_parser.add_argument('--standard', action='store_true', help='Standard test (50 instances)')
    run_parser.add_argument('--full', action='store_true', help='Full test (300 instances)')
    run_parser.add_argument('--no-eval', action='store_true', help='Skip Docker evaluation')
    run_parser.add_argument('--dataset', default='princeton-nlp/SWE-bench_Lite', help='Dataset to use')
    run_parser.add_argument('--max-workers', type=int, default=2, help='Max parallel Docker containers')
    run_parser.add_argument('--notes', default='', help='Optional notes about this run')
    run_parser.add_argument('--model', type=str, help='Model to use (e.g., opus-4.1, codex-4.2)')
    run_parser.add_argument('--backend', type=str, choices=['claude', 'codex'], help='Code model backend')
    
    # EVAL command
    eval_parser = subparsers.add_parser('eval', help='Evaluate past predictions')
    eval_group = eval_parser.add_mutually_exclusive_group()
    eval_group.add_argument('--file', type=str, help='Specific prediction file')
    eval_group.add_argument('--date', type=str, help='All predictions from date (YYYY-MM-DD)')
    eval_group.add_argument('--date-range', nargs=2, metavar=('START', 'END'), help='Date range')
    eval_group.add_argument('--last', type=int, help='Last N prediction files')
    eval_group.add_argument('--pattern', type=str, help='Files matching pattern')
    eval_group.add_argument('--interactive', action='store_true', help='Interactive selection (default)')
    eval_parser.add_argument('--dataset', default='princeton-nlp/SWE-bench_Lite', help='Dataset name')
    eval_parser.add_argument('--max-workers', type=int, default=2, help='Max parallel Docker containers')
    eval_parser.add_argument('--dry-run', action='store_true', help='Show what would be evaluated')
    eval_parser.add_argument('--no-update-log', action='store_true', help="Don't update log file")
    eval_parser.add_argument('--force', '--yes', action='store_true',
                              help='Skip confirmation prompts and re-evaluate files')
    
    # SCORES command
    scores_parser = subparsers.add_parser('scores', help='View and analyze scores')
    scores_parser.add_argument('--filter', choices=['all', 'evaluated', 'pending'], default='all', help='Filter scores')
    scores_parser.add_argument('--stats', action='store_true', help='Show statistics')
    scores_parser.add_argument('--trends', action='store_true', help='Show trends over time')
    scores_parser.add_argument('--pending', action='store_true', help='Show pending evaluations')
    scores_parser.add_argument('--export', type=str, metavar='FILE.csv', help='Export to CSV')
    scores_parser.add_argument('--last', type=int, metavar='N', help='Show only last N entries')
    
    # Shortcut commands
    subparsers.add_parser('quick', help='Quick test (10 instances with eval)')
    subparsers.add_parser('full', help='Full test (300 instances with eval)')
    subparsers.add_parser('check', help='Check scores (stats + pending)')
    list_parser = subparsers.add_parser('list-models', help='List available models')
    list_parser.add_argument('--backend', type=str, choices=['claude', 'codex'], help='Backend to list')
    
    args = parser.parse_args()
    
    # Default to full test if no command specified
    if not args.command:
        args.command = 'run'
        args.limit = 300
        args.no_eval = False
        args.dataset = 'princeton-nlp/SWE-bench_Lite'
        args.max_workers = 2
        args.notes = 'Full benchmark (default)'
        args.quick = False
        args.standard = False
        args.full = True
        args.model = None
    
    # Route to appropriate handler
    if args.command == 'run':
        return run_command(args)
    elif args.command == 'eval':
        if not any([args.file, args.date, args.date_range, args.last, args.pattern, args.interactive]):
            args.interactive = True  # Default to interactive
        return eval_command(args)
    elif args.command == 'scores':
        return scores_command(args)
    elif args.command == 'quick':
        # Create args for quick command
        class QuickArgs:
            limit = 10
            no_eval = False
            dataset = 'princeton-nlp/SWE-bench_Lite'
            max_workers = 2
            notes = 'Quick test'
            quick = True
            standard = False
            full = False
            model = None
        return run_command(QuickArgs())
    elif args.command == 'full':
        # Create args for full command
        class FullArgs:
            limit = 300
            no_eval = False
            dataset = 'princeton-nlp/SWE-bench_Lite'
            max_workers = 2
            notes = 'Full benchmark'
            quick = False
            standard = False
            full = True
            model = None
        return run_command(FullArgs())
    elif args.command == 'check':
        # Create args for check command
        class CheckArgs:
            stats = True
            pending = True
            trends = False
            filter = 'all'
            export = None
            last = None
        return scores_command(CheckArgs())
    elif args.command == 'list-models':
        return list_models_command(args)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())