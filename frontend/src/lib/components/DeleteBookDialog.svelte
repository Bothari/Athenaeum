<script lang="ts">
	import { untrack } from 'svelte';
	import { deleteBook, previewFormatFiles } from '$lib/api/books';
	import type { FormatFilesPreview } from '$lib/api/books';
	import { toasts } from '$lib/stores/toast.svelte';
	import type { FormatType } from '$lib/types/library';

	/**
	 * Confirms deleting a book, with the option to narrow it to some of its formats
	 * and to remove the files too.
	 *
	 * One control rather than one per format, because deleting every format used to
	 * leave the books row behind and the detail page stayed reachable with nothing
	 * on it. Clearing the last format now removes the entry, so the question the
	 * dialog asks is "what goes" rather than "which row".
	 *
	 * File lists are fetched, not described: the organized path is re-derived from
	 * author and title rather than recorded, so it can miss, and the user should see
	 * the paths that were actually found before agreeing.
	 */
	interface Props {
		bookId: string;
		title: string;
		/** Everything deletable: formats held, plus any that exist only as a request.
		 *  A request left behind is enough to keep the book alive, so it has to be
		 *  offered here or the book cannot be removed at all. */
		deletableFormats: FormatType[];
		onclose: () => void;
		ondeleted: () => void;
	}

	let { bookId, title, deletableFormats, onclose, ondeleted }: Props = $props();

	let dialog = $state<HTMLDialogElement | null>(null);
	let selected = $state<Set<FormatType>>(new Set(untrack(() => deletableFormats)));
	let previews = $state<Partial<Record<FormatType, FormatFilesPreview>>>({});
	let fetched = $state(false);
	let withFiles = $state(false);
	const loaded = $derived(deletableFormats.length === 0 || fetched);
	let busy = $state(false);

	$effect(() => {
		dialog?.showModal();
	});

	$effect(() => {
		if (deletableFormats.length === 0) return;
		let cancelled = false;
		Promise.all(
			deletableFormats.map((t) =>
				previewFormatFiles(bookId, t)
					.then((p) => [t, p] as const)
					// Fail soft per format: the rows can still be deleted without
					// knowing the files, so only the file option depends on this.
					.catch(() => [t, null] as const)
			)
		).then((pairs) => {
			if (cancelled) return;
			const next: Partial<Record<FormatType, FormatFilesPreview>> = {};
			for (const [t, p] of pairs) if (p) next[t] = p;
			previews = next;
			fetched = true;
		});
		return () => {
			cancelled = true;
		};
	});

	/** Deleting everything the book holds also removes the entry. So does deleting
	 *  from a book that already holds nothing. */
	const entryGoes = $derived(
		deletableFormats.length === 0 || deletableFormats.every((t) => selected.has(t))
	);
	const selectedList = $derived(deletableFormats.filter((t) => selected.has(t)));
	const filesForSelection = $derived(
		selectedList.flatMap((t) => previews[t]?.files.filter((f) => f.kind !== 'other') ?? [])
	);
	const anyLocatable = $derived(selectedList.some((t) => previews[t]?.locatable === true));
	const nothingSelected = $derived(deletableFormats.length > 0 && selectedList.length === 0);

	function toggle(t: FormatType) {
		const next = new Set(selected);
		if (next.has(t)) next.delete(t);
		else next.add(t);
		selected = next;
	}

	function label(t: FormatType): string {
		const p = previews[t];
		if (!p) return t;
		const media = p.files.filter((f) => f.kind === 'media');
		if (media.length === 0) return `${t} — no file found`;
		const bytes = media.reduce((n, f) => n + f.size, 0);
		const size =
			bytes >= 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.round(bytes / 1024)} KB`;
		return `${t} — ${media.length} file${media.length === 1 ? '' : 's'}, ${size}`;
	}

	async function confirm() {
		busy = true;
		try {
			const result = await deleteBook(bookId, selectedList, withFiles && anyLocatable);
			const n = result.files_removed.length;
			toasts.success(
				result.entry_deleted
					? n > 0
						? `Deleted ${title} and ${n} file${n === 1 ? '' : 's'}.`
						: `Deleted ${title}.`
					: `Deleted ${result.formats_deleted.join(' and ')}.`
			);
			if (result.files_failed.length > 0) {
				toasts.error(`${result.files_failed.length} file(s) could not be removed.`);
			}
			ondeleted();
			onclose();
		} catch {
			toasts.error('Could not delete.');
			busy = false;
		}
	}
</script>

<dialog bind:this={dialog} onclose={onclose}>
	<h2>Delete {title}?</h2>

	{#if deletableFormats.length === 0}
		<p class="what">
			This book holds nothing and nothing is requested for it, so only the entry itself
			is left to remove.
		</p>
	{:else}
		<p class="what">Choose what to remove. Clearing everything removes the book entry too.</p>

		{#if !loaded}
			<p class="dim">Looking for the files…</p>
		{:else}
			<ul class="formats">
				{#each deletableFormats as t (t)}
					<li>
						<label>
							<input type="checkbox" checked={selected.has(t)} onchange={() => toggle(t)} />
							<span class="fmt">{label(t)}</span>
						</label>
					</li>
				{/each}
			</ul>

			{#if anyLocatable}
				<label class="opt">
					<input type="checkbox" bind:checked={withFiles} />
					<span>Also delete the files from the library</span>
				</label>
				{#if withFiles}
					<ul class="files">
						{#each filesForSelection as f (f.path)}
							<li class:side={f.kind === 'sidecar'}>
								{f.path.slice(f.path.lastIndexOf('/') + 1)}
							</li>
						{/each}
					</ul>
				{/if}
				<p class="dim">
					The library copy only. If it came from a torrent, the downloader keeps its own
					copy and carries on seeding.
				</p>
			{:else if selectedList.length > 0}
				<p class="dim">
					No files could be found where these would have been organized, so there is
					nothing on disk to delete.
				</p>
			{/if}
		{/if}
	{/if}

	{#if entryGoes && deletableFormats.length > 0}
		<p class="dim strong">The book entry will be removed as well.</p>
	{/if}

	<div class="actions">
		<button type="button" class="danger" onclick={confirm} disabled={busy || nothingSelected}>
			{busy ? 'Deleting…' : entryGoes ? 'Delete book' : 'Delete selected'}
		</button>
		<button type="button" onclick={onclose} disabled={busy}>Cancel</button>
		{#if nothingSelected}<span class="dim">Nothing selected.</span>{/if}
	</div>
</dialog>

<style>
	dialog {
		background: var(--surface);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 1.25rem;
		min-width: min(30rem, 92vw);
		max-width: min(36rem, 92vw);
	}

	dialog::backdrop {
		background: rgb(0 0 0 / 0.5);
	}

	h2 {
		font-size: 1rem;
		font-weight: 600;
		margin-bottom: 0.6rem;
	}

	.what {
		font-size: 0.9rem;
		margin-bottom: 0.85rem;
	}

	.dim {
		color: var(--text-dim);
		font-size: 0.82rem;
		margin-bottom: 0.6rem;
	}

	.dim.strong {
		color: var(--color-error, crimson);
	}

	.formats {
		list-style: none;
		margin: 0 0 0.85rem;
		padding: 0;
	}

	.formats label,
	.opt {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.9rem;
		padding: 0.15rem 0;
		cursor: pointer;
	}

	.fmt {
		text-transform: capitalize;
	}

	.opt {
		margin-bottom: 0.6rem;
	}

	/* Long paths wrap and a big folder scrolls, rather than truncating — the list is
	   the point of the dialog. */
	.files {
		list-style: none;
		margin: 0 0 0.6rem;
		padding: 0.5rem 0.6rem;
		max-height: 9rem;
		overflow-y: auto;
		background: var(--bg);
		border: 1px solid var(--color-error, crimson);
		border-radius: var(--radius);
		font-size: 0.8rem;
	}

	.files li {
		padding: 0.1rem 0;
		overflow-wrap: anywhere;
	}

	.files li.side {
		color: var(--text-dim);
	}

	.actions {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-top: 0.4rem;
	}

	.actions button {
		padding: 0.35rem 0.75rem;
		background: var(--bg);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		cursor: pointer;
	}

	.actions button.danger {
		background: var(--color-error, crimson);
		border-color: var(--color-error, crimson);
		color: white;
	}

	.actions button:disabled {
		opacity: 0.6;
		cursor: default;
	}
</style>
