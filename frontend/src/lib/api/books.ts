import { request } from './client';
import type { BookDetail } from '$lib/types/detail';
import type { SearchResult } from '$lib/types/search';
import type { FormatType } from '$lib/types/library';

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

/** One file in an organized format directory, as the delete preview reports it. */
export interface FormatFile {
	path: string;
	size: number;
	/** media is the book, sidecar is metadata/cover, other is anything unrecognised. */
	kind: 'media' | 'sidecar' | 'other';
}

export interface FormatFilesPreview {
	dir: string | null;
	files: FormatFile[];
	/**
	 * False when nothing in the derived directory looks like the book. The path is
	 * re-derived from author and title rather than recorded, so it can miss — offer
	 * no file deletion in that case.
	 */
	locatable: boolean;
}

/** What deleting this format would remove from disk. Does not delete anything. */
export function previewFormatFiles(
	bookId: string,
	type: FormatType
): Promise<FormatFilesPreview> {
	return request<FormatFilesPreview>(`/books/${bookId}/formats/${type}/files`);
}

export interface DeleteFormatResult {
	files_removed: string[];
	files_failed: { path: string; error: string }[];
	dir_removed: boolean;
	requests_deleted: number;
	book_orphaned: boolean;
}

/**
 * Removes one format: its row, its requests, and optionally its library files.
 * Never touches the downloader's copy, which may still be seeding.
 */
export function deleteBookFormat(
	bookId: string,
	type: FormatType,
	deleteFiles: boolean
): Promise<DeleteFormatResult> {
	const q = deleteFiles ? '?delete_files=true' : '';
	return request<DeleteFormatResult>(`/books/${bookId}/formats/${type}${q}`, {
		method: 'DELETE'
	});
}
