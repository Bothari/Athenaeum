<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import Nav from '$lib/components/Nav.svelte';
	import BottomNav from '$lib/components/BottomNav.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import { auth } from '$lib/stores/auth.svelte';
	import { isForceLocal, FORCE_LOCAL_KEY } from '$lib/api/client';

	let { children } = $props();

	const path = $derived(page.url.pathname);

	/**
	 * Auth guard for everything inside the app shell.
	 *
	 * Waits on auth.resolved before acting: without that, a cold load redirects an
	 * authenticated user to login because the session has not been fetched yet.
	 */
	$effect(() => {
		if (!auth.resolved) return;

		if (!auth.isAuthenticated) {
			const params = new URLSearchParams();
			const dest = path + page.url.search;
			if (dest !== '/') params.set('next', dest);
			if (isForceLocal()) params.set(FORCE_LOCAL_KEY, '1');
			const qs = params.toString();
			goto(`/login${qs ? `?${qs}` : ''}`, { replaceState: true });
			return;
		}

		// Forced after an admin password reset. Excluded on its own route, or this
		// would loop.
		if (auth.mustChangePassword && path !== '/change-password') {
			goto('/change-password', { replaceState: true });
		}
	});
</script>

{#if !auth.resolved}
	<div class="boot"><Icon name="spinner" size={24} /></div>
{:else if auth.isAuthenticated}
	<Nav />
	<main>
		{@render children()}
	</main>
	<BottomNav />
{/if}

<style>
	.boot {
		display: flex;
		justify-content: center;
		margin-top: 4rem;
		color: var(--text-dim);
	}

	main {
		max-width: 1100px;
		margin: 0 auto;
		padding: 1.5rem 1rem;
	}

	@media (max-width: 640px) {
		main {
			/* Clear the fixed bottom nav. */
			padding: 1rem 0.75rem calc(56px + env(safe-area-inset-bottom) + 1rem);
		}
	}
</style>
