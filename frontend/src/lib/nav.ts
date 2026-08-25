import type { IconName } from '$lib/components/Icon.svelte';

export interface NavItem {
	href: string;
	label: string;
	icon: IconName;
	adminOnly?: boolean;
	/** Shown only to non-admins (v1 exposed Profile this way). */
	nonAdminOnly?: boolean;
	/** Extra path prefixes that should light this item up. */
	alsoMatches?: string[];
}

/** Single source of truth for both the desktop and mobile navs. v1 duplicated
 *  this across index.html markup and updateActiveNav's nbMap, which is how they
 *  drifted. */
export const NAV_ITEMS: NavItem[] = [
	{ href: '/', label: 'Search', icon: 'search' },
	{ href: '/library/books', label: 'Library', icon: 'library', alsoMatches: ['/library'] },
	{ href: '/requests', label: 'Queue', icon: 'requests', alsoMatches: ['/downloads'] },
	{ href: '/dashboard', label: 'Dashboard', icon: 'dashboard', adminOnly: true },
	{ href: '/settings', label: 'Settings', icon: 'settings', adminOnly: true },
	{ href: '/profile', label: 'Profile', icon: 'author', nonAdminOnly: true }
];

export const LIBRARY_ITEMS = [
	{ href: '/library/books', label: 'Books' },
	{ href: '/library/authors', label: 'Authors' },
	{ href: '/library/series', label: 'Series' }
];

/** Root only matches exactly; everything else matches by prefix, as in v1. */
export function isActive(item: NavItem, path: string): boolean {
	const targets = [item.href, ...(item.alsoMatches ?? [])];
	return targets.some((t) => (t === '/' ? path === '/' : path.startsWith(t)));
}

export function visibleItems(items: NavItem[], isAdmin: boolean): NavItem[] {
	return items.filter((i) => {
		if (i.adminOnly && !isAdmin) return false;
		if (i.nonAdminOnly && isAdmin) return false;
		return true;
	});
}

/** v1 renamed Queue to Requests for non-admins. */
export function labelFor(item: NavItem, isAdmin: boolean): string {
	if (item.href === '/requests' && !isAdmin) return 'Requests';
	return item.label;
}
