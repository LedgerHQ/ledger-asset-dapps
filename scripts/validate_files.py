#!/usr/bin/env python3
import logging

from jsonschema.exceptions import ValidationError
from validation.validators import (
    endlines_validator,
    format_validator,
    run_validations,
    schema_validator,
)

logging.basicConfig(level="INFO")

VALIDATIONS = {
    "json": ("./ethereum/**/*.json", format_validator, endlines_validator),
    "contracts": (
        "./ethereum/*/b2c.json",
        schema_validator("./ethereum/schema.json")
    )
}


if __name__ == "__main__":
    failed = False
    logger = logging.getLogger(__name__)
    for name, args in VALIDATIONS.items():
        logger.info("Running validation for %s", name)
        try:
            run_validations(*args)
        except ValidationError:
            failed = True
    if failed:
        exit(1)
