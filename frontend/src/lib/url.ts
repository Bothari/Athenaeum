import { goto } from '$app/navigation';
import { page } from '$app/state';

/**
 * Updates query parameters on the current route.
 *
 * Uses goto rather than $app/navigation's replaceState. replaceState is the
 * shallow-routing API: it exists to attach `page.state` to a history entry, and
 * on the first page a user lands on that state is not applied until they
 * navigate. Filters written against it silently did nothing on a hard load —
 * which is how "hide unreleased" appeared broken on mobile, where deep-linking
 * straight to a route is the normal case.
 *
 * goto performs a real client-side navigation, so `page.url` updates and any
 * derived reading it re-runs. noScroll and keepFocus keep it feeling like an
 * in-place filter change rather than a page change.
 */
export async function setSearchParams(updates: Record<string, string | null>): Promise<void> {
	const params = new URLSearchParams(page.url.searchParams);

	for (const [key, value] of Object.entries(updates)) {
		if (value === null || value === '') params.delete(key);
		else params.set(key, value);
	}

	const qs = params.toString();
	await goto(`${page.url.pathname}${qs ? `?${qs}` : ''}`, {
		replaceState: true,
		noScroll: true,
		keepFocus: true
	});
}

export function setSearchParam(key: string, value: string | null): Promise<void> {
	return setSearchParams({ [key]: value });
}
