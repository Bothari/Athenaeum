import type { PageParams, PageResult } from '$lib/types/table';

export const DEFAULT_LIMIT = 50;

export type FetchPage<T> = (params: PageParams) => Promise<PageResult<T>>;

/**
 * Append-style pagination state, extracted from DataTable so the fetch/append
 * state machine is independent of the markup and can be reused by grid views
 * (books, authors, series) that are not tables.
 *
 * Callers own sort/filter; this only tracks the resulting page window.
 */
export function createPager<T>(fetchPage: FetchPage<T>, limit = DEFAULT_LIMIT) {
	let items = $state<T[]>([]);
	let total = $state(0);
	let offset = $state(0);
	let loading = $state(false);
	let allLoaded = $state(false);
	let failed = $state(false);
	let initialised = $state(false);

	async function load(params: Omit<PageParams, 'limit' | 'offset'>, reset: boolean) {
		// Re-entry guard. Read outside any effect that also calls load, or the read
		// becomes a tracked dependency of state this function writes.
		if (loading) return;
		loading = true;
		failed = false;
		try {
			const start = reset ? 0 : offset;
			const result = await fetchPage({ ...params, limit, offset: start });
			total = result.total;
			items = reset ? result.items : [...items, ...result.items];
			offset = start + result.items.length;
			allLoaded = result.items.length < limit;
		} catch {
			failed = true;
			// Stop the observer retrying a failing request on every scroll tick.
			allLoaded = true;
		} finally {
			loading = false;
			initialised = true;
		}
	}

	return {
		get items() {
			return items;
		},
		get total() {
			return total;
		},
		get loading() {
			return loading;
		},
		get allLoaded() {
			return allLoaded;
		},
		get failed() {
			return failed;
		},
		get initialised() {
			return initialised;
		},
		load
	};
}
