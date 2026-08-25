<script lang="ts">
	import { page } from '$app/state';
	import Icon from './Icon.svelte';
	import ThemeToggle from './ThemeToggle.svelte';
	import { auth } from '$lib/stores/auth.svelte';
	import { NAV_ITEMS, LIBRARY_ITEMS, isActive, labelFor, visibleItems } from '$lib/nav';

	const path = $derived(page.url.pathname);
	const items = $derived(visibleItems(NAV_ITEMS, auth.isAdmin));
</script>

<nav class="nav">
	<div class="nav-inner">
		<a href="/" class="nav-logo">Athenaeum</a>
		<div class="nav-links">
			{#each items as item (item.href)}
				{#if item.href === '/library/books'}
					<div class="nav-dropdown">
						<a
							href={item.href}
							class="nav-btn nav-dropdown-trigger"
							class:active={isActive(item, path)}
						>
							{item.label}
							<Icon name="chevron-down" size={12} />
						</a>
						<div class="nav-dropdown-menu">
							{#each LIBRARY_ITEMS as sub (sub.href)}
								<a href={sub.href} class="nav-dropdown-item">{sub.label}</a>
							{/each}
						</div>
					</div>
				{:else}
					<a href={item.href} class="nav-btn" class:active={isActive(item, path)}>
						{labelFor(item, auth.isAdmin)}
					</a>
				{/if}
			{/each}
		</div>
		<ThemeToggle />
	</div>
</nav>

<style>
	.nav {
		position: sticky;
		top: 0;
		z-index: 100;
		height: 48px;
		background: var(--surface);
		border-bottom: 1px solid var(--border);
	}

	.nav-inner {
		max-width: 860px;
		margin: 0 auto;
		height: 100%;
		display: flex;
		align-items: center;
		gap: 0.25rem;
		padding: 0 1rem;
	}

	.nav-logo {
		font-size: 1.1rem;
		font-weight: 600;
		color: var(--text);
		text-decoration: none;
		margin-right: 1rem;
		letter-spacing: -0.02em;
	}

	.nav-logo:hover {
		color: var(--accent);
		text-decoration: none;
	}

	.nav-links {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		flex: 1;
	}

	.nav-btn {
		background: none;
		border: none;
		color: var(--text-dim);
		padding: 0.3rem 0.6rem;
		border-radius: var(--radius);
		font-size: 0.9rem;
		display: flex;
		align-items: center;
		gap: 0.25rem;
		transition:
			color 0.15s,
			background 0.15s;
	}

	.nav-btn:hover,
	.nav-btn.active {
		color: var(--text);
		background: var(--surface2);
		text-decoration: none;
	}

	.nav-dropdown {
		position: relative;
	}

	.nav-dropdown-menu {
		display: none;
		position: absolute;
		top: 100%;
		left: 0;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		min-width: 140px;
		z-index: 200;
	}

	.nav-dropdown:hover .nav-dropdown-menu {
		display: block;
	}

	.nav-dropdown-item {
		display: block;
		padding: 0.5rem 1rem;
		color: var(--text-dim);
		font-size: 0.9rem;
	}

	.nav-dropdown-item:hover {
		color: var(--text);
		background: var(--surface2);
		text-decoration: none;
	}

	/* Mobile: the bottom nav takes over, so hide the links but keep the bar for
	   the logo and theme toggle. Matches v1. */
	@media (max-width: 640px) {
		.nav-links {
			display: none;
		}

		.nav-dropdown:hover .nav-dropdown-menu {
			display: none;
		}
	}
</style>
