import { request } from './client';
import type { BookDetail } from '$lib/types/detail';

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

export const HC_BASE: Record<string, string> = {
	book: 'https://hardcover.app/books',
	author: 'https://hardcover.app/authors',
	series: 'https://hardcover.app/series'
};

export function hardcoverUrl(type: string, slug?: string | null): string | null {
	if (!slug) return null;
	return `${HC_BASE[type]}/${encodeURIComponent(slug)}`;
}
