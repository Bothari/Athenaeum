import { request } from './client';
import type { FormatType } from '$lib/types/library';
import type { PageParams, PageResult } from '$lib/types/table';
import type {
	CreateRequestResult,
	HistoryEvent,
	IndexerResult,
	PendingGroup,
	RequestListItem,
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

export interface ListRequestsQuery extends Partial<PageParams> {
	status?: string;
	type?: string;
}

export function listRequests(params: ListRequestsQuery): Promise<PageResult<RequestListItem>> {
	const q = new URLSearchParams();
	if (params.q) q.set('q', params.q);
	if (params.sort) q.set('sort', params.sort);
	if (params.dir) q.set('dir', params.dir);
	if (params.limit != null) q.set('limit', String(params.limit));
	if (params.offset != null) q.set('offset', String(params.offset));
	if (params.status) q.set('status', params.status);
	if (params.type) q.set('type', params.type);
	return request<PageResult<RequestListItem>>(`/requests?${q}`);
}

export function getPending(): Promise<{ groups: PendingGroup[] }> {
	return request<{ groups: PendingGroup[] }>('/requests/pending');
}

/** Approving takes the format list, so an admin can add a format the user did
 *  not ask for. */
export function approveBook(bookId: string, types: string[]): Promise<unknown> {
	return request<unknown>(`/requests/book/${bookId}/approve`, { method: 'POST', body: { types } });
}

export function rejectBook(bookId: string): Promise<unknown> {
	return request<unknown>(`/requests/book/${bookId}/reject`, { method: 'POST' });
}

export function retryFailed(): Promise<{ count: number }> {
	return request<{ count: number }>('/requests/retry-failed', { method: 'POST' });
}

export interface ManualRequestBody {
	title: string;
	author: string;
	type: FormatType;
}

export function createManualRequest(body: ManualRequestBody): Promise<{ book_id: string }> {
	return request<{ book_id: string }>('/requests/manual', { method: 'POST', body });
}
