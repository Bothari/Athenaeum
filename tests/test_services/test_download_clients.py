import re

import pytest
from pytest_httpx import HTTPXMock

from app.services.download_clients import (
    get_torrent_client, get_usenet_client, QBittorrentClient, DelugeClient, SABnzbdClient,
    drop_apostrophe_words, prowlarr_search,
)


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


class TestDropApostropheWords:
    def test_drops_curly_contraction(self):
        assert drop_apostrophe_words("You’re the One That I Haunt Jung") == "the One That I Haunt Jung"

    def test_drops_straight_contraction(self):
        assert drop_apostrophe_words("We've Always Lived in the Castle Jackson") == "Always Lived in the Castle Jackson"

    def test_drops_possessive(self):
        assert drop_apostrophe_words("Emily Wilde's Encyclopaedia of Faeries Fawcett") == "Emily Encyclopaedia of Faeries Fawcett"

    def test_none_without_apostrophe(self):
        assert drop_apostrophe_words("The Name of the Wind Rothfuss") is None

    def test_none_when_too_little_remains(self):
        assert drop_apostrophe_words("Ender's Game") is None


PROWLARR = {"url": "http://prowlarr.local:9696", "api_key": "k"}
SEARCH_URL = "http://prowlarr.local:9696/api/v1/search"


class TestProwlarrSearchApostropheRetry:
    async def test_retries_without_contraction_when_nothing_found(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=re.compile(re.escape(SEARCH_URL) + r"\?query=You"), json=[])
        httpx_mock.add_response(
            url=re.compile(re.escape(SEARCH_URL) + r"\?query=the"),
            json=[{"title": "You’re the One That I Haunt by Katie Jung [ENG / EPUB]"}],
        )
        results = await prowlarr_search(PROWLARR, "You’re the One That I Haunt Jung",
                                        title="You’re the One That I Haunt", author="Katie Jung")
        assert [r["title"] for r in results] == ["You’re the One That I Haunt by Katie Jung [ENG / EPUB]"]
        queries = [r.url.params["query"] for r in httpx_mock.get_requests()]
        assert queries == ["You’re the One That I Haunt Jung", "the One That I Haunt Jung"]

    async def test_no_retry_when_first_search_finds_something(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=re.compile(re.escape(SEARCH_URL)), json=[{"title": "Ender's Game by Orson Scott Card"}])
        results = await prowlarr_search(PROWLARR, "Ender's Game Card", title="Ender's Game", author="Orson Scott Card")
        assert len(results) == 1
        assert len(httpx_mock.get_requests()) == 1

    async def test_no_retry_without_apostrophe(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=re.compile(re.escape(SEARCH_URL)), json=[])
        assert await prowlarr_search(PROWLARR, "The Name of the Wind Rothfuss") == []
        assert len(httpx_mock.get_requests()) == 1
