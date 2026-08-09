<script lang="ts">
	import Icon from './Icon.svelte';
	import { downloadResult } from '$lib/api/requests';
	import { formatBytes } from '$lib/format';
	import { auth } from '$lib/stores/auth.svelte';
	import { toasts } from '$lib/stores/toast.svelte';
	import type { IndexerResult } from '$lib/types/requests';

	interface Props {
		results: IndexerResult[];
		requestId: string;
		onsuccess?: () => void;
	}

	let { results, requestId, onsuccess }: Props = $props();

	let grabbing = $state<number | null>(null);
	let grabbed = $state<Set<number>>(new Set());

	const FORMAT_RE = /\b(mp3|m4b|m4a|flac|opus|ogg|aac|epub|mobi|azw3?|pdf)\b/i;

	function formatTag(title?: string | null): string {
		return title?.match(FORMAT_RE)?.[1].toUpperCase() ?? '';
	}

	/** v1's thresholds: >=60 would auto-download, >=40 borderline. */
	function scoreTone(score?: number | null): string {
		if (score == null) return '';
		if (score >= 60) return 'good';
		if (score >= 40) return 'mid';
		return 'bad';
	}

	function age(days?: number | null): string | null {
		if (days == null) return null;
		if (days === 0) return 'today';
		if (days < 365) return `${days}d`;
		return `${Math.floor(days / 365)}y`;
	}

	async function grab(result: IndexerResult, index: number) {
		grabbing = index;
		try {
			await downloadResult(requestId, result);
			grabbed.add(index);
			toasts.success('Download started!');
			onsuccess?.();
		} catch (err) {
			toasts.error(`Download failed: ${err instanceof Error ? err.message : String(err)}`);
		} finally {
			grabbing = null;
		}
	}
</script>

{#if results.length === 0}
	<p class="none">No results found.</p>
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
						{#if formatTag(result.title)}
							<span class="tag">{formatTag(result.title)}</span>
						{/if}
						<span>{result.protocol === 'torrent' ? 'Torrent' : 'Usenet'}</span>
						<span>{formatBytes(result.size)}</span>
						{#if result.seeders != null}<span>{result.seeders}S</span>{/if}
						{#if age(result.age)}<span class="dim">{age(result.age)}</span>{/if}
						<span>{result.indexer || '—'}</span>
						{#if result.score != null}
							<span
								class="score {scoreTone(result.score)}"
								title={result.score >= 60 ? 'Would auto-download' : 'Would NOT auto-download'}
							>
								{result.score}%
							</span>
						{/if}
					</div>

					<!--
						v1 called querySelector('.prowlarr-dl-btn').onclick unconditionally
						while only rendering the button for admins, so a non-admin reaching
						this code threw and killed the whole result list. Guarded properly
						here.
					-->
					{#if auth.isAdmin}
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
					{/if}
				</div>
			</div>
		{/each}
	</div>
{/if}

<style>
	.none {
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
		word-break: break-word;
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
		color: var(--text);
	}

	.tag {
		background: var(--surface2);
		border-radius: 999px;
		padding: 0.1rem 0.4rem;
		font-size: 0.72rem;
	}

	.dim {
		color: var(--text-dim);
	}

	.score {
		font-weight: 600;
	}

	.score.good {
		color: var(--green);
	}

	.score.mid {
		color: var(--yellow);
	}

	.score.bad {
		color: var(--red);
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
