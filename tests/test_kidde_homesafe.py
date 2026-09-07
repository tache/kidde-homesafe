"""Tests for the kidde_homesafe API wrapper."""

import dataclasses

import pytest

from kidde_homesafe import (
    KiddeClient,
    KiddeClientAuthError,
    KiddeCommand,
    KiddeDataset,
    _dict_by_ids,
)

# MARK: - _dict_by_ids


def test_dict_by_ids_keys_by_id() -> None:
    """Items are rekeyed by their "id" field."""
    items = [{"id": 7, "label": "kitchen"}, {"id": 9, "label": "hall"}]

    assert _dict_by_ids(items) == {
        7: {"id": 7, "label": "kitchen"},
        9: {"id": 9, "label": "hall"},
    }


def test_dict_by_ids_accepts_empty_list() -> None:
    """An empty list is not a duplicate-ID error."""
    assert _dict_by_ids([]) == {}


def test_dict_by_ids_rejects_duplicate_ids() -> None:
    """Duplicate IDs raise rather than silently dropping an item.

    get_data() concatenates devices across every location before rekeying, so a
    duplicate here means real data would go missing.
    """
    items = [{"id": 1, "label": "first"}, {"id": 1, "label": "second"}]

    with pytest.raises(ValueError, match="Duplicate IDs"):
        _dict_by_ids(items)


def test_dict_by_ids_error_names_the_duplicate() -> None:
    """The raised error identifies which item collided."""
    items = [{"id": 1, "label": "first"}, {"id": 2}, {"id": 1, "label": "second"}]

    with pytest.raises(ValueError) as excinfo:
        _dict_by_ids(items)

    assert "second" in str(excinfo.value)


# MARK: - KiddeCommand


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        (KiddeCommand.IDENTIFY, "identify"),
        (KiddeCommand.IDENTIFYCANCEL, "identifycancel"),
        (KiddeCommand.TEST, "test"),
        (KiddeCommand.HUSH, "hush"),
    ],
)
def test_command_formats_as_its_api_value(command: KiddeCommand, expected: str) -> None:
    """Commands interpolate into a URL path as the bare API verb.

    device_command() builds its path with an f-string, so a plain Enum here
    would produce ".../KiddeCommand.HUSH" instead of ".../hush".
    """
    assert f"{command}" == expected


# MARK: - KiddeDataset


def test_dataset_is_frozen() -> None:
    """The dataset is immutable, so callers cannot corrupt a shared refresh."""
    dataset = KiddeDataset(locations={}, devices=None, events=None)

    with pytest.raises(dataclasses.FrozenInstanceError):
        dataset.locations = {1: {}}


def test_dataset_allows_unrequested_sections_to_be_none() -> None:
    """Devices and events are None when get_data() was told to skip them."""
    dataset = KiddeDataset(locations={1: {"id": 1}}, devices=None, events=None)

    assert (dataset.devices, dataset.events) == (None, None)


# MARK: - KiddeClient


def test_client_retains_cookies() -> None:
    """Cookies handed to the constructor are the ones later requests reuse."""
    cookies = {"session": "abc123"}

    assert KiddeClient(cookies).cookies == cookies


def test_auth_error_is_an_exception() -> None:
    """Callers can catch the auth failure without importing anything else."""
    assert issubclass(KiddeClientAuthError, Exception)
