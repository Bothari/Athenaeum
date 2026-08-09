import type { FormatType } from './library';

export interface SearchAuthor {
	/** Hardcover author id, used to pivot the search to that author. */
	id?: string | null;
	name: string;
}

export interface SearchSeries {
	name: string;
	position?: string | null;
	hardcover_series_id?: string | null;
}

/** A format already held, as reported by the search endpoints. */
export interface SearchLibraryFormat {
	type: FormatType;
	narrator?: string | null;
}

export interface SearchExistingRequest {
	id?: string | null;
	type: FormatType;
	status?: string | null;
	narrator?: string | null;
	requested_by_user_id?: string | null;
}

/** GET /api/search/metadata and /api/search/advanced */
export interface SearchResult {
	title: string;
	/** Present once the book exists locally. */
	book_id?: string | null;
	author?: string | null;
	author_id?: string | null;
	authors?: SearchAuthor[];
	series?: SearchSeries[];
	cover_url?: string | null;
	rating?: number | null;
	rating_count?: number | null;
	release_date?: string | null;
	release_date_fetched?: boolean;
	published_year?: number | string | null;
	hardcover_url?: string | null;
	slug?: string | null;
	metadata_source?: string | null;
	metadata_id?: string | null;
	metadata_url?: string | null;
	library_formats?: SearchLibraryFormat[];
	existing_requests?: SearchExistingRequest[];
}

/** State of one format pill on a search card. */
export type FormatMode = 'in-library' | 'requested' | 'failed' | 'unmonitored';
