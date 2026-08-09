<script lang="ts">
	import { replaceState } from '$app/navigation';
	import { page } from '$app/state';
	import DataTable from '$lib/components/DataTable.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import UnlinkedToggle from '$lib/components/UnlinkedToggle.svelte';
	import { listAuthors } from '$lib/api/library';
	import type { AuthorListItem } from '$lib/types/library';
	import type { Column, PageParams } from '$lib/types/table';

	const columns: Column[] = [
		{ key: 'name', label: 'Name' },
		{ key: 'book_count', label: 'Books', width: '80px' }
	];

	const unlinked = $derived(page.url.searchParams.get('unlinked') === '1');

	function setUnlinked(value: boolean) {
		const params = new URLSearchParams(page.url.searchParams);
		if (value) params.set('unlinked', '1');
		else params.delete('unlinked');
		replaceState(`${page.url.pathname}?${params}`, page.state);
	}

	function fetchPage(params: PageParams) {
		return listAuthors({ ...params, unlinked });
	}
</script>

<PageHeader title="Authors" icon="author" />

<DataTable
	{columns}
	stateKey="authors"
	{fetchPage}
	extraParams={() => ({ unlinked })}
	emptyMessage="No authors yet. Authors are added automatically when books are synced."
>
	{#snippet toolbar()}
		<UnlinkedToggle checked={unlinked} onchange={setUnlinked} />
	{/snippet}

	{#snippet row(author: AuthorListItem)}
		<td><a href="/library/authors/{author.id}">{author.name}</a></td>
		<td class="dim">{author.book_count ?? 0}</td>
	{/snippet}
</DataTable>

<style>
	/* Cell padding, borders and vertical-align come from DataTable. */
	.dim {
		color: var(--text-dim);
	}
</style>
