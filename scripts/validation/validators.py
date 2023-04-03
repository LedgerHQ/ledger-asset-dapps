#!/usr/bin/env python3
import glob
import json
import logging
import re
from json.decoder import JSONDecodeError
from pathlib import Path
from typing import Callable, Optional, Tuple, List

from eth_utils import to_checksum_address
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
            return False, "Not formatted correctly. Fixed."
    except JSONDecodeError as err:
        logger.debug("\tinvalid: File %s is not a valid json", filename, exc_info=True)
        return False, str(err)
    return True, ""


def endlines_validator(data: str, filename: str) -> Tuple[bool, str]:
    is_valid = "\\r\\n" not in data
    error_message = ""
    if not is_valid:
        error_message = "File has some endlines chars"
        logger.debug("\tinvalid: File %s has some endlines chars", filename)
    return is_valid, error_message


def unique_field_validator(
    field_names: List[str], skip: Optional[Callable] = None
):
    unique = dict()

    def _inner_validator(data: str, filename: str) -> Tuple[bool, str]:
        if skip and skip(data, filename):
            return True, ""

        try:
            json_data = json.loads(data)
        except JSONDecodeError as err:
            logger.debug("\tinvalid: File %s is not a valid json", filename, exc_info=True)
            return False, str(err)
        field_value = next(
            json_data[field_name]
            for field_name in field_names
            if field_name in json_data
        )
        coin_name = Path(filename).parts[0]
        identifier = f"{coin_name}/{field_value}".lower()

        if identifier in unique:
            logger.info(
                "\tinvalid: File %s has the same %s as %s",
                filename,
                field_names,
                unique[identifier],
            )
            return False, f"{field_names} is not unique."
        else:
            unique[identifier] = filename
            return True, ""

    return _inner_validator


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


def eip712_schema_validator(data: str, filename: str) -> Tuple[bool, str]:
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
                f.write(formatted)
            return False, "Not formatted, corrected"
    except JSONDecodeError as err:
        logger.debug("\tinvalid: File %s is not a valid json", filename, exc_info=True)
        return False, str(err)
    return True, ""


def missing_schema_validator():
    coins = set()

    def _inner_validator(data: str, filename: str) -> Tuple[bool, str]:
        parser_path = Path(filename)
        coin_name = parser_path.parts[0]
        if coin_name in coins:
            return True, ""
        coins.add(coin_name)
        target_name = parser_path.name.removesuffix(".json")
        schema_path = parser_path.parent.parent / f"{target_name}.schema.json"
        if schema_path.exists():
            return True, ""
        else:
            return False, f"Missing schema {schema_path}"

    return _inner_validator


def missing_abi_validator(skip: Optional[Callable] = None):
    def _inner_validator(data: str, filename: str) -> Tuple[bool, str]:
        if skip and skip(data, filename):
            return True, ""

        try:
            dapp_addresses = set(
                contract.get("address", "").lower()
                for contract in json.loads(data).get("contracts", [])
            )
            abi_addresses = set(
                p.name.split(".")[0].lower()
                for p in Path(filename).parent.glob("abis/*.abi.json")
            )
            if not dapp_addresses.issubset(abi_addresses):
                return (
                    False,
                    f"Missing ABI for contract {dapp_addresses.difference(abi_addresses)}",
                )
        except Exception as err:
            return False, str(err)
        return True, ""

    return _inner_validator


def abi_filename_validator(data: str, filename: str) -> Tuple[bool, str]:
    lowercase_address_regex = r"^0x[a-f0-9]{40}\.abi\.json$"
    if re.match(lowercase_address_regex, Path(filename).name):
        return True, ""
    else:
        return False, f"ABI filename is not matching {lowercase_address_regex}"


def eip55_address_validator(data: str, filename: str) -> Tuple[bool, str]:
    error = False
    try:
        json_data = json.loads(data)
    except JSONDecodeError as err:
        logger.debug("\tinvalid: File %s is not a valid json", filename, exc_info=True)
        return False, str(err)

    for contract in json_data.get("contracts", []):
        # Address respects EIP55 format
        address = contract.get("address", "")
        expected = to_checksum_address(address)
        is_valid = address == expected
        if not is_valid:
            error = True
            logger.info(
                "\tinvalid: Contract address %s not in eip55 format",
                address,
            )
            contract["address"] = expected
    if error:
        formatted = json.dumps(json_data, indent=4, sort_keys=True, ensure_ascii=False)
        with open(filename, "w") as f:
            f.write(formatted)
        return False, "Some addresses not correctly formatted, fixing..."

    return True, ""


def contract_matching_validator(skip: Optional[Callable] = None):
    def _inner_validator(data: str, filename: str) -> Tuple[bool, str]:
        if skip and skip(data, filename):
            return True, ""

        error = False
        try:
            target_path = Path(filename)
            target_data = json.loads(data)
        except JSONDecodeError as err:
            logger.debug("\tinvalid: File %s is not a valid json", filename, exc_info=True)
            return False, str(err)

        for contract in target_data.get("contracts", []):
            logger.info(
                "\tchecking contract %s...",
                contract['address'],
            )
            abi_path = target_path.parent / "abis" / f"{contract['address'].lower()}.abi.json"
            abi_data = json.load(abi_path.open())

            target_functions = {parser["functionName"]: parser for parser in contract.get("parsers", [])}
            abi_functions = {function["name"]: function for function in abi_data if function["type"] == "function"}

            for name, function in target_functions.items():
                if name not in abi_functions:
                    error = True
                    logger.info(
                        "\tinvalid: Function %s not defined in ABI",
                        function,
                    )
                    continue

                logger.info(
                    "\tchecking function %s...",
                    name,
                )

                function_args = {arg["name"] for arg in function.get("arguments", [])}
                screen_args = {arg["name"] for arg in function.get("screen", []) if arg["label"] != "Function"}
                if not screen_args <= function_args:
                    error = True
                    logger.info(
                        "\tinvalid: Screen %s not matching function arguments %s.",
                        function_args,
                        screen_args,
                    )

        if error:
            return False, f"Errors found on file content"

        return True, ""

    return _inner_validator
