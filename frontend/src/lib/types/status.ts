/** GET /api/status — counts for the dashboard (app/main.py). */
export interface StatusCounts {
	books: number;
	authors: number;
	series: number;
	audiobooks: number;
	ebooks: number;
	unlinked_books: number;
	unlinked_authors: number;
	unlinked_series: number;
	/** Keyed by request status: requested, snatched, downloading, failed, ... */
	requests: Record<string, number>;
}

/** One scheduled task in GET /api/sync/status. */
export interface TaskStatus {
	running?: boolean;
	/** Null when no schedule is configured — the task is effectively disabled. */
	next_run?: string | null;
	last_run?: string | null;
	last_result?: string | null;
}

export type SyncStatus = Record<string, TaskStatus>;

/** GET /api/downloads */
export interface DownloadItem {
	book_title?: string | null;
	author?: string | null;
	type?: 'audiobook' | 'ebook' | null;
	status?: string | null;
	/** Percent, 0-100. Null when the downloader reports nothing. */
	progress?: number | null;
	eta?: number | string | null;
	speed?: number | null;
	size?: number | null;
}
