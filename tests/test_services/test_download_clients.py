import pytest
from app.services.download_clients import get_torrent_client, get_usenet_client, QBittorrentClient, DelugeClient, SABnzbdClient


def make_settings(*downloaders):
    return {"downloaders": list(downloaders)}


def qbit(id="qbit-1", name="qBittorrent", enabled=True, url="http://qbit.local:8116"):
    return {"id": id, "type": "qbittorrent", "name": name, "enabled": enabled, "url": url}


def deluge(id="deluge-1", name="Deluge", enabled=True, url="http://deluge.local:8112"):
    return {"id": id, "type": "deluge", "name": name, "enabled": enabled, "url": url}


def sabnzbd(id="sab-1", name="SABnzbd", enabled=True, url="http://sab.local:8080"):
    return {"id": id, "type": "sabnzbd", "name": name, "enabled": enabled, "url": url}


class TestGetTorrentClient:
    def test_returns_none_when_no_downloaders(self):
        client, ref = get_torrent_client({})
        assert client is None
        assert ref is None

    def test_returns_none_when_only_usenet(self):
        client, ref = get_torrent_client(make_settings(sabnzbd()))
        assert client is None

    def test_returns_qbittorrent(self):
        client, ref = get_torrent_client(make_settings(qbit()))
        assert isinstance(client, QBittorrentClient)
        assert ref == "qbit-1"

    def test_returns_deluge(self):
        client, ref = get_torrent_client(make_settings(deluge()))
        assert isinstance(client, DelugeClient)
        assert ref == "deluge-1"

    def test_first_wins_when_multiple_torrent_clients(self):
        # qbittorrent is listed first — it must win, deluge is ignored
        client, ref = get_torrent_client(make_settings(qbit(), deluge()))
        assert isinstance(client, QBittorrentClient)
        assert ref == "qbit-1"

    def test_first_wins_deluge_before_qbittorrent(self):
        # deluge is listed first — it wins
        client, ref = get_torrent_client(make_settings(deluge(), qbit()))
        assert isinstance(client, DelugeClient)
        assert ref == "deluge-1"

    def test_skips_disabled_client(self):
        client, ref = get_torrent_client(make_settings(qbit(enabled=False), deluge()))
        assert isinstance(client, DelugeClient)
        assert ref == "deluge-1"

    def test_skips_client_without_url(self):
        client, ref = get_torrent_client(make_settings(qbit(url=""), deluge()))
        assert isinstance(client, DelugeClient)

    def test_usenet_client_not_returned_as_torrent(self):
        client, ref = get_torrent_client(make_settings(sabnzbd(), qbit()))
        assert isinstance(client, QBittorrentClient)


class TestGetUsenetClient:
    def test_returns_none_when_no_downloaders(self):
        client, ref = get_usenet_client({})
        assert client is None

    def test_returns_sabnzbd(self):
        client, ref = get_usenet_client(make_settings(sabnzbd()))
        assert isinstance(client, SABnzbdClient)
        assert ref == "sab-1"

    def test_torrent_clients_not_returned_as_usenet(self):
        client, ref = get_usenet_client(make_settings(qbit(), deluge()))
        assert client is None
