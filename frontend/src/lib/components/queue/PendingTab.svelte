<script lang="ts">
	import Badge from '../Badge.svelte';
	import EmptyState from '../EmptyState.svelte';
	import ErrorState from '../ErrorState.svelte';
	import Icon from '../Icon.svelte';
	import LoadingState from '../LoadingState.svelte';
	import { approveBook, getPending, rejectBook } from '$lib/api/requests';
	import { formatDate } from '$lib/format';
	import { toasts } from '$lib/stores/toast.svelte';
	import type { FormatType } from '$lib/types/library';
	import type { PendingGroup } from '$lib/types/requests';

	const TYPES: FormatType[] = ['audiobook', 'ebook'];

	let groups = $state<PendingGroup[]>([]);
	let loaded = $state(false);
	let failed = $state(false);

	/** Formats the admin has added on top of what was asked for, per book. */
	let extras = $state<Record<string, Set<FormatType>>>({});
	/** Terminal state per book, so a resolved card stays put instead of vanishing. */
	let resolved = $state<Record<string, 'approved' | 'rejected'>>({});
	let busy = $state<string | null>(null);

	async function load() {
		loaded = false;
		failed = false;
		try {
			const data = await getPending();
			groups = data.groups ?? [];
		} catch {
			failed = true;
		} finally {
			loaded = true;
		}
	}

	$effect(() => {
		load();
	});

	function requestedTypes(g: PendingGroup): Set<FormatType> {
		return new Set(g.requests.map((r) => r.type));
	}

	function toggleExtra(g: PendingGroup, type: FormatType) {
		const current = new Set(extras[g.book_id] ?? []);
		if (current.has(type)) current.delete(type);
		else current.add(type);
		extras = { ...extras, [g.book_id]: current };
	}

	function requesters(g: PendingGroup): string {
		return [...new Set(g.requests.map((r) => r.requested_by).filter(Boolean))].join(', ') || '—';
	}

	function earliest(g: PendingGroup): string {
		return g.requests.reduce((a, b) => (a.created_at < b.created_at ? a : b)).created_at;
	}

	async function approve(g: PendingGroup) {
		busy = g.book_id;
		const types = [...requestedTypes(g), ...(extras[g.book_id] ?? [])];
		try {
			await approveBook(g.book_id, types);
			resolved = { ...resolved, [g.book_id]: 'approved' };
		} catch {
			toasts.error('Failed to approve.');
		} finally {
			busy = null;
		}
	}

	async function reject(g: PendingGroup) {
		busy = g.book_id;
		try {
			await rejectBook(g.book_id);
			resolved = { ...resolved, [g.book_id]: 'rejected' };
		} catch {
			toasts.error('Failed to reject.');
		} finally {
			busy = null;
		}
	}
</script>

{#if !loaded}
	<LoadingState />
{:else if failed}
	<ErrorState message="Failed to load pending requests." onretry={load} />
{:else if groups.length === 0}
	<EmptyState message="No pending requests." />
{:else}
	{#each groups as g (g.book_id)}
		{@const asked = requestedTypes(g)}
		{@const extra = extras[g.book_id] ?? new Set()}
		{@const state = resolved[g.book_id]}
		<div class="card" class:done={state}>
			<div class="body">
				<div class="title">
					<a href="/library/book/{g.book_id}">{g.book_title}</a>
					<span class="author">{g.author || ''}</span>
				</div>

				<div class="row">
					<div class="pills">
						{#each TYPES as type (type)}
							{#if asked.has(type)}
								<Badge variant="pending" title={type}>
									<Icon name={type === 'audiobook' ? 'audiobook' : 'ebook'} size={12} />
								</Badge>
							{:else}
								<!-- Not asked for, but an admin can add it to the approval. -->
								<button
									type="button"
									class="pill"
									class:added={extra.has(type)}
									disabled={!!state}
									title={extra.has(type) ? `Remove ${type}` : `Also approve ${type}`}
									onclick={() => toggleExtra(g, type)}
								>
									<Badge variant={extra.has(type) ? 'requested' : 'neutral'}>
										<Icon name={type === 'audiobook' ? 'audiobook' : 'ebook'} size={12} />
									</Badge>
								</button>
							{/if}
						{/each}
					</div>

					<div class="meta">{requesters(g)} · {formatDate(earliest(g))}</div>
				</div>
			</div>

			<div class="actions">
				{#if state === 'approved'}
					<Badge variant="requested">Approved</Badge>
				{:else if state === 'rejected'}
					<Badge variant="failed">Rejected</Badge>
				{:else}
					<button
						type="button"
						class="act approve"
						disabled={busy === g.book_id}
						onclick={() => approve(g)}
						aria-label="Approve">✓</button
					>
					<button
						type="button"
						class="act reject"
						disabled={busy === g.book_id}
						onclick={() => reject(g)}
						aria-label="Reject">✕</button
					>
				{/if}
			</div>
		</div>
	{/each}
{/if}

<style>
	.card {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 0.75rem 1rem;
		margin-bottom: 0.5rem;
	}

	.card.done {
		opacity: 0.6;
	}

	.body {
		min-width: 0;
		flex: 1;
	}

	.title {
		font-weight: 500;
	}

	.author {
		color: var(--text-dim);
		font-size: 0.85rem;
		margin-left: 0.4rem;
		font-weight: 400;
	}

	.row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.75rem;
		margin-top: 0.4rem;
		flex-wrap: wrap;
	}

	.pills {
		display: flex;
		gap: 0.25rem;
	}

	.pill {
		background: none;
		border: none;
		padding: 0;
		cursor: pointer;
	}

	.meta {
		font-size: 0.8rem;
		color: var(--text-dim);
		white-space: nowrap;
	}

	.actions {
		display: flex;
		gap: 0.35rem;
		flex-shrink: 0;
	}

	.act {
		width: 2rem;
		height: 2rem;
		border-radius: var(--radius);
		border: 1px solid var(--border);
		background: none;
		font-size: 0.95rem;
	}

	.act.approve {
		color: var(--green);
	}

	.act.reject {
		color: var(--red);
	}

	.act:hover:not(:disabled) {
		border-color: currentColor;
	}

	.act:disabled {
		opacity: 0.5;
	}
</style>
