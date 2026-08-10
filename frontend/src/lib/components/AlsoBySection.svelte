<script lang="ts">
	import LoadingState from './LoadingState.svelte';
	import SearchCard from './SearchCard.svelte';
	import { getAlsoBy } from '$lib/api/books';
	import type { SearchResult } from '$lib/types/search';

	/**
	 * Books by this author that aren't in the library, per Hardcover. Results are
	 * search-shaped, so each one carries the usual request pills.
	 */
	interface Props {
		authorId: string;
	}

	let { authorId }: Props = $props();

	let items = $state<SearchResult[]>([]);
	let loading = $state(true);
	let failed = $state(false);

	$effect(() => {
		const id = authorId;
		let cancelled = false;
		loading = true;
		failed = false;

		getAlsoBy(id)
			.then((data) => {
				if (cancelled) return;
				if (data.error) failed = true;
				else items = data.items ?? [];
			})
			.catch(() => {
				if (!cancelled) failed = true;
			})
			.finally(() => {
				if (!cancelled) loading = false;
			});

		return () => {
			cancelled = true;
		};
	});
</script>

<h2 class="heading">
	Also by this Author{#if !loading && !failed && items.length}&nbsp;({items.length}){/if}
</h2>

{#if loading}
	<p class="dim">Checking Hardcover…</p>
{:else if failed}
	<!-- v1's wording, kept. -->
	<p class="dim">Could not reach Hardcover to check for more books.</p>
{:else if items.length === 0}
	<p class="dim">You already have everything. True super fan status achieved.</p>
{:else}
	{#each items as item, i (item.book_id ?? item.metadata_id ?? `${item.title}-${i}`)}
		<SearchCard result={item} />
	{/each}
{/if}

<style>
	.heading {
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--text-dim);
		margin: 1.5rem 0 0.5rem;
	}

	.dim {
		color: var(--text-dim);
		font-size: 0.9rem;
		padding: 0.5rem 0;
	}
</style>
