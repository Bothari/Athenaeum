"""Which release auto-search picks.

Regression: requesting "Pines" reported no results while three releases scoring
100 were available. auto_search scored only ranked[0], and rank_results sorts by
quality (format, indexer priority, seeders, age, size) — so with "size prefer
larger" a 3-book omnibus took position 0, scored 55 on relevance, and the whole
request was abandoned with the exact matches sitting directly beneath it.
"""
import pytest

from app.services.auto_search import (
    DEFAULT_MIN_RELEVANCE,
    explain_rejections,
    is_series_pack,
    rank_results,
    rejection_reason,
)
from app.services.download_clients import _score_result

RANKING = [
    {"criterion": "format", "enabled": True},
    {"criterion": "seeders", "enabled": True},
    {"criterion": "size", "enabled": True, "prefer": "larger"},
]
FORMATS = ["epub", "mobi", "azw3"]


def _r(title, size=0, seeders=10, protocol="torrent"):
    return {"title": title, "size": size, "seeders": seeders, "protocol": protocol,
            "indexer": "Test", "downloadUrl": "http://stub/" + title[:8]}


# The shapes the real Prowlarr search returned for "Pines" by Blake Crouch.
PINES = [
    _r("Wayward Pines 1-3 by Blake Crouch [ENG / EPUB MOBI]", size=3 * 1024 * 1024),
    _r("Pines (2012) by Blake Crouch [ENG / EPUB MOBI] [VIP]", size=0),
    _r("Blake Crouch - [Wayward Pines 02] - Wayward (retail) (epub)", size=1024 * 1024),
    _r("Crouch, Blake - Pines  [epub]", size=0),
]


class TestRelevanceFiltersBeforeRanking:
    def test_the_exact_match_is_not_hidden_by_a_larger_bundle(self):
        """The bug, stated as a test: quality ranking must not get to veto relevance."""
        relevant = [
            r for r in PINES
            if _score_result(r["title"], "Pines", "Blake Crouch") >= DEFAULT_MIN_RELEVANCE
        ]
        assert relevant, "the exact matches must survive the relevance filter"
        ranked = rank_results(relevant, RANKING, FORMATS, min_seeders=1)
        assert ranked, "something relevant must survive the quality filters"
        chosen = ranked[0]["title"]
        assert "Pines" in chosen
        assert "1-3" not in chosen and "Wayward (" not in chosen, (
            f"picked {chosen!r} — a bundle or the wrong book in the series"
        )

    def test_ranking_alone_would_have_picked_the_bundle(self):
        """Guards the diagnosis: without the relevance filter, size wins."""
        ranked = rank_results(PINES, RANKING, FORMATS, min_seeders=1,
                              filter_series_packs=False)
        assert "1-3" in ranked[0]["title"], (
            "if this stops being true the regression test above is no longer "
            "exercising the ordering it was written for"
        )
        assert _score_result(ranked[0]["title"], "Pines", "Blake Crouch") < DEFAULT_MIN_RELEVANCE

    def test_a_different_book_in_the_series_scores_below_the_threshold(self):
        """What keeps book 2 from being grabbed when book 1 was requested."""
        score = _score_result(
            "Blake Crouch - [Wayward Pines 02] - Wayward (retail) (epub)",
            "Pines", "Blake Crouch")
        assert score < DEFAULT_MIN_RELEVANCE, score

    def test_exact_matches_score_at_the_top(self):
        for title in ("Crouch, Blake - Pines  [epub]",
                      "Pines (2012) by Blake Crouch [ENG / EPUB MOBI] [VIP]"):
            assert _score_result(title, "Pines", "Blake Crouch") >= DEFAULT_MIN_RELEVANCE, title


class TestSeriesPackDetection:
    @pytest.mark.parametrize("title", [
        "Wayward Pines 1-3 by Blake Crouch [ENG / EPUB MOBI]",   # bare range, no "book"
        "Wayward Pines Trilogy by Blake Crouch [ENG / M4B]",     # collective noun
        "The Expanse Books 1-9 Omnibus",
        "Discworld Complete Collection",
        "Foundation box set",
        "The Dark Tower 1-7",
    ])
    def test_packs_are_detected(self, title):
        assert is_series_pack(title), title

    @pytest.mark.parametrize("title", [
        "Pines (2012) by Blake Crouch [ENG / EPUB MOBI] [VIP]",
        "Crouch, Blake - Pines  [epub]",
        "Blake Crouch - [Wayward Pines 01] - Pines (retail) (epub)",
        # The number-range pattern must not swallow these:
        "The Second World War 1939-1945 by John Keegan",          # year range
        "Catch-22 by Joseph Heller",
        "Slaughterhouse-Five",
        "1984 by George Orwell",
    ])
    def test_single_books_are_not_mistaken_for_packs(self, title):
        assert not is_series_pack(title), title


