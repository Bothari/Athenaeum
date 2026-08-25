<script lang="ts">
	import Icon from '../Icon.svelte';
	import LoadingState from '../LoadingState.svelte';
	import PackReview from './PackReview.svelte';
	import { downloadPack, listSeriesDownloads, searchPack } from '$lib/api/series';
	import { formatBytes } from '$lib/format';
	import { toasts } from '$lib/stores/toast.svelte';
	import type { IndexerResult } from '$lib/types/requests';
	import type { SeriesDownload } from '$lib/types/series';

	/**
	 * Admin-only: find and download a whole-series pack, then review how its files
	 * map onto books before anything is organised into the library.
	 */
	interface Props {
		seriesId: string;
	}

	let { seriesId }: Props = $props();

	/** Poll intervals per state, matching v1: fast while rescanning, slow while
	 *  waiting on a download. */
	const POLL_MS: Record<string, number> = {
		snatched: 10000,
		downloading: 10000,
		rescanning: 3000,
		organizing: 5000
	};

	let download = $state<SeriesDownload | null>(null);
	let loaded = $state(false);
	let searching = $state(false);
	let results = $state<IndexerResult[] | null>(null);
	let searchError = $state('');
	let grabbing = $state<number | null>(null);
	let grabbed = $state<Set<number>>(new Set());

	async function refresh() {
		try {
			const downloads = await listSeriesDownloads(seriesId);
			download = downloads?.[0] ?? null;
		} catch {
			// Treat an unreachable list as "no active download" so the search UI
			// still works, as v1 did.
			download = null;
		} finally {
			loaded = true;
		}
	}

	$effect(() => {
		void seriesId;
		refresh();
	});

	/** Re-polls only while the pack is in a transient state. */
	$effect(() => {
		const interval = download ? POLL_MS[download.status] : undefined;
		if (!interval) return;
		const timer = setInterval(refresh, interval);
		return () => clearInterval(timer);
	});

	async function search() {
		searching = true;
		searchError = '';
		results = null;
		try {
			const data = await searchPack(seriesId);
			if (data.error) searchError = data.error;
			// Packs are big; the freshest is usually the best bet, so sort by age.
			else results = [...(data.results ?? [])].sort((a, b) => (a.age ?? Infinity) - (b.age ?? Infinity));
		} catch {
			searchError = 'Search failed.';
		} finally {
			searching = false;
		}
	}

	async function grab(result: IndexerResult, index: number) {
		grabbing = index;
		try {
			await downloadPack(seriesId, result);
			grabbed.add(index);
			toasts.success('Series pack download started!');
			setTimeout(refresh, 1500);
		} catch (err) {
			toasts.error(`Download failed: ${err instanceof Error ? err.message : String(err)}`);
		} finally {
			grabbing = null;
		}
	}

	const FORMAT_RE = /\b(epub|mobi|azw3?|pdf)\b/i;

	function age(days?: number | null): string | null {
		if (days == null) return null;
		if (days === 0) return 'today';
		if (days < 365) return `${days}d`;
		return `${Math.floor(days / 365)}y`;
	}

	const BUSY_LABEL: Record<string, string> = {
		snatched: 'Downloading pack…',
		downloading: 'Downloading pack…',
		rescanning: 'Re-scanning mappings…',
		organizing: 'Organising…'
	};
</script>

{#if !loaded}
	<LoadingState compact />
{:else if download && BUSY_LABEL[download.status]}
	<h2 class="heading">Series Pack</h2>
	<div class="card busy">
		<Icon name="spinner" size={16} />
		{BUSY_LABEL[download.status]}
	</div>
{:else if download && download.status === 'awaiting_review'}
	<PackReview {seriesId} {download} onchange={refresh} />
{:else}
	<h2 class="heading">Series Pack</h2>
	<button type="button" class="search" onclick={search} disabled={searching}>
		{searching ? 'Searching…' : 'Search Prowlarr'}
	</button>

	{#if searchError}
		<p class="dim">{searchError}</p>
	{/if}

	{#if results}
		{#if results.length === 0}
			<p class="dim">No results found.</p>
		{:else}
			<div class="results">
				{#each results as result, i (result.guid ?? i)}
					<div class="result">
						{#if result.info_url}
							<a class="title" href={result.info_url} target="_blank" rel="noreferrer">
								{result.title || '—'}
							</a>
						{:else}
							<div class="title">{result.title || '—'}</div>
						{/if}
						<div class="meta">
							<div class="info">
								{#if result.title?.match(FORMAT_RE)}
									<span class="tag">{result.title.match(FORMAT_RE)![1].toUpperCase()}</span>
								{/if}
								<span>{result.protocol === 'torrent' ? 'Torrent' : 'Usenet'}</span>
								<span>{formatBytes(result.size)}</span>
								{#if result.seeders != null}<span>{result.seeders}S</span>{/if}
								{#if age(result.age)}<span class="dim">{age(result.age)}</span>{/if}
								<span>{result.indexer || '—'}</span>
							</div>
							<button
								type="button"
								class="grab"
								class:done={grabbed.has(i)}
								disabled={grabbing === i || grabbed.has(i)}
								onclick={() => grab(result, i)}
							>
								{#if grabbing === i}
									<Icon name="spinner" size={14} />
								{:else if grabbed.has(i)}
									Sent
								{:else}
									Download
								{/if}
							</button>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	{/if}
{/if}

<style>
	.heading {
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--text-dim);
		margin: 1.5rem 0 0.5rem;
	}

	.card {
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 0.75rem 1rem;
	}

	.busy {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		color: var(--text-dim);
	}

	.search {
		padding: 0.35rem 0.8rem;
		font-size: 0.85rem;
		background: var(--accent);
		color: #fff;
		border: none;
		border-radius: var(--radius);
		margin-bottom: 0.75rem;
	}

	.search:disabled {
		opacity: 0.6;
	}

	.dim {
		color: var(--text-dim);
		font-size: 0.85rem;
	}

	.results {
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
	}

	.result {
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 0.5rem 0.65rem;
	}

	.title {
		display: block;
		font-size: 0.85rem;
		overflow-wrap: anywhere;
	}

	.meta {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.5rem;
		margin-top: 0.35rem;
	}

	.info {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.78rem;
	}

	.tag {
		background: var(--surface2);
		border-radius: 999px;
		padding: 0.1rem 0.4rem;
		font-size: 0.72rem;
	}

	.grab {
		flex-shrink: 0;
		padding: 0.2rem 0.6rem;
		font-size: 0.8rem;
		background: var(--accent);
		color: #fff;
		border: none;
		border-radius: var(--radius);
	}

	.grab.done {
		background: var(--green);
	}

	.grab:disabled {
		opacity: 0.7;
	}
</style>
