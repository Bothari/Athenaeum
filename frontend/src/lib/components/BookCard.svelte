<script lang="ts">
	import Icon from './Icon.svelte';
	import Badge from './Badge.svelte';
	import type { BadgeVariant } from './Badge.svelte';
	import type { BookCardData } from '$lib/types/library';

	interface Props {
		book: BookCardData;
	}

	let { book }: Props = $props();

	const authorLine = $derived(
		book.authors?.length ? book.authors.map((a) => a.name).join(', ') : (book.author ?? '')
	);

	const formats = $derived(book.formats ?? []);

	/** Requests are only shown for formats not already in the library, so a book
	 *  held in one format does not display a stale request badge for it. */
	const pendingRequests = $derived(
		(book.requests ?? []).filter((r) => !formats.some((f) => f.type === r.type))
	);

	function formatTitle(f: { type: string; narrator?: string | null }): string {
		return f.narrator ? `${f.type} — ${f.narrator}` : f.type;
	}
</script>

<a class="book-card" href="/library/book/{book.id}">
	{#if book.cover_url}
		<img class="book-card-cover" src={book.cover_url} alt="" loading="lazy" />
	{:else}
		<div class="book-card-cover-placeholder"><Icon name="ebook" size={32} /></div>
	{/if}

	<div class="book-card-body">
		<div class="book-card-title">{book.title}</div>
		<div class="book-card-author">{authorLine}</div>
		<div class="book-card-meta">
			{#each formats as format (format.type)}
				<Badge variant="in_library" title={formatTitle(format)}>
					<Icon name={format.type === 'audiobook' ? 'audiobook' : 'ebook'} size={12} />
				</Badge>
			{/each}
			{#each pendingRequests as request (request.type)}
				<Badge variant={request.status as BadgeVariant}>
					<Icon name={request.type === 'audiobook' ? 'audiobook' : 'ebook'} size={12} />
				</Badge>
			{/each}
		</div>
	</div>
</a>

<style>
	/* Anchor rather than v1's clickable div — see EntityCard for the reasoning.
	   The book detail id also moves from a query param to a path segment. */
	.book-card {
		display: block;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		overflow: hidden;
		cursor: pointer;
		transition: border-color 0.15s;
		color: inherit;
		text-decoration: none;
	}

	.book-card:hover {
		border-color: var(--accent);
		text-decoration: none;
	}

	.book-card-cover {
		width: 100%;
		aspect-ratio: 2/3;
		object-fit: cover;
		display: block;
		background: var(--surface2);
	}

	.book-card-cover-placeholder {
		width: 100%;
		aspect-ratio: 2/3;
		background: var(--surface2);
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--text-dim);
	}

	.book-card-body {
		padding: 0.75rem;
	}

	.book-card-title {
		font-size: 0.85rem;
		font-weight: 600;
		line-height: 1.3;
		overflow: hidden;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		-webkit-box-orient: vertical;
	}

	.book-card-author {
		font-size: 0.75rem;
		color: var(--text-dim);
		margin-top: 0.25rem;
	}

	.book-card-meta {
		margin-top: 0.5rem;
		display: flex;
		gap: 0.25rem;
		flex-wrap: wrap;
	}

	/* Square-cover mode is a body class set from settings. */
	:global(body.square-covers) .book-card-cover,
	:global(body.square-covers) .book-card-cover-placeholder {
		aspect-ratio: 1 / 1;
	}
</style>
