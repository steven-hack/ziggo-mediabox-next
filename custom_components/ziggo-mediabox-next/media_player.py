"""Support for interface with a Ziggo Mediabox Next."""
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from homeassistant.const import CONF_NAME, CONF_HOST, CONF_PORT, CONF_USERNAME, CONF_PASSWORD
from homeassistant.components.media_player import (PLATFORM_SCHEMA, MEDIA_PLAYER_SCHEMA)

from .mediabox_next import MediaboxNext

_LOGGER = logging.getLogger(__name__)


# Default configuration, some configuration items cannot be changed by the user.
DEFAULT_NAME = 'Mediabox Next'


# Validation of the user's configuration.
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_NAME, default = DEFAULT_NAME): cv.string,
})


def setup_platform(hass, config, add_entities, discovery_info = None):
    # Assign configuration variables.
    # The configuration check takes care they are present.
    name = config[CONF_NAME]
    username = config[CONF_USERNAME]
    password = config.get(CONF_PASSWORD)

    add_entities([MediaboxNext(name, username, password)], True)