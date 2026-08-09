import { request } from './client';
import type { SearchResult } from '$lib/types/search';

interface SearchResponse {
	results?: SearchResult[];
}

/** Quick title search. */
export function searchMetadata(q: string): Promise<SearchResponse> {
	return request<SearchResponse>(`/search/metadata?q=${encodeURIComponent(q)}`);
}

export interface AdvancedQuery {
	title?: string;
	author?: string;
	series?: string;
	/** Hardcover author id — pivots to everything by that author. */
	author_id?: string;
	/** Hardcover series id — pivots to that whole series. */
	hc_series_id?: string;
}

export function searchAdvanced(params: AdvancedQuery): Promise<SearchResponse> {
	const q = new URLSearchParams();
	for (const [key, value] of Object.entries(params)) {
		if (value) q.set(key, value);
	}
	return request<SearchResponse>(`/search/advanced?${q}`);
}

export interface CreateBookBody {
	title: string;
	authors: { name: string; hc_id: string | null }[];
	cover_url: string | null;
	series_list: { name: string; position: string | null; hardcover_id: string | null }[];
	metadata_source: string | null;
	metadata_id: string | null;
	metadata_url: string | null;
	hardcover_slug: string | null;
}

/**
 * Creates (or returns) the local book for a search result. v1 always POSTed this
 * even when book_id was already known, so that series associations get created
 * for books that predate the series data.
 */
export function createBook(body: CreateBookBody): Promise<{ id: string }> {
	return request<{ id: string }>('/books', { method: 'POST', body });
}
