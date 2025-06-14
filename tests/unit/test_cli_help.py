"""
Unit tests for CLI help functionality
"""

import io
import sys
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

import pytest

from buckia.cli import parse_args


class TestCLIHelpParsing:
    """Test CLI help parsing without subprocess"""
    
    def test_main_help_parsing(self):
        """Test that main help can be parsed"""
        # Capture help output
        with redirect_stdout(io.StringIO()) as stdout, redirect_stderr(io.StringIO()) as stderr:
            with pytest.raises(SystemExit) as exc_info:
                parse_args(["--help"])
        
        # Help should exit with code 0
        assert exc_info.value.code == 0, "Help should exit with code 0"
        
        # Should have output
        help_output = stdout.getvalue()
        assert len(help_output) > 0, "Help should produce output"
        assert "Buckia" in help_output, "Help should mention Buckia"
        
    def test_sync_help_parsing(self):
        """Test that sync help can be parsed"""
        with redirect_stdout(io.StringIO()) as stdout, redirect_stderr(io.StringIO()) as stderr:
            with pytest.raises(SystemExit) as exc_info:
                parse_args(["sync", "--help"])
        
        # Help should exit with code 0
        assert exc_info.value.code == 0, "Sync help should exit with code 0"
        
        # Should have output
        help_output = stdout.getvalue()
        assert len(help_output) > 0, "Sync help should produce output"
        assert "sync" in help_output.lower(), "Sync help should mention sync"
        
    def test_config_help_parsing(self):
        """Test that config help can be parsed"""
        with redirect_stdout(io.StringIO()) as stdout, redirect_stderr(io.StringIO()) as stderr:
            with pytest.raises(SystemExit) as exc_info:
                parse_args(["config", "--help"])
        
        # Help should exit with code 0
        assert exc_info.value.code == 0, "Config help should exit with code 0"
        
        # Should have output
        help_output = stdout.getvalue()
        assert len(help_output) > 0, "Config help should produce output"
        
    def test_auth_help_parsing(self):
        """Test that auth help can be parsed"""
        with redirect_stdout(io.StringIO()) as stdout, redirect_stderr(io.StringIO()) as stderr:
            with pytest.raises(SystemExit) as exc_info:
                parse_args(["auth", "--help"])
        
        # Help should exit with code 0
        assert exc_info.value.code == 0, "Auth help should exit with code 0"
        
        # Should have output
        help_output = stdout.getvalue()
        assert len(help_output) > 0, "Auth help should produce output"
        
    def test_pdf_help_parsing(self):
        """Test that PDF help can be parsed"""
        with redirect_stdout(io.StringIO()) as stdout, redirect_stderr(io.StringIO()) as stderr:
            with pytest.raises(SystemExit) as exc_info:
                parse_args(["pdf", "--help"])
        
        # Help should exit with code 0
        assert exc_info.value.code == 0, "PDF help should exit with code 0"
        
        # Should have output
        help_output = stdout.getvalue()
        assert len(help_output) > 0, "PDF help should produce output"


class TestCLIHelpContent:
    """Test CLI help content validation"""
    
    def test_main_help_contains_commands(self):
        """Test that main help contains expected commands"""
        with redirect_stdout(io.StringIO()) as stdout:
            with pytest.raises(SystemExit):
                parse_args(["--help"])
        
        help_output = stdout.getvalue()
        
        # Should contain main commands
        expected_commands = ["sync", "config", "auth", "pdf"]
        for command in expected_commands:
            assert command in help_output, f"Main help should contain '{command}' command"
            
    def test_sync_help_contains_options(self):
        """Test that sync help contains expected options"""
        with redirect_stdout(io.StringIO()) as stdout:
            with pytest.raises(SystemExit):
                parse_args(["sync", "--help"])
        
        help_output = stdout.getvalue()
        
        # Should contain key options
        expected_options = ["--bucket", "--dry-run", "--verbose"]
        for option in expected_options:
            assert option in help_output, f"Sync help should contain '{option}' option"
            
    def test_pdf_render_help_contains_options(self):
        """Test that PDF render help contains expected options"""
        with redirect_stdout(io.StringIO()) as stdout:
            with pytest.raises(SystemExit):
                parse_args(["pdf", "render", "--help"])
        
        help_output = stdout.getvalue()
        
        # Should contain PDF-specific options
        expected_options = ["--local-only", "--output-dir"]
        for option in expected_options:
            assert option in help_output, f"PDF render help should contain '{option}' option"


