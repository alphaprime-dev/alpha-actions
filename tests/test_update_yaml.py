import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "update-yaml.py"


def test_nested_key_update_succeeds(tmp_path):
    """Updates an existing nested key from the command line."""
    # given
    yaml_path = tmp_path / "values.yaml"
    yaml_path.write_text("image:\n  repository: app\n  tag: old\n", encoding="utf-8")

    # when
    result = run_update_yaml(yaml_path, "image.tag", "new")

    # then
    assert result.returncode == 0, result.stderr
    assert yaml_path.read_text(encoding="utf-8") == "image:\n  repository: app\n  tag: new\n"


def test_missing_key_fails(tmp_path):
    """Fails when any key in the requested path is missing."""
    # given
    yaml_path = tmp_path / "values.yaml"
    original_yaml = "image:\n  tag: old\n"
    yaml_path.write_text(original_yaml, encoding="utf-8")

    # when
    result = run_update_yaml(yaml_path, "image.digest", "sha256:abc")

    # then
    assert result.returncode != 0
    assert 'key "digest" not found in YAML' in result.stderr
    assert yaml_path.read_text(encoding="utf-8") == original_yaml


def test_invalid_yaml_fails(tmp_path):
    """Fails when the target file is not valid YAML."""
    # given
    yaml_path = tmp_path / "values.yaml"
    original_yaml = "image: [unterminated\n"
    yaml_path.write_text(original_yaml, encoding="utf-8")

    # when
    result = run_update_yaml(yaml_path, "image.tag", "new")

    # then
    assert result.returncode != 0
    assert "error:" in result.stderr
    assert yaml_path.read_text(encoding="utf-8") == original_yaml


def test_invalid_key_format_fails(tmp_path):
    """Fails when the key path is empty or contains empty segments."""
    # given
    yaml_path = tmp_path / "values.yaml"
    original_yaml = "image:\n  tag: old\n"
    yaml_path.write_text(original_yaml, encoding="utf-8")

    # when
    result = run_update_yaml(yaml_path, "image..tag", "new")

    # then
    assert result.returncode != 0
    assert "key must be a non-empty dot-separated path" in result.stderr
    assert yaml_path.read_text(encoding="utf-8") == original_yaml


def test_unchanged_value_produces_identical_output(tmp_path):
    """Leaves the YAML file byte-for-byte unchanged when the requested value already exists."""
    # given
    yaml_path = tmp_path / "values.yaml"
    original_yaml = "image:\n  tag: current # deployed image\n"
    yaml_path.write_text(original_yaml, encoding="utf-8")

    # when
    result = run_update_yaml(yaml_path, "image.tag", "current")

    # then
    assert result.returncode == 0, result.stderr
    assert yaml_path.read_text(encoding="utf-8") == original_yaml


def test_yaml_key_order_is_preserved(tmp_path):
    """Preserves existing mapping key order when writing an updated YAML file."""
    # given
    yaml_path = tmp_path / "values.yaml"
    yaml_path.write_text(
        "alpha: 1\nimage:\n  repository: app\n  tag: old\nomega: 2\n",
        encoding="utf-8",
    )

    # when
    result = run_update_yaml(yaml_path, "image.tag", "new")

    # then
    assert result.returncode == 0, result.stderr
    assert (
        yaml_path.read_text(encoding="utf-8")
        == "alpha: 1\nimage:\n  repository: app\n  tag: new\nomega: 2\n"
    )


def run_update_yaml(yaml_path: Path, key: str, value: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(yaml_path), key, value],
        check=False,
        capture_output=True,
        text=True,
    )
