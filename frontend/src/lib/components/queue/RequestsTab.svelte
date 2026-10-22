<script lang="ts">
	import { page } from '$app/state';
	import { setSearchParam } from '$lib/url';
	import Badge from '../Badge.svelte';
	import type { BadgeVariant } from '../Badge.svelte';
	import ConfirmButton from '../ConfirmButton.svelte';
	import DataTable from '../DataTable.svelte';
	import Icon from '../Icon.svelte';
	import { cancelRequest, listRequests, organizeRequest, retryFailed } from '$lib/api/requests';
	import { formatDate } from '$lib/format';
	import { isUnreleased, releaseBadge } from '$lib/release';
	import { toasts } from '$lib/stores/toast.svelte';
	import type { RequestListItem } from '$lib/types/requests';
	import type { Column, PageParams } from '$lib/types/table';

	const STATUSES = [
		'requested',
		'snatched',
		'downloading',
		'downloaded',
		'merging',
		'organizing',
		'in_library',
		'completed',
		'failed'
	];

	const columns: Column[] = [
		{ key: 'book_title', label: 'Book' },
		{ key: 'author', label: 'Author', sortable: false, hideOnMobile: true },
		{ key: 'type', label: 'Format', sortable: false },
		{ key: 'narrator', label: 'Narrator', sortable: false, hideOnMobile: true },
		{ key: 'created_at', label: 'Created', hideOnMobile: true },
		{ key: '_actions', label: '', sortable: false, width: '110px' }
	];

	const status = $derived(page.url.searchParams.get('requests_status') ?? '');
	const type = $derived(page.url.searchParams.get('requests_type') ?? '');
	const hideUnreleased = $derived(page.url.searchParams.get('hide_unreleased') === '1');

	let retrying = $state(false);
	/** Bumped to force DataTable to remount and refetch after a mutation. */
	let reloadKey = $state(0);

	function setParam(key: string, value: string | null) {
		setSearchParam(key, value);
	}

	function fetchPage(params: PageParams) {
		return listRequests({ ...params, status, type });
	}

	/**
	 * v1 hid unreleased rows with a CSS class on tbody, so hidden rows still
	 * occupied the page and the list could look half-empty. Filtering the fetched
	 * rows instead keeps the empty state honest.
	 */
	function keep(r: RequestListItem): boolean {
		return !hideUnreleased || !isUnreleased(r.release_date, r.release_date_fetched);
	}

	async function retryOne(r: RequestListItem) {
		try {
			await organizeRequest(r.id);
			toasts.success('Retrying…');
			reloadKey++;
		} catch {
			toasts.error('Retry failed.');
		}
	}

	async function remove(r: RequestListItem) {
		try {
			await cancelRequest(r.id);
			toasts.success('Request deleted.');
			reloadKey++;
		} catch {
			toasts.error('Failed to delete request.');
		}
	}

	async function retryAll() {
		retrying = true;
		try {
			const res = await retryFailed();
			toasts.success(`Retrying ${res.count} failed request${res.count === 1 ? '' : 's'}…`);
			reloadKey++;
		} catch {
			toasts.error('Failed to retry.');
		} finally {
			retrying = false;
		}
	}
</script>

{#key reloadKey}
	<DataTable
		{columns}
		stateKey="requests"
		{fetchPage}
		extraParams={() => ({ status, type })}
		filter={keep}
		emptyMessage={status ? `No ${status} requests.` : 'No requests yet.'}
	>
		{#snippet toolbar()}
			<select value={status} onchange={(e) => setParam('requests_status', e.currentTarget.value)}>
				<option value="">All statuses</option>
				{#each STATUSES as s (s)}<option value={s}>{s}</option>{/each}
			</select>

			<select value={type} onchange={(e) => setParam('requests_type', e.currentTarget.value)}>
				<option value="">All types</option>
				<option value="audiobook">Audiobook</option>
				<option value="ebook">Ebook</option>
			</select>

			<label class="toggle">
				<input
					type="checkbox"
					checked={hideUnreleased}
					onchange={(e) => setParam('hide_unreleased', e.currentTarget.checked ? '1' : null)}
				/>
				Hide unreleased
			</label>

			{#if !status || status === 'failed'}
				<button type="button" class="retry-all" onclick={retryAll} disabled={retrying}>
					{retrying ? 'Retrying…' : 'Retry all failed'}
				</button>
			{/if}
		{/snippet}

		{#snippet row(r: RequestListItem)}
			{@const badge = releaseBadge(r.release_date, r.release_date_fetched)}
			<td>
				<a href="/library/book/{r.book_id}">{r.book_title || r.title || '—'}</a>
				{#if badge}
					<Badge variant="neutral" title={badge.title}>{badge.label}</Badge>
				{/if}
			</td>
			<td class="dim hide-mobile">{r.author || '—'}</td>
			<td>
				<Badge variant={r.status as BadgeVariant} title="{r.type} — {r.status}">
					<Icon name={r.type === 'audiobook' ? 'audiobook' : 'ebook'} size={12} />
					<span class="hide-mobile">{r.status}</span>
				</Badge>
			</td>
			<td class="dim hide-mobile">{r.narrator || '—'}</td>
			<td class="dim hide-mobile">{formatDate(r.created_at)}</td>
			<td class="actions">
				{#if r.status === 'failed'}
					<button type="button" class="link" onclick={() => retryOne(r)}>Retry</button>
				{/if}
				<ConfirmButton danger onconfirm={() => remove(r)}>Delete</ConfirmButton>
			</td>
		{/snippet}
	</DataTable>
{/key}

<style>
	select {
		padding: 0.35rem 0.5rem;
		background: var(--bg);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
	}

	.toggle {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		font-size: 0.875rem;
		color: var(--text-dim);
		white-space: nowrap;
		cursor: pointer;
	}

	.retry-all,
	.link {
		padding: 0.2rem 0.6rem;
		font-size: 0.8rem;
		background: none;
		color: var(--text-dim);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		white-space: nowrap;
	}

	.retry-all:hover:not(:disabled),
	.link:hover {
		color: var(--text);
		border-color: var(--accent);
	}

	.dim {
		color: var(--text-dim);
	}

	.actions {
		white-space: nowrap;
	}

	/* v1 hid these columns below 640px to keep the row readable on a phone. */
	@media (max-width: 640px) {
		.hide-mobile {
			display: none;
		}
	}
</style>
