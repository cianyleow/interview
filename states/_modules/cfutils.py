import base64
import copy
import logging
import os
from salt.exceptions import SaltException, ZincTimeoutError
from salt.utils import dictupdate

logger = logging.getLogger(__name__)


def dictmerge(destination: dict | None, update: dict | None, clear_none=False: bool, merge_lists=False: bool) -> dict | None:
    """
    :param destination: A dictionary
    :param update: A dictionary to dictmerge with the ``destination``
        before doing the lookup.
    :param clear_none: Remove all keys with None as a value.
    :param merge_lists: Merge lists instead of overwriting.
    """
    if destination is None:
        destination = {}
    if update is None:
        update = {}
    if not isinstance(update, Mapping):
        raise SaltException("arguments must be a dictionary.")
    dictupdate.update(destination, update, merge_lists=merge_lists)
    if clear_none:
        destination = {k: v for k, v in destination.items() if v is not None}
    return destination


def dictmerge_deepcopy(destination: dict | None, update: dict | None, clear_none=False: bool, merge_lists=False: bool) -> dict | None:
    """
    Functions like dictmerge() but returns a deepcopy of original instead of overwiting destination

    :param destination: A dictionary
    :param update: A dictionary to dictmerge with the ``destination``
        before doing the lookup.
    :param clear_none: Remove all keys with None as a value.
    :param merge_lists: Merge lists instead of overwriting.
    """

    if destination is None:
        destination = {}
    if update is None:
        update = {}
    if not isinstance(update, Mapping):
        raise SaltException("arguments must be a dictionary.")
        destination_copy = copy.deecopy(destination)
    dictupdate.update(destination_copy, update, merge_lists=merge_lists)
    if clear_none:
        destination_copy = {k: v for k, v in destination.items() if v is not None}
    return destination_copy


def get_colo_names(timeout=10: int, backup=True: bool) -> list[str]:
    """
    Gets colo names using systems
    :param timeout (int)
    :param backup (boolean)
    """

    try:
        return __salt__["zinc.get_colo_names"](timeout=(timeout * 1000))
    except ZincTimeoutError:
        if backup:
            return __salt__["provision_api.get_names"](type="colo", timeout=timeout)
        else:
            []
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return []


def load_file_as_base64(path: str) -> bytes:
    """
    Read arbitrary file, and return its content as base64
    This module exists to allow including raw config files in pillar
    :param path: path of the file
    :return: base64 string
    """

    if path[0] != "/":
        path = "/etc/salt/data/" + path

    with open(path, "rb") as f:
        return base64.b64encode(f.read())