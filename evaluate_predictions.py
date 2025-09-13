#!/usr/bin/env python3
"""
Flexible evaluation script for past SWE-bench predictions
Supports individual files, date ranges, patterns, and interactive selection
"""

import argparse
import json
import os
import sys
import subprocess
import time
import re
from datetime import datetime, timedelta
from pathlib import Path
import jsonlines
from typing import List, Tuple
import logging

class PredictionEvaluator:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.predictions_dir = self.base_dir / "predictions"
        self.log_file = self.base_dir / "benchmark_scores.log"
        self.eval_results_dir = self.base_dir / "evaluation_results"
        self.eval_results_dir.mkdir(exist_ok=True)
        
    def get_prediction_files(self) -> List[Tuple[Path, datetime, int]]:
        """Get all prediction files with metadata"""
        files = []
        for f in self.predictions_dir.glob("predictions_*.jsonl"):
            # Skip eval files
            if "_eval.jsonl" in str(f):
                continue
            
            # Extract timestamp from filename (predictions_YYYYMMDD_HHMMSS.jsonl)
            match = re.search(r'predictions_(\d{8})_(\d{6})\.jsonl', f.name)
            if match:
                date_str = match.group(1)
                time_str = match.group(2)
                timestamp = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                
                # Count instances
                instance_count = 0
                try:
                    with jsonlines.open(f) as reader:
                        instance_count = sum(1 for _ in reader)
                except (jsonlines.Error, OSError) as exc:
                    print(f"Warning: Could not read {f}: {exc}")
                    continue

                files.append((f, timestamp, instance_count))
        
        return sorted(files, key=lambda x: x[1], reverse=True)
    
    def filter_by_date(self, files, date_str) -> List:
        """Filter files by specific date"""
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        return [(f, t, c) for f, t, c in files if t.date() == target_date]
    
    def filter_by_date_range(self, files, start_str, end_str) -> List:
        """Filter files by date range"""
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
        return [(f, t, c) for f, t, c in files 
                if start_date <= t.date() <= end_date]
    
    def filter_by_pattern(self, files, pattern) -> List:
        """Filter files by filename pattern"""
        import fnmatch
        return [(f, t, c) for f, t, c in files 
                if fnmatch.fnmatch(f.name, pattern)]
    
    def interactive_selection(self, files) -> List:
        """Interactive file selection"""
        if not files:
            print("No prediction files found.")
            return []
        
        print("\n" + "="*70)
        print("Available prediction files:")
        print("="*70)
        
        for i, (f, timestamp, count) in enumerate(files, 1):
            # Check if already evaluated
            eval_status = self.check_evaluation_status(f)
            status_marker = "✓" if eval_status == "completed" else "○"
            
            print(f"[{i:2}] {status_marker} {timestamp.strftime('%Y-%m-%d %H:%M:%S')} - "
                  f"{count:3} instances - {f.name}")
        
        print("\n✓ = Already evaluated, ○ = Not evaluated")
        print("\nSelect files to evaluate:")
        print("  - Enter numbers (e.g., '1' or '1,3,5' or '1-5')")
        print("  - Enter 'all' for all files")
        print("  - Enter 'pending' for unevaluated files only")
        print("  - Enter 'q' to quit")

        try:
            selection = input("\nYour choice: ").strip().lower()
        except EOFError:
            print("\nNo input detected. Exiting selection.")
            return []
        
        if selection == 'q':
            return []
        elif selection == 'all':
            return files
        elif selection == 'pending':
            return [(f, t, c) for f, t, c in files 
                    if self.check_evaluation_status(f) != "completed"]
        else:
            selected = []
            try:
                # Parse selection (supports: 1,3,5 or 1-5 or combinations)
                parts = selection.split(',')
                for part in parts:
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        for i in range(start, end + 1):
                            if 1 <= i <= len(files):
                                selected.append(files[i-1])
                    else:
                        i = int(part)
                        if 1 <= i <= len(files):
                            selected.append(files[i-1])
            except ValueError as exc:
                print(f"Invalid selection: {exc}")
                return []

            return selected

    def check_evaluation_status(self, prediction_file) -> str:
        """Check if a prediction file has been evaluated"""
        if not self.log_file.exists():
            return "unknown"
        
        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("prediction_file", "").endswith(prediction_file.name):
                        return entry.get("evaluation_status", "unknown")
                except json.JSONDecodeError:
                    print(f"Warning: Skipping invalid JSON line: {line.strip()}")
                except Exception as exc:
                    print(f"Warning: Failed to parse log line due to {exc}: {line.strip()}")

        return "unknown"
    
    def evaluate_file(self, prediction_file: Path, dataset_name="princeton-nlp/SWE-bench_Lite",
                      max_workers=2, update_log=True, force=False) -> Tuple[float, float]:
        """Evaluate a single prediction file"""
        print(f"\n{'='*70}")
        print(f"Evaluating: {prediction_file.name}")
        print(f"{'='*70}")
        
        # Check current status
        status = self.check_evaluation_status(prediction_file)
        if status == "completed":
            if force:
                print("⚠️ This file has already been evaluated. Re-evaluating due to --force.")
            else:
                print("⚠️ This file has already been evaluated.")
                try:
                    response = input("Re-evaluate? (y/n): ").strip().lower()
                except EOFError:
                    response = 'n'
                if response != 'y':
                    return None, 0
        
        # Prepare for evaluation
        eval_file = str(prediction_file).replace('.jsonl', '_eval.jsonl')
        
        # Convert to evaluation format
        predictions = []
        with jsonlines.open(prediction_file) as reader:
            for obj in reader:
                predictions.append(obj)

        model_name = None
        with jsonlines.open(eval_file, mode='w') as writer:
            for pred in predictions:
                if model_name is None:
                    model_name = pred.get("model", "claude-code")
                eval_pred = {
                    "instance_id": pred.get("instance_id", ""),
                    "model_name_or_path": model_name,
                    "model_patch": pred.get("prediction", "")
                }
                writer.write(eval_pred)
        
        # Run evaluation
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = f"eval_{timestamp}"
        
        cmd = [
            sys.executable, "-m", "swebench.harness.run_evaluation",
            "--predictions_path", eval_file,
            "--dataset_name", dataset_name,
            "--split", "test",
            "--run_id", run_id,
            "--max_workers", str(max_workers),
            "--timeout", "600",
            "--cache_level", "env",
            "--report_dir", str(self.eval_results_dir),
        ]
        
        print(f"\n🔬 Running Docker evaluation...")
        print(f"Command: {' '.join(cmd)}")
        
        try:
            start_time = time.time()
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=str(self.eval_results_dir),
            )
            
            output_lines = []
            for line in iter(process.stdout.readline, ''):
                print(line, end='')
                output_lines.append(line)
            
            process.wait()
            eval_time = time.time() - start_time

            json_path = self.eval_results_dir / f"{model_name}.{run_id}.json"
            resolved = total = None
            if json_path.exists():
                try:
                    with open(json_path) as f:
                        data = json.load(f)
                    resolved = data.get("resolved_instances")
                    total = data.get("total_instances") or len(predictions)
                except (OSError, json.JSONDecodeError) as exc:
                    logging.warning(f"Failed to parse evaluation JSON: {exc}")

            if resolved is None or total is None:
                logging.warning("Structured evaluation results missing; falling back to regex parsing.")
                output_text = ''.join(output_lines)
                patterns = [
                    r'(\d+) of (\d+) instances',
                    r'(\d+)/(\d+) resolved',
                    r'resolved (\d+) of (\d+)',
                    r'Success Rate: (\d+\.?\d*)\%'
                ]
                resolved = None
                total = None
                for pattern in patterns:
                    match = re.search(pattern, output_text)
                    if match:
                        if '%' in pattern:
                            score = float(match.group(1))
                            print(f"\n✅ Evaluation Score: {score:.2f}%")
                            return score, eval_time
                        else:
                            resolved = int(match.group(1))
                            total = int(match.group(2)) if len(match.groups()) > 1 else len(predictions)
                            break
                if resolved is None or total is None:
                    print("\n⚠️ Could not parse evaluation results")
                    return None, eval_time

            score = (resolved / total) * 100 if total else 0
            print(f"\n✅ Evaluation Score: {score:.2f}% ({resolved}/{total} issues fixed)")

            if update_log:
                self.update_log_entry(prediction_file, score, eval_time)

            return score, eval_time
                
        except Exception as e:
            print(f"\n❌ Evaluation error: {e}")
            return None, 0
    
    def update_log_entry(self, prediction_file: Path, eval_score: float, eval_time: float):
        """Update log file with evaluation results"""
        if not self.log_file.exists():
            return
        
        # Read existing entries
        entries = []
        updated = False
        
        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("prediction_file", "").endswith(prediction_file.name):
                        # Update this entry
                        entry["evaluation_score"] = eval_score
                        entry["evaluation_time"] = eval_time
                        entry["evaluation_status"] = "completed"
                        entry["evaluation_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        updated = True
                    entries.append(entry)
                except json.JSONDecodeError:
                    print(f"Warning: Skipping invalid JSON line: {line.strip()}")
                    entries.append(line.strip())
                except Exception as exc:
                    print(f"Warning: Failed to parse log line due to {exc}: {line.strip()}")
                    entries.append(line.strip())
        
        # Write back
        with open(self.log_file, 'w') as f:
            for entry in entries:
                if isinstance(entry, dict):
                    f.write(json.dumps(entry) + '\n')
                else:
                    f.write(entry + '\n')
        
        if updated:
            print(f"✅ Updated log file with evaluation score: {eval_score:.2f}%")

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate past SWE-bench predictions with flexible selection"
    )
    
    # Selection modes
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--file", type=str,
                      help="Evaluate a specific prediction file")
    group.add_argument("--date", type=str,
                      help="Evaluate all predictions from date (YYYY-MM-DD)")
    group.add_argument("--date-range", nargs=2, metavar=('START', 'END'),
                      help="Evaluate predictions in date range")
    group.add_argument("--last", type=int,
                      help="Evaluate last N prediction files")
    group.add_argument("--pattern", type=str,
                      help="Evaluate files matching pattern (e.g., '*_16*')")
    group.add_argument("--interactive", action="store_true",
                      help="Interactive selection mode (default)")
    
    # Other options
    parser.add_argument("--dataset", default="princeton-nlp/SWE-bench_Lite",
                       help="Dataset name")
    parser.add_argument("--max-workers", type=int, default=2,
                       help="Max parallel Docker containers")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be evaluated without running")
    parser.add_argument("--no-update-log", action="store_true",
                       help="Don't update the log file")
    parser.add_argument("--force", "--yes", action="store_true",
                        help="Skip confirmation prompts and re-evaluate files")
    
    args = parser.parse_args()
    
    evaluator = PredictionEvaluator()
    
    # Get all prediction files
    all_files = evaluator.get_prediction_files()
    
    if not all_files:
        print("No prediction files found in predictions/")
        return
    
    # Filter based on selection mode
    selected_files = []
    
    if args.file:
        # Specific file
        file_path = Path(args.file)
        if not file_path.exists():
            # Try in predictions directory
            file_path = evaluator.predictions_dir / args.file
        
        if file_path.exists():
            # Find in list
            for f, t, c in all_files:
                if f == file_path:
                    selected_files = [(f, t, c)]
                    break
        else:
            print(f"File not found: {args.file}")
            return
            
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
        return
    
    # Show selection summary
    print(f"\n{'='*70}")
    print(f"Selected {len(selected_files)} file(s) for evaluation:")
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
        return
    
    # Confirm
    if len(selected_files) > 1 and not args.force:
        try:
            response = input("\nProceed with evaluation? (y/n): ").strip().lower()
        except EOFError:
            response = 'n'
        if response != 'y':
            return
    
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

if __name__ == "__main__":
    main()