<script lang="ts">
	/**
	 * Feather-style icons ported from v1's ICON_* template strings. v1 injected
	 * those via innerHTML; here they are real markup, so no {@html} and no XSS
	 * surface. Add cases as later phases need them.
	 */
	export type IconName =
		| 'search'
		| 'library'
		| 'requests'
		| 'dashboard'
		| 'settings'
		| 'author'
		| 'series'
		| 'audiobook'
		| 'ebook'
		| 'sun'
		| 'moon'
		| 'chevron-down'
		| 'arrow-up'
		| 'arrow-down'
		| 'spinner';

	interface Props {
		name: IconName;
		size?: number;
	}

	let { name, size = 18 }: Props = $props();
</script>

<svg
	width={size}
	height={size}
	viewBox="0 0 24 24"
	fill="none"
	stroke="currentColor"
	stroke-width="1.5"
	stroke-linecap="round"
	stroke-linejoin="round"
	aria-hidden="true"
	class={name === 'spinner' ? 'spin' : undefined}
>
	{#if name === 'search'}
		<circle cx="11" cy="11" r="8" />
		<line x1="21" y1="21" x2="16.65" y2="16.65" />
	{:else if name === 'library'}
		<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
		<path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
	{:else if name === 'requests'}
		<line x1="8" y1="6" x2="21" y2="6" />
		<line x1="8" y1="12" x2="21" y2="12" />
		<line x1="8" y1="18" x2="21" y2="18" />
		<line x1="3" y1="6" x2="3.01" y2="6" />
		<line x1="3" y1="12" x2="3.01" y2="12" />
		<line x1="3" y1="18" x2="3.01" y2="18" />
	{:else if name === 'dashboard'}
		<line x1="18" y1="20" x2="18" y2="10" />
		<line x1="12" y1="20" x2="12" y2="4" />
		<line x1="6" y1="20" x2="6" y2="14" />
	{:else if name === 'settings'}
		<line x1="4" y1="21" x2="4" y2="14" />
		<line x1="4" y1="10" x2="4" y2="3" />
		<line x1="12" y1="21" x2="12" y2="12" />
		<line x1="12" y1="8" x2="12" y2="3" />
		<line x1="20" y1="21" x2="20" y2="16" />
		<line x1="20" y1="12" x2="20" y2="3" />
		<line x1="1" y1="14" x2="7" y2="14" />
		<line x1="9" y1="8" x2="15" y2="8" />
		<line x1="17" y1="16" x2="23" y2="16" />
	{:else if name === 'author'}
		<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
		<circle cx="12" cy="7" r="4" />
	{:else if name === 'series'}
		<rect x="2" y="4" width="4" height="16" rx="1" />
		<rect x="8" y="6" width="4" height="14" rx="1" />
		<rect x="14" y="3" width="4" height="17" rx="1" />
		<line x1="1" y1="21" x2="22" y2="21" />
	{:else if name === 'audiobook'}
		<path d="M3 18v-6a9 9 0 0 1 18 0v6" />
		<path
			d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"
		/>
	{:else if name === 'ebook'}
		<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
		<path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
	{:else if name === 'sun'}
		<circle cx="12" cy="12" r="5" />
		<line x1="12" y1="1" x2="12" y2="3" />
		<line x1="12" y1="21" x2="12" y2="23" />
		<line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
		<line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
		<line x1="1" y1="12" x2="3" y2="12" />
		<line x1="21" y1="12" x2="23" y2="12" />
		<line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
		<line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
	{:else if name === 'moon'}
		<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
	{:else if name === 'chevron-down'}
		<polyline points="6 9 12 15 18 9" />
	{:else if name === 'arrow-up'}
		<line x1="12" y1="19" x2="12" y2="5" />
		<polyline points="5 12 12 5 19 12" />
	{:else if name === 'arrow-down'}
		<line x1="12" y1="5" x2="12" y2="19" />
		<polyline points="19 12 12 19 5 12" />
	{:else if name === 'spinner'}
		<path d="M21 12a9 9 0 1 1-6.219-8.56" />
	{/if}
</svg>

<style>
	.spin {
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
</style>
