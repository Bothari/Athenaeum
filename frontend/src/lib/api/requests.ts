import { request } from './client';
import type { FormatType } from '$lib/types/library';
import type {
	CreateRequestResult,
	HistoryEvent,
	IndexerResult,
	SearchIndexersResult
} from '$lib/types/requests';

export interface CreateRequestBody {
	book_id: string;
	type: FormatType;
	narrator?: string | null;
	/** Creates a replacement request for a format already in the library. */
	replace?: boolean;
}

export function createRequest(body: CreateRequestBody): Promise<CreateRequestResult> {
	return request<CreateRequestResult>('/requests', { method: 'POST', body });
}

export function cancelRequest(id: string): Promise<unknown> {
	return request<unknown>(`/requests/${id}`, { method: 'DELETE' });
}

/** Re-runs the organize step for a request that failed during it. */
export function organizeRequest(id: string): Promise<unknown> {
	return request<unknown>(`/requests/${id}/organize`, { method: 'POST' });
}

export function searchIndexers(id: string): Promise<SearchIndexersResult> {
	return request<SearchIndexersResult>(`/requests/${id}/search-indexers`, { method: 'POST' });
}

/** Sends the chosen release to the configured downloader. */
export function downloadResult(id: string, result: IndexerResult): Promise<unknown> {
	return request<unknown>(`/requests/${id}/download`, {
		method: 'POST',
		body: {
			download_url: result.download_url,
			protocol: result.protocol,
			indexer: result.indexer,
			guid: result.guid,
			title: result.title,
			info_url: result.info_url,
			size: result.size
		}
	});
}

export function getRequestHistory(bookId: string): Promise<HistoryEvent[]> {
	return request<HistoryEvent[]>(`/books/${bookId}/request-history`);
}
