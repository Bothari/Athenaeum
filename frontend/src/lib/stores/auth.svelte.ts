import * as authApi from '$lib/api/auth';
import { ApiError, clearForceLocal } from '$lib/api/client';
import type { AuthMode, AuthUser } from '$lib/types/auth';

/**
 * Session state. Replaces v1's module-level `let _authUser`, which was a de facto
 * global mutated from route handlers.
 */
class AuthStore {
	user = $state<AuthUser | null>(null);
	/** False until the first /auth/me settles. Guards must wait on this, otherwise
	 *  they redirect an authenticated user to login on a cold load. */
	resolved = $state(false);
	/** Login modes offered by the backend when unauthenticated. */
	modes = $state<AuthMode[]>([]);

	/**
	 * Deliberately false when there is no user.
	 *
	 * v1's isAdmin() returned TRUE when _authUser was null, so admin-only nav
	 * flashed before the session resolved. The backend always gated properly via
	 * require_admin, so this was cosmetic — but it is still wrong, and it is not
	 * being ported.
	 */
	get isAdmin(): boolean {
		return this.user?.role === 'admin';
	}

	get isAuthenticated(): boolean {
		return this.user !== null;
	}

	get mustChangePassword(): boolean {
		return this.user?.force_password_change === true;
	}

	/** Loads the session. Never throws: an unauthenticated result is a normal
	 *  outcome, recorded as user = null plus the offered modes. */
	async load(): Promise<void> {
		try {
			this.user = await authApi.me({ noRedirect: true });
			this.modes = [];
		} catch (err) {
			this.user = null;
			this.modes = err instanceof ApiError && err.status === 401 ? err.modes : [];
		} finally {
			this.resolved = true;
		}
	}

	/** Re-reads the session after login so the user object matches /auth/me. The
	 *  login response omits user_id, so it cannot be used directly. */
	async completeLogin(): Promise<void> {
		clearForceLocal();
		await this.load();
	}

	async signOut(): Promise<void> {
		try {
			await authApi.logout();
		} finally {
			this.user = null;
			this.resolved = true;
		}
	}
}

export const auth = new AuthStore();