class TestManualSearchOrdering:
    """The manual "Search Prowlarr" list shows everything, packs included — but the
    exact match has to be at the top. It previously led with the quality ranking
    alone, so "size prefer larger" listed the Wayward Pines 1-3 pack above Pines.
    """

    def _manual_order(self, results, title, author):
        """What routes/requests.py:search_indexers now does."""
        ranked = rank_results(results, RANKING, FORMATS, min_seeders=0,
                              filter_series_packs=False)
        scored = [(_score_result(r["title"], title, author), r) for r in ranked]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return scored

    def test_exact_match_leads_and_the_pack_is_still_listed(self):
        order = self._manual_order(PINES, "Pines", "Blake Crouch")
        assert order[0][0] == 100, f"led with relevance {order[0][0]}: {order[0][1]['title']!r}"
        assert "1-3" not in order[0][1]["title"]
        titles = [r["title"] for _, r in order]
        assert any("1-3" in t for t in titles), "the pack must still be offered, just not first"
        assert len(titles) == len(PINES), "manual search must not drop candidates"

    def test_quality_ranking_still_applies_within_one_relevance_band(self):
        """The sort is stable, so equal-relevance results keep their quality order."""
        same_score = [
            _r("Pines by Blake Crouch [small]", size=1),
            _r("Pines by Blake Crouch [large]", size=99 * 1024 * 1024),
        ]
        order = self._manual_order(same_score, "Pines", "Blake Crouch")
        assert len({s for s, _ in order}) == 1, "fixture should be one relevance band"
        assert "large" in order[0][1]["title"], (
            "within equal relevance, the ranking stack (size prefer larger) should lead"
        )


class TestRejectionReasons:
    """Auto-search reported "no results" when every relevant release had been
    removed by a hard filter, which reads as "this book does not exist" when the
    truth is "your settings excluded everything that matched" (ath-b9k.7).

    rejection_reason is the single source of truth for those filters, so nothing
    can be excluded for a reason the user is not told about.
    """

    def test_a_disallowed_format_says_so(self):
        r = _r("Some Book by An Author (mobi)")
        why = rejection_reason(r, ["epub", "azw3"], min_seeders=0)
        assert why and "mobi" in why and "allowed formats" in why

    def test_a_series_pack_says_so(self):
        r = _r("Some Series 1-3 by An Author [epub]")
        why = rejection_reason(r, ["epub"], min_seeders=0)
        assert why and "series pack" in why

    def test_too_few_seeders_names_the_threshold(self):
        r = _r("Some Book by An Author [epub]", seeders=2, protocol="torrent")
        why = rejection_reason(r, ["epub"], min_seeders=5)
        assert why and "2 seeder" in why and "minimum of 5" in why

    def test_a_usable_release_has_no_reason(self):
        r = _r("Some Book by An Author [epub]", seeders=10, protocol="torrent")
        assert rejection_reason(r, ["epub"], min_seeders=1) is None

    def test_usenet_is_not_judged_on_seeders(self):
        r = _r("Some Book by An Author [epub]", seeders=None, protocol="usenet")
        assert rejection_reason(r, ["epub"], min_seeders=5) is None

    def test_no_configured_formats_rejects_nothing_on_format(self):
        """With an empty allowed list the old predicate rejected every release whose
        format it could detect, so auto-search could never grab anything."""
        r = _r("Some Book by An Author (mobi)")
        assert rejection_reason(r, [], min_seeders=0) is None

    def test_an_undetectable_format_is_not_rejected(self):
        r = _r("Some Book by An Author")
        assert rejection_reason(r, ["epub"], min_seeders=0) is None


class TestExplainRejections:
    def test_it_groups_and_counts_the_reasons(self):
        results = [
            _r("A Book by An Author (mobi)"),
            _r("A Book by An Author (mobi)"),
            _r("A Series 1-3 by An Author [epub]"),
        ]
        out = explain_rejections(results, ["epub"], min_seeders=0)
        assert sum(out["counts"].values()) == 3
        assert any("mobi" in k for k in out["counts"])
        assert any("series pack" in k for k in out["counts"])
        assert "3 matching release" in out["summary"]

    def test_usable_releases_are_not_counted(self):
        results = [
            _r("A Book by An Author [epub]"),
            _r("A Book by An Author (mobi)"),
        ]
        out = explain_rejections(results, ["epub"], min_seeders=0)
        assert sum(out["counts"].values()) == 1

    def test_nothing_rejected_gives_an_empty_summary(self):
        out = explain_rejections([_r("A Book by An Author [epub]")], ["epub"], min_seeders=0)
        assert out["counts"] == {} and out["summary"] == ""

    def test_examples_are_capped(self):
        results = [_r(f"Book {i} by An Author (mobi)") for i in range(10)]
        out = explain_rejections(results, ["epub"], min_seeders=0)
        assert len(out["examples"]) == 3


class TestRankResultsStillFiltersTheSame:
    """The predicate moved out of rank_results; its behaviour must not have."""

    def test_the_filters_still_apply(self):
        results = [
            _r("Good Book by An Author [epub]", seeders=10),
            _r("Good Book by An Author (mobi)", seeders=10),
            _r("Good Series 1-3 by An Author [epub]", seeders=10),
            _r("Good Book by An Author [epub]", seeders=0, protocol="torrent"),
        ]
        kept = rank_results(results, RANKING, ["epub"], min_seeders=1)
        assert len(kept) == 1
        assert "mobi" not in kept[0]["title"] and "1-3" not in kept[0]["title"]

    def test_filter_series_packs_false_keeps_packs(self):
        results = [_r("Good Series 1-3 by An Author [epub]", seeders=10)]
        assert rank_results(results, RANKING, ["epub"], 1, filter_series_packs=False)
        assert rank_results(results, RANKING, ["epub"], 1) == []
