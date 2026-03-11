"""
Unit tests for setup wizard components: bootstrap, profiles, setup command.

Tests:
  - Bootstrap: prerequisite checks, env generation, env reading
  - Profiles: profile lookup, listing, data integrity
  - Setup command: registration, --check, --profile, --env-only
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vitruvyan_core.core.platform.package_manager.bootstrap import (
    BootstrapReport,
    DEFAULT_INFRA_PORTS,
    ENV_TEMPLATE,
    PrereqResult,
    _parse_compose_ports,
    check_docker,
    check_docker_compose,
    check_port,
    check_python,
    generate_env_file,
    read_existing_env,
    run_all_checks,
)
from vitruvyan_core.core.platform.package_manager.profiles import (
    ALL_PROFILES,
    CUSTOM,
    FINANCE,
    FULL,
    MINIMAL,
    STANDARD,
    InstallProfile,
    get_profile,
    list_profiles,
)


# ══════════════════════════════════════════════════════════════════
# Bootstrap tests
# ══════════════════════════════════════════════════════════════════


class TestPrereqResult:
    def test_passed_check(self):
        r = PrereqResult("Docker", True, "running")
        assert r.passed
        assert r.required

    def test_failed_required(self):
        r = PrereqResult("Docker", False, "not found", required=True)
        assert not r.passed
        assert r.required

    def test_failed_optional(self):
        r = PrereqResult("Redis", False, "not running", required=False)
        assert not r.passed
        assert not r.required


class TestBootstrapReport:
    def test_all_required_passed(self):
        report = BootstrapReport(checks=[
            PrereqResult("A", True, "ok", required=True),
            PrereqResult("B", True, "ok", required=True),
            PrereqResult("C", False, "down", required=False),  # optional
        ])
        assert report.all_required_passed

    def test_required_failed(self):
        report = BootstrapReport(checks=[
            PrereqResult("A", True, "ok", required=True),
            PrereqResult("B", False, "missing", required=True),
        ])
        assert not report.all_required_passed

    def test_empty_report(self):
        report = BootstrapReport()
        assert report.all_required_passed  # vacuously true

    def test_summary_lines(self):
        report = BootstrapReport(checks=[
            PrereqResult("Docker", True, "running", required=True),
            PrereqResult("Redis", False, "down", required=False),
        ])
        lines = report.summary_lines
        assert len(lines) == 2
        assert "✅" in lines[0]
        assert "⚠️" in lines[1]


class TestCheckPython:
    def test_python_passes(self):
        """Current Python should be >= 3.10 (test environment)."""
        result = check_python()
        assert result.name == "Python"
        assert result.passed


class TestCheckDocker:
    @patch("vitruvyan_core.core.platform.package_manager.bootstrap.shutil.which")
    def test_docker_not_found(self, mock_which):
        mock_which.return_value = None
        result = check_docker()
        assert not result.passed
        assert "not found" in result.message

    @patch("vitruvyan_core.core.platform.package_manager.bootstrap.subprocess.run")
    @patch("vitruvyan_core.core.platform.package_manager.bootstrap.shutil.which")
    def test_docker_running(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/docker"
        mock_run.return_value = MagicMock(returncode=0)
        result = check_docker()
        assert result.passed

    @patch("vitruvyan_core.core.platform.package_manager.bootstrap.subprocess.run")
    @patch("vitruvyan_core.core.platform.package_manager.bootstrap.shutil.which")
    def test_docker_not_responding(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/docker"
        mock_run.return_value = MagicMock(returncode=1)
        result = check_docker()
        assert not result.passed


class TestCheckDockerCompose:
    @patch("vitruvyan_core.core.platform.package_manager.bootstrap.subprocess.run")
    def test_compose_available(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="Docker Compose version v2.24.0")
        result = check_docker_compose()
        assert result.passed

    @patch("vitruvyan_core.core.platform.package_manager.bootstrap.subprocess.run")
    def test_compose_not_available(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = check_docker_compose()
        assert not result.passed


class TestCheckPort:
    def test_closed_port(self):
        """Port 19999 should not be in use."""
        assert not check_port(19999)


class TestEnvFile:
    def test_generate_new_env(self):
        with tempfile.NamedTemporaryFile(suffix=".env", delete=False) as f:
            env_path = Path(f.name)
        try:
            # Remove the file so generate_env_file creates it fresh
            env_path.unlink()
            result = generate_env_file(env_path, {"OPENAI_API_KEY": "sk-test123"})
            assert result == env_path
            content = env_path.read_text()
            assert "OPENAI_API_KEY=sk-test123" in content
            assert "POSTGRES_USER=vitruvyan" in content  # default
        finally:
            env_path.unlink(missing_ok=True)

    def test_preserve_existing_values(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("POSTGRES_USER=custom_user\nMY_EXTRA=hello\n")
            env_path = Path(f.name)
        try:
            generate_env_file(env_path)
            content = env_path.read_text()
            assert "POSTGRES_USER=custom_user" in content
            assert "MY_EXTRA=hello" in content
        finally:
            env_path.unlink(missing_ok=True)

    def test_read_existing_env(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("KEY1=value1\n# comment\nKEY2=value2\n\n")
            env_path = Path(f.name)
        try:
            result = read_existing_env(env_path)
            assert result == {"KEY1": "value1", "KEY2": "value2"}
        finally:
            env_path.unlink(missing_ok=True)

    def test_read_nonexistent_env(self):
        result = read_existing_env(Path("/nonexistent/.env"))
        assert result == {}


class TestRunAllChecks:
    @patch("vitruvyan_core.core.platform.package_manager.bootstrap.subprocess.run")
    @patch("vitruvyan_core.core.platform.package_manager.bootstrap.shutil.which")
    def test_runs_all_checks(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/docker"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="/home/user/vitruvyan-core\n",
        )
        # Mock vitruvyan_core dir exists
        with patch("vitruvyan_core.core.platform.package_manager.bootstrap.Path.is_dir", return_value=True):
            report = run_all_checks()
        assert len(report.checks) >= 4  # git, python, docker, compose + infra


class TestComposePortParsing:
    def test_parses_custom_ports(self):
        """Verify _parse_compose_ports reads host ports from docker-compose.yml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            compose_dir = Path(tmpdir) / "infrastructure" / "docker"
            compose_dir.mkdir(parents=True)
            compose_file = compose_dir / "docker-compose.yml"
            compose_file.write_text(
                "services:\n"
                "  redis:\n"
                "    ports:\n"
                "      - '9379:6379'\n"
                "  postgres:\n"
                "    ports:\n"
                "      - '9432:5432'\n"
                "  qdrant:\n"
                "    ports:\n"
                "      - '9333:6333'\n"
                "      - '9334:6334'\n"
            )
            # Also create vitruvyan_core dir so find_repo_root would work
            (Path(tmpdir) / "vitruvyan_core").mkdir()
            ports = _parse_compose_ports(repo_root=Path(tmpdir))
            assert ports["redis"] == 9379
            assert ports["postgres"] == 9432
            assert ports["qdrant_rest"] == 9333
            assert ports["qdrant_grpc"] == 9334

    def test_falls_back_to_defaults(self):
        """Without compose file, should return default ports."""
        ports = _parse_compose_ports(repo_root=Path("/nonexistent"))
        assert ports == DEFAULT_INFRA_PORTS


