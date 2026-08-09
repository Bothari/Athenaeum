import { request } from './client';
import type { AuthUser, LoginResult } from '$lib/types/auth';

/** Current session. Throws ApiError(401) when unauthenticated — callers that want
 *  to inspect the offered login modes should pass noRedirect. */
export function me(opts: { noRedirect?: boolean } = {}): Promise<AuthUser> {
	return request<AuthUser>('/auth/me', { noRedirect: opts.noRedirect });
}

export function login(username: string, password: string): Promise<LoginResult> {
	return request<LoginResult>('/auth/login', {
		method: 'POST',
		body: { username, password },
		noRedirect: true
	});
}

export function logout(): Promise<{ ok: true }> {
	return request<{ ok: true }>('/auth/logout', { method: 'POST' });
}

export function changePassword(currentPassword: string, newPassword: string): Promise<{ ok: true }> {
	return request<{ ok: true }>('/auth/change-password', {
		method: 'POST',
		body: { current_password: currentPassword, new_password: newPassword },
		noRedirect: true
	});
}

/** Full page navigation, not a fetch: the backend 302s to the identity provider. */
export const OIDC_START_URL = '/api/auth/oidc/start';
