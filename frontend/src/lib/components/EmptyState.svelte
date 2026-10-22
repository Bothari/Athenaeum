<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		message?: string;
		/** Overrides message when richer content (links, actions) is needed. */
		children?: Snippet;
	}

	let { message = 'No items found.', children }: Props = $props();
</script>

<div class="state-empty">
	{#if children}
		{@render children()}
	{:else}
		{message}
	{/if}
</div>

<style>
	.state-empty {
		text-align: center;
		padding: 3rem 1rem;
		color: var(--text-dim);
		line-height: 2;
	}

	.state-empty :global(a) {
		color: var(--accent);
	}
</style>
