<script lang="ts">
	import { confirmPack, rescanPack } from '$lib/api/series';
	import { toasts } from '$lib/stores/toast.svelte';
	import type {
		ConfirmedMapping,
		PackFileMapping,
		PackSeriesBook,
		SeriesDownload
	} from '$lib/types/series';

	/**
	 * Review step for a downloaded series pack: each file in the pack is matched
	 * to a book, and the operator confirms or corrects the matches before anything
	 * is moved into the library.
	 */
	interface Props {
		seriesId: string;
		download: SeriesDownload;
		onchange: () => void;
	}

	let { seriesId, download, onchange }: Props = $props();

	/** Older records stored a bare array; newer ones an object. Both still exist. */
	const raw = $derived(download.proposed_mappings ?? {});
	const fileMappings = $derived<PackFileMapping[]>(
		Array.isArray(raw) ? raw : (raw.file_mappings ?? [])
	);
	const seriesBooks = $derived<PackSeriesBook[]>(Array.isArray(raw) ? [] : (raw.series_books ?? []));

	/** Seeded from the matcher's best guess; empty string means skip this file. */
	let selections = $state<string[]>([]);
	let seeded = $state(false);
	let busy = $state(false);
	let rescanning = $state(false);

	$effect(() => {
		if (seeded) return;
		selections = fileMappings.map((m) => m.book_id ?? '');
		seeded = true;
	});

	const confirmed = $derived.by<ConfirmedMapping[]>(() => {
		const out: ConfirmedMapping[] = [];
		for (const [i, m] of fileMappings.entries()) {
			const bookId = selections[i];
			if (!bookId) continue;
			out.push({
				filepath: m.filepath,
				filename: m.filename,
				book_id: bookId,
				book_title: seriesBooks.find((b) => b.id === bookId)?.title ?? m.book_title ?? '',
				score: m.score,
				action: 'place'
			});
		}
		return out;
	});

	/** Books in the series that no file was assigned to and we don't already hold. */
	const gaps = $derived.by(() => {
		const used = new Set(selections.filter(Boolean));
		return seriesBooks.filter((b) => !used.has(b.id) && !b.in_library);
	});

	async function rescan() {
		rescanning = true;
		try {
			await rescanPack(seriesId, download.id);
			onchange();
		} catch (err) {
			toasts.error(`Re-scan failed: ${err instanceof Error ? err.message : String(err)}`);
			rescanning = false;
		}
	}

	async function confirm() {
		busy = true;
		try {
			await confirmPack(seriesId, download.id, confirmed);
			toasts.success('Organising series pack…');
			onchange();
		} catch (err) {
			toasts.error(`Failed: ${err instanceof Error ? err.message : String(err)}`);
			busy = false;
		}
	}
</script>

<div class="heading-row">
	<span class="heading">Series Pack — Review Mappings</span>
	<button type="button" class="rescan" onclick={rescan} disabled={rescanning}>
		{rescanning ? 'Re-scanning…' : 'Re-scan'}
	</button>
</div>

<div class="card">
	{#each fileMappings as m, i (m.filepath)}
		<div class="row">
			<div class="filename">{m.filename}</div>
			<div class="controls">
				<select bind:value={selections[i]}>
					<option value="">— Skip —</option>
					{#each seriesBooks as book (book.id)}
						<option value={book.id}>{book.title}{book.in_library ? ' (in library)' : ''}</option>
					{/each}
				</select>
				{#if m.score != null && m.score > 0}
					<span class="score">{m.score}</span>
				{/if}
			</div>
		</div>
	{/each}

	{#if gaps.length}
		<div class="gaps">
			{gaps.length} book{gaps.length === 1 ? '' : 's'} without a file: {gaps
				.map((g) => g.title)
				.join(', ')}
		</div>
	{/if}

	<div class="footer">
		<button type="button" class="confirm" disabled={confirmed.length === 0 || busy} onclick={confirm}>
			{#if busy}
				Starting…
			{:else if confirmed.length === 0}
				Nothing to organise
			{:else}
				Confirm &amp; organise ({confirmed.length} file{confirmed.length === 1 ? '' : 's'})
			{/if}
		</button>
	</div>
</div>

<style>
	.heading-row {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin: 1.5rem 0 0.5rem;
	}

	.heading {
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--text-dim);
	}

	.rescan {
		margin-left: auto;
		padding: 0.2rem 0.6rem;
		font-size: 0.8rem;
		background: var(--surface2);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
	}

	.card {
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
	}

	.row {
		padding: 0.5rem 1rem;
		border-bottom: 1px solid var(--border);
	}

	.filename {
		font-family: ui-monospace, monospace;
		font-size: 0.75rem;
		color: var(--text-dim);
		overflow-wrap: anywhere;
		margin-bottom: 0.3rem;
	}

	.controls {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		flex-wrap: wrap;
	}

	/* Padding sets the height; font-size stays >=16px or iOS zooms on focus. */
	select {
		flex: 1;
		min-width: 120px;
		max-width: 340px;
		padding: 0.2rem 0.4rem;
		background: var(--bg);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
	}

	.score {
		background: var(--surface2);
		color: var(--text-dim);
		font-size: 0.7rem;
		border-radius: 999px;
		padding: 0.1rem 0.4rem;
		flex-shrink: 0;
	}

	.gaps {
		padding: 0.5rem 1rem;
		font-size: 0.8rem;
		color: var(--text-dim);
		border-top: 1px solid var(--border);
	}

	.footer {
		padding: 0.75rem 1rem;
		display: flex;
		justify-content: flex-end;
		border-top: 1px solid var(--border);
	}

	.confirm {
		padding: 0.35rem 0.8rem;
		font-size: 0.85rem;
		background: var(--accent);
		color: #fff;
		border: none;
		border-radius: var(--radius);
	}

	.confirm:disabled {
		opacity: 0.6;
	}
</style>