# ══════════════════════════════════════════════════════════════════
# Profile tests
# ══════════════════════════════════════════════════════════════════


class TestProfiles:
    def test_all_profiles_defined(self):
        assert len(ALL_PROFILES) == 5

    def test_profile_names_unique(self):
        names = [p.name for p in ALL_PROFILES]
        assert len(names) == len(set(names))

    def test_get_profile_by_name(self):
        for p in ALL_PROFILES:
            result = get_profile(p.name)
            assert result is not None
            assert result.name == p.name

    def test_get_profile_unknown(self):
        assert get_profile("nonexistent") is None

    def test_list_profiles_order(self):
        profiles = list_profiles()
        assert profiles[0].name == "minimal"
        assert profiles[-1].name == "custom"

    def test_minimal_has_no_packages(self):
        assert MINIMAL.packages == []

    def test_standard_includes_neural(self):
        assert "neural_engine" in STANDARD.packages

    def test_finance_includes_vertical(self):
        assert "vertical_finance" in FINANCE.packages
        assert "neural_engine" in FINANCE.packages

    def test_full_includes_all(self):
        assert "neural_engine" in FULL.packages
        assert "mcp" in FULL.packages
        assert "edge_dse" in FULL.packages
        assert "vertical_finance" in FULL.packages

    def test_custom_starts_empty(self):
        assert CUSTOM.packages == []

    def test_profile_summary(self):
        s = MINIMAL.summary
        assert "Minimal" in s
        assert "~2 GB" in s

    def test_finance_requires_openai_key(self):
        assert "OPENAI_API_KEY" in FINANCE.env_keys


class TestInstallProfile:
    def test_frozen_fields(self):
        p = InstallProfile(
            name="test",
            label="Test",
            description="Test profile",
            packages=["pkg1"],
            size_estimate="~1 GB",
        )
        assert p.name == "test"
        assert p.packages == ["pkg1"]


# ══════════════════════════════════════════════════════════════════
# Setup command registration test
# ══════════════════════════════════════════════════════════════════


class TestSetupRegistration:
    def test_register_adds_setup_parser(self):
        """Verify 'vit setup' is registered as a valid subcommand."""
        import argparse
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")

        from vitruvyan_core.core.platform.update_manager.cli.commands.setup import (
            register_setup_command,
        )
        register_setup_command(subparsers)

        # Parse valid setup commands
        args = parser.parse_args(["setup", "--check"])
        assert args.check is True

        args = parser.parse_args(["setup", "--profile", "minimal"])
        assert args.profile == "minimal"

        args = parser.parse_args(["setup", "--env-only"])
        assert args.env_only is True

        args = parser.parse_args(["setup", "-y"])
        assert args.yes is True

    def test_check_only_succeeds(self):
        """vit setup --check should run checks and return 0 or 1."""
        from vitruvyan_core.core.platform.update_manager.cli.commands.setup import (
            _run_checks_only,
        )
        # Just verify it runs without error (result depends on environment)
        result = _run_checks_only()
        assert result in (0, 1)

    def test_profile_minimal_no_install(self):
        """Minimal profile has no packages — should return 0 immediately."""
        from vitruvyan_core.core.platform.update_manager.cli.commands.setup import (
            _run_with_profile,
        )
        result = _run_with_profile(MINIMAL, skip_confirm=True)
        assert result == 0
