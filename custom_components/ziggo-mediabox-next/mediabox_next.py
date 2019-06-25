"""Entity used to control the Mediabox Next"""
import uuid
import logging

from enum import Enum

from homeassistant.const import (STATE_PLAYING, STATE_PAUSED, STATE_ON, STATE_IDLE, STATE_OFF)

from homeassistant.components.media_player import MediaPlayerDevice
from homeassistant.components.media_player.const import (
    MEDIA_TYPE_TVSHOW, 
    SUPPORT_PLAY, SUPPORT_PAUSE, SUPPORT_PLAY_MEDIA, SUPPORT_STOP, 
    SUPPORT_NEXT_TRACK, SUPPORT_PREVIOUS_TRACK, 
    SUPPORT_SELECT_SOURCE, 
    SUPPORT_TURN_ON, SUPPORT_TURN_OFF)

from .mqtt_client import MqttClient
from .api_client import get_channels

_LOGGER = logging.getLogger(__name__)


# Global setting for all available channels.
DATA_CHANNEL_LIST = "mediabox_next_channel_list"

# List with available media keys.
MEDIA_KEY_POWER = 'Power'
MEDIA_KEY_ENTER = 'Enter' # Not yet implemented
MEDIA_KEY_ESCAPE = 'Escape' # Not yet implemented

MEDIA_KEY_HELP = 'Help' # Not yet implemented
MEDIA_KEY_INFO = 'Info' # Not yet implemented
MEDIA_KEY_GUIDE = 'Guide' # Not yet implemented

MEDIA_KEY_CONTEXT_MENU = 'ContextMenu' # Not yet implemented
MEDIA_KEY_CHANNEL_UP = 'ChannelUp'
MEDIA_KEY_CHANNEL_DOWN = 'ChannelDown'

MEDIA_KEY_RECORD = 'MediaRecord' # Not yet implemented
MEDIA_KEY_PLAY_PAUSE = 'MediaPlayPause'
MEDIA_KEY_STOP = 'MediaStop' # Not yet implemented
MEDIA_KEY_REWIND = 'MediaRewind' # Not yet implemented
MEDIA_KEY_FAST_FORWARD = 'MediaFastForward' # Not yet implemented


class MediaboxNext(MediaPlayerDevice):

    def __init__(self, name, username, password):
        _LOGGER.info("Initializing MediaboxNext player device")

        self._name = name
        self._state = None
        self._current_channel = None

        self._clientId = str(uuid.uuid4())

        self._client = MqttClient(self._clientId, username, password)

        # Register events.
        self._client.on_payload = self.__on_payload


    @property
    def icon(self):
        """Return the icon of the player."""
        return "mdi:television-classic"


    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name


    @property
    def state(self):
        """Return the state of the player."""
        return self._state


    @property
    def available(self):
        """Return True if the device is available."""
        return self._client.is_connected


    @property
    def media_content_id(self):
        """Content ID of current playing channel."""
        if (self._current_channel == None):
            return None
        else:
            return self._current_channel['channelNumber']


    @property
    def media_content_type(self):
        """Content type of current playing media."""
        return MEDIA_TYPE_TVSHOW


    @property
    def media_title(self):
        """Title of current playing media."""
        if (self._current_channel == None):
            return None
        else:
            return self._current_channel['title']


    @property
    def media_image_url(self):
        """Image url of current playing media."""
        if (self._current_channel == None):
            return None
        else:
            return self._current_channel['stationSchedules'][0]['station']['images'][0]['url']


    @property
    def media_channel(self):
        """Channel currently playing."""
        if (self._current_channel == None):
            return None
        else:
            return self._current_channel['title']


    @property
    def source(self):
        """Name of the current channel."""
        if (self._current_channel == None):
            return None
        else:
            return self._current_channel['title']


    @property
    def source_list(self):
        """List of available channels."""
        channels = self.hass.data.get(DATA_CHANNEL_LIST, None)

        if (channels == None):
            return None
        else:
            return [channel['title'] for channel in channels]


    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_PREVIOUS_TRACK | SUPPORT_NEXT_TRACK | SUPPORT_SELECT_SOURCE | SUPPORT_TURN_ON | SUPPORT_TURN_OFF


    def update(self):
        # Make sure we are connected to the device.
        if (self._client.is_connected == False):
            self._client.start()


        # Certain updates are only needed when the device is activated.
        if (self._state == STATE_ON):
            # Refresh the channel information.
            self.hass.data[DATA_CHANNEL_LIST] = get_channels()


    def toggle(self):
        """Toggles the media player power state."""
        _LOGGER.info("Toggling the media player power state.")

        self.__send_key(MEDIA_KEY_POWER)


    def turn_on(self):
        """Turn the media player on."""
        _LOGGER.info("Turning the media player on.")

        self.__send_key(MEDIA_KEY_POWER)


    def turn_off(self):
        """Turn the media player off."""
        _LOGGER.info("Turning the media player off.")

        self.__send_key(MEDIA_KEY_POWER)


    def media_play(self):
        """Send play command."""
        _LOGGER.info("Play the media player.")

        self.__send_key(MEDIA_KEY_PLAY_PAUSE)


    def media_pause(self):
        """Send pause command."""
        _LOGGER.info("Pause the media player.")

        self.__send_key(MEDIA_KEY_PLAY_PAUSE)


    def media_play_pause(self):
        """Simulate play pause media player."""
        _LOGGER.info("Play/pause the media player.")

        self.__send_key(MEDIA_KEY_PLAY_PAUSE)


    def media_next_track(self):
        """Send next track command."""
        _LOGGER.info("Switching to the next channel.")

        self.__send_key(MEDIA_KEY_CHANNEL_UP)


    def media_previous_track(self):
        """Send previous track command."""
        _LOGGER.info("Switching to the previous channel.")

        self.__send_key(MEDIA_KEY_CHANNEL_DOWN)


    def __send_key(self, key):
        _LOGGER.info("Sending key '" + key + "' to device")

        self._client.publish('CPE.KeyEvent', {
            'w3cKey': key,
            'eventType': 'keyDownUp'
        })


    def select_source(self, source):
        """Select the channel."""
        _LOGGER.info("Switching source to '" + source + "'")

        if (self._state == STATE_ON):
            self._current_channel = next((c for c in self.hass.data[DATA_CHANNEL_LIST] if c['title'] == source), None)
            station = self._current_channel['stationSchedules'][0]['station']

            _LOGGER.info("Switching to channel '" + station['serviceId'] + "' on device")

            self._client.publish('CPE.pushToTV', {
                'sourceType': 'linear',
                'source': {
                    'channelId': station['serviceId']
                },
                'relativePosition': 0,
                'speed': 1
            })


    def __on_payload(self, payload):
        _LOGGER.info("Incoming payload: " + str(payload))

        status = payload.get('state', None)

        if (status == 'ONLINE_RUNNING'):
            self._state = STATE_ON
        elif (status == 'ONLINE_STANDBY' or status == 'OFFLINE_NETWORK_STANDBY'):
            self._state = STATE_IDLE
        elif (status == 'OFFLINE'):
            self._state = STATE_OFF