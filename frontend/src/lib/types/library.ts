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
