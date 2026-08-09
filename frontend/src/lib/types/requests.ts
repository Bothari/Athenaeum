import type { FormatType } from './library';

/** POST /api/requests — `skipped` means an equivalent request already existed. */
export interface CreateRequestResult {
	id: string;
	skipped?: boolean;
}

/** One Prowlarr result from POST /api/requests/{id}/search-indexers */
export interface IndexerResult {
	title?: string | null;
	protocol?: 'torrent' | 'usenet' | string | null;
	indexer?: string | null;
	size?: number | null;
	seeders?: number | null;
	/** Age in days. */
	age?: number | null;
	/** Percentage; >=60 would auto-download. */
	score?: number | null;
	info_url?: string | null;
	download_url?: string | null;
	guid?: string | null;
}

export interface SearchIndexersResult {
	results?: IndexerResult[];
	error?: string | null;
}

export type HistoryEventType =
	| 'created'
	| 'state_change'
	| 'searched'
	| 'grabbed'
	| 'cancelled'
	| string;

/** GET /api/books/{id}/request-history */
export interface HistoryEvent {
	request_id: string;
	event_type: HistoryEventType;
	created_at?: string | null;
	/** Present when the join found the live request; otherwise inferred from the
	 *  `created` event's detail. */
	request_type?: FormatType | null;
	detail?: {
		type?: FormatType;
		status?: string;
		from?: string;
		to?: string;
		reason?: string;
		results?: number;
		title?: string;
		indexer?: string;
		size?: number;
		info_url?: string;
	} | null;
}
