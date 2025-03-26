#!/usr/bin/env python3
import glob
import logging
from pathlib import Path
from typing import Callable, Iterable, Tuple

from jsonschema.exceptions import ValidationError

from validation.validators import (
    abi_filename_validator,
    eip712_schema_validator,
    endlines_validator,
    format_validator,
    missing_abi_validator,
    run_validations,
    check_duplicate_contract,
    schema_validator,
    unique_field_validator,
    contract_matching_validator,
    missing_schema_validator,
    eip55_address_validator,
    check_duplicate_plugin,
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
            schema_validator(str(schema_path)),
        )


SCHEMA_VALIDATORS = {
    validator_name: validator
    for validator_name, validator in schema_validator_generator()
}

VALIDATORS = {
    "json": ("./*/**/*.json", format_validator),
    "endlines": ("./*/**/*.json", endlines_validator),
    "eip712_schema": ("./*/**/eip712.json", eip712_schema_validator),
    "abis_format": ("./*/**/abis/*.json", abi_filename_validator),
    "unique_id": ("./*/**/parsers.json", unique_field_validator(["id"])),
    "parsers_abi_not_missing": ("./*/**/parsers.json", missing_abi_validator),
    "b2c_abi_not_missing": ("./*/**/b2c.json", missing_abi_validator),
    "parsers_schema_not_missing": ("./*/**/parsers.json", missing_schema_validator()),
    "b2c_schema_not_missing": ("./*/**/b2c.json", missing_schema_validator()),
    "eip55_parser": ("./*/**/parsers.json", eip55_address_validator),
    "contract_matching": ("./*/**/parsers.json", contract_matching_validator),
    **SCHEMA_VALIDATORS,
}

if __name__ == "__main__":
    failed = False
    logging.basicConfig(level=logging.INFO, format='%(message)s', force=True)
    logger = logging.getLogger(__name__)

    try:
        logger.info("Running duplicate contract check")
        check_duplicate_contract("./*/**/b2c.json")
        logger.info("Running duplicate plugin check")
        check_duplicate_plugin("./*/**/b2c.json")
    except ValidationError:
        failed = True

    for validator_name, (path, validator) in VALIDATORS.items():
        logger.info("Running validation for %s", validator_name)
        try:
            run_validations(path, validator)
        except ValidationError:
            failed = True

    if failed:
        exit(1)
