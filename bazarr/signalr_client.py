# coding=utf-8

import logging
from requests import Session
from signalr import Connection
from requests.exceptions import ConnectionError
from signalrcore.hub_connection_builder import HubConnectionBuilder

from config import settings, url_sonarr, url_radarr
from get_episodes import sync_episodes, sync_one_episode
from get_series import update_series, update_one_series
from scheduler import scheduler


class SonarrSignalrClient:
    def __init__(self):
        self.apikey_sonarr = settings.sonarr.apikey
        self.session = Session()
        self.connection = None

    def start(self):
        self.connection = Connection(url_sonarr() + "/signalr", self.session)
        self.connection.qs = {'apikey': self.apikey_sonarr}
        sonarr_hub = self.connection.register_hub('')  # Sonarr doesn't use named hub

        sonarr_method = ['series', 'episode']
        for item in sonarr_method:
            sonarr_hub.client.on(item, dispatcher)

        try:
            self.connection.start()
        except ConnectionError:
            pass
        else:
            logging.debug('BAZARR SignalR client for Sonarr is connected.')
            scheduler.add_job(update_series)
            scheduler.add_job(sync_episodes)


class RadarrSignalrClient:
    def __init__(self):
        self.apikey_radarr = settings.radarr.apikey

    def start(self):
        hub_connection = HubConnectionBuilder() \
            .with_url(url_radarr() + "/signalr/messages?access_token={}".format(self.apikey_radarr),
                      options={
                          "verify_ssl": False
                      }) \
            .configure_logging(logging.INFO) \
            .with_automatic_reconnect({
                "type": "interval",
                "keep_alive_interval": 10,
                "reconnect_interval": 5,
                "max_attempts": 0
            }).build()
        hub_connection.on_open(lambda: logging.debug("BAZARR SignalR client for Radarr is connected."))
        hub_connection.on_close(lambda: logging.debug("BAZARR SignalR client for Radarr is disconnected."))
        hub_connection.on_error(lambda data: logging.debug(f"BAZARR SignalR client for Radarr: An exception was thrown "
                                                           f"closed{data.error}"))
        hub_connection.on("receiveMessage", dispatcher)
        hub_connection.start()

    @staticmethod
    def devnull(data):
        pass


def dispatcher(data):
    if isinstance(data, dict):
        topic = data['name']
    elif isinstance(data, list):
        topic = data[0]['name']

    if topic in ['version', 'queue/details', 'queue', 'health', 'command']:
        return
    if topic == 'series':
        update_one_series(data)
    elif topic == 'episode':
        sync_one_episode(data)
    elif topic == 'movie':
        print(data[0])


sonarr_signalr_client = SonarrSignalrClient()
radarr_signalr_client = RadarrSignalrClient()
