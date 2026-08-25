/**
 * Scroll restoration for lists.
 *
 * SvelteKit restores scroll on back/forward by itself, but that only works when
 * the page is as tall as it was when you left. These routes fetch on mount, so
 * at restore time the page is empty and the browser lands at the top. Paginated
 * lists are worse: returning to row 400 needs eight pages re-fetched before the
 * position even exists.
 *
 * So the position is saved on the way out along with how many rows were loaded,
 * and replayed on the way back.
 */

const PREFIX = 'scroll:';

export interface SavedScroll {
	y: number;
	/** Rows loaded when leaving; 0 for non-paginated lists. */
	count: number;
}

export function saveScroll(key: string, count = 0): void {
	if (typeof window === 'undefined') return;
	const y = window.scrollY;
	// Nothing worth restoring, and storing it would override a real position
	// saved by an earlier visit.
	if (y === 0) {
		sessionStorage.removeItem(PREFIX + key);
		return;
	}
	sessionStorage.setItem(PREFIX + key, JSON.stringify({ y, count } satisfies SavedScroll));
}

/** Reads and clears the saved position, so a later fresh visit starts at the top. */
export function takeScroll(key: string): SavedScroll | null {
	if (typeof window === 'undefined') return null;
	const raw = sessionStorage.getItem(PREFIX + key);
	if (!raw) return null;
	sessionStorage.removeItem(PREFIX + key);
	try {
		const parsed = JSON.parse(raw) as SavedScroll;
		return typeof parsed?.y === 'number' ? parsed : null;
	} catch {
		return null;
	}
}

/**
 * Waits for layout before scrolling: content has just been rendered, and the
 * browser needs a frame to know how tall the page is.
 */
export function restoreScrollPosition(y: number): void {
	requestAnimationFrame(() => {
		requestAnimationFrame(() => window.scrollTo({ top: y, behavior: 'instant' }));
	});
}
