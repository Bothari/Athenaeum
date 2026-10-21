<script lang="ts">
	import Badge from './Badge.svelte';
	import type { BadgeVariant } from './Badge.svelte';
	import FormatHistory from './FormatHistory.svelte';
	import Icon from './Icon.svelte';
	import ProwlarrResults from './ProwlarrResults.svelte';
	import {
		cancelRequest,
		createRequest,
		organizeRequest,
		searchIndexers
	} from '$lib/api/requests';
	import { auth } from '$lib/stores/auth.svelte';
	import { toasts } from '$lib/stores/toast.svelte';
	import type { FormatType } from '$lib/types/library';
	import type { BookFormatDetail, BookRequestDetail } from '$lib/types/detail';
	import type { IndexerResult } from '$lib/types/requests';

	/**
	 * One expandable format row on book detail. Three states, as in v1:
	 * in_library (held), a live request, or missing.
	 */
	interface Props {
		bookId: string;
		type: FormatType;
		status: 'in_library' | 'missing' | string;
		narrator?: string | null;
		format?: BookFormatDetail | null;
		request?: BookRequestDetail | null;
		onrefresh: () => void;
	}

	let { bookId, type, status, narrator, format, request, onrefresh }: Props = $props();

	let open = $state(false);
	let busy = $state(false);
	let searching = $state(false);
	let results = $state<IndexerResult[] | null>(null);
	let searchError = $state('');
	let activeRequestId = $state<string | null>(null);
	let narratorInput = $state('');

	const isAudio = $derived(type === 'audiobook');
	const typeLabel = $derived(isAudio ? 'Audiobook' : 'Ebook');

	const badgeVariant = $derived<BadgeVariant>(
		status === 'in_library' ? 'completed' : status === 'missing' ? 'neutral' : (status as BadgeVariant)
	);

	/** Searching is only meaningful in states where a grab could still help. */
	const canSearch = $derived(
		auth.isAdmin && !!request && ['requested', 'failed', 'completed'].includes(request.status)
	);
	const canRetry = $derived(auth.isAdmin && request?.status === 'failed');
	/** Users may cancel their own requests; admins may cancel any. */
	const canCancel = $derived(
		!!request &&
			(auth.isAdmin ||
				!request.requested_by_user_id ||
				request.requested_by_user_id === auth.user?.user_id)
	);

	async function runSearch(requestId: string) {
		searching = true;
		searchError = '';
		results = null;
		try {
			const data = await searchIndexers(requestId);
			if (data.error) searchError = data.error;
			else {
				results = data.results ?? [];
				activeRequestId = requestId;
			}
		} catch (err) {
			searchError = `Search failed: ${err instanceof Error ? err.message : String(err)}`;
		} finally {
			searching = false;
		}
	}

	/** For a held format: creates a replacement request, then searches against it. */
	async function searchReplacement() {
		searching = true;
		searchError = '';
		results = null;
		try {
			const created = await createRequest({
				book_id: bookId,
				type,
				narrator: isAudio ? narratorInput.trim() || null : null,
				replace: true
			});
			if (created.skipped) {
				searchError = 'Could not create replacement request.';
				return;
			}
			await runSearch(created.id);
		} catch (err) {
			searchError = `Search failed: ${err instanceof Error ? err.message : String(err)}`;
		} finally {
			searching = false;
		}
	}

	async function requestFormat() {
		busy = true;
		try {
			const result = await createRequest({
				book_id: bookId,
				type,
				narrator: isAudio ? narratorInput.trim() || null : null
			});
			if (result.skipped) toasts.info('Already requested');
			else toasts.success('Request created');
			onrefresh();
		} catch {
			toasts.error('Failed to create request');
		} finally {
			busy = false;
		}
	}

	async function retryOrganize() {
		if (!request) return;
		busy = true;
		try {
			await organizeRequest(request.id);
			toasts.success('Organize restarted');
			// The backend works asynchronously; v1 waited before refetching.
			setTimeout(onrefresh, 1500);
		} catch {
			toasts.error('Retry failed');
			busy = false;
		}
	}

	async function cancel() {
		if (!request) return;
		busy = true;
		try {
			await cancelRequest(request.id);
			toasts.success('Request cancelled');
			onrefresh();
		} catch {
			toasts.error('Failed to cancel request');
			busy = false;
		}
	}
