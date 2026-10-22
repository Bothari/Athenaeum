<script lang="ts">
	import { page } from '$app/state';
	import { setSearchParam } from '$lib/url';
	import Badge from '$lib/components/Badge.svelte';
	import DataTable from '$lib/components/DataTable.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import UnlinkedToggle from '$lib/components/UnlinkedToggle.svelte';
	import { listSeries } from '$lib/api/library';
	import type { SeriesListItem } from '$lib/types/library';
	import type { Column, PageParams } from '$lib/types/table';

	const columns: Column[] = [
		{ key: 'name', label: 'Name' },
		{ key: 'library_count', label: 'Books', width: '80px' },
		{ key: 'missing', label: 'Missing', width: '90px' }
	];

	const unlinked = $derived(page.url.searchParams.get('unlinked') === '1');

	function setUnlinked(value: boolean) {
		setSearchParam('unlinked', value ? '1' : null);
	}

	function fetchPage(params: PageParams) {
		return listSeries({ ...params, unlinked });
	}

	/** show_secondary_works selects which pair of counts applies. */
	function counts(s: SeriesListItem) {
		return s.show_secondary_works
			? { missing: s.missing_all, upcoming: s.upcoming_all }
			: { missing: s.missing_primary, upcoming: s.upcoming_primary };
	}
</script>

<PageHeader title="Series" icon="series" />

<DataTable
	{columns}
	stateKey="series"
	{fetchPage}
	extraParams={() => ({ unlinked })}
	emptyMessage="No series yet. Series are added automatically when books with series data are synced."
>
	{#snippet toolbar()}
		<UnlinkedToggle checked={unlinked} onchange={setUnlinked} />
	{/snippet}

	{#snippet row(s: SeriesListItem)}
		{@const c = counts(s)}
		<td><a href="/library/series/{s.id}">{s.name}</a></td>
		<td>
			<!-- Flex on an inner wrapper, never on the td — see DataTable. -->
			<div class="badges">
				<Badge variant="in_library">{s.library_count ?? 0}</Badge>
				{#if (s.requested_count ?? 0) > 0}
					<Badge variant="requested">{s.requested_count}</Badge>
				{/if}
			</div>
		</td>
		<td>
			<!-- Counts arrive from a later Hardcover lookup; until then show a dash
			     rather than asserting the series is complete. -->
			{#if c.missing == null && c.upcoming == null}
				<span class="none">—</span>
			{:else if (c.missing ?? 0) > 0}
				<Badge variant="missing" small>{c.missing} missing</Badge>
			{:else if (c.upcoming ?? 0) > 0}
				<Badge variant="upcoming" small>{c.upcoming} upcoming</Badge>
			{:else}
				<Badge variant="completed" small>Complete</Badge>
			{/if}
		</td>
	{/snippet}
</DataTable>

<style>
	/* Cell padding, borders and vertical-align come from DataTable. */
	.badges {
		display: flex;
		gap: 0.25rem;
		white-space: nowrap;
	}

	.none {
		color: var(--text-dim);
		font-size: 0.75rem;
	}
</style>
