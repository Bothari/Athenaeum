<script lang="ts">
	import Badge from '../Badge.svelte';
	import type { BadgeVariant } from '../Badge.svelte';
	import EmptyState from '../EmptyState.svelte';
	import ErrorState from '../ErrorState.svelte';
	import Icon from '../Icon.svelte';
	import LoadingState from '../LoadingState.svelte';
	import ProwlarrResults from '../ProwlarrResults.svelte';
	import { listRequests, searchIndexers } from '$lib/api/requests';
	import { isSearchable } from '$lib/release';
	import type { IndexerResult, RequestListItem } from '$lib/types/requests';

	/** v1 pulled a single large page rather than paginating this view. */
	const MAX = 200;

	interface Group {
		book_id: string;
		title: string;
		author: string;
		requests: RequestListItem[];
	}

	let groups = $state<Group[]>([]);
	let loaded = $state(false);
	let failed = $state(false);

	/** Per-request search outcome, filled in as the queue works through them. */
	let results = $state<Record<string, IndexerResult[] | null>>({});
	let errors = $state<Record<string, string>>({});
	let searching = $state<string | null>(null);

	async function load() {
		loaded = false;
		failed = false;
		try {
			const data = await listRequests({ status: 'requested', limit: MAX });
			// Unreleased items can't be found, so searching them just wastes indexer
			// queries. Same filter v1 applied.
			const eligible = (data.items ?? []).filter((r) =>
				isSearchable(r.release_date, r.release_date_fetched)
			);

			const byBook = new Map<string, Group>();
			for (const r of eligible) {
				let g = byBook.get(r.book_id);
				if (!g) {
					g = {
						book_id: r.book_id,
						title: r.book_title || r.title || '—',
						author: r.author || '',
						requests: []
					};
					byBook.set(r.book_id, g);
				}
				g.requests.push(r);
			}
			groups = [...byBook.values()];
		} catch {
			failed = true;
		} finally {
			loaded = true;
		}
	}

	$effect(() => {
		load();
	});

	/**
	 * Searches run one at a time. Prowlarr fans each query out to every indexer,
	 * so firing all of them at once is a good way to get rate-limited.
	 */
	async function runAll() {
		for (const g of groups) {
			for (const r of g.requests) {
				if (results[r.id] !== undefined) continue;
				searching = r.id;
				try {
					const data = await searchIndexers(r.id);
					if (data.error) errors = { ...errors, [r.id]: data.error };
					else results = { ...results, [r.id]: data.results ?? [] };
				} catch (err) {
					errors = { ...errors, [r.id]: err instanceof Error ? err.message : String(err) };
				}
			}
		}
		searching = null;
	}
</script>

{#if !loaded}
	<LoadingState />
{:else if failed}
	<ErrorState onretry={load} />
{:else if groups.length === 0}
	<EmptyState message="No searchable requests — all items are unreleased." />
{:else}
	<div class="bar">
		<button type="button" onclick={runAll} disabled={searching !== null}>
			{searching ? 'Searching…' : `Search all (${groups.length} books)`}
		</button>
	</div>

	{#each groups as g (g.book_id)}
		<div class="card">
			<div class="head">
				<a href="/library/book/{g.book_id}">{g.title}</a>
				<span class="author">{g.author}</span>
			</div>

			{#each g.requests as r (r.id)}
				<div class="format">
					<Badge variant={r.status as BadgeVariant} title={r.type}>
						<Icon name={r.type === 'audiobook' ? 'audiobook' : 'ebook'} size={12} />
					</Badge>

					<div class="results">
						{#if searching === r.id}
							<LoadingState compact />
						{:else if errors[r.id]}
							<p class="err">{errors[r.id]}</p>
						{:else if results[r.id]}
							<ProwlarrResults results={results[r.id]!} requestId={r.id} />
						{:else}
							<span class="idle">Not searched yet</span>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/each}
{/if}

<style>
	.bar {
		margin-bottom: 1rem;
	}

	.bar button {
		padding: 0.35rem 0.8rem;
		font-size: 0.85rem;
		background: var(--accent);
		color: #fff;
		border: none;
		border-radius: var(--radius);
	}

	.bar button:disabled {
		opacity: 0.6;
	}

	.card {
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 0.75rem 1rem;
		margin-bottom: 0.5rem;
	}

	.head {
		font-weight: 500;
		margin-bottom: 0.5rem;
	}

	.author {
		color: var(--text-dim);
		font-size: 0.85rem;
		margin-left: 0.4rem;
		font-weight: 400;
	}

	.format {
		display: flex;
		gap: 0.6rem;
		align-items: flex-start;
		padding: 0.35rem 0;
	}

	.results {
		flex: 1;
		min-width: 0;
	}

	.idle,
	.err {
		font-size: 0.8rem;
		color: var(--text-dim);
	}

	.err {
		color: var(--red);
	}
</style>
