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
    "json": ("./*/**/*.json", format_validator, endlines_validator),
    "eth_b2c": (
        "./ethereum/*/b2c.json",
        schema_validator("./ethereum/b2c.schema.json")
    ),
    "eth_parsers": (
        "./ethereum/*/parsers.json",
        schema_validator("./ethereum/parsers.schema.json")
    ),
    "eth_ropsten_b2c": (
        "./ethereum_ropsten/*/b2c.json",
        schema_validator("./ethereum_ropsten/b2c.schema.json")
    ),
    "eth_ropsten_parsers": (
        "./ethereum_ropsten/*/parsers.json",
        schema_validator("./ethereum_ropsten/parsers.schema.json")
    ),
    "eth_goerli_b2c": (
        "./ethereum_goerli/*/b2c.json",
        schema_validator("./ethereum_goerli/b2c.schema.json")
    ),
    "eth_goerli_parsers": (
        "./ethereum_goerli/*/parsers.json",
        schema_validator("./ethereum_goerli/parsers.schema.json")
    ),
    "bsc_b2c": (
        "./bsc/*/b2c.json",
        schema_validator("./bsc/b2c.schema.json")
    ),
    "polygon": (
        "./polygon/*/b2c.json",
        schema_validator("./polygon/b2c.schema.json")
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
