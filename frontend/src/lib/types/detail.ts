import type { BookAuthor, FormatType } from './library';

/** Author as returned inside a book detail — carries link ids the list omits. */
export interface BookDetailAuthor extends BookAuthor {
	id: string;
	position?: number;
	abs_author_id?: string | null;
	hardcover_author_id?: string | null;
	hardcover_author_slug?: string | null;
}

export interface BookSeriesRef {
	id: string;
	name: string;
	/** String because positions can be fractional ("1.5"). */
	position?: string | null;
	library_count?: number;
}

export interface BookFormatDetail {
	id: string;
	type: FormatType;
	narrator?: string | null;
	abs_id?: string | null;
	abs_url?: string | null;
	fulfilled_by_request_id?: string | null;
}

export interface BookRequestDetail {
	id: string;
	type: FormatType;
	status: string;
	narrator?: string | null;
	requested_by_user_id?: string | null;
}

export interface BookLink {
	abs_id?: string | null;
	hardcover_id?: string | null;
	hardcover_slug?: string | null;
}

/** GET /api/books/{id} */
export interface BookDetail {
	id: string;
	title: string;
	cover_url?: string | null;
	release_date?: string | null;
	rating?: number | null;
	rating_count?: number | null;
	authors?: BookDetailAuthor[];
	series?: BookSeriesRef[];
	link?: BookLink;
	requests?: BookRequestDetail[];
	formats?: BookFormatDetail[];
}

/** Entities that can be linked to Hardcover. */
export type HcEntityType = 'book' | 'author' | 'series';

/** One candidate from POST /api/sync/try-link/{type}/{id} */
export interface TryLinkCandidate {
	hc_id: string;
	slug?: string | null;
	/** Books use title, authors and series use name. */
	title?: string;
	name?: string;
	author?: string | null;
	is_best?: boolean;
	score?: number | null;
	t_score?: number | null;
	a_score?: number | null;
}

export type TryLinkResult =
	| 'match'
	| 'linked'
	| 'no_match'
	| 'no_results'
	| 'conflict'
	| 'error'
	| 'no_api_key'
	| 'not_found';

export interface TryLinkLog {
	result: TryLinkResult;
	error?: string | null;
	candidates?: TryLinkCandidate[];
}