class TestCLIVersionFlag:
    """Test CLI version flag functionality"""
    
    def test_version_flag_parsing(self):
        """Test that --version flag can be parsed"""
        with redirect_stdout(io.StringIO()) as stdout:
            with pytest.raises(SystemExit) as exc_info:
                parse_args(["--version"])
        
        # Version should exit with code 0
        assert exc_info.value.code == 0, "Version should exit with code 0"
        
        # Should have output
        version_output = stdout.getvalue()
        assert len(version_output) > 0, "Version should produce output"


class TestCLIErrorMessages:
    """Test CLI error message handling"""
    
    def test_invalid_command_error(self):
        """Test that invalid commands produce helpful errors"""
        with redirect_stderr(io.StringIO()) as stderr:
            with pytest.raises(SystemExit) as exc_info:
                parse_args(["invalid-command"])
        
        # Should exit with non-zero code
        assert exc_info.value.code != 0, "Invalid command should exit with non-zero code"
        
        # Should have error output
        error_output = stderr.getvalue()
        assert len(error_output) > 0, "Invalid command should produce error output"
        
    def test_missing_required_args_error(self):
        """Test that missing required arguments produce helpful errors"""
        with redirect_stderr(io.StringIO()) as stderr:
            with pytest.raises(SystemExit) as exc_info:
                # PDF render requires arguments
                parse_args(["pdf", "render"])
        
        # Should exit with non-zero code
        assert exc_info.value.code != 0, "Missing args should exit with non-zero code"
        
        # Should have error output
        error_output = stderr.getvalue()
        assert len(error_output) > 0, "Missing args should produce error output"


class TestCLIHelpAccessibility:
    """Test CLI help accessibility and usability"""
    
    def test_help_is_readable(self):
        """Test that help output is readable and well-formatted"""
        with redirect_stdout(io.StringIO()) as stdout:
            with pytest.raises(SystemExit):
                parse_args(["--help"])
        
        help_output = stdout.getvalue()
        
        # Should be substantial but not overwhelming
        lines = help_output.split('\n')
        assert 10 <= len(lines) <= 100, f"Help should be 10-100 lines, got {len(lines)}"
        
        # Should contain usage section
        assert "usage:" in help_output.lower(), "Help should contain usage section"
        
        # Should not be empty lines only
        non_empty_lines = [line for line in lines if line.strip()]
        assert len(non_empty_lines) >= 5, "Help should have substantial content"
        
    def test_subcommand_help_is_specific(self):
        """Test that subcommand help is specific to the command"""
        commands_to_test = [
            (["sync", "--help"], "sync"),
            (["config", "--help"], "config"),
            (["auth", "--help"], "auth"),
            (["pdf", "--help"], "pdf"),
        ]
        
        for args, expected_keyword in commands_to_test:
            with redirect_stdout(io.StringIO()) as stdout:
                with pytest.raises(SystemExit):
                    parse_args(args)
            
            help_output = stdout.getvalue()
            assert expected_keyword in help_output.lower(), \
                f"Help for {args[0]} should mention '{expected_keyword}'"
            
            # Should be command-specific (not just generic help)
            assert len(help_output) > 50, f"Help for {args[0]} should be substantial"


@pytest.mark.parametrize("help_flag", ["--help", "-h"])
class TestCLIHelpFlags:
    """Test both long and short help flags"""
    
    def test_main_help_flags(self, help_flag):
        """Test both --help and -h flags work for main command"""
        with redirect_stdout(io.StringIO()) as stdout:
            with pytest.raises(SystemExit) as exc_info:
                parse_args([help_flag])
        
        assert exc_info.value.code == 0, f"{help_flag} should exit with code 0"
        
        help_output = stdout.getvalue()
        assert len(help_output) > 0, f"{help_flag} should produce output"
        assert "Buckia" in help_output, f"{help_flag} should mention Buckia"
        
    def test_subcommand_help_flags(self, help_flag):
        """Test help flags work for subcommands"""
        subcommands = ["sync", "config", "auth", "pdf"]
        
        for subcmd in subcommands:
            with redirect_stdout(io.StringIO()) as stdout:
                with pytest.raises(SystemExit) as exc_info:
                    parse_args([subcmd, help_flag])
            
            assert exc_info.value.code == 0, f"{subcmd} {help_flag} should exit with code 0"
            
            help_output = stdout.getvalue()
            assert len(help_output) > 0, f"{subcmd} {help_flag} should produce output"
