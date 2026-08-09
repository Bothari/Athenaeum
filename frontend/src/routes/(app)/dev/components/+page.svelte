<script lang="ts">
	/**
	 * Component gallery. Development aid only — delete at cutover along with the
	 * rest of the v1 shim. Renders every shared component against fixture data so
	 * visual drift from v1 is visible before real routes depend on them.
	 */
	import Badge from '$lib/components/Badge.svelte';
	import type { BadgeVariant } from '$lib/components/Badge.svelte';
	import BookCard from '$lib/components/BookCard.svelte';
	import AuthorCard from '$lib/components/AuthorCard.svelte';
	import SeriesCard from '$lib/components/SeriesCard.svelte';
	import DataTable from '$lib/components/DataTable.svelte';
	import DetailStats from '$lib/components/DetailStats.svelte';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import ErrorState from '$lib/components/ErrorState.svelte';
	import LoadingState from '$lib/components/LoadingState.svelte';
	import { toasts } from '$lib/stores/toast.svelte';
	import type { Column } from '$lib/types/table';
	import {
		authors,
		books,
		series,
		fetchDemoPage,
		fetchEmptyPage,
		fetchFailingPage,
		type DemoRow
	} from './fixtures';

	const BADGES: BadgeVariant[] = [
		'pending',
		'requested',
		'sso',
		'snatched',
		'downloading',
		'downloaded',
		'merging',
		'organizing',
		'completed',
		'in_library',
		'failed',
		'missing',
		'upcoming',
		'warn',
		'neutral'
	];

	const columns: Column[] = [
		{ key: 'title', label: 'Title' },
		{ key: 'author', label: 'Author' },
		{ key: 'year', label: 'Year', width: '6rem' }
	];

	let tableMode = $state<'data' | 'empty' | 'error'>('data');

	const fetcher = $derived(
		tableMode === 'data' ? fetchDemoPage : tableMode === 'empty' ? fetchEmptyPage : fetchFailingPage
	);
</script>

<h1>Component gallery</h1>
<p class="note">Development aid. Not part of the shipped app — delete at cutover.</p>

<section>
	<h2>Badges</h2>
	<div class="row">
		{#each BADGES as variant (variant)}
			<Badge {variant}>{variant}</Badge>
		{/each}
	</div>
	<p class="note">Toggle the theme in the nav — every badge has a separate light palette.</p>
</section>

<section>
	<h2>Book cards</h2>
	<p class="note">
		Third card holds an ebook and has requests for both formats; only the audiobook request badge
		should show.
	</p>
	<div class="book-grid">
		{#each books as book (book.id)}
			<BookCard {book} />
		{/each}
	</div>
</section>

<section>
	<h2>Author cards</h2>
	<div class="card-grid">
		{#each authors as author (author.id)}
			<AuthorCard {author} />
		{/each}
	</div>
</section>

<section>
	<h2>Series cards</h2>
	<p class="note">Last card has uncomputed counts and should show no status badge at all.</p>
	<div class="card-grid">
		{#each series as s (s.id)}
			<SeriesCard series={s} />
		{/each}
	</div>
</section>

<section>
	<h2>Detail stats</h2>
	<div class="stack">
		<div><p class="label">Partial, with missing</p>
			<DetailStats inLibrary={3} requested={1} missing={2} upcoming={1} total={7} /></div>
		<div><p class="label">Upcoming only</p>
			<DetailStats inLibrary={5} missing={0} upcoming={2} total={7} /></div>
		<div><p class="label">Complete</p>
			<DetailStats inLibrary={7} missing={0} upcoming={0} total={7} /></div>
		<div><p class="label">Still checking (missing = null)</p>
			<DetailStats inLibrary={4} /></div>
	</div>
</section>

<section>
	<h2>States</h2>
	<div class="stack">
		<div><p class="label">Loading</p><LoadingState /></div>
		<div><p class="label">Loading (compact)</p><LoadingState compact /></div>
		<div><p class="label">Error</p>
			<ErrorState onretry={() => toasts.info('Retry clicked')} /></div>
		<div><p class="label">Empty</p><EmptyState /></div>
	</div>
</section>

<section>
	<h2>Toasts</h2>
	<div class="row">
		<button type="button" onclick={() => toasts.success('Saved.')}>Success</button>
		<button type="button" onclick={() => toasts.error('Something broke.')}>Error</button>
		<button type="button" onclick={() => toasts.info('For your information.')}>Info</button>
	</div>
</section>

<section>
	<h2>Data table</h2>
	<p class="note">
		137 fixture rows in pages of 50. Scroll to the bottom to trigger the next page; sort and filter
		write to the URL and survive reload.
	</p>
	<div class="row">
		{#each ['data', 'empty', 'error'] as const as mode (mode)}
			<button type="button" class:selected={tableMode === mode} onclick={() => (tableMode = mode)}>
				{mode}
			</button>
		{/each}
	</div>

	{#key tableMode}
		<DataTable {columns} stateKey="demo" fetchPage={fetcher} emptyMessage="Nothing here.">
			{#snippet row(item: DemoRow)}
				<td>{item.title}</td>
				<td>{item.author}</td>
				<td>{item.year}</td>
			{/snippet}
		</DataTable>
	{/key}
</section>

<style>
	h1 {
		font-size: 1.5rem;
		font-weight: 700;
	}

	h2 {
		font-size: 1rem;
		font-weight: 600;
		margin-bottom: 0.5rem;
	}

	section {
		margin-top: 2.5rem;
		padding-top: 1.5rem;
		border-top: 1px solid var(--border);
	}

	.note {
		color: var(--text-dim);
		font-size: 0.85rem;
		margin-bottom: 0.75rem;
	}

	.label {
		color: var(--text-dim);
		font-size: 0.78rem;
		margin-bottom: 0.25rem;
	}

	.row {
		display: flex;
		gap: 0.4rem;
		flex-wrap: wrap;
		align-items: center;
	}

	.stack {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.book-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
		gap: 1rem;
	}

	.card-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
		gap: 0.75rem;
	}

	button {
		padding: 0.35rem 0.7rem;
		background: var(--surface2);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		font-size: 0.85rem;
	}

	button.selected {
		border-color: var(--accent);
		color: var(--accent);
	}

</style>
