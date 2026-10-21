<script lang="ts">
	import { deleteBookFormat, previewFormatFiles } from '$lib/api/books';
	import type { FormatFilesPreview } from '$lib/api/books';
	import { toasts } from '$lib/stores/toast.svelte';
	import type { FormatType } from '$lib/types/library';

	/**
	 * Confirms removing one format of a book, optionally with its files.
	 *
	 * The file list is fetched rather than described, because the organized path is
	 * not recorded anywhere — it is re-derived from the book's author and title, and
	 * a title can change after the fact. So the user is shown the actual paths that
	 * were found before agreeing to anything, and the option is withheld entirely
	 * when nothing matching the book could be located.
	 */
	interface Props {
		bookId: string;
		type: FormatType;
		title: string;
		onclose: () => void;
		ondeleted: () => void;
	}

	let { bookId, type, title, onclose, ondeleted }: Props = $props();

	let dialog = $state<HTMLDialogElement | null>(null);
	let preview = $state<FormatFilesPreview | null>(null);
	let loadFailed = $state(false);
	let withFiles = $state(false);
	let busy = $state(false);

	$effect(() => {
		dialog?.showModal();
	});

	$effect(() => {
		let cancelled = false;
		previewFormatFiles(bookId, type)
			.then((p) => {
				if (!cancelled) preview = p;
			})
			.catch(() => {
				// The rows can still be deleted without knowing the files; only the
				// file option depends on this, so fail soft rather than blocking.
				if (!cancelled) loadFailed = true;
			});
		return () => {
			cancelled = true;
		};
	});

	const media = $derived(preview?.files.filter((f) => f.kind === 'media') ?? []);
	const sidecars = $derived(preview?.files.filter((f) => f.kind === 'sidecar') ?? []);
	const others = $derived(preview?.files.filter((f) => f.kind === 'other') ?? []);
	const canDeleteFiles = $derived(preview?.locatable === true);

	function kb(bytes: number): string {
		if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
		return `${Math.max(1, Math.round(bytes / 1024))} KB`;
	}

	/** Trailing path segment, which is all that distinguishes these entries. */
	function basename(path: string): string {
		return path.slice(path.lastIndexOf('/') + 1);
	}

	async function confirm() {
		busy = true;
		try {
			const result = await deleteBookFormat(bookId, type, withFiles && canDeleteFiles);
			const removed = result.files_removed.length;
			toasts.success(
				removed > 0
					? `Deleted ${type} and ${removed} file${removed === 1 ? '' : 's'}.`
					: `Deleted ${type}.`
			);
			if (result.files_failed.length > 0) {
				toasts.error(`${result.files_failed.length} file(s) could not be removed.`);
			}
			ondeleted();
			onclose();
		} catch {
			toasts.error(`Could not delete the ${type}.`);
			busy = false;
		}
	}
</script>

<dialog bind:this={dialog} onclose={onclose}>
	<h2>Delete {type}?</h2>

	<p class="what">
		Removes the {type} of <strong>{title}</strong> from Athenaeum — its library entry
		and any request history for it. The other format, if you hold one, is untouched.
	</p>

	{#if preview === null && !loadFailed}
		<p class="dim">Looking for the files…</p>
	{:else if loadFailed}
		<p class="dim">Could not check for files, so only the library entry can be removed.</p>
	{:else if canDeleteFiles}
		<label class="opt">
			<input type="checkbox" bind:checked={withFiles} />
			<span>Also delete the files below</span>
		</label>

		<ul class="files" class:armed={withFiles}>
			{#each media as f (f.path)}
				<li><span class="name">{basename(f.path)}</span><span class="size">{kb(f.size)}</span></li>
			{/each}
			{#each sidecars as f (f.path)}
				<li class="side">
					<span class="name">{basename(f.path)}</span><span class="size">{kb(f.size)}</span>
				</li>
			{/each}
		</ul>

		{#if others.length > 0}
			<p class="dim">
				{others.length} other file{others.length === 1 ? '' : 's'} in that folder will be left
				alone, and the folder kept.
			</p>
		{/if}

		<p class="dim">
			This is the library copy only. If it came from a torrent, the downloader still
			has its own copy and will keep seeding.
		</p>
	{:else}
		<label class="opt disabled">
			<input type="checkbox" disabled />
			<span>Also delete the files</span>
		</label>
		<p class="dim">
			No {type} file could be found where this book would have been organized, so there
			is nothing to delete. The library entry can still be removed.
		</p>
	{/if}

	<div class="actions">
		<button type="button" class="danger" onclick={confirm} disabled={busy}>
			{busy ? 'Deleting…' : withFiles && canDeleteFiles ? 'Delete and remove files' : 'Delete'}
		</button>
		<button type="button" onclick={onclose} disabled={busy}>Cancel</button>
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
		text-transform: capitalize;
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

	.opt {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.9rem;
		margin-bottom: 0.6rem;
		cursor: pointer;
	}

	.opt.disabled {
		cursor: default;
		color: var(--text-dim);
	}

	/* The list is the point of the dialog, so it stays readable rather than
	   truncating: long paths wrap and a big folder scrolls. */
	.files {
		list-style: none;
		margin: 0 0 0.6rem;
		padding: 0.5rem 0.6rem;
		max-height: 11rem;
		overflow-y: auto;
		background: var(--bg);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		font-size: 0.82rem;
	}

	.files.armed {
		border-color: var(--color-error, crimson);
	}

	.files li {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		padding: 0.15rem 0;
	}

	.files li.side {
		color: var(--text-dim);
	}

	.files .name {
		overflow-wrap: anywhere;
	}

	.files .size {
		flex: none;
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
