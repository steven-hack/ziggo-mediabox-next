"""Client used to retrieve information from API endpoints"""
import logging
import requests

_LOGGER = logging.getLogger(__name__)


# Static properties for the API url endpoints.
API_URL_CHANNELS = "https://web-api-prod-obo.horizon.tv/oesp/v3/NL/nld/web/channels"
API_URL_SESSION  = "https://web-api-prod-obo.horizon.tv/oesp/v3/NL/nld/web/session"
API_URL_TOKEN    = "https://web-api-prod-obo.horizon.tv/oesp/v3/NL/nld/web/tokens/jwt"


def get_channels():
    _LOGGER.info("Retrieving channels")

    r = requests.get(API_URL_CHANNELS)

    if (r.status_code == 200):
        content = r.json()

        _LOGGER.debug("Retrieved channels: " + str(content))

        return content['channels']
    else:
        _LOGGER.error("Error retrieving channels: " + str(r.status_code))
        _LOGGER.error("- Result headers: " + str(r.headers))
        _LOGGER.error("- Result body: " + str(r.content))

        return ""


def get_session(username, password):
    _LOGGER.info("Retrieving session")

    payload = {
        'username': username,
		'password': password
    }
    r = requests.post(API_URL_SESSION, json = payload)

    if (r.status_code == 200):
        session = r.json()

        _LOGGER.debug("Retrieved session: " + str(session))

        return session
    else:
        _LOGGER.error("Error retrieving session: " + str(r.status_code))
        _LOGGER.error("- Result headers: " + str(r.headers))
        _LOGGER.error("- Result body: " + str(r.content))

        return ""


def get_jwt_token(sessionToken, username):
    _LOGGER.info("Retrieving JWT token")

    headers = {
        'X-OESP-Token': sessionToken,
		'X-OESP-Username': username
    }
    r = requests.get(API_URL_TOKEN, headers = headers)

    if (r.status_code == 200):
        jwtToken = r.json()

        _LOGGER.debug("Retrieved JWT token: " + str(jwtToken))

        return jwtToken
    else:
        _LOGGER.error("Error retrieving JWT token: " + str(r.status_code))
        _LOGGER.error("- Result headers: " + str(r.headers))
        _LOGGER.error("- Result body: " + str(r.content))

        return ""
