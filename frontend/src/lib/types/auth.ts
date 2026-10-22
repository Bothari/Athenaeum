/** Shapes returned by app/routes/auth.py. Kept in step with the backend by hand —
 *  these are the contract, so change them only alongside a backend change. */

export type Role = 'admin' | 'user';

/** GET /api/auth/me */
export interface AuthUser {
	user_id: string;
	username: string;
	email?: string;
	role: Role;
	force_password_change: boolean;
}

/** Login modes offered when unauthenticated: 401 detail from /api/auth/me. */
export type AuthMode = 'form' | 'oidc';

/** POST /api/auth/login. Note the backend does NOT return user_id here, unlike
 *  /auth/me — so a logged-in user is re-fetched rather than built from this. */
export interface LoginResult {
	ok: true;
	username: string;
	role: Role;
	force_password_change: boolean;
}
