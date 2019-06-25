"""MQTT client used to communicate with the Mediabox Next"""
import ssl
import json
import uuid
import logging
import threading

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

from .api_client import get_session, get_jwt_token

_LOGGER = logging.getLogger(__name__)


# Default endpoint configuration for the MQTT connection used by the device.
DEFAULT_HOST = "obomsg.prod.nl.horizon.tv"
DEFAULT_PORT = 443


class MqttClient():

    def __init__(self, clientId, username, password):
        _LOGGER.info("Initializing MQTT client")

        self._isConnected = False

        # Save configuration options.
        self._clientId = clientId
        self._username = username
        self._password = password

        self._client = mqtt.Client(client_id = clientId, transport = "websockets")

        # Set the credentials and save the user data
        self._client.user_data_set({
            'clientId': clientId,
            'householdId': self._set_credentials()
        })

        # Set additional configuration.
        self._client.tls_set()
        self._client.enable_logger(_LOGGER)

        # Register events.
        self._client.on_connect = self.__on_connect
        self._client.on_message = self.__on_message
        self._client.on_publish = self.__on_publish
        self._client.on_disconnect = self.__on_disconnect

        # Register callbacks.
        self._on_payload = None
        self._callback_mutex = threading.RLock()
        self._in_callback_mutex = threading.Lock()


    @property
    def is_connected(self):
        """True / False if the client is currently connected."""
        return self._isConnected


    @property
    def on_payload(self):
        return self._on_payload


    @on_payload.setter
    def on_payload(self, func):
        with self._callback_mutex:
            self._on_payload = func


    def start(self):
        _LOGGER.info("Starting MQTT client")
        _LOGGER.debug("Using endpoint '" + DEFAULT_HOST + ":" + str(DEFAULT_PORT))

        self._client.connect(DEFAULT_HOST, DEFAULT_PORT)
        self._client.loop_start()


    def stop(self):
        _LOGGER.info("Stopping MQTT client")

        self._client.loop_stop()
        self._client.disconnect()


    def publish(self, event, status = None):
        _LOGGER.info("PUBLISH " + self._topic)

        # Prepare the payload.
        payload = {
            'id': str(uuid.uuid4()),
            'source': {
                'clientId': str(self._clientId),
                'friendlyDeviceName': "Home Assistant"
            },
            'type': event
        }

        # Check if the payload requires additional information.
        if (status != None):
            payload['status'] = status

        _LOGGER.info("With payload: " + str(payload))

        # Publish the payload on the active topic.
        self._client.publish(self._topic, json.dumps(payload))


    def _set_credentials(self):
        # Retrieve a session and JWT token, which can be used as identification by the device.
        session = get_session(self._username, self._password)
        jwtToken = get_jwt_token(session['oespToken'], self._username)

        # Update the client with the correct credentials
        self._client.username_pw_set(session['customer']['householdId'], jwtToken['token'])

        return session['customer']['householdId']


    def __on_connect(self, client, userdata, flags, resultCode):
        _LOGGER.info("Connected with result code " + str(resultCode))

        if (resultCode == 0):
            # Connection was succesful.
            self._topic = None
            self._isConnected = True

            self._client.subscribe("$SYS") # Does this work?
            self._client.subscribe(userdata['householdId']) # Shouldn't be needed because of the below
            self._client.subscribe(userdata['householdId'] + "/#")
            self._client.subscribe(userdata['householdId'] + "/$SYS") # Shouldn't be needed because of the above
            self._client.subscribe(userdata['householdId'] + "/+/#") # Shouldn't be needed because of the above
            self._client.subscribe(userdata['householdId'] + "/+/status") # Shouldn't be needed because of the above
            self._client.subscribe(userdata['householdId'] + "/" + userdata['clientId']) # Shouldn't be needed because of the above

        elif (resultCode == 5):
            # Connection refused - not authorised.
            # This can occur if the current connection expires, so refresh the credentials and try again.
            self._set_credentials()
            self.start()

        else:
            _LOGGER.error("Could not establish a MQTT connection with the device.")


    def __on_message(self, client, userdata, message):
        _LOGGER.info("MESSAGE " + message.topic)

        payload = json.loads(message.payload.decode('utf-8'))

        _LOGGER.info("Contains payload: " + str(payload))

        if (payload['deviceType'] == 'STB'):
            # If this is the first time we receive a message, register additional subscriptions.
            if (self._topic == None):
                self._topic = userdata['householdId'] + "/" + payload['source']

                self._client.subscribe(self._topic) # Shouldn't be needed because of the below
                self._client.subscribe(self._topic + "/#")
                self._client.subscribe(self._topic + "/$SYS") # Shouldn't be needed because of the above
                self._client.subscribe(self._topic + "/status") # Shouldn't be needed because of the above

            # Make sure we notify any subscribers about the incoming message.
            with self._in_callback_mutex:
                if (self.on_payload):
                    self.on_payload(payload)


    def __on_publish(self, client, userdata, messageId):
        _LOGGER.info("PUBLISH " + str(messageId))


    def __on_disconnect(self, client, userdata, resultCode):
        _LOGGER.info("Disconnected with result code " + str(resultCode))

        self._isConnected = False