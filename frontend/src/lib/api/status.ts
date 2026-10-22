import { request } from './client';
import type { DownloadItem, StatusCounts, SyncStatus } from '$lib/types/status';

export function getStatus(): Promise<StatusCounts> {
	return request<StatusCounts>('/status');
}

export function getSyncStatus(): Promise<SyncStatus> {
	return request<SyncStatus>('/sync/status');
}

export function listDownloads(): Promise<{ items: DownloadItem[] }> {
	return request<{ items: DownloadItem[] }>('/downloads');
}

/** Scheduled tasks the dashboard can trigger by hand. */
export const SYNC_TASKS = [
	{ key: 'library_sync', label: 'Library sync', endpoint: '/sync/library' },
	{ key: 'cache_refresh', label: 'Cache refresh', endpoint: '/sync/cache-refresh' },
	{ key: 'auto_search', label: 'Auto-search', endpoint: '/sync/auto-search' }
] as const;

export function runSyncTask(endpoint: string): Promise<unknown> {
	return request<unknown>(endpoint, { method: 'POST' });
}

/** Only the slice of settings the dashboard reads. */
export function getSettings(): Promise<{ general?: { debug_view?: boolean } }> {
	return request<{ general?: { debug_view?: boolean } }>('/settings');
}
