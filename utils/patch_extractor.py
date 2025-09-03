import re
import os
import subprocess
from typing import List, Dict, Optional, Tuple
from unidiff import PatchSet
import tempfile

class PatchExtractor:
    """Extract patches from Claude Code's responses and file changes."""
    
    def __init__(self):
        self.file_edit_pattern = re.compile(
            r"(?:Creating|Editing|Modifying|Writing to) file: (.*?)$",
            re.MULTILINE
        )
        self.diff_pattern = re.compile(
            r"```diff\n(.*?)```",
            re.DOTALL
        )
        
    def extract_from_cli_output(self, output: str, repo_path: str) -> str:
        """Extract patch from Claude Code CLI output by analyzing git diff."""
        try:
            # Change to repo directory
            original_cwd = os.getcwd()
            os.chdir(repo_path)
            
            # First, add any untracked files to the index so they appear in diff
            subprocess.run(
                ["git", "add", "-N", "."],
                capture_output=True,
                text=True
            )
            
            # Get the diff against HEAD to capture all changes
            result = subprocess.run(
                ["git", "diff", "HEAD", "--no-color", "--no-ext-diff"],
                capture_output=True,
                text=True
            )
            
            os.chdir(original_cwd)
            
            if result.returncode == 0:
                return result.stdout
            else:
                print(f"Git diff failed: {result.stderr}")
                return ""
                
        except Exception as e:
            print(f"Error extracting patch: {e}")
            return ""
            
    def extract_from_response(self, response: str) -> List[Dict[str, str]]:
        """Extract file changes from Claude's response text."""
        changes = []
        
        # Look for diff blocks
        diff_matches = self.diff_pattern.findall(response)
        for diff in diff_matches:
            changes.append({
                "type": "diff",
                "content": diff
            })
            
        # Look for file edits mentioned in the response
        file_mentions = self.file_edit_pattern.findall(response)
        for file_path in file_mentions:
            changes.append({
                "type": "file_mention",
                "path": file_path.strip()
            })
            
        return changes
    
    def create_patch_from_changes(self, before_state: Dict[str, str], 
                                after_state: Dict[str, str]) -> str:
        """Create a unified diff patch from before/after file states."""
        patch_lines = []
        
        # Find all files that changed
        all_files = set(before_state.keys()) | set(after_state.keys())
        
        for file_path in sorted(all_files):
            before_content = before_state.get(file_path, "")
            after_content = after_state.get(file_path, "")
            
            if before_content == after_content:
                continue
                
            # Create temporary files for diff
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
                f1.write(before_content)
                temp_before = f1.name
                
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
                f2.write(after_content)
                temp_after = f2.name
                
            try:
                # Generate unified diff
                result = subprocess.run(
                    ["diff", "-u", temp_before, temp_after],
                    capture_output=True,
                    text=True
                )
                
                if result.stdout:
                    # Replace temp filenames with actual paths
                    diff_output = result.stdout
                    diff_output = diff_output.replace(temp_before, f"a/{file_path}")
                    diff_output = diff_output.replace(temp_after, f"b/{file_path}")
                    patch_lines.append(diff_output)
                    
            finally:
                os.unlink(temp_before)
                os.unlink(temp_after)
                
        return "\n".join(patch_lines)
    
    def validate_patch(self, patch: str) -> Tuple[bool, Optional[str]]:
        """Validate that a patch is well-formed."""
        if not patch or not patch.strip():
            return False, "Empty patch"
            
        try:
            # Try to parse the patch
            patchset = PatchSet(patch)
            
            # Check if patch has any files
            if not patchset:
                return False, "Patch contains no file changes"
                
            # Basic validation passed
            return True, None
            
        except Exception as e:
            return False, f"Invalid patch format: {str(e)}"
            
    def apply_patch_test(self, patch: str, repo_path: str) -> Tuple[bool, str]:
        """Test if a patch can be applied cleanly."""
        try:
            # Save patch to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
                f.write(patch)
                patch_file = f.name
                
            original_cwd = os.getcwd()
            os.chdir(repo_path)
            
            # Test patch application
            result = subprocess.run(
                ["git", "apply", "--check", patch_file],
                capture_output=True,
                text=True
            )
            
            os.chdir(original_cwd)
            os.unlink(patch_file)
            
            if result.returncode == 0:
                return True, "Patch can be applied cleanly"
            else:
                return False, f"Patch application failed: {result.stderr}"
                
        except Exception as e:
            return False, f"Error testing patch: {str(e)}"
            
    def format_for_swebench(self, patch: str, instance_id: str, model_name: str = "claude-code") -> Dict:
        """Format patch for SWE-bench submission."""
        return {
            "instance_id": instance_id,
            "model": model_name,
            "prediction": patch
        }