</script>

<div class="row" class:missing={status === 'missing'}>
	<button type="button" class="trigger" onclick={() => (open = !open)} aria-expanded={open}>
		<Badge variant={badgeVariant} title={status === 'in_library' ? 'In library' : status}>
			<Icon name={isAudio ? 'audiobook' : 'ebook'} size={12} />
		</Badge>
		<span class="type">{typeLabel}</span>
		{#if narrator}<span class="narrator">{narrator}</span>{/if}
		<span class="chevron" class:open><Icon name="chevron-down" size={14} /></span>
	</button>

	{#if open}
		<div class="content">
			{#if status === 'in_library' && format}
				{#if format.abs_url}
					<a href={format.abs_url} target="_blank" rel="noreferrer">Open in AudioBookShelf</a>
				{:else}
					<div class="dim">Added from AudioBookShelf library</div>
				{/if}

				{#if auth.isAdmin}
					<div class="actions">
						{#if isAudio}
							<input type="text" bind:value={narratorInput} placeholder="Narrator (optional)" />
						{/if}
						<button type="button" onclick={searchReplacement} disabled={searching}>
							{searching ? 'Searching…' : 'Search Prowlarr'}
						</button>
					</div>
				{/if}
			{:else if request}
				<div class="kv">
					<span class="dim">Status</span>
					<Badge variant={request.status as BadgeVariant}>{request.status}</Badge>
				</div>

				<div class="actions">
					{#if canRetry}
						<button type="button" onclick={retryOrganize} disabled={busy}>Retry organize</button>
					{/if}
					{#if canSearch}
						<button type="button" onclick={() => runSearch(request.id)} disabled={searching}>
							{searching ? 'Searching…' : 'Search Prowlarr'}
						</button>
					{/if}
					{#if canCancel}
						<button type="button" onclick={cancel} disabled={busy}>Cancel</button>
					{/if}
				</div>
			{:else}
				<div class="actions">
					{#if isAudio}
						<input type="text" bind:value={narratorInput} placeholder="Narrator (optional)" />
					{/if}
					<button type="button" class="primary" onclick={requestFormat} disabled={busy}>
						Request {type}
					</button>
				</div>
			{/if}

			{#if searchError}
				<p class="dim">{searchError}</p>
			{/if}

			{#if results && activeRequestId}
				<div class="results">
					<ProwlarrResults {results} requestId={activeRequestId} onsuccess={onrefresh} />
				</div>
			{/if}

			<FormatHistory {bookId} {type} />
		</div>
	{/if}
</div>

<style>
	.row {
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		margin-bottom: 0.25rem;
	}

	.row.missing .trigger {
		opacity: 0.75;
	}

	.trigger {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		width: 100%;
		background: none;
		border: none;
		padding: 0.5rem 0.75rem;
		color: inherit;
		font-size: 0.875rem;
		text-align: left;
	}

	.type {
		font-weight: 500;
	}

	.narrator {
		color: var(--text-dim);
		font-size: 0.8rem;
	}

	.chevron {
		margin-left: auto;
		display: flex;
		color: var(--text-dim);
		transition: transform 0.15s;
	}

	.chevron.open {
		transform: rotate(180deg);
	}

	.content {
		padding: 0 0.75rem 0.75rem;
		font-size: 0.85rem;
	}

	.kv {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.dim {
		color: var(--text-dim);
	}

	.actions {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
		margin-top: 0.5rem;
	}

	/* Height from padding; font-size stays >=16px or iOS zooms on focus. */
	input {
		flex: 1;
		min-width: 8rem;
		padding: 0.3rem 0.5rem;
		background: var(--bg);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
	}

	.actions button {
		padding: 0.2rem 0.6rem;
		font-size: 0.8rem;
		background: var(--surface2);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		white-space: nowrap;
	}

	.actions button.primary {
		background: var(--accent);
		color: #fff;
		border-color: var(--accent);
	}

	.actions button:disabled {
		opacity: 0.6;
	}

	.results {
		margin-top: 0.5rem;
	}
</style>
