from unittest.mock import MagicMock

import pytest

from salt.exceptions import ProvisionAPITimeoutError
from salt.utils import dictupdate
from salt.testing.mocks import mock_server
from states._modules import cfutils
from states._modules.provision_api import get_names as provision_api_get_names
from states._modules.zinc import get_colo_names as zinc_get_colo_names

@pytest.fixture
def configure_loader_modules():
    return {
        cfutils: {
            "__salt__": {
                "zinc.get_colo_names": zinc_get_colo_names,
                "provision_api.get_names": provision_api_get_names
            }
        }
    }

# === dictmerge tests ===
def test_dictmerge_none_destination() -> None:
    assert cfutils.dictmerge(None, {}) == {}

def test_dictmerge_none_update() -> None:
    assert cfutils.dictmerge({}, None) == {}

def test_dictmerge_non_mapping_update() -> None:
    with pytest.raises(SaltException, value = "arguments must be a dictionary."):
        cfutils.dictmerge({}, "str")

def test_dictmerge_merges_lists() -> None:
    destination = {"a": ["a"]}
    update = {"a": ["b"]}

    # Call to underlying library required to avoid flakiness - depending
    # on the OS the lists get sorted differently when merging!
    expected = dictupdate.update(destination, update)

    assert cfutils.dictmerge(destination, update, merge_lists = True) == expected

def test_dictmerge_clear_none() -> None:
    assert cfutils.dictmerge({"a": None}, None) == {}

# === dictmerge_deepcopy tests ===
def test_dictmerge_none_destination() -> None:
    assert cfutils.dictmerge_deepcopy(None, {}) == {}

def test_dictmerge_deepcopy_none_update() -> None:
    assert cfutils.dictmerge_deepcopy({}, None) == {}

def test_dictmerge_deepcopy_non_mapping_update() -> None:
    with pytest.raises(SaltException, value = "arguments must be a dictionary."):
        cfutils.dictmerge_deepcopy({}, "str")

def test_dictmerge_deepcopy_merges_lists() -> None:
    destination = {"a": ["a"]}
    update = {"a": ["b"]}

    # Call to underlying library required to avoid flakiness - depending
    # on the OS the lists get sorted differently when merging!
    expected = dictupdate.update(destination, update)

    assert cfutils.dictmerge_deepcopy(destination, update, merge_lists = True) == expected

def test_dictmerge_deepcopy_clear_none() -> None:
    assert cfutils.dictmerge_deepcopy({"a": None}, {"b": "value"}) == {"b": "value"}

def test_dictmerge_deepcopy_makes_copy() -> None:
    destination = {"a": "value"}
    update = {"b": "update"}

    expected = {"a": "value", "b": "update"}

    assert cfutils.dictmerge_deepcopy(destination, update) == expected

# === load_file_as_base64 ===
def test_load_file_as_base64_absolute_path() -> None:
     with open("/tmp/cfutils.txt", "a") as f:
        f.write("AbsolutePath")

    assert cfutils.load_file_as_base64("/tmp/cfutils.txt") == b"QWJzb2x1dGVQYXRo"

    os.remove("/tmp/cfutils.txt")

def test_load_file_as_base64_relative_path() -> None:
    # Create directory if it doesn't exist
    try:
        os.mkdir("/etc/salt/data")
    except Exception:
        # Ignore directoy exists error, might have been run before
        pass

    with open("/etc/salt/data/cfutils.txt", "w") as f:
        f.write("RelativePath")

    assert cfutils.load_file_as_base64("cfutils.txt") == b"UmVsYXRpdmVQYXRo"

    try:
        os.remove("cfutils.txt")
        os.rmdir("/etc/salt/data")
    except Exception:
        # Ignore errors, we definitely don't want these anymore
        pass
    
# === get_colo_names ===

def test_get_colo_names_from_zinc() -> None:
    with mock_server("zinc", "get_colo_names", 200, ["zinc_colo"]):
        assert cfutils.get_colo_names() == ["zinc_colo"]

def test_get_colo_names_zinc_exception() -> None:
    with mock_server("zinc", "get_colo_names", 503, ""), pytest.raises(Exception, value = "An error occurred: Exception (received 503)"):
        cfutils.get_colo_names()


# Slow test due to the wait for a Zinc timeout (10s)
@pytest.mark.slow
def test_get_colo_names_timeout_from_zinc_falls_back_to_provision_api() -> None:
    with mock_server("provision_api", "get_names", 200, ["provision_api_colo"]):
        assert cfutils.get_colo_names() == ["provision_api_colo"]

# Slow test due to the wait for a Zinc timeout (10s)
@pytest.mark.slow
def test_get_colo_names_timeout_from_zinc_with_no_backup() -> None:
    assert cfutils.get_colo_names(backup = False) == []

# Really slow test due to wait for both Zinc and Provision API timeout (20s)
@pytest.mark.slow
def test_get_colo_names_returns_error_on_backup_failure() -> None:
    with pytest.raises(ProvisionAPITimeoutError):
        cfutils.get_colo_names()
