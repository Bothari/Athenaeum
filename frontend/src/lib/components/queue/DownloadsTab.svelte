<script lang="ts">
	import Badge from '../Badge.svelte';
	import type { BadgeVariant } from '../Badge.svelte';
	import EmptyState from '../EmptyState.svelte';
	import ErrorState from '../ErrorState.svelte';
	import Icon from '../Icon.svelte';
	import LoadingState from '../LoadingState.svelte';
	import { listDownloads } from '$lib/api/status';
	import { formatBytes, formatEta } from '$lib/format';
	import type { DownloadItem } from '$lib/types/status';

	const POLL_MS = 5000;

	interface DownloadsResponse {
		items?: DownloadItem[];
		client_unreachable?: boolean;
	}

	let items = $state<DownloadItem[]>([]);
	let unreachable = $state(false);
	let loaded = $state(false);
	let failed = $state(false);

	async function refresh() {
		try {
			const data = (await listDownloads()) as DownloadsResponse;
			items = data.items ?? [];
			unreachable = data.client_unreachable === true;
			failed = false;
		} catch {
			failed = true;
		} finally {
			loaded = true;
		}
	}

	$effect(() => {
		refresh();
		const timer = setInterval(refresh, POLL_MS);
		return () => clearInterval(timer);
	});
</script>

{#if !loaded}
	<LoadingState />
{:else if failed}
	<ErrorState onretry={refresh} />
{:else}
	{#if unreachable}
		<div class="warn">Download client unreachable — showing last known status.</div>
	{/if}

	{#if items.length === 0}
		<EmptyState message="Nothing downloading right now." />
	{:else}
		{#each items as dl, i (i)}
			<div class="card">
				<div class="head">
					<div class="who">
						<div class="title">{dl.book_title || '—'}</div>
						<div class="sub">
							{dl.author || ''}{dl.author && dl.type ? ' · ' : ''}
							{#if dl.type}
								<Icon name={dl.type === 'audiobook' ? 'audiobook' : 'ebook'} size={12} />
							{/if}
						</div>
						{#if dl.release_title || dl.indexer}
							<div class="release">{dl.release_title || dl.indexer}</div>
						{/if}
					</div>
					<Badge variant={(dl.status || 'downloading') as BadgeVariant}>
						{dl.status || 'downloading'}
					</Badge>
				</div>

				{#if dl.progress != null}
					<div class="track"><div class="fill" style="width:{Math.round(dl.progress)}%"></div></div>
					<div class="meta">
						{Math.round(dl.progress)}%{formatEta(dl.eta) != null
							? ` · ETA ${formatEta(dl.eta)}`
							: ''}{dl.speed ? ` · ${formatBytes(dl.speed)}/s` : ''}{dl.size
							? ` · ${formatBytes(dl.size)}`
							: ''}
					</div>
				{/if}
			</div>
		{/each}
	{/if}
{/if}

<style>
	.warn {
		background: var(--surface2);
		border-left: 3px solid var(--yellow);
		border-radius: var(--radius);
		padding: 0.6rem 0.8rem;
		font-size: 0.85rem;
		margin-bottom: 1rem;
	}

	.card {
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 0.75rem 1rem;
		margin-bottom: 0.5rem;
	}

	.head {
		display: flex;
		justify-content: space-between;
		gap: 0.5rem;
		align-items: flex-start;
	}

	.who {
		min-width: 0;
	}

	.title {
		font-weight: 500;
	}

	.sub {
		display: flex;
		align-items: center;
		gap: 0.2rem;
		font-size: 0.8rem;
		color: var(--text-dim);
	}

	.release {
		font-size: 0.75rem;
		color: var(--text-dim);
		margin-top: 0.2rem;
		word-break: break-word;
	}

	.track {
		height: 6px;
		border-radius: 3px;
		background: var(--surface2);
		overflow: hidden;
		margin-top: 0.5rem;
	}

	.fill {
		height: 100%;
		background: var(--accent);
		transition: width 0.4s ease;
	}

	.meta {
		font-size: 0.78rem;
		color: var(--text-dim);
		margin-top: 0.25rem;
	}
</style>
