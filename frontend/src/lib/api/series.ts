import { request } from './client';
import type { IndexerResult } from '$lib/types/requests';
import type {
	ConfirmedMapping,
	MissingResponse,
	SeriesBook,
	SeriesDetail,
	SeriesDownload
} from '$lib/types/series';

export function getSeries(id: string): Promise<SeriesDetail> {
	return request<SeriesDetail>(`/series/${id}`);
}

/** Returns a bare array, not a paged envelope. */
export function getSeriesBooks(id: string): Promise<SeriesBook[]> {
	return request<SeriesBook[]>(`/series/${id}/books`);
}

/** Asks Hardcover what else belongs to this series. Can be slow. */
export function getMissing(id: string): Promise<MissingResponse> {
	return request<MissingResponse>(`/series/${id}/missing`);
}

/** Toggles whether non-primary works count toward missing/upcoming. */
export function setShowSecondaryWorks(id: string, value: boolean): Promise<unknown> {
	return request<unknown>(`/series/${id}`, {
		method: 'PATCH',
		body: { show_secondary_works: value }
	});
}

/** Attaches a book we already hold to this series. */
export function linkLibraryBook(
	id: string,
	bookId: string,
	position: number | string | null
): Promise<unknown> {
	return request<unknown>(`/series/${id}/link-library-book`, {
		method: 'POST',
		body: { book_id: bookId, position }
	});
}

/** Active pack downloads. Index 0 is the current one, if any. */
export function listSeriesDownloads(id: string): Promise<SeriesDownload[]> {
	return request<SeriesDownload[]>(`/series/${id}/series-downloads`);
}

export function searchPack(id: string): Promise<{ results?: IndexerResult[]; error?: string | null }> {
	return request<{ results?: IndexerResult[]; error?: string | null }>(`/series/${id}/search-pack`, {
		method: 'POST'
	});
}

/** Packs are ebook-only, as in v1. */
export function downloadPack(id: string, result: IndexerResult): Promise<unknown> {
	return request<unknown>(`/series/${id}/download-pack`, {
		method: 'POST',
		body: {
			download_url: result.download_url,
			protocol: result.protocol,
			indexer: result.indexer,
			guid: result.guid,
			title: result.title,
			info_url: result.info_url,
			size: result.size,
			type: 'ebook'
		}
	});
}

export function confirmPack(
	id: string,
	downloadId: string,
	mappings: ConfirmedMapping[]
): Promise<unknown> {
	return request<unknown>(`/series/${id}/series-downloads/${downloadId}/confirm`, {
		method: 'POST',
		body: { mappings }
	});
}

export function rescanPack(id: string, downloadId: string): Promise<unknown> {
	return request<unknown>(`/series/${id}/series-downloads/${downloadId}/rescan`, {
		method: 'POST'
	});
}
