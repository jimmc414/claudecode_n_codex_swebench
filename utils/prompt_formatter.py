import tempfile
from pathlib import Path
from typing import Dict, Optional

class PromptFormatter:
    """Format SWE-bench issues into prompts for Claude Code."""
    
    def __init__(self, prompt_template_path: Optional[str] = None):
        self.prompt_template_path = prompt_template_path
        self.base_template = self._load_base_template()
        
    def _load_base_template(self) -> str:
        """Load the base prompt template."""
        if self.prompt_template_path:
            try:
                with open(self.prompt_template_path, 'r') as f:
                    return f.read()
            except FileNotFoundError:
                pass
        
        # Default template if no file provided
        return """You are being evaluated on SWE-bench. You have access to a repository with a software issue that needs to be fixed.

Repository: {repo_name}
Issue: {issue_title}

Issue Description:
{issue_description}

Your task:
1. Understand the issue by carefully reading the description
2. Search the codebase to find relevant files using grep, find, or other search tools
3. Analyze the code to understand the root cause
4. Generate a fix that resolves the issue
5. Ensure your fix doesn't break existing functionality

Important notes:
- Focus on making minimal, targeted changes
- Consider edge cases and potential side effects
- The tests should pass after applying your fix
- Output clear file edits showing exactly what needs to be changed

Base directory: {base_path}
"""
    
    def format_issue(self, instance: Dict) -> str:
        """Format a SWE-bench instance into a prompt for Claude Code."""
        # Extract key information from the instance
        repo_name = instance.get("repo", "")
        issue_title = instance.get("problem_statement", "").split('\n')[0]
        issue_description = instance.get("problem_statement", "")
        base_commit = instance.get("base_commit", "")
        
        # Get instance_id for tracking
        instance_id = instance.get("instance_id", "")
        
        # Format the prompt
        base_path = Path(tempfile.gettempdir()) / f"swe_bench_{instance_id}"

        prompt = self.base_template.format(
            repo_name=repo_name,
            issue_title=issue_title,
            issue_description=issue_description,
            base_path=str(base_path),
            instance_id=instance_id,
            base_commit=base_commit,
        )
        
        # Add any hints if available
        if "hints_text" in instance and instance["hints_text"]:
            prompt += f"\n\nHints:\n{instance['hints_text']}"
            
        return prompt
    
    def format_for_cli(self, instance: Dict) -> str:
        """Format the prompt for Claude Code CLI execution."""
        base_prompt = self.format_issue(instance)

        # Return the raw prompt without escaping for CLI input
        return base_prompt
    
    def extract_instance_info(self, instance: Dict) -> Dict:
        """Extract key information from a SWE-bench instance."""
        return {
            "instance_id": instance.get("instance_id", ""),
            "repo": instance.get("repo", ""),
            "version": instance.get("version", ""),
            "base_commit": instance.get("base_commit", ""),
            "problem_statement": instance.get("problem_statement", ""),
            "hints_text": instance.get("hints_text", ""),
            "created_at": instance.get("created_at", ""),
            "test_patch": instance.get("test_patch", ""),
            "environment_setup_commit": instance.get("environment_setup_commit", "")
        }
