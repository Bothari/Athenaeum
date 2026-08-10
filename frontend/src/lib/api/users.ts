import { request } from './client';
import type { Role } from '$lib/types/auth';

/** GET /api/users — note the integer flags, which SQLite stores as 0/1. */
export interface ManagedUser {
	id: string;
	username: string;
	email?: string | null;
	role: Role;
	force_password_change?: number | boolean;
	oidc_linked?: number | boolean;
	created_at?: string | null;
}

export function listUsers(): Promise<{ users: ManagedUser[] }> {
	return request<{ users: ManagedUser[] }>('/users');
}

export interface CreateUserBody {
	username: string;
	password: string;
	role: Role;
	email?: string;
}

export function createUser(body: CreateUserBody): Promise<unknown> {
	return request<unknown>('/users', { method: 'POST', body });
}

/** Partial update — send only what changed. */
export function updateUser(
	id: string,
	patch: { email?: string; role?: Role }
): Promise<unknown> {
	return request<unknown>(`/users/${id}`, { method: 'PATCH', body: patch });
}

export function deleteUser(id: string): Promise<unknown> {
	return request<unknown>(`/users/${id}`, { method: 'DELETE' });
}

/** Sets a temporary password; the user is forced to change it at next login. */
export function resetPassword(id: string, newPassword: string): Promise<unknown> {
	return request<unknown>(`/users/${id}/reset-password`, {
		method: 'POST',
		body: { new_password: newPassword }
	});
}

export interface OidcVerifyResult {
	ok?: boolean;
	issuer?: string;
	authorization_endpoint?: string;
	token_endpoint?: string;
	userinfo_endpoint?: string;
}

/** Fetches the provider's discovery document so the URL can be checked before saving. */
export function verifyOidcProvider(providerUrl: string): Promise<OidcVerifyResult> {
	return request<OidcVerifyResult>('/auth/oidc/verify', {
		method: 'POST',
		body: { provider_url: providerUrl }
	});
}
