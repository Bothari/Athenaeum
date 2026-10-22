<script lang="ts">
	import EntityCard from './EntityCard.svelte';
	import type { AuthorCardData } from '$lib/types/library';

	interface Props {
		author: AuthorCardData;
	}

	let { author }: Props = $props();

	const count = $derived(author.book_count ?? 0);
</script>

<EntityCard href="/library/authors/{author.id}" name={author.name}>
	{#snippet meta()}
		<span>{count} book{count === 1 ? '' : 's'}</span>
	{/snippet}
</EntityCard>
