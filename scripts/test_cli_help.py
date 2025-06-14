#!/usr/bin/env python3
"""
Test script to verify all CLI help functionality works correctly
"""

import subprocess
import sys
from typing import List, Tuple, Dict, Any


def run_cli_command(args: List[str]) -> Tuple[int, str, str]:
    """Run a CLI command and return exit code, stdout, stderr"""
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


def test_help_command(args: List[str], description: str) -> Dict[str, Any]:
    """Test a specific help command and return results"""
    print(f"Testing: {description}")
    print(f"Command: buckia {' '.join(args)}")
    
    exit_code, stdout, stderr = run_cli_command(args)
    
    result = {
        "command": args,
        "description": description,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "success": exit_code == 0,
        "has_output": len(stdout.strip()) > 0
    }
    
    if result["success"]:
        print("✅ PASSED")
    else:
        print("❌ FAILED")
        if stderr:
            print(f"Error: {stderr}")
    
    print(f"Output length: {len(stdout)} characters")
    print("-" * 60)
    
    return result


def main():
    """Run all CLI help tests"""
    print("🧪 Testing Buckia CLI Help Functionality")
    print("=" * 60)
    
    # Define all help commands to test
    help_tests = [
        # Main help
        (["--help"], "Main help (--help)"),
        (["-h"], "Main help (-h)"),
        (["--version"], "Version flag"),
        
        # Core commands
        (["sync", "--help"], "Sync command help"),
        (["sync", "-h"], "Sync command help (short)"),
        (["config", "--help"], "Config command help"),
        (["config", "-h"], "Config command help (short)"),
        (["auth", "--help"], "Auth command help"),
        (["auth", "-h"], "Auth command help (short)"),
        (["pdf", "--help"], "PDF command help"),
        (["pdf", "-h"], "PDF command help (short)"),
        
        # Subcommands
        (["pdf", "render", "--help"], "PDF render subcommand help"),
        (["pdf", "render", "-h"], "PDF render subcommand help (short)"),
        (["config", "show", "--help"], "Config show subcommand help"),
        (["config", "validate", "--help"], "Config validate subcommand help"),
        (["config", "init", "--help"], "Config init subcommand help"),
        (["auth", "set", "--help"], "Auth set subcommand help"),
        (["auth", "list", "--help"], "Auth list subcommand help"),
        (["auth", "remove", "--help"], "Auth remove subcommand help"),
    ]
    
    # Run all tests
    results = []
    for args, description in help_tests:
        result = test_help_command(args, description)
        results.append(result)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success rate: {passed/total*100:.1f}%")
    
    # Show failed tests
    failed_tests = [r for r in results if not r["success"]]
    if failed_tests:
        print("\n❌ FAILED TESTS:")
        for result in failed_tests:
            print(f"  • {result['description']}")
            if result["stderr"]:
                print(f"    Error: {result['stderr']}")
    
    # Show tests with no output
    no_output_tests = [r for r in results if r["success"] and not r["has_output"]]
    if no_output_tests:
        print("\n⚠️  TESTS WITH NO OUTPUT:")
        for result in no_output_tests:
            print(f"  • {result['description']}")
    
    # Content validation
    print("\n🔍 CONTENT VALIDATION")
    print("-" * 30)
    
    # Check main help content
    main_help_results = [r for r in results if r["command"] == ["--help"]]
    if main_help_results and main_help_results[0]["success"]:
        stdout = main_help_results[0]["stdout"]
        
        # Check for expected content
        checks = [
            ("Buckia mentioned", "Buckia" in stdout or "buckia" in stdout),
            ("Usage shown", "usage:" in stdout.lower()),
            ("Commands listed", "sync" in stdout and "config" in stdout),
            ("Options shown", "--help" in stdout or "--version" in stdout),
        ]
        
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"  {status} {check_name}")
    
    # Check PDF render help content
    pdf_render_results = [r for r in results if r["command"] == ["pdf", "render", "--help"]]
    if pdf_render_results and pdf_render_results[0]["success"]:
        stdout = pdf_render_results[0]["stdout"]
        
        checks = [
            ("Local-only option", "--local-only" in stdout),
            ("Output-dir option", "--output-dir" in stdout),
            ("Required args shown", "HTML_FILE" in stdout or "html" in stdout.lower()),
        ]
        
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"  {status} {check_name}")
    
    # Exit with appropriate code
    if passed == total:
        print("\n🎉 All CLI help tests passed!")
        sys.exit(0)
    else:
        print(f"\n💥 {total - passed} CLI help tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
