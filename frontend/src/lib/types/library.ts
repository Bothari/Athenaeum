/** Shapes consumed by the shared cards. Derived from what v1's renderers actually
 *  read, so they are intentionally narrower than the full API responses — routes
 *  can extend these where they need more. */

export type FormatType = 'audiobook' | 'ebook';

export interface BookFormat {
	type: FormatType;
	narrator?: string | null;
}

export interface BookRequestSummary {
	type: FormatType;
	status: string;
}

export interface BookAuthor {
	id?: string;
	name: string;
}

export interface BookCardData {
	id: string;
	title: string;
	/** Present on some endpoints; `authors` wins when both exist. */
	author?: string;
	authors?: BookAuthor[];
	cover_url?: string | null;
	formats?: BookFormat[];
	requests?: BookRequestSummary[];
}

export interface AuthorCardData {
	id: string;
	name: string;
	book_count?: number;
}

/** Hardcover linkage, present on list rows. Empty ids mean "not linked". */
export interface AuthorLink {
	hardcover_author_id?: string | null;
	hardcover_author_slug?: string | null;
}

export interface SeriesLink {
	hardcover_series_id?: string | null;
	hardcover_series_slug?: string | null;
}

/** GET /api/books — extends the card shape with what the table column needs. */
export interface BookListItem extends BookCardData {
	updated_at?: string;
	link?: { abs_id?: string | null; hardcover_id?: string | null };
}

/** GET /api/authors */
export interface AuthorListItem extends AuthorCardData {
	link?: AuthorLink;
}

/** GET /api/series */
export interface SeriesListItem extends SeriesCardData {
	link?: SeriesLink;
}

export interface SeriesCardData {
	id: string;
	name: string;
	library_count?: number;
	requested_count?: number;
	/** Chooses which missing/upcoming pair applies. */
	show_secondary_works?: boolean;
	missing_primary?: number | null;
	missing_all?: number | null;
	upcoming_primary?: number | null;
	upcoming_all?: number | null;
}
