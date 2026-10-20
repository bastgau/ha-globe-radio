"""Globe Radio: play a radio station on Music Assistant with its name and logo."""

from __future__ import annotations

import logging
from typing import Any

import probatio

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

DOMAIN = "globe_radio"
SERVICE_PLAY_STATION = "play_station"
SERVICE_CLEANUP = "cleanup"
NAME_PREFIX = "[Globe Radio] "
MUSIC_ASSISTANT_DOMAIN = "music_assistant"

ATTR_URL = "url"
ATTR_NAME = "name"
ATTR_IMAGE_URL = "image_url"
ATTR_DRY_RUN = "dry_run"

PAGE_SIZE = 500

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

PLAY_STATION_SCHEMA = probatio.Schema(
    {
        probatio.Required("entity_id"): cv.entity_id,
        probatio.Required(ATTR_URL): cv.url,
        probatio.Required(ATTR_NAME): cv.string,
        probatio.Optional(ATTR_IMAGE_URL): cv.string,
    }
)

CLEANUP_SCHEMA = probatio.Schema({probatio.Optional(ATTR_DRY_RUN, default=False): cv.boolean})

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the play_station service."""

    async def handle_play_station(call: ServiceCall) -> None:
        """Add the station to Music Assistant, then play it."""
        mass = _get_client(hass)
        url: str = call.data[ATTR_URL]
        name: str = call.data[ATTR_NAME]
        args: dict[str, Any] = {"url": url, "name": f"{NAME_PREFIX}{name}"}
        if image_url := call.data.get(ATTR_IMAGE_URL):
            args["image_url"] = image_url

        radio = await mass.send_command("builtin/add_radio", **args)
        # Play the stored radio by its URI; the raw URL still works if no URI comes back
        media_id = radio.get("uri") if isinstance(radio, dict) else None
        _LOGGER.debug("Radio added, playing %s", media_id or url)

        await hass.services.async_call(
            MUSIC_ASSISTANT_DOMAIN,
            "play_media",
            {
                "entity_id": call.data["entity_id"],
                "media_id": media_id or url,
                "media_type": "radio",
            },
            blocking=True,
            context=call.context,
        )

    async def handle_cleanup(call: ServiceCall) -> ServiceResponse:
        """Remove the Globe Radio stations from the Music Assistant library."""
        mass = _get_client(hass)
        dry_run: bool = call.data[ATTR_DRY_RUN]

        playing = await _playing_names(mass)
        removed: list[str] = []
        skipped: list[str] = []
        for radio in await _list_globe_radios(mass):
            name = radio["name"]
            # Favorites and the station being played are kept
            if radio.get("favorite") or name in playing:
                skipped.append(name)
                continue
            if not dry_run:
                await mass.send_command(
                    "music/library/remove_item",
                    media_type="radio",
                    library_item_id=radio["item_id"],
                )
            removed.append(name)
        _LOGGER.debug("Cleanup (dry run: %s): %s removed, %s kept", dry_run, len(removed), len(skipped))
        return {"dry_run": dry_run, "removed": removed, "skipped": skipped}

    hass.services.async_register(DOMAIN, SERVICE_PLAY_STATION, handle_play_station, schema=PLAY_STATION_SCHEMA)
    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEANUP,
        handle_cleanup,
        schema=CLEANUP_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    return True


async def _list_globe_radios(mass: Any) -> list[dict[str, Any]]:
    """Return the library radios whose name starts with the Globe Radio prefix."""
    radios: list[dict[str, Any]] = []
    offset = 0
    while True:
        page = await mass.send_command(
            "music/radios/library_items",
            search=NAME_PREFIX.strip(),
            limit=PAGE_SIZE,
            offset=offset,
            summary=False,
        )
        radios.extend(radio for radio in page if str(radio.get("name", "")).startswith(NAME_PREFIX))
        if len(page) < PAGE_SIZE:
            return radios
        offset += PAGE_SIZE


async def _playing_names(mass: Any) -> set[str]:
    """Return the names of the items that a Music Assistant queue is playing or has paused."""
    names: set[str] = set()
    for queue in await mass.send_command("player_queues/all"):
        if queue.get("state") == "idle":
            continue
        media_item = (queue.get("current_item") or {}).get("media_item") or {}
        if name := media_item.get("name"):
            names.add(name)
    return names


def _get_client(hass: HomeAssistant) -> Any:
    """Return the Music Assistant client of the loaded Music Assistant integration."""
    for entry in hass.config_entries.async_entries(MUSIC_ASSISTANT_DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return entry.runtime_data.mass
    raise ServiceValidationError("Music Assistant is not loaded")
