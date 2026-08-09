<script lang="ts">
	import { page } from '$app/state';
	import BookCard from '$lib/components/BookCard.svelte';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import ErrorState from '$lib/components/ErrorState.svelte';
	import HardcoverCard from '$lib/components/HardcoverCard.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import LoadingState from '$lib/components/LoadingState.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import { getAuthorBooks } from '$lib/api/books';
	import type { BookDetail } from '$lib/types/detail';

	const authorId = $derived(page.params.id!);

	type View = 'list' | 'poster';
	const VIEW_KEY = 'detail_view';

	let books = $state<BookDetail[]>([]);
	let loading = $state(true);
	let failed = $state(false);
	let view = $state<View>('list');
	let sortKey = $state<'title' | 'series'>('title');
	let sortDir = $state<'asc' | 'desc'>('asc');

	/** The author endpoint returns books, not the author, so the name and link ids
	 *  are read off whichever book carries this author. Same approach as v1. */
	const authorEntry = $derived(
		books.flatMap((b) => b.authors ?? []).find((a) => a.id === authorId)
	);
	const authorName = $derived(authorEntry?.name ?? 'Author');

	async function load() {
		loading = true;
		failed = false;
		try {
			books = await getAuthorBooks(authorId);
		} catch {
			failed = true;
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		void authorId;
		load();
	});

	$effect(() => {
		const stored = localStorage.getItem(VIEW_KEY);
		if (stored === 'poster' || stored === 'list') view = stored;
	});

	function setView(next: View) {
		view = next;
		localStorage.setItem(VIEW_KEY, next);
	}

	function seriesLabel(b: BookDetail): string {
		return (b.series ?? []).map((s) => `${s.name}${s.position ? ` #${s.position}` : ''}`).join(', ');
	}

	const sorted = $derived.by(() => {
		const key = sortKey;
		const dir = sortDir;
		return [...books].sort((a, b) => {
			const av = key === 'title' ? (a.title ?? '') : seriesLabel(a);
			const bv = key === 'title' ? (b.title ?? '') : seriesLabel(b);
			const cmp = av.toLowerCase().localeCompare(bv.toLowerCase());
			return dir === 'asc' ? cmp : -cmp;
		});
	});

	function toggleSort(key: 'title' | 'series') {
		if (key === sortKey) sortDir = sortDir === 'asc' ? 'desc' : 'asc';
		else {
			sortKey = key;
			sortDir = 'asc';
		}
	}
</script>

{#if failed}
	<ErrorState onretry={load} />
{:else if loading}
	<LoadingState />
{:else}
	<PageHeader title={authorName} icon="author">
		{#snippet actions()}
			<div class="view-toggle">
				<button
					type="button"
					class:active={view === 'poster'}
					onclick={() => setView('poster')}
					title="Poster"
					aria-label="Poster view">▦</button
				>
				<button
					type="button"
					class:active={view === 'list'}
					onclick={() => setView('list')}
					title="List"
					aria-label="List view">☰</button
				>
			</div>
		{/snippet}
	</PageHeader>

	{#if books.length === 0}
		<EmptyState message="No books found." />
	{:else if view === 'list'}
		<div class="table-wrap">
			<table>
				<thead>
					<tr>
						{#each [{ key: 'title', label: 'Title' }, { key: 'series', label: 'Series' }] as const as col (col.key)}
							<th class:sort-active={sortKey === col.key}>
								<button type="button" onclick={() => toggleSort(col.key)}>
									{col.label}
									{#if sortKey === col.key}
										<Icon name={sortDir === 'asc' ? 'arrow-up' : 'arrow-down'} size={12} />
									{/if}
								</button>
							</th>
						{/each}
					</tr>
				</thead>
				<tbody>
					{#each sorted as b (b.id)}
						<tr>
							<td><a href="/library/book/{b.id}">{b.title}</a></td>
							<td class="dim">{seriesLabel(b) || '—'}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{:else}
		<div class="grid">
			{#each sorted as b (b.id)}
				<BookCard book={b} />
			{/each}
		</div>
	{/if}

	<p class="deferred">"Also by this Author" arrives with the search card in phase 5b.</p>

	<HardcoverCard
		type="author"
		entityId={authorId}
		hcId={authorEntry?.hardcover_author_id}
		hcSlug={authorEntry?.hardcover_author_slug}
	/>
{/if}

<style>
	.view-toggle {
		display: flex;
		gap: 0.15rem;
	}

	.view-toggle button {
		background: none;
		border: 1px solid var(--border);
		border-radius: var(--radius);
		color: var(--text-dim);
		padding: 0.2rem 0.45rem;
		font-size: 0.9rem;
	}

	.view-toggle button.active {
		color: var(--accent);
		border-color: var(--accent);
	}

	.table-wrap {
		overflow-x: auto;
	}

	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.875rem;
	}

	th {
		text-align: left;
		font-weight: 600;
		color: var(--text-dim);
		padding: 0.5rem;
		border-bottom: 1px solid var(--border);
		white-space: nowrap;
	}

	th.sort-active {
		color: var(--text);
	}

	th button {
		display: inline-flex;
		align-items: center;
		gap: 0.25rem;
		background: none;
		border: none;
		padding: 0;
		font: inherit;
		color: inherit;
		cursor: pointer;
	}

	td {
		padding: 0.5rem;
		border-bottom: 1px solid var(--border);
		vertical-align: top;
	}

	.dim {
		color: var(--text-dim);
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
		gap: 1rem;
	}

	.deferred {
		margin-top: 1rem;
		font-size: 0.78rem;
		color: var(--text-dim);
	}
</style>
