<script lang="ts">
	import { goto } from '$app/navigation';
	import { createManualRequest } from '$lib/api/requests';
	import { toasts } from '$lib/stores/toast.svelte';
	import type { FormatType } from '$lib/types/library';

	interface Props {
		onclose: () => void;
	}

	let { onclose }: Props = $props();

	let title = $state('');
	let author = $state('');
	let type = $state<FormatType>('audiobook');
	let error = $state('');
	let busy = $state(false);
	let dialog = $state<HTMLDialogElement | null>(null);

	/**
	 * A native <dialog> rather than v1's hand-built overlay: focus trapping,
	 * Escape-to-close and the backdrop come for free, where v1 wired each by hand
	 * and its Escape handler only fired when focus was already inside the overlay.
	 */
	$effect(() => {
		dialog?.showModal();
	});

	async function submit(event: Event) {
		event.preventDefault();
		if (!title.trim() || !author.trim()) {
			error = 'Title and author are required.';
			return;
		}
		busy = true;
		error = '';
		try {
			const result = await createManualRequest({
				title: title.trim(),
				author: author.trim(),
				type
			});
			toasts.success('Request created.');
			onclose();
			await goto(`/library/book/${result.book_id}`);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to create request.';
			busy = false;
		}
	}
</script>

<dialog bind:this={dialog} onclose={onclose} oncancel={onclose}>
	<form onsubmit={submit}>
		<h2>Manual Request</h2>

		<label for="mr-title">Title</label>
		<!-- svelte-ignore a11y_autofocus -->
		<input id="mr-title" bind:value={title} type="text" placeholder="Book title" autofocus />

		<label for="mr-author">Author</label>
		<input id="mr-author" bind:value={author} type="text" placeholder="Author name" />

		<label for="mr-type">Format</label>
		<select id="mr-type" bind:value={type}>
			<option value="audiobook">Audiobook</option>
			<option value="ebook">Ebook</option>
		</select>

		<div class="actions">
			<button type="submit" class="primary" disabled={busy}>
				{busy ? 'Requesting…' : 'Request'}
			</button>
			<button type="button" onclick={onclose}>Cancel</button>
			<span class="error">{error}</span>
		</div>
	</form>
</dialog>

<style>
	dialog {
		background: var(--surface);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 1.25rem;
		min-width: min(24rem, 90vw);
	}

	dialog::backdrop {
		background: rgb(0 0 0 / 0.5);
	}

	h2 {
		font-size: 1rem;
		font-weight: 600;
		margin-bottom: 0.75rem;
	}

	label {
		display: block;
		font-size: 0.85rem;
		color: var(--text-dim);
		margin-bottom: 0.35rem;
	}

	/* Padding sets the height; font-size stays >=16px or iOS zooms on focus. */
	input,
	select {
		width: 100%;
		padding: 0.4rem 0.6rem;
		margin-bottom: 0.85rem;
		background: var(--bg);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
	}

	input:focus,
	select:focus {
		border-color: var(--accent);
		outline: none;
	}

	.actions {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.actions button {
		padding: 0.35rem 0.8rem;
		font-size: 0.85rem;
		background: var(--surface2);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
	}

	.actions button.primary {
		background: var(--accent);
		border-color: var(--accent);
		color: #fff;
	}

	.actions button:disabled {
		opacity: 0.6;
	}

	.error {
		font-size: 0.85rem;
		color: var(--red);
	}
</style>
