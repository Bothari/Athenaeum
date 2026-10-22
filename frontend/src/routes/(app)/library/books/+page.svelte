<script lang="ts">
	import { page } from '$app/state';
	import { setSearchParam } from '$lib/url';
	import Badge from '$lib/components/Badge.svelte';
	import type { BadgeVariant } from '$lib/components/Badge.svelte';
	import DataTable from '$lib/components/DataTable.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import UnlinkedToggle from '$lib/components/UnlinkedToggle.svelte';
	import { listBooks } from '$lib/api/library';
	import type { BookListItem } from '$lib/types/library';
	import type { Column, PageParams } from '$lib/types/table';

	const columns: Column[] = [
		{ key: 'title', label: 'Title' },
		{ key: 'author', label: 'Author' },
		{ key: 'formats', label: 'Formats', sortable: false, width: '90px' }
	];

	const unlinked = $derived(page.url.searchParams.get('unlinked') === '1');

	function setUnlinked(value: boolean) {
		setSearchParam('unlinked', value ? '1' : null);
	}

	function fetchPage(params: PageParams) {
		return listBooks({ ...params, unlinked });
	}

	function authorNames(book: BookListItem): string {
		return book.authors?.length ? book.authors.map((a) => a.name).join(', ') : '—';
	}
</script>

<PageHeader title="Books" icon="library" />

<DataTable
	{columns}
	stateKey="books"
	{fetchPage}
	extraParams={() => ({ unlinked })}
	emptyMessage="Your library is empty."
>
	{#snippet toolbar()}
		<UnlinkedToggle checked={unlinked} onchange={setUnlinked} />
	{/snippet}

	{#snippet row(book: BookListItem)}
		<td><a href="/library/book/{book.id}">{book.title}</a></td>
		<td class="dim">{authorNames(book)}</td>
		<td>
			<!-- Flex lives on an inner wrapper: setting display on the td itself
			     breaks table-cell layout. See DataTable's cell styles. -->
			<div class="badges">
				{#each book.formats ?? [] as format (format.type)}
					<Badge
						variant="in_library"
						title={format.narrator ? `${format.type} — ${format.narrator}` : format.type}
					>
						<Icon name={format.type === 'audiobook' ? 'audiobook' : 'ebook'} size={12} />
					</Badge>
				{/each}
				<!-- Unlike the book card, the table shows every request regardless of
				     whether the format is already held. Matches v1. -->
				{#each book.requests ?? [] as req (req.type + req.status)}
					<Badge variant={req.status as BadgeVariant} title="{req.type} — {req.status}">
						<Icon name={req.type === 'audiobook' ? 'audiobook' : 'ebook'} size={12} />
					</Badge>
				{/each}
			</div>
		</td>
	{/snippet}
</DataTable>

<style>
	/* Cell padding, borders and vertical-align come from DataTable. */
	.dim {
		color: var(--text-dim);
	}

	.badges {
		display: flex;
		gap: 0.25rem;
		white-space: nowrap;
	}
</style>
