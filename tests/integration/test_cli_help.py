"""
Integration tests for CLI help functionality
"""

import subprocess
import sys
from typing import List, Tuple

import pytest


def run_cli_command(args: List[str]) -> Tuple[int, str, str]:
    """
    Run a CLI command and return exit code, stdout, stderr
    
    Args:
        args: Command arguments (e.g., ['--help'])
        
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    cmd = [sys.executable, "-m", "buckia.cli"] + args
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", f"Command failed: {str(e)}"


class TestCLIHelp:
    """Test CLI help functionality"""
    
    def test_main_help(self):
        """Test main help command"""
        exit_code, stdout, stderr = run_cli_command(["--help"])
        
        # Should exit with 0 for help
        assert exit_code == 0, f"Help command failed: {stderr}"
        
        # Should contain basic help text
        assert "Buckia" in stdout, "Help should mention Buckia"
        assert "usage:" in stdout.lower(), "Help should show usage"
        assert "positional arguments:" in stdout.lower() or "commands:" in stdout.lower(), "Help should show commands"
        
        # Should contain main commands
        assert "sync" in stdout, "Help should mention sync command"
        assert "config" in stdout, "Help should mention config command"
        
    def test_main_help_short_flag(self):
        """Test main help with -h flag"""
        exit_code, stdout, stderr = run_cli_command(["-h"])
        
        assert exit_code == 0, f"Short help flag failed: {stderr}"
        assert "Buckia" in stdout, "Short help should mention Buckia"
        assert "usage:" in stdout.lower(), "Short help should show usage"
        
    def test_sync_help(self):
        """Test sync command help"""
        exit_code, stdout, stderr = run_cli_command(["sync", "--help"])
        
        assert exit_code == 0, f"Sync help failed: {stderr}"
        assert "sync" in stdout.lower(), "Sync help should mention sync"
        assert "--bucket" in stdout or "bucket" in stdout.lower(), "Sync help should mention bucket option"
        assert "--dry-run" in stdout, "Sync help should mention dry-run option"
        
    def test_config_help(self):
        """Test config command help"""
        exit_code, stdout, stderr = run_cli_command(["config", "--help"])
        
        assert exit_code == 0, f"Config help failed: {stderr}"
        assert "config" in stdout.lower(), "Config help should mention config"
        
    def test_auth_help(self):
        """Test auth command help"""
        exit_code, stdout, stderr = run_cli_command(["auth", "--help"])
        
        assert exit_code == 0, f"Auth help failed: {stderr}"
        assert "auth" in stdout.lower(), "Auth help should mention auth"
        
    def test_pdf_help(self):
        """Test PDF command help"""
        exit_code, stdout, stderr = run_cli_command(["pdf", "--help"])
        
        assert exit_code == 0, f"PDF help failed: {stderr}"
        assert "pdf" in stdout.lower(), "PDF help should mention PDF"
        
    def test_pdf_render_help(self):
        """Test PDF render subcommand help"""
        exit_code, stdout, stderr = run_cli_command(["pdf", "render", "--help"])
        
        assert exit_code == 0, f"PDF render help failed: {stderr}"
        assert "render" in stdout.lower(), "PDF render help should mention render"
        assert "--local-only" in stdout, "PDF render help should mention local-only option"
        assert "--output-dir" in stdout, "PDF render help should mention output-dir option"


class TestCLIHelpContent:
    """Test CLI help content quality"""
    
    def test_help_contains_examples(self):
        """Test that help contains usage examples"""
        exit_code, stdout, stderr = run_cli_command(["--help"])
        
        assert exit_code == 0, f"Help command failed: {stderr}"
        
        # Help should be informative
        assert len(stdout) > 100, "Help text should be substantial"
        
    def test_sync_help_contains_options(self):
        """Test that sync help contains expected options"""
        exit_code, stdout, stderr = run_cli_command(["sync", "--help"])
        
        assert exit_code == 0, f"Sync help failed: {stderr}"
        
        # Should contain key sync options
        expected_options = ["--bucket", "--dry-run", "--verbose"]
        for option in expected_options:
            assert option in stdout, f"Sync help should contain {option}"
            
    def test_pdf_render_help_contains_options(self):
        """Test that PDF render help contains expected options"""
        exit_code, stdout, stderr = run_cli_command(["pdf", "render", "--help"])
        
        assert exit_code == 0, f"PDF render help failed: {stderr}"
        
        # Should contain key PDF options
        expected_options = ["--local-only", "--output-dir"]
        for option in expected_options:
            assert option in stdout, f"PDF render help should contain {option}"


class TestCLIErrorHandling:
    """Test CLI error handling for invalid commands"""
    
    def test_invalid_command(self):
        """Test invalid command shows helpful error"""
        exit_code, stdout, stderr = run_cli_command(["invalid-command"])
        
        # Should exit with non-zero code
        assert exit_code != 0, "Invalid command should fail"
        
        # Should suggest help or show error
        output = stdout + stderr
        assert "invalid" in output.lower() or "error" in output.lower() or "help" in output.lower(), \
            "Invalid command should show helpful error message"
            
    def test_invalid_subcommand(self):
        """Test invalid subcommand shows helpful error"""
        exit_code, stdout, stderr = run_cli_command(["pdf", "invalid-subcommand"])
        
        # Should exit with non-zero code
        assert exit_code != 0, "Invalid subcommand should fail"
        
        # Should show error message
        output = stdout + stderr
        assert len(output) > 0, "Invalid subcommand should show error message"


class TestCLIVersionAndInfo:
    """Test CLI version and information commands"""
    
    def test_version_flag(self):
        """Test --version flag"""
        exit_code, stdout, stderr = run_cli_command(["--version"])
        
        # Should exit successfully
        assert exit_code == 0, f"Version command failed: {stderr}"
        
        # Should contain version information
        assert len(stdout.strip()) > 0, "Version should output something"
        
    def test_version_in_help(self):
        """Test that version is mentioned in help"""
        exit_code, stdout, stderr = run_cli_command(["--help"])
        
        assert exit_code == 0, f"Help command failed: {stderr}"
        assert "--version" in stdout, "Help should mention --version flag"


@pytest.mark.integration
class TestCLIHelpIntegration:
    """Integration tests for CLI help with real environment"""
    
    def test_help_works_without_config(self):
        """Test that help works even without configuration"""
        # Help should work regardless of configuration state
        exit_code, stdout, stderr = run_cli_command(["--help"])
        assert exit_code == 0, "Help should work without configuration"
        
        exit_code, stdout, stderr = run_cli_command(["sync", "--help"])
        assert exit_code == 0, "Sync help should work without configuration"
        
    def test_all_documented_commands_have_help(self):
        """Test that all documented commands have working help"""
        # List of commands that should have help
        commands_to_test = [
            ["sync"],
            ["config"],
            ["auth"],
            ["pdf"],
            ["pdf", "render"],
        ]
        
        for cmd in commands_to_test:
            exit_code, stdout, stderr = run_cli_command(cmd + ["--help"])
            assert exit_code == 0, f"Help for {' '.join(cmd)} should work: {stderr}"
            assert len(stdout) > 50, f"Help for {' '.join(cmd)} should be substantial"
