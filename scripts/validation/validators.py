#!/usr/bin/env python3
import glob
import json
import logging
from json.decoder import JSONDecodeError
from typing import Callable, Tuple

from jsonschema import ValidationError
from jsonschema.validators import validator_for

logger = logging.getLogger(__name__)


def run_validations(glob_path: str, validator: Callable[[str, str], Tuple[bool, str]]):
    valid, invalid, errors = 0, 0, []
    for filename in glob.iglob(glob_path, recursive=True):
        logger.debug("Validating %s...", filename)
        with open(filename, "r", newline="") as f:
            data = f.read()
        is_valid, error_message = validator(data, filename)
        if is_valid:
            valid += 1
        else:
            invalid += 1
            errors.append({"file": filename, "message": error_message})

    logger.info(f"Result: {valid} valid, {invalid} invalid")
    if invalid:
        for error in errors:
            logger.error(f"Validation error: {error}")
        raise ValidationError(f"Invalid files: {errors}")


def format_validator(data: str, filename: str) -> Tuple[bool, str]:
    try:
        loaded = json.loads(data)
        formatted = json.dumps(loaded, indent=4, sort_keys=True, ensure_ascii=False)
        if formatted != data and (formatted + "\n") != data:
            logger.debug(
                "\tinvalid: File %s is not formatted correctly ; expected: %s",
                filename,
                formatted,
            )
            with open(filename, "w") as f:
                json.dump(loaded, f, indent=4, sort_keys=True, ensure_ascii=False)
            return False, "Not formatted corrected"
    except JSONDecodeError as err:
        logger.debug("\tinvalid: File %s is not a valid json", filename, exc_info=True)
        return False, str(err)
    return True, ""


def endlines_validator(data: str, filename: str) -> Tuple[bool, str]:
    is_valid = "\\r\\n" not in data
    error_message = ""
    if not is_valid:
        error_message = "File has some endlines chars"
        logger.debug("Invalid: File %s has some endlines chars", filename)
    return is_valid, error_message


def schema_validator(schema_path: str):
    with open(schema_path, "r") as f:
        schema = json.load(f)
    validator_class = validator_for(schema)
    validator_class.check_schema(schema)
    validator = validator_class(schema)

    def _inner_validator(data: str, filename: str) -> Tuple[bool, str]:
        try:
            validator.validate(json.loads(data))
            return True, ""
        except ValidationError as err:
            logger.debug(
                "\tinvalid: File %s doesn't match the schema", filename, exc_info=True
            )
            return False, err.message

    return _inner_validator
