<script lang="ts">
	import { page } from '$app/state';
	import Icon from './Icon.svelte';
	import { auth } from '$lib/stores/auth.svelte';
	import { NAV_ITEMS, LIBRARY_ITEMS, isActive, labelFor, visibleItems } from '$lib/nav';

	const path = $derived(page.url.pathname);
	const items = $derived(visibleItems(NAV_ITEMS, auth.isAdmin));

	let libraryOpen = $state(false);
	let popupEl = $state<HTMLElement | null>(null);

	// Any navigation closes the popup, including one started from inside it.
	$effect(() => {
		void path;
		libraryOpen = false;
	});

	/** Close on outside click. Testing containment rather than stopping propagation
	 *  inside the popup keeps it free of click handlers, so links stay plain links
	 *  and no keyboard-handler a11y problem is introduced. */
	function onWindowClick(event: MouseEvent) {
		if (!libraryOpen) return;
		if (popupEl?.contains(event.target as Node)) return;
		libraryOpen = false;
	}

	function onWindowKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') libraryOpen = false;
	}
</script>

<svelte:window onclick={onWindowClick} onkeydown={onWindowKeydown} />

{#if libraryOpen}
	<div class="popup" bind:this={popupEl}>
		{#each LIBRARY_ITEMS as item (item.href)}
			<a href={item.href} class="popup-item">{item.label}</a>
		{/each}
	</div>
{/if}

<nav class="bottom-nav">
	{#each items as item (item.href)}
		{#if item.href === '/library/books'}
			<button
				class="bottom-btn"
				class:active={isActive(item, path)}
				aria-label="Library"
				aria-expanded={libraryOpen}
				onclick={(e) => {
					e.stopPropagation();
					libraryOpen = !libraryOpen;
				}}
			>
				<Icon name={item.icon} />
			</button>
		{:else}
			<a
				href={item.href}
				class="bottom-btn"
				class:active={isActive(item, path)}
				aria-label={labelFor(item, auth.isAdmin)}
			>
				<Icon name={item.icon} />
			</a>
		{/if}
	{/each}
</nav>

<style>
	.bottom-nav {
		display: none;
		position: fixed;
		bottom: 0;
		left: 0;
		right: 0;
		height: calc(56px + env(safe-area-inset-bottom));
		background: var(--surface);
		border-top: 1px solid var(--border);
		z-index: 100;
		justify-content: space-around;
		align-items: flex-start;
		padding-bottom: env(safe-area-inset-bottom);
	}

	.bottom-btn {
		display: flex;
		flex: 1;
		height: 56px;
		align-items: center;
		justify-content: center;
		color: var(--text-dim);
		background: none;
		border: none;
		text-decoration: none;
		transition: color 0.15s;
		-webkit-tap-highlight-color: transparent;
		touch-action: manipulation;
	}

	.bottom-btn:hover,
	.bottom-btn.active {
		color: var(--accent);
		text-decoration: none;
	}

	.popup {
		position: fixed;
		bottom: calc(56px + env(safe-area-inset-bottom) + 4px);
		left: 50%;
		transform: translateX(-50%);
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		min-width: 160px;
		z-index: 200;
		overflow: hidden;
		display: none;
	}

	.popup-item {
		display: block;
		padding: 0.75rem 1rem;
		color: var(--text-dim);
		font-size: 0.9rem;
		text-align: center;
	}

	.popup-item:hover {
		color: var(--text);
		background: var(--surface2);
		text-decoration: none;
	}

	@media (max-width: 640px) {
		.bottom-nav {
			display: flex;
		}

		.popup {
			display: block;
		}
	}
</style>
