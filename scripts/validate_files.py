#!/usr/bin/env python3
import logging
import glob
from pathlib import Path
from typing import Callable, Iterable, Tuple

from jsonschema.exceptions import ValidationError
from validation.validators import (
    endlines_validator,
    format_validator,
    run_validations,
    schema_validator,
)

logging.basicConfig(level="INFO")


def schema_validator_generator() -> Iterable[Tuple[str, Tuple[str, Callable]]]:
    json_schema_paths = "./*/*.schema.json"
    for json_schema in glob.iglob(json_schema_paths, recursive=True):
        schema_path = Path(json_schema)
        coin_name = schema_path.parent.name
        target_name = schema_path.name.removesuffix(".schema.json")
        yield f"{coin_name}_{target_name}", (
            str(schema_path.parent / "*" / f"{target_name}.json"),
            schema_validator(str(schema_path))
        )


SCHEMA_VALIDATORS = {
    validator_name: validator for validator_name, validator in schema_validator_generator()
}


VALIDATORS = {
    "json": ("./*/**/*.json", format_validator),
    "endlines": ("./*/**/*.json", endlines_validator),
    **SCHEMA_VALIDATORS
}


if __name__ == "__main__":
    failed = False
    logger = logging.getLogger(__name__)
    for validator_name, (path, validator) in VALIDATORS.items():
        logger.info("Running validation for %s", validator_name)
        try:
            run_validations(path, validator)
        except ValidationError:
            failed = True
    if failed:
        exit(1)
