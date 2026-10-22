import { goto } from '$app/navigation';
import type { AuthMode } from '$lib/types/auth';

/** Thrown for any non-2xx response. `detail` carries FastAPI's error body when
 *  present, which is how login modes arrive on a 401. */
export class ApiError extends Error {
	status: number;
	detail: unknown;

	constructor(status: number, message: string, detail?: unknown) {
		super(message);
		this.name = 'ApiError';
		this.status = status;
		this.detail = detail;
	}

	/** Login modes offered by a 401 from an unauthenticated request. */
	get modes(): AuthMode[] {
		const d = this.detail;
		if (d && typeof d === 'object' && 'modes' in d && Array.isArray(d.modes)) {
			return d.modes as AuthMode[];
		}
		return [];
	}
}

/** Set by /login?force_local=1 to suppress the automatic SSO redirect, so a local
 *  account can be used while OIDC is enabled. Survives the OIDC round trip within
 *  the tab, matching v1. */
export const FORCE_LOCAL_KEY = 'force_local';

export function isForceLocal(): boolean {
	return sessionStorage.getItem(FORCE_LOCAL_KEY) === '1';
}

export function setForceLocal(): void {
	sessionStorage.setItem(FORCE_LOCAL_KEY, '1');
}

export function clearForceLocal(): void {
	sessionStorage.removeItem(FORCE_LOCAL_KEY);
}

interface RequestOptions {
	method?: string;
	/** Serialised as JSON. Do not pre-stringify. */
	body?: unknown;
	/** Skip the automatic redirect-to-login on 401. Used by auth calls that need
	 *  to inspect the 401 themselves rather than bounce the user. */
	noRedirect?: boolean;
	signal?: AbortSignal;
}

/**
 * Single entry point for every backend call. Components must not call fetch
 * directly — see CLAUDE.md.
 *
 * Session auth is cookie-based and set by FastAPI, so there is no token handling
 * here; the browser attaches the cookie automatically on same-origin requests.
 */
export async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
	const { method = 'GET', body, noRedirect = false, signal } = opts;

	const res = await fetch(`/api${path}`, {
		method,
		headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
		body: body === undefined ? undefined : JSON.stringify(body),
		signal
	});

	if (res.ok) {
		// 204 and other empty bodies would blow up res.json().
		if (res.status === 204) return undefined as T;
		const text = await res.text();
		return (text ? JSON.parse(text) : undefined) as T;
	}

	let detail: unknown;
	let message = `${res.status}`;
	try {
		const parsed = await res.json();
		detail = parsed?.detail ?? parsed;
		if (typeof detail === 'string') message = detail;
	} catch {
		// Non-JSON error body; keep the status-only message.
	}

	if (res.status === 401 && !noRedirect) {
		// Session expired mid-use. Preserve where the user was so login can return
		// them there, and keep the force_local choice across the bounce.
		const dest = window.location.pathname + window.location.search;
		const params = new URLSearchParams();
		if (dest && dest !== '/login') params.set('next', dest);
		if (isForceLocal()) params.set(FORCE_LOCAL_KEY, '1');
		const qs = params.toString();
		await goto(`/login${qs ? `?${qs}` : ''}`, { replaceState: true });
	}

	throw new ApiError(res.status, message, detail);
}
