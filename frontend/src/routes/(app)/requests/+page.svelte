<script lang="ts">
	import { page } from '$app/state';
	import { setSearchParam } from '$lib/url';
	import ManualRequestDialog from '$lib/components/ManualRequestDialog.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import DownloadsTab from '$lib/components/queue/DownloadsTab.svelte';
	import PendingTab from '$lib/components/queue/PendingTab.svelte';
	import RequestsTab from '$lib/components/queue/RequestsTab.svelte';
	import SearchAllTab from '$lib/components/queue/SearchAllTab.svelte';
	import { auth } from '$lib/stores/auth.svelte';

	const TABS = [
		{ key: 'requests', label: 'Requests' },
		{ key: 'downloads', label: 'Downloads' },
		{ key: 'pending', label: 'Pending' },
		{ key: 'search', label: 'Search' }
	] as const;

	type TabKey = (typeof TABS)[number]['key'];

	const tab = $derived.by<TabKey>(() => {
		const value = page.url.searchParams.get('tab');
		return TABS.some((t) => t.key === value) ? (value as TabKey) : 'requests';
	});

	let showManual = $state(false);

	function setTab(next: TabKey) {
		// 'requests' is the default, so it stays out of the URL.
		setSearchParam('tab', next === 'requests' ? null : next);
	}
</script>

<!-- Non-admins get the plain requests list: no tabs, no manual request. -->
<PageHeader title={auth.isAdmin ? 'Queue' : 'Requests'} icon="requests">
	{#snippet actions()}
		{#if auth.isAdmin}
			<button type="button" class="manual" onclick={() => (showManual = true)}>
				+ Manual Request
			</button>
		{/if}
	{/snippet}
</PageHeader>

{#if auth.isAdmin}
	<div class="tabs" role="tablist">
		{#each TABS as t (t.key)}
			<button
				type="button"
				role="tab"
				aria-selected={tab === t.key}
				class:active={tab === t.key}
				onclick={() => setTab(t.key)}
			>
				{t.label}
			</button>
		{/each}
	</div>
{/if}

{#if !auth.isAdmin || tab === 'requests'}
	<RequestsTab />
{:else if tab === 'downloads'}
	<DownloadsTab />
{:else if tab === 'pending'}
	<PendingTab />
{:else}
	<SearchAllTab />
{/if}

{#if showManual}
	<ManualRequestDialog onclose={() => (showManual = false)} />
{/if}

<style>
	.manual {
		padding: 0.25rem 0.6rem;
		font-size: 0.85rem;
		background: none;
		color: var(--text-dim);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		white-space: nowrap;
	}

	.manual:hover {
		color: var(--text);
		border-color: var(--accent);
	}

	.tabs {
		display: flex;
		gap: 0.25rem;
		border-bottom: 1px solid var(--border);
		margin-bottom: 1rem;
		overflow-x: auto;
	}

	.tabs button {
		background: none;
		border: none;
		border-bottom: 2px solid transparent;
		color: var(--text-dim);
		padding: 0.4rem 0.7rem;
		font-size: 0.9rem;
		white-space: nowrap;
	}

	.tabs button:hover {
		color: var(--text);
	}

	.tabs button.active {
		color: var(--text);
		border-bottom-color: var(--accent);
	}
</style>
