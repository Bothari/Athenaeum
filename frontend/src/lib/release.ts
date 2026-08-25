/**
 * Release-date rules, which v1 reimplemented inline in four places (book detail,
 * the requests table, its unreleased filter, and the search-all filter) with
 * slightly different wording each time.
 *
 * Hardcover uses Jan 1 as a placeholder when only the year is known, so a
 * `YYYY-01-01` in the current year or later means "sometime this year", not
 * "released on New Year's Day".
 */

function today(): string {
	return new Date().toISOString().slice(0, 10);
}

function isYearOnlyPlaceholder(date: string): boolean {
	return date.endsWith('-01-01') && date.slice(0, 4) >= String(new Date().getFullYear());
}

export function isUnreleased(date?: string | null, fetched?: boolean): boolean {
	// Hardcover was asked and has no date at all: treat as unreleased.
	if (fetched && !date) return true;
	if (!date) return false;
	if (date > today()) return true;
	return isYearOnlyPlaceholder(date);
}

/** What to show next to a title: a badge label, or null when it is released. */
export function releaseBadge(
	date?: string | null,
	fetched?: boolean
): { label: string; title: string } | null {
	if (fetched && !date) return { label: 'No date', title: 'No release date known' };
	if (!date) return null;

	if (isYearOnlyPlaceholder(date)) {
		return { label: 'Unreleased', title: `Expected ${date.slice(0, 4)}` };
	}
	if (date > today()) {
		return { label: 'Unreleased', title: `Releases ${date}` };
	}
	return null;
}

/** Requests worth searching for: released, with a known date. */
export function isSearchable(date?: string | null, fetched?: boolean): boolean {
	return !isUnreleased(date, fetched);
}
