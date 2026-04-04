"""Tests for the CLI interface."""
import subprocess
import sys


class TestCLIHelp:
    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, "-m", "briefkit", "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "briefkit" in result.stdout.lower() or "generate" in result.stdout.lower()

    def test_version(self):
        result = subprocess.run(
            [sys.executable, "-m", "briefkit", "--version"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "1.0.0" in result.stdout


class TestCLIPresets:
    def test_presets_command(self):
        result = subprocess.run(
            [sys.executable, "-m", "briefkit", "presets"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "navy" in result.stdout
        assert "ocean" in result.stdout


class TestCLITemplates:
    def test_templates_command(self):
        result = subprocess.run(
            [sys.executable, "-m", "briefkit", "templates"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "briefing" in result.stdout
        assert "report" in result.stdout


class TestCLIConfig:
    def test_config_command(self):
        result = subprocess.run(
            [sys.executable, "-m", "briefkit", "config"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "brand" in result.stdout or "project" in result.stdout
