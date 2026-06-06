"""Unit tests for _score_result — real-world Prowlarr result titles we have seen."""
import pytest
from app.services.download_clients import _score_result

AUTO_DOWNLOAD_THRESHOLD = 60


def should_grab(result, title, author=""):
    return _score_result(result, title, author) >= AUTO_DOWNLOAD_THRESHOLD


def should_reject(result, title, author=""):
    return _score_result(result, title, author) < AUTO_DOWNLOAD_THRESHOLD


# ── Correct matches (must score >= 60) ────────────────────────────────────────

class TestCorrectMatches:
    def test_exact_with_format_tag(self):
        assert should_grab(
            "The Bone Ships by RJ Barker [MP3]",
            "The Bone Ships", "RJ Barker",
        )

    def test_exact_with_epub(self):
        assert should_grab(
            "Call of the Bone Ships by R J Barker [ENG / EPUB]",
            "Call of the Bone Ships", "RJ Barker",
        )

    def test_exact_with_m4b(self):
        assert should_grab(
            "Caine black knife - Matthew Woodring Stover.m4b",
            "Caine Black Knife", "Matthew Woodring Stover",
        )

    def test_exact_name_of_the_wind(self):
        assert should_grab(
            "The Name of the Wind Patrick Rothfuss Audiobook",
            "The Name of the Wind", "Patrick Rothfuss",
        )

    def test_exact_wise_mans_fear(self):
        assert should_grab(
            "A Wise Man's Fear - Patrick Rothfuss [MP3]",
            "A Wise Man's Fear", "Patrick Rothfuss",
        )

    def test_unabridged_prefix_ok(self):
        # "Unabridged" is noise — should not penalise
        assert should_grab(
            "Unabridged The Bone Ships RJ Barker",
            "The Bone Ships", "RJ Barker",
        )

    def test_author_pen_name_initials(self):
        # "S. A. Chakraborty" filed as "Shannon Chakraborty" — surname match saves it
        assert should_grab(
            "The City of Brass Shannon Chakraborty MP3",
            "The City of Brass", "S. A. Chakraborty",
        )

    def test_words_of_radiance(self):
        assert should_grab(
            "Words of Radiance Brandon Sanderson M4B",
            "Words of Radiance", "Brandon Sanderson",
        )

    def test_subtitle_present(self):
        # Subtitle appears in result — should score well
        assert should_grab(
            "Exodus The Helium Sea John Hemry MP3",
            "Exodus: The Helium Sea", "John Hemry",
        )

    def test_no_author(self):
        assert should_grab(
            "The Blade Itself Joe Abercrombie EPUB",
            "The Blade Itself",
        )

    def test_series_pack_exact(self):
        # Series pack search where title IS the series name
        assert should_grab(
            "The Acts of Caine Complete Series Matthew Stover M4B",
            "The Acts of Caine", "Matthew Woodring Stover",
        )

    def test_different_word_order_narrator(self):
        # Narrator name added — token_set_ratio handles extra tokens
        assert should_grab(
            "The Name of the Wind Rothfuss read by Nick Podehl MP3",
            "The Name of the Wind", "Patrick Rothfuss",
        )


# ── Wrong book — different title in same series (must score < 60) ─────────────

class TestWrongBook:
    def test_series_sequel_epub(self):
        # "Call of the Bone Ships" grabbed when searching for "The Bone Ships"
        assert should_reject(
            "Call of the Bone Ships by R J Barker [ENG / EPUB]",
            "The Bone Ships", "RJ Barker",
        )

    def test_series_sequel_mp3(self):
        assert should_reject(
            "Call of the Bone Ships by RJ Barker [MP3]",
            "The Bone Ships", "RJ Barker",
        )

    def test_series_name_not_book(self):
        # "The Acts of Caine" is the series; "Caine Black Knife" is book 3
        assert should_reject(
            "The Acts of Caine Matthew Woodring Stover M4B",
            "Caine Black Knife", "Matthew Woodring Stover",
        )

    def test_different_stormlight_book(self):
        assert should_reject(
            "The Way of Kings Brandon Sanderson M4B",
            "Words of Radiance", "Brandon Sanderson",
        )

    def test_different_kingkiller_book(self):
        assert should_reject(
            "A Wise Man's Fear Patrick Rothfuss MP3",
            "The Name of the Wind", "Patrick Rothfuss",
        )

    def test_prequel_title(self):
        assert should_reject(
            "The Final Empire Brandon Sanderson EPUB",
            "The Well of Ascension", "Brandon Sanderson",
        )

    def test_multi_word_prefix(self):
        # Two meaningful prefix words — should be rejected firmly
        assert should_reject(
            "Shadow and Bone by Leigh Bardugo [EPUB]",
            "Bone Ships", "RJ Barker",
        )

    def test_reverse_sequel_check(self):
        # Don't grab "The Bone Ships" when searching for "Call of the Bone Ships"
        assert should_reject(
            "The Bone Ships by RJ Barker [MP3]",
            "Call of the Bone Ships", "RJ Barker",
        )

    def test_subtitle_mismatch(self):
        # Same series prefix, different subtitle → wrong book
        assert should_reject(
            "Exodus The Archimedes Engine John Hemry MP3",
            "Exodus: The Helium Sea", "John Hemry",
        )


# ── Score boundary sanity ──────────────────────────────────────────────────────

class TestScoreBoundaries:
    def test_score_range(self):
        s = _score_result("The Bone Ships by RJ Barker MP3", "The Bone Ships", "RJ Barker")
        assert 0 <= s <= 100

    def test_prefix_penalty_caps_at_55(self):
        # One meaningful prefix word → capped at 55
        s = _score_result(
            "Call of the Bone Ships by RJ Barker EPUB",
            "The Bone Ships", "RJ Barker",
        )
        assert s <= 55

    def test_missing_keyword_caps_at_40(self):
        # "ships" is entirely absent from "Shadow and Bone" → missing keyword penalty
        s = _score_result(
            "Shadow and Bone by Leigh Bardugo EPUB",
            "Bone Ships", "RJ Barker",
        )
        assert s <= 40

    def test_two_meaningful_prefix_words_caps_at_40(self):
        # "New Spring" are two meaningful words before "The Wheel of Time" keywords
        s = _score_result(
            "New Spring Robert Jordan MP3",
            "The Wheel of Time", "Robert Jordan",
        )
        assert s <= 40

    def test_correct_match_well_above_threshold(self):
        s = _score_result(
            "The Bone Ships RJ Barker MP3",
            "The Bone Ships", "RJ Barker",
        )
        assert s >= 75
