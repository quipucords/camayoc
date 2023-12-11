from copy import deepcopy
from pathlib import Path
from unittest import mock

import pytest
import yaml
from pydantic import ValidationError

import camayoc.config
from camayoc.config import get_config
from camayoc.config import get_settings

EXAMPLE_CONFIG_PATH = Path(__file__).parent / "../example_config.yaml"
with open(EXAMPLE_CONFIG_PATH) as fh:
    EXAMPLE_CONFIG = yaml.load(fh, Loader=yaml.FullLoader)

# FIXME: this should be an enum
SOURCE_TYPES = ("network", "satellite", "vcenter")


@pytest.fixture
def example_config():
    return deepcopy(EXAMPLE_CONFIG)


def test_read_example_config():
    settings = get_settings(path=EXAMPLE_CONFIG_PATH)
    assert settings.quipucords_server


def test_invalid_missing_section(tmp_path, example_config):
    config_file = tmp_path / "config.yaml"
    example_config.pop("quipucords_server")
    with open(config_file, "w") as fh:
        yaml.dump(data=example_config, stream=fh)

    with pytest.raises(ValidationError):
        get_settings(config_file)


@pytest.mark.parametrize("option", ("credentials", "sources", "scans"))
def test_invalid_not_unique_names(tmp_path, example_config, option):
    config_file = tmp_path / "config.yaml"
    example_config[option].append(example_config[option][0])
    with open(config_file, "w") as fh:
        yaml.dump(data=example_config, stream=fh)

    with pytest.raises(ValidationError):
        get_settings(config_file)


def test_invalid_non_existing_credential(tmp_path, faker, example_config):
    config_file = tmp_path / "config.yaml"
    new_source = {
        "hosts": [faker.ipv4()],
        "name": faker.name(),
        "type": "network",
        "credentials": [faker.name()],
    }
    example_config["sources"].append(new_source)
    with open(config_file, "w") as fh:
        yaml.dump(data=example_config, stream=fh)

    with pytest.raises(ValidationError):
        get_settings(config_file)


def test_invalid_non_existing_source(tmp_path, faker, example_config):
    config_file = tmp_path / "config.yaml"
    new_scan = {"name": faker.name(), "sources": [faker.name()]}
    example_config["scans"].append(new_scan)
    with open(config_file, "w") as fh:
        yaml.dump(data=example_config, stream=fh)

    with pytest.raises(ValidationError):
        get_settings(config_file)


@pytest.mark.parametrize("stype", SOURCE_TYPES)
def test_invalid_source_credential_type_mismatch(tmp_path, faker, example_config, stype):
    config_file = tmp_path / "config.yaml"
    new_type = faker.random_element([_ for _ in SOURCE_TYPES if _ != stype])
    source = faker.random_element(
        [source for source in example_config.get("sources") if source.get("type") == stype]
    )
    credential_name = faker.random_element(source.get("credentials"))
    credential = faker.random_element(
        [
            credential
            for credential in example_config.get("credentials")
            if credential.get("name") == credential_name
        ]
    )
    credential["type"] = new_type
    if new_type in ("satellite", "vcenter", "openshift") and not credential.get("password"):
        credential["password"] = faker.password()
    with open(config_file, "w") as fh:
        yaml.dump(data=example_config, stream=fh)

    with pytest.raises(ValidationError):
        get_settings(config_file)


def test_get_config_backward_compatibility():
    global_settings = get_settings(path=EXAMPLE_CONFIG_PATH)
    with mock.patch.object(camayoc.config, "settings", global_settings):
        settings = get_config()
        assert "qpc" in settings
        assert "quipucords_server" not in settings
