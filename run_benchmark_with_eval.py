#!/usr/bin/env python3
"""
Enhanced SWE-bench benchmark runner with real evaluation support
"""

import argparse
import json
import os
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path
import logging
import jsonlines
from datasets import load_dataset

class EnhancedBenchmarkRunner:
    def __init__(self, model=None, backend="claude"):
        self.base_dir = Path.cwd()
        self.log_file = self.base_dir / "benchmark_scores.log"
        self.predictions_dir = self.base_dir / "predictions"
        self.results_dir = self.base_dir / "results"
        self.eval_results_dir = self.base_dir / "evaluation_results"
        self.model = model
        self.backend = backend
        
        # Create directories
        self.predictions_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)
        self.eval_results_dir.mkdir(exist_ok=True)
        
    def log_result(self, dataset_name, num_instances, generation_score, 
                   evaluation_score, generation_time, evaluation_time, 
                   prediction_file, notes="", evaluation_status="pending"):
        """Log comprehensive benchmark results"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = {
            "timestamp": timestamp,
            "prediction_file": str(prediction_file),
            "dataset": dataset_name,
            "num_instances": num_instances,
            "generation_score": generation_score,
            "evaluation_score": evaluation_score,
            "evaluation_status": evaluation_status,
            "generation_time": generation_time,
            "evaluation_time": evaluation_time,
            "model": self.model,
            "backend": self.backend,
            "notes": notes
        }
        
        # Append to log file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        print(f"\n✅ Results logged to {self.log_file}")
        if evaluation_status == "completed":
            print(f"   Generation Score: {generation_score:.2f}% (patches created)")
            print(f"   Evaluation Score: {evaluation_score:.2f}% (issues fixed) ← REAL SCORE")
        else:
            print(f"   Generation Score: {generation_score:.2f}% (patches created)")
            print(f"   Evaluation: {evaluation_status}")
            
    def run_inference(self, dataset_name, limit):
        """Run code model on the dataset"""
        model_info = f" with model {self.model}" if self.model else ""
        print(f"\n🚀 Running {self.backend.title()} Code{model_info} on {dataset_name} (limit: {limit})...")

        cmd = [
            sys.executable,
            "code_swe_agent.py",
            "--dataset_name", dataset_name,
            "--limit", str(limit),
            "--backend", self.backend,
        ]

        if self.model:
            cmd.extend(["--model", self.model])
        
        try:
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)  # 2 hour timeout
            execution_time = time.time() - start_time
            
            if result.returncode != 0:
                print(f"⚠️ Warning: Inference had issues but continuing...")
                if result.stderr:
                    print(f"Stderr: {result.stderr[:500]}")
            
            # Find the latest prediction file
            pred_files = sorted(self.predictions_dir.glob("predictions_*.jsonl"), reverse=True)
            
            if not pred_files:
                print("❌ No prediction files generated")
                return None, execution_time
                
            latest_pred = pred_files[0]
            print(f"✅ Predictions saved to: {latest_pred}")
            return str(latest_pred), execution_time
            
        except subprocess.TimeoutExpired:
            print("❌ Inference timed out after 2 hours")
            return None, 7200
        except Exception as e:
            print(f"❌ Error during inference: {e}")
            return None, 0
            
    def calculate_generation_score(self, prediction_file):
        """Calculate score based on patch generation (not real score)"""
        if not prediction_file or not Path(prediction_file).exists():
            return 0.0, 0
        
        total = 0
        generated = 0
        
        with jsonlines.open(prediction_file) as reader:
            for obj in reader:
                total += 1
                # Check if a non-empty patch was generated
                if obj.get("prediction", "").strip():
                    generated += 1
        
        if total == 0:
            return 0.0, 0
            
        score = (generated / total) * 100
        return score, total
        
    def run_evaluation(self, prediction_file, dataset_name, max_workers=2):
        """Run real SWE-bench evaluation using Docker"""
        print(f"\n🔬 Running real evaluation on {prediction_file}...")
        print("This will test if patches actually fix the issues (takes time)...")
        
        # Prepare predictions for evaluation format
        eval_file = prediction_file.replace('.jsonl', '_eval.jsonl')
        
        predictions = []
        with jsonlines.open(prediction_file) as reader:
            for obj in reader:
                predictions.append(obj)

        model_name = f"{self.backend}-code"
        with jsonlines.open(eval_file, mode='w') as writer:
            for pred in predictions:
                eval_pred = {
                    "instance_id": pred.get("instance_id", ""),
                    "model_name_or_path": model_name,
                    "model_patch": pred.get("prediction", "")
                }
                writer.write(eval_pred)
        
        # Run evaluation
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = f"{self.backend}_code_{timestamp}"
        
        cmd = [
            sys.executable, "-m", "swebench.harness.run_evaluation",
            "--predictions_path", eval_file,
            "--dataset_name", dataset_name,
            "--split", "test",
            "--run_id", run_id,
            "--max_workers", str(max_workers),
            "--timeout", "600",  # 10 minutes per instance
            "--cache_level", "env",
            "--report_dir", str(self.eval_results_dir),
        ]
        
        print(f"Running: {' '.join(cmd)}")
        
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
            
            # Print output in real-time
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
                import re
                patterns = [
                    r'Instances resolved: (\d+)',
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
                            return float(match.group(1)), eval_time
                        elif 'Instances resolved' in pattern:
                            resolved = int(match.group(1))
                            total = len(predictions)
                            break
                        else:
                            resolved = int(match.group(1))
                            total = int(match.group(2)) if len(match.groups()) > 1 else len(predictions)
                            break
                if resolved is None or total is None:
                    print("\n⚠️ Could not parse evaluation results")
                    return None, eval_time

            score = (resolved / total) * 100 if total else 0
            print(f"\n📊 Real Evaluation Score: {score:.2f}% ({resolved}/{total} issues fixed)")
            return score, eval_time
                
        except subprocess.TimeoutExpired:
            print("\n⚠️ Evaluation timed out")
            return None, 1800
        except Exception as e:
            print(f"\n⚠️ Evaluation error: {e}")
            return None, 0

def main():
    parser = argparse.ArgumentParser(
        description="Run SWE-bench benchmark with real evaluation scores"
    )
    parser.add_argument("--dataset", default="princeton-nlp/SWE-bench_Lite", 
                       help="Dataset to use")
    parser.add_argument("--limit", type=int, default=5,
                       help="Number of instances to test (default: 5)")
    parser.add_argument("--skip-eval", action="store_true",
                       help="Skip Docker evaluation (faster but no real scores)")
    parser.add_argument("--max-workers", type=int, default=2,
                       help="Max parallel Docker containers for evaluation (default: 2)")
    parser.add_argument("--notes", default="",
                       help="Optional notes about this run")
    
    args = parser.parse_args()
    
    runner = EnhancedBenchmarkRunner()
    
    print("="*60)
    print("Enhanced SWE-bench Benchmark Runner")
    print("="*60)
    print(f"Dataset: {args.dataset}")
    print(f"Instances: {args.limit}")
    print(f"Evaluation: {'SKIPPED (fast mode)' if args.skip_eval else 'ENABLED (real scores)'}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run inference
    print("\nPhase 1: Generating patches with Claude Code...")
    start_time = time.time()
    prediction_file, generation_time = runner.run_inference(args.dataset, args.limit)
    
    if not prediction_file:
        print("❌ Failed to generate predictions")
        runner.log_result(
            args.dataset, args.limit, 0.0, None, generation_time, 0,
            None, f"Failed to generate predictions. {args.notes}", "failed"
        )
        return
    
    # Calculate generation score
    generation_score, total_instances = runner.calculate_generation_score(prediction_file)
    print(f"\n📈 Generation Score: {generation_score:.2f}% ({int(generation_score * total_instances / 100)}/{total_instances} patches generated)")
    
    # Run evaluation if not skipped
    evaluation_score = None
    evaluation_time = 0
    evaluation_status = "skipped" if args.skip_eval else "pending"
    
    if not args.skip_eval:
        print("\nPhase 2: Evaluating patches with Docker (testing if they work)...")
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
        print(f"Evaluation Score: {evaluation_score:.2f}% (issues actually fixed) ← REAL SCORE")
        print(f"\n🎯 Real Success Rate: {evaluation_score:.2f}%")
    elif evaluation_status == "skipped":
        print("Evaluation: SKIPPED (use without --skip-eval for real scores)")
    else:
        print("Evaluation: FAILED")
    
    print(f"\nTotal time: {total_time:.1f} seconds")
    print(f"  Generation: {generation_time:.1f}s")
    if evaluation_time > 0:
        print(f"  Evaluation: {evaluation_time:.1f}s")
    
    print(f"\nResults logged to: {runner.log_file}")
    
    # Show recent scores
    print("\n📊 Recent runs:")
    if runner.log_file.exists():
        with open(runner.log_file, 'r') as f:
            lines = f.readlines()
            recent = lines[-5:] if len(lines) >= 5 else lines
            for line in recent:
                entry = json.loads(line)
                gen_score = entry.get('generation_score', 0)
                eval_score = entry.get('evaluation_score')
                status = entry.get('evaluation_status', 'unknown')
                
                if status == "completed" and eval_score is not None:
                    print(f"  {entry['timestamp']}: Gen={gen_score:.1f}% → Eval={eval_score:.1f}% (real)")
                else:
                    print(f"  {entry['timestamp']}: Gen={gen_score:.1f}% ({status})")

if __name__ == "__main__":
    main()