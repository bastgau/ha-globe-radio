"""Globe Radio: play a radio station on Music Assistant with its name and logo."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

DOMAIN = "globe_radio"
SERVICE_PLAY_STATION = "play_station"
NAME_PREFIX = "[Globe Radio] "
MUSIC_ASSISTANT_DOMAIN = "music_assistant"

ATTR_URL = "url"
ATTR_NAME = "name"
ATTR_IMAGE_URL = "image_url"

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

PLAY_STATION_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Required(ATTR_URL): cv.url,
        vol.Required(ATTR_NAME): cv.string,
        vol.Optional(ATTR_IMAGE_URL): cv.string,
    }
)

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

    hass.services.async_register(
        DOMAIN, SERVICE_PLAY_STATION, handle_play_station, schema=PLAY_STATION_SCHEMA
    )
    return True


def _get_client(hass: HomeAssistant) -> Any:
    """Return the Music Assistant client of the loaded Music Assistant integration."""
    for entry in hass.config_entries.async_entries(MUSIC_ASSISTANT_DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return entry.runtime_data.mass
    raise ServiceValidationError("Music Assistant is not loaded")
