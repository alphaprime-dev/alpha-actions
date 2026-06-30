#!/usr/bin/env python3
from pathlib import Path
from typing import Annotated

import typer
import yaml

app = typer.Typer(help="Update a dot-separated key in a YAML file.")


class CliError(Exception):
    pass


@app.command()
def main(
    file_path: Annotated[Path, typer.Argument(help="Path to the YAML file to update.")],
    key: Annotated[str, typer.Argument(help="Dot-separated YAML key path, for example image.tag.")],
    value: Annotated[str, typer.Argument(help="Value to write to the YAML key.")],
) -> None:
    try:
        update_yaml(file_path, key, value)
    except (CliError, OSError, yaml.YAMLError) as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1) from exc


def update_yaml(file_path: Path, key_path: str, value: str) -> None:
    keys = parse_key_path(key_path)
    values = load_yaml(file_path)
    changed = update_nested_value(values, keys, value)
    if changed:
        write_yaml(file_path, values)


def parse_key_path(key_path: str) -> list[str]:
    keys = key_path.split(".")
    if not key_path or any(not key for key in keys):
        raise CliError("key must be a non-empty dot-separated path")
    return keys


def load_yaml(file_path: Path) -> dict:
    with file_path.open("r", encoding="utf-8") as values_file:
        values = yaml.safe_load(values_file)
    if not isinstance(values, dict):
        raise CliError("YAML root must be a mapping")
    return values


def update_nested_value(values: dict, keys: list[str], value: str) -> bool:
    cursor = values
    for key in keys[:-1]:
        if not isinstance(cursor, dict) or key not in cursor:
            raise CliError(f'key "{key}" not found in YAML')
        cursor = cursor[key]

    target_key = keys[-1]
    if not isinstance(cursor, dict) or target_key not in cursor:
        raise CliError(f'key "{target_key}" not found in YAML')

    if cursor[target_key] == value:
        return False

    cursor[target_key] = value
    return True


def write_yaml(file_path: Path, values: dict) -> None:
    with file_path.open("w", encoding="utf-8") as values_file:
        yaml.safe_dump(values, values_file, default_flow_style=False, sort_keys=False)


if __name__ == "__main__":
    app()
