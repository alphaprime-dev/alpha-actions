import os
import subprocess
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "commit-manifest.sh"


@pytest.mark.parametrize("concurrent_push", [False, True])
def test_publish_preserves_remote_changes(tmp_path, concurrent_push):
    """Publishes the manifest while preserving another deployment on the remote branch."""
    # Given
    remote, checkout, other = prepare_repositories(tmp_path)
    if concurrent_push:
        (other / "other.yaml").write_text("tag: other-release\n")
        git(other, "add", ".")
        git(other, "commit", "-m", "Deploy another service")
        git(other, "push", "origin", "gke")
    (checkout / "values.yaml").write_text("tag: new\n")

    # When
    result = publish(checkout)

    # Then
    assert result.returncode == 0, result.stderr
    assert git(remote, "show", "gke:values.yaml") == "tag: new"
    expected_other = "tag: other-release" if concurrent_push else "tag: old"
    assert git(remote, "show", "gke:other.yaml") == expected_other
    assert git(checkout, "status", "--porcelain") == ""


def test_unchanged_manifest_does_not_commit(tmp_path):
    """Leaves branch history unchanged when the manifest already has the desired value."""
    # Given
    remote, checkout, _ = prepare_repositories(tmp_path)
    original_head = git(remote, "rev-parse", "gke")

    # When
    result = publish(checkout)

    # Then
    assert result.returncode == 0, result.stderr
    assert git(remote, "rev-parse", "gke") == original_head
    assert git(checkout, "rev-parse", "HEAD") == original_head


def test_conflicting_deployment_fails_without_overwriting_remote(tmp_path):
    """Fails and aborts the rebase when another deployment changes the same image tag."""
    # Given
    remote, checkout, other = prepare_repositories(tmp_path)
    (other / "values.yaml").write_text("tag: competing\n")
    git(other, "add", ".")
    git(other, "commit", "-m", "Deploy competing image")
    git(other, "push", "origin", "gke")
    (checkout / "values.yaml").write_text("tag: new\n")

    # When
    result = publish(checkout)

    # Then
    assert result.returncode != 0
    assert "Manifest update conflicts" in result.stderr
    assert git(remote, "show", "gke:values.yaml") == "tag: competing"
    assert git(checkout, "status", "--porcelain") == ""
    assert not (checkout / ".git" / "rebase-merge").exists()


def test_rejected_push_stops_after_five_attempts(tmp_path):
    """Fails after five rejected pushes and leaves the remote manifest unchanged."""
    # Given
    remote, checkout, _ = prepare_repositories(tmp_path)
    hook = remote / "hooks" / "pre-receive"
    hook.write_text("#!/bin/sh\necho rejected >> attempts\nexit 1\n")
    hook.chmod(0o755)
    (checkout / "values.yaml").write_text("tag: new\n")

    # When
    result = publish(checkout)

    # Then
    assert result.returncode != 0
    assert "after 5 attempts" in result.stderr
    assert (remote / "attempts").read_text().splitlines() == ["rejected"] * 5
    assert git(remote, "show", "gke:values.yaml") == "tag: old"


def prepare_repositories(tmp_path):
    remote = tmp_path / "remote.git"
    checkout = tmp_path / "checkout"
    other = tmp_path / "other"
    git(tmp_path, "init", "--bare", str(remote))
    git(tmp_path, "clone", str(remote), str(other))
    git(other, "config", "user.name", "Test")
    git(other, "config", "user.email", "test@example.com")
    git(other, "switch", "-c", "gke")
    (other / "values.yaml").write_text("tag: old\n")
    (other / "other.yaml").write_text("tag: old\n")
    git(other, "add", ".")
    git(other, "commit", "-m", "Initial manifests")
    git(other, "push", "origin", "gke")
    # Match actions/checkout's shallow history to exercise the deployed rebase behavior.
    git(tmp_path, "clone", "--depth=1", "--branch=gke", remote.as_uri(), str(checkout))
    return remote, checkout, other


def publish(checkout):
    return subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        cwd=checkout,
        env={
            **os.environ,
            "FILE_PATH": "values.yaml",
            "TARGET_BRANCH": "gke",
            "COMMIT_MESSAGE": "Deploy cluster-ops",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
        },
        capture_output=True,
        text=True,
        timeout=30,
    )


def git(cwd, *args):
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull},
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
