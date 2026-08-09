<script lang="ts">
	import Badge from './Badge.svelte';
	import type { BadgeVariant } from './Badge.svelte';
	import Icon from './Icon.svelte';
	import { listDownloads } from '$lib/api/status';
	import { formatBytes, formatEta } from '$lib/format';
	import type { DownloadItem } from '$lib/types/status';

	const POLL_MS = 5000;

	let items = $state<DownloadItem[]>([]);

	async function refresh() {
		try {
			const data = await listDownloads();
			// Only things actually moving; v1 applied the same filter.
			items = (data.items ?? []).filter(
				(d) => d.progress != null || d.status === 'snatched' || d.status === 'downloading'
			);
		} catch {
			// Transient failures shouldn't blank the section mid-poll.
			items = [];
		}
	}

	/** Polls while mounted. The interval is cleared on unmount by the returned
	 *  teardown, replacing v1's one-shot hashchange listener. */
	$effect(() => {
		refresh();
		const timer = setInterval(refresh, POLL_MS);
		return () => clearInterval(timer);
	});
</script>

{#if items.length > 0}
	<h2 class="section-heading">Active Downloads</h2>
	{#each items as dl, i (i)}
		<div class="card">
			<div class="head">
				<div>
					<div class="title">{dl.book_title || '—'}</div>
					<div class="sub">
						{dl.author || ''}{dl.author && dl.type ? ' · ' : ''}
						{#if dl.type}
							<Icon name={dl.type === 'audiobook' ? 'audiobook' : 'ebook'} size={12} />
						{/if}
					</div>
				</div>
				<Badge variant={(dl.status || 'downloading') as BadgeVariant}>
					{dl.status || 'downloading'}
				</Badge>
			</div>

			{#if dl.progress != null}
				<div class="track">
					<div class="fill" style="width:{Math.round(dl.progress)}%"></div>
				</div>
				<div class="meta">
					{Math.round(dl.progress)}%{formatEta(dl.eta) != null ? ` · ETA ${formatEta(dl.eta)}` : ''}{dl.speed
						? ` · ${formatBytes(dl.speed)}/s`
						: ''}{dl.size ? ` · ${formatBytes(dl.size)}` : ''}
				</div>
			{/if}
		</div>
	{/each}
{/if}

<style>
	.section-heading {
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
		margin-bottom: 0.5rem;
	}

	.head {
		display: flex;
		justify-content: space-between;
		gap: 0.5rem;
		align-items: flex-start;
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
