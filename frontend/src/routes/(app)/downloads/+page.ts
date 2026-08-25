import { redirect } from '@sveltejs/kit';

/**
 * v1 kept /downloads as a shim that rewrote the hash to the requests page's
 * downloads tab. A load-time redirect does the same job without rendering
 * anything, and keeps old links working.
 */
export function load() {
	redirect(307, '/requests?tab=downloads');
}
