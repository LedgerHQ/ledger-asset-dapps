#!/usr/bin/env python3
import logging
import glob
from pathlib import Path

from jsonschema.exceptions import ValidationError
from validation.validators import (
    endlines_validator,
    format_validator,
    run_validations,
    schema_validator,
)

logging.basicConfig(level="INFO")


VALIDATIONS = {
    "json": ("./*/**/*.json", format_validator),
    "endlines": ("./*/**/*.json", endlines_validator),
}

for schema in glob.iglob("./*/*.schema.json", recursive=True):
    schema = Path(schema)
    coin_name = schema.parent.name
    target_name = schema.name.removesuffix(".schema.json")
    VALIDATIONS[f"{coin_name}_{target_name}"] = (
        str(schema.parent / "*" / f"{target_name}.json"),
        schema_validator(str(schema))
    )

if __name__ == "__main__":
    failed = False
    logger = logging.getLogger(__name__)
    for validator_name, (path, validator) in VALIDATIONS.items():
        logger.info("Running validation for %s", validator_name)
        try:
            run_validations(path, validator)
        except ValidationError:
            failed = True
    if failed:
        exit(1)
