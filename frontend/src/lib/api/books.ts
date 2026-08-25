import { request } from './client';
import type { BookDetail } from '$lib/types/detail';
import type { SearchResult } from '$lib/types/search';

export function getBook(id: string): Promise<BookDetail> {
	return request<BookDetail>(`/books/${id}`);
}

/** Re-pulls metadata from Hardcover for an already-linked book. */
export function refreshHardcover(
	id: string
): Promise<{ canonical_id?: string | null; slug?: string | null }> {
	return request<{ canonical_id?: string | null; slug?: string | null }>(`/books/${id}/refresh-hc`, {
		method: 'POST'
	});
}

/** Returns a bare array, not a paged envelope. */
export function getAuthorBooks(authorId: string): Promise<BookDetail[]> {
	return request<BookDetail[]>(`/authors/${authorId}/books`);
}

/**
 * Books by this author that are not in the library, per Hardcover. Returns
 * search-shaped results so they render with SearchCard. `error` is set when
 * Hardcover could not be reached.
 */
export function getAlsoBy(
	authorId: string
): Promise<{ items?: SearchResult[]; error?: string | null }> {
	return request<{ items?: SearchResult[]; error?: string | null }>(
		`/authors/${authorId}/also-by`
	);
}

export const HC_BASE: Record<string, string> = {
	book: 'https://hardcover.app/books',
	author: 'https://hardcover.app/authors',
	series: 'https://hardcover.app/series'
};

export function hardcoverUrl(type: string, slug?: string | null): string | null {
	if (!slug) return null;
	return `${HC_BASE[type]}/${encodeURIComponent(slug)}`;
}
