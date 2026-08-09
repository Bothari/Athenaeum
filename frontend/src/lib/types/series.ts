import type { BookDetail } from './detail';
import type { SearchResult } from './search';

/** GET /api/series/{id} */
export interface SeriesDetail {
	id: string;
	name: string;
	show_secondary_works: boolean;
	library_count?: number;
	requested_count?: number;
	link?: {
		hardcover_series_id?: string | null;
		hardcover_series_slug?: string | null;
		abs_series_id?: string | null;
	};
}

/** GET /api/series/{id}/books — a book plus its position in this series. */
export interface SeriesBook extends BookDetail {
	series_position?: number | string | null;
}

/**
 * GET /api/series/{id}/missing. Items are search results, so they render with
 * SearchCard; `in_library` marks a book we hold that is not yet linked to this
 * series, which is what the "Add to this series" action fixes.
 */
export interface MissingItem extends SearchResult {
	series_position?: number | string | null;
	in_library?: boolean;
}

export interface MissingResponse {
	items?: MissingItem[];
	show_secondary_works?: boolean;
	/** True when the upstream list was cut short. */
	truncated?: boolean;
	error?: string | null;
}

export type SeriesDownloadStatus =
	| 'snatched'
	| 'downloading'
	| 'rescanning'
	| 'awaiting_review'
	| 'organizing'
	| string;

/** One file inside a downloaded pack, matched to a book. */
export interface PackFileMapping {
	filepath: string;
	filename: string;
	book_id?: string | null;
	book_title?: string | null;
	score?: number | null;
	action?: string | null;
}

export interface PackSeriesBook {
	id: string;
	title: string;
	in_library?: boolean;
}

export interface SeriesDownload {
	id: string;
	status: SeriesDownloadStatus;
	/**
	 * Older records stored a bare array of file mappings; newer ones an object
	 * with the series book list alongside. Both shapes still exist in the wild.
	 */
	proposed_mappings?: PackFileMapping[] | { file_mappings?: PackFileMapping[]; series_books?: PackSeriesBook[] };
}

/** A confirmed file→book placement sent back to the backend. */
export interface ConfirmedMapping {
	filepath: string;
	filename: string;
	book_id: string;
	book_title: string;
	score?: number | null;
	action: 'place';
}
