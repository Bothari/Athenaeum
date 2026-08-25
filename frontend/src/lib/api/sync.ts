import { request } from './client';
import type { HcEntityType, TryLinkLog } from '$lib/types/detail';

/** Ask the backend to search Hardcover for candidates. Does not link anything. */
export function tryLink(type: HcEntityType, id: string): Promise<TryLinkLog> {
	return request<TryLinkLog>(`/sync/try-link/${type}/${id}`, { method: 'POST' });
}

/** Set or clear the Hardcover link. Empty strings unlink, as in v1. */
export function setLink(
	type: HcEntityType,
	id: string,
	hardcoverId: string,
	hardcoverSlug: string
): Promise<unknown> {
	return request<unknown>(`/sync/link/${type}/${id}`, {
		method: 'PUT',
		body: { hardcover_id: hardcoverId, hardcover_slug: hardcoverSlug }
	});
}

export function unlink(type: HcEntityType, id: string): Promise<unknown> {
	return setLink(type, id, '', '');
}

export interface ResolvedHcUrl {
	hardcover_id?: string | null;
	hardcover_slug?: string | null;
	error?: string | null;
}

/** Turns a pasted hardcover.app URL into an id/slug pair. */
export function resolveHcUrl(url: string, type: HcEntityType): Promise<ResolvedHcUrl> {
	return request<ResolvedHcUrl>('/sync/resolve-hc-url', {
		method: 'POST',
		body: { url, type }
	});
}
