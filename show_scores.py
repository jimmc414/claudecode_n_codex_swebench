#!/usr/bin/env python3
"""
Score summary viewer for SWE-bench benchmark results
Shows all tests with real vs placeholder scores, trends, and statistics
"""

import json
import argparse
from datetime import datetime
from pathlib import Path
import csv
from typing import List, Dict

class ScoreViewer:
    def __init__(self):
        self.log_file = Path("benchmark_scores.log")
        
    def load_scores(self) -> List[Dict]:
        """Load all scores from log file"""
        if not self.log_file.exists():
            print(f"No log file found at {self.log_file}")
            return []
        
        scores = []
        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    scores.append(entry)
                except json.JSONDecodeError:
                    print(f"Warning: Skipping invalid JSON line: {line.strip()}")
                except Exception as exc:
                    print(f"Warning: Failed to parse line due to {exc}: {line.strip()}")

        return scores
    
    def display_scores(self, scores: List[Dict], filter_type="all"):
        """Display scores in a formatted table"""
        if not scores:
            print("No scores to display.")
            return
        
        # Filter scores
        if filter_type == "evaluated":
            scores = [s for s in scores if s.get("evaluation_status") == "completed"]
        elif filter_type == "pending":
            scores = [s for s in scores if s.get("evaluation_status") != "completed"]
        
        print("\n" + "="*100)
        print(f"{'Timestamp':<20} {'Instances':>10} {'Gen Score':>10} {'Eval Score':>10} {'Status':<12} {'Notes'}")
        print("="*100)
        
        for entry in scores:
            timestamp = entry.get("timestamp", "Unknown")[:19]
            instances = entry.get("num_instances", 0)
            gen_score = entry.get("generation_score", 0)
            eval_score = entry.get("evaluation_score")
            status = entry.get("evaluation_status", "unknown")
            notes = entry.get("notes", "")[:30]
            
            # Format eval score
            if eval_score is not None:
                eval_str = f"{eval_score:>9.1f}%"
            else:
                eval_str = "      -   "
            
            # Status indicator
            if status == "completed":
                status_str = "✓ Evaluated"
            elif status == "pending":
                status_str = "○ Pending"
            elif status == "skipped":
                status_str = "- Skipped"
            else:
                status_str = "? " + status[:10]
            
            print(f"{timestamp:<20} {instances:>10} {gen_score:>9.1f}% {eval_str} {status_str:<12} {notes}")
        
        print("="*100)
    
    def show_statistics(self, scores: List[Dict]):
        """Show statistics and trends"""
        if not scores:
            return
        
        evaluated = [s for s in scores if s.get("evaluation_status") == "completed"]
        pending = [s for s in scores if s.get("evaluation_status") != "completed"]
        
        print("\n" + "="*60)
        print("STATISTICS")
        print("="*60)
        
        print(f"Total runs: {len(scores)}")
        print(f"  - Evaluated: {len(evaluated)}")
        print(f"  - Pending evaluation: {len(pending)}")
        
        if evaluated:
            gen_scores = [s.get("generation_score", 0) for s in evaluated]
            eval_scores = [s.get("evaluation_score", 0) for s in evaluated 
                          if s.get("evaluation_score") is not None]
            
            print(f"\nGeneration Scores (patches created):")
            print(f"  Average: {sum(gen_scores)/len(gen_scores):.1f}%")
            print(f"  Min: {min(gen_scores):.1f}%")
            print(f"  Max: {max(gen_scores):.1f}%")
            
            if eval_scores:
                print(f"\nEvaluation Scores (issues fixed - REAL):")
                print(f"  Average: {sum(eval_scores)/len(eval_scores):.1f}%")
                print(f"  Min: {min(eval_scores):.1f}%")
                print(f"  Max: {max(eval_scores):.1f}%")
                
                # Show average drop from generation to evaluation
                avg_gen = sum(gen_scores)/len(gen_scores)
                avg_eval = sum(eval_scores)/len(eval_scores)
                drop = avg_gen - avg_eval
                print(f"\nAverage drop from generation to evaluation: {drop:.1f}%")
                if avg_gen == 0:
                    print("No patches generated; success rate unavailable.")
                else:
                    print(f"Success rate: {avg_eval/avg_gen*100:.1f}% of generated patches actually work")
        
        # Time statistics
        all_gen_times = [s.get("generation_time", 0) for s in scores 
                        if s.get("generation_time")]
        all_eval_times = [s.get("evaluation_time", 0) for s in evaluated 
                         if s.get("evaluation_time")]
        
        if all_gen_times:
            print(f"\nGeneration times:")
            print(f"  Average: {sum(all_gen_times)/len(all_gen_times):.1f}s")
            print(f"  Total: {sum(all_gen_times):.1f}s")
        
        if all_eval_times:
            print(f"\nEvaluation times:")
            print(f"  Average: {sum(all_eval_times)/len(all_eval_times):.1f}s")
            print(f"  Total: {sum(all_eval_times):.1f}s")
    
    def show_trends(self, scores: List[Dict]):
        """Show score trends over time"""
        evaluated = [s for s in scores if s.get("evaluation_status") == "completed"]
        
        if len(evaluated) < 2:
            return
        
        print("\n" + "="*60)
        print("TRENDS (Evaluated Runs Only)")
        print("="*60)
        
        # Sort by timestamp
        evaluated.sort(key=lambda x: x.get("timestamp", ""))
        
        # Show last 10 runs
        recent = evaluated[-10:] if len(evaluated) >= 10 else evaluated
        
        print("\nRecent evaluation scores:")
        for entry in recent:
            timestamp = entry.get("timestamp", "Unknown")[:10]
            eval_score = entry.get("evaluation_score", 0)
            instances = entry.get("num_instances", 0)
            print(f"  {timestamp}: {eval_score:5.1f}% on {instances} instances")
        
        # Calculate trend
        if len(evaluated) >= 3:
            first_half = evaluated[:len(evaluated)//2]
            second_half = evaluated[len(evaluated)//2:]
            
            first_avg = sum(e.get("evaluation_score", 0) for e in first_half) / len(first_half)
            second_avg = sum(e.get("evaluation_score", 0) for e in second_half) / len(second_half)
            
            trend = second_avg - first_avg
            if trend > 0:
                print(f"\n📈 Improving trend: +{trend:.1f}% from first to second half")
            elif trend < 0:
                print(f"\n📉 Declining trend: {trend:.1f}% from first to second half")
            else:
                print(f"\n➡️  Stable performance")
    
    def export_to_csv(self, scores: List[Dict], filename: str):
        """Export scores to CSV file"""
        if not scores:
            print("No scores to export.")
            return
        
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = [
                'timestamp', 'dataset', 'num_instances', 
                'generation_score', 'evaluation_score', 
                'evaluation_status', 'generation_time', 
                'evaluation_time', 'notes'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for entry in scores:
                row = {k: entry.get(k, '') for k in fieldnames}
                writer.writerow(row)
        
        print(f"\n✅ Exported {len(scores)} entries to {filename}")
    
    def show_pending_evaluations(self, scores: List[Dict]):
        """Show which predictions still need evaluation"""
        pending = []
        
        for entry in scores:
            if entry.get("evaluation_status") != "completed":
                pred_file = entry.get("prediction_file", "Unknown")
                timestamp = entry.get("timestamp", "Unknown")
                instances = entry.get("num_instances", 0)
                pending.append((timestamp, pred_file, instances))
        
        if not pending:
            print("\n✅ All runs have been evaluated!")
            return
        
        print("\n" + "="*60)
        print(f"PENDING EVALUATIONS ({len(pending)} runs)")
        print("="*60)
        
        for timestamp, pred_file, instances in pending:
            filename = Path(pred_file).name if pred_file != "Unknown" else "Unknown"
            print(f"  {timestamp[:19]}: {filename} ({instances} instances)")
        
        print(f"\nTo evaluate these, run:")
        print(f"  python swe_bench.py eval --interactive")
        print(f"  (then select 'pending')")

def main():
    parser = argparse.ArgumentParser(
        description="View and analyze SWE-bench benchmark scores"
    )
    
    parser.add_argument("--filter", choices=["all", "evaluated", "pending"],
                       default="all", help="Filter scores to display")
    parser.add_argument("--export", type=str, metavar="FILE.csv",
                       help="Export scores to CSV file")
    parser.add_argument("--stats", action="store_true",
                       help="Show detailed statistics")
    parser.add_argument("--trends", action="store_true",
                       help="Show score trends over time")
    parser.add_argument("--pending", action="store_true",
                       help="Show pending evaluations")
    parser.add_argument("--last", type=int, metavar="N",
                       help="Show only last N entries")
    
    args = parser.parse_args()
    
    viewer = ScoreViewer()
    scores = viewer.load_scores()
    
    if not scores:
        print("No benchmark scores found.")
        print("Run benchmarks first with:")
        print("  python run_benchmark_with_eval.py --limit 5")
        return
    
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
    
    if pending > 0:
        print(f"\n💡 Tip: You have {pending} runs pending evaluation.")
        print(f"   Run: python swe_bench.py eval --interactive")

if __name__ == "__main__":
    main()
