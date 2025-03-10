"""Tests for the validators module."""

import pytest


@pytest.mark.parametrize("shortcut", ["excel", "excel_tab", "unix_dialect"])
def test_shortcut_dialects_roundtrip(shortcut):
    """Test that the shortcut dialects roundtrip to the actual dialects."""
    import csv

    from csvy.validators import CSVDialectValidator

    validator = getattr(CSVDialectValidator, shortcut)()
    dialect = validator.to_dialect()
    actual = getattr(csv, shortcut)()

    assert dialect.delimiter == actual.delimiter
    assert dialect.doublequote == actual.doublequote
    assert dialect.escapechar == actual.escapechar
    assert dialect.lineterminator == actual.lineterminator
    assert dialect.quotechar == actual.quotechar
    assert dialect.skipinitialspace == actual.skipinitialspace


def test_register_validator(validators_registry):
    """Test that we can register a new validator."""
    from pydantic import BaseModel

    from csvy.validators import register_validator

    @register_validator("my_validator")
    class MyValidator(BaseModel):
        pass

    assert validators_registry["my_validator"] == MyValidator


def test_register_validator_duplicate(validators_registry):
    """Test that we cannot register a validator with the same name."""
    from pydantic import BaseModel

    from csvy.validators import register_validator

    # With overwriting, we should not raise an error.
    name = "my_validator"

    @register_validator(name)
    class _(BaseModel):
        pass

    # Without overwriting, we should raise an error.
    with pytest.raises(ValueError):

        @register_validator(name)
        class _(BaseModel):  # type: ignore [no-redef]
            pass

    # With overwriting, we should not raise an error,
    # and the validator should be overwritten.
    @register_validator(name, overwrite=True)
    class MyNewOverwritingValidator(BaseModel):
        pass

    assert validators_registry[name] == MyNewOverwritingValidator


def test_register_validator_not_base_model(validators_registry):
    """Test that we cannot register a validator that is not a BaseModel."""
    from csvy.validators import register_validator

    with pytest.raises(TypeError):

        @register_validator("not_base_model")  # type: ignore [arg-type]
        class _:
            pass


def test_validate_read(validators_registry):
    """Test that we can run validators on the header."""
    from pydantic import BaseModel, PositiveInt

    from csvy.validators import register_validator, validate_read

    @register_validator("my_validator")
    class MyValidator(BaseModel):
        value: PositiveInt

    header = {"author": "Gandalf", "my_validator": {"value": 42}}
    validated_header = validate_read(header)

    assert isinstance(validated_header["my_validator"], MyValidator)
    assert validated_header["my_validator"].value == 42
    assert validated_header["author"] == header["author"]


def test_validate_read_missing(validators_registry):
    """Test that we can run validators on the header."""
    from pydantic import BaseModel, PositiveInt, ValidationError

    from csvy.validators import register_validator, validate_read

    @register_validator("my_validator")
    class _(BaseModel):
        value: PositiveInt

    header = {"author": "Gandalf", "my_validator": {}}

    with pytest.raises(ValidationError):
        validate_read(header)


def test_validate_write(validators_registry):
    """Test that we can create the header using the validators."""
    from pydantic import BaseModel, PositiveInt

    from csvy.validators import register_validator, validate_read, validate_write

    @register_validator("my_validator")
    class _(BaseModel):
        value: PositiveInt

    header = {"author": "Gandalf", "my_validator": {"value": 42}}
    validated_header = validate_read(header)
    new_header = validate_write(validated_header)

    assert new_header == header
