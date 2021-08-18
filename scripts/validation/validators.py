#!/usr/bin/env python3
import glob
import json
import logging
from json.decoder import JSONDecodeError

from jsonschema import ValidationError
from jsonschema.validators import validator_for

logger = logging.getLogger(__name__)


def run_validations(glob_path: str, *validators):
    result = {True: [], False: []}
    for fname, is_valid in _validate_json_files(glob_path, *validators):
        result[is_valid].append(fname)
    logger.info("Result: %s valid, %s invalid", len(result[True]), len(result[False]))
    if result[False]:
        logger.error("Invalid files: %s", result[False])
        raise ValidationError(f"Invalid files: {result[False]}")


def format_validator(data: str, fname) -> bool:
    try:
        loaded = json.loads(data)
        formatted = json.dumps(loaded, indent=4, sort_keys=True, ensure_ascii=False)
        if formatted != data and (formatted + "\n") != data:
            logger.debug(
                "\tinvalid: File %s is not formatted correctly ; expected: %s",
                fname,
                formatted,
            )
            with open(fname, "w") as f:
                json.dump(loaded, f, indent=4, sort_keys=True, ensure_ascii=False)
            return False
    except JSONDecodeError:
        logger.debug("\tinvalid: File %s is not a valid json", fname, exc_info=True)
        return False
    return True


def endlines_validator(data: str, fname) -> bool:
    return "\\r\\n" not in data


def schema_validator(schema_path: str):
    with open(schema_path, "r") as f:
        schema = json.load(f)
    validator_class = validator_for(schema)
    validator_class.check_schema(schema)
    validator = validator_class(schema)

    def _inner_validator(data, fname) -> bool:
        try:
            validator.validate(json.loads(data))
            return True
        except ValidationError:
            logger.debug(
                "\tinvalid: File %s doesn't match the schema", fname, exc_info=True
            )
            return False

    return _inner_validator


def _validate_json_files(glob_path: str, *validators):
    for fname in glob.iglob(glob_path, recursive=True):
        logger.debug("Validating %s...", fname)
        with open(fname, "r", newline="") as f:
            data = f.read()
        is_valid = all([validator(data, fname) for validator in validators])
        yield fname, is_valid
