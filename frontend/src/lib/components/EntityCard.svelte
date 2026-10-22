<script lang="ts">
	import type { Snippet } from 'svelte';

	/**
	 * Base for the author and series cards, which in v1 were two separate renderers
	 * producing identical markup with different meta lines. One component now, with
	 * the meta row supplied as a snippet.
	 */
	interface Props {
		href: string;
		name: string;
		meta: Snippet;
	}

	let { href, name, meta }: Props = $props();
</script>

<a class="entity-card" {href}>
	<div class="entity-card-name">{name}</div>
	<div class="entity-card-meta">{@render meta()}</div>
</a>

<style>
	/* v1 used a div with an onclick, which meant no middle-click, no open-in-new-tab
	   and no keyboard access. A real anchor fixes all three at no visual cost. */
	.entity-card {
		display: block;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 1rem;
		cursor: pointer;
		transition: border-color 0.15s;
		color: inherit;
		text-decoration: none;
	}

	.entity-card:hover {
		border-color: var(--accent);
		text-decoration: none;
	}

	.entity-card-name {
		font-weight: 600;
	}

	.entity-card-meta {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		flex-wrap: wrap;
		font-size: 0.8rem;
		color: var(--text-dim);
		margin-top: 0.25rem;
	}
</style>
