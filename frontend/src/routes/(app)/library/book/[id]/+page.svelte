<script lang="ts">
	import { page } from '$app/state';
	import Badge from '$lib/components/Badge.svelte';
	import type { BadgeVariant } from '$lib/components/Badge.svelte';
	import ErrorState from '$lib/components/ErrorState.svelte';
	import HardcoverCard from '$lib/components/HardcoverCard.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import LoadingState from '$lib/components/LoadingState.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import { getBook, hardcoverUrl } from '$lib/api/books';
	import type { BookDetail, BookSeriesRef } from '$lib/types/detail';

	const bookId = $derived(page.params.id!);

	let book = $state<BookDetail | null>(null);
	let failed = $state(false);

	async function load() {
		failed = false;
		book = null;
		try {
			book = await getBook(bookId);
		} catch {
			failed = true;
		}
	}

	$effect(() => {
		void bookId;
		load();
	});

	const hcUrl = $derived(hardcoverUrl('book', book?.link?.hardcover_slug));

	/** Trims a trailing ".0" so "1.0" shows as "1" but "1.5" survives. */
	function position(s: BookSeriesRef): string {
		if (!s.position) return '';
		const n = parseFloat(s.position);
		if (isNaN(n)) return s.position;
		return n % 1 === 0 ? String(Math.floor(n)) : String(n);
	}

	/**
	 * A date of Jan 1 in the current year or later is Hardcover's placeholder for
	 * "year known, day unknown", so it counts as unreleased and displays as just
	 * the year. Ported from v1.
	 */
	function releaseInfo(date?: string | null) {
		if (!date) return null;
		const today = new Date().toISOString().slice(0, 10);
		const yearOnly = date.endsWith('-01-01') && date.slice(0, 4) >= String(new Date().getFullYear());
		return { unreleased: date >= today || yearOnly, label: yearOnly ? date.slice(0, 4) : date };
	}

	const release = $derived(releaseInfo(book?.release_date));
</script>

{#if failed}
	<ErrorState onretry={load} />
{:else if !book}
	<LoadingState />
{:else}
	<PageHeader title={book.title} icon="ebook" />

	<div class="card">
		<div class="detail">
			{#if book.cover_url}
				<img class="cover" src={book.cover_url} alt="" loading="lazy" />
			{:else}
				<div class="cover placeholder"><Icon name="ebook" size={40} /></div>
			{/if}

			<div class="meta">
				{#if book.authors?.length}
					<div class="authors">
						{#each book.authors as author, i (author.id)}
							{#if i > 0}<span>, </span>{/if}
							<a href="/library/authors/{author.id}">{author.name}</a>
						{/each}
					</div>
				{/if}

				{#if book.series?.length}
					<div class="series">
						{#each book.series as s (s.id)}
							<div>
								<!-- Only link series we actually hold books from; v1 did the same,
								     since an empty series page is a dead end. -->
								{#if s.id && (s.library_count ?? 0) > 0}
									<a href="/library/series/{s.id}">
										{s.name}{position(s) ? ` #${position(s)}` : ''}
									</a>
								{:else}
									{s.name}{position(s) ? ` #${position(s)}` : ''}
								{/if}
							</div>
						{/each}
					</div>
				{/if}

				{#if book.rating}
					<div class="rating">
						{book.rating.toFixed(1)}
						<span class="faint">({book.rating_count ?? 0})</span>
					</div>
				{/if}

				{#if release}
					<div class="release">
						{#if release.unreleased}<Badge variant="neutral">Unreleased</Badge>{/if}
						{release.label}
					</div>
				{/if}

				{#if hcUrl}
					<a class="hc" href={hcUrl} target="_blank" rel="noreferrer">Hardcover</a>
				{/if}
			</div>
		</div>
	</div>

	<h2 class="section">Formats</h2>
	<div class="formats">
		{#each book.formats ?? [] as format (format.id)}
			<div class="format">
				<Badge variant="completed" title="In library">
					<Icon name={format.type === 'audiobook' ? 'audiobook' : 'ebook'} size={12} />
				</Badge>
				<span class="type">{format.type === 'audiobook' ? 'Audiobook' : 'Ebook'}</span>
				{#if format.narrator}<span class="narrator">{format.narrator}</span>{/if}
				{#if format.abs_url}
					<a class="abs" href={format.abs_url} target="_blank" rel="noreferrer">Listen</a>
				{/if}
			</div>
		{/each}

		{#each book.requests ?? [] as req (req.id)}
			<div class="format">
				<Badge variant={req.status as BadgeVariant} title={req.status}>
					<Icon name={req.type === 'audiobook' ? 'audiobook' : 'ebook'} size={12} />
				</Badge>
				<span class="type">{req.type === 'audiobook' ? 'Audiobook' : 'Ebook'}</span>
				{#if req.narrator}<span class="narrator">{req.narrator}</span>{/if}
				<span class="faint">{req.status}</span>
			</div>
		{/each}

		{#each ['ebook', 'audiobook'] as const as type (type)}
			{#if !book.formats?.some((f) => f.type === type) && !book.requests?.some((r) => r.type === type)}
				<div class="format missing">
					<Badge variant="neutral" title="missing">
						<Icon name={type === 'audiobook' ? 'audiobook' : 'ebook'} size={12} />
					</Badge>
					<span class="type">{type === 'audiobook' ? 'Audiobook' : 'Ebook'}</span>
					<span class="faint">not in library</span>
				</div>
			{/if}
		{/each}
	</div>
	<p class="deferred">Per-format search and download arrive in phase 5b.</p>

	<HardcoverCard
		type="book"
		entityId={bookId}
		hcId={book.link?.hardcover_id}
		hcSlug={book.link?.hardcover_slug}
		onchange={load}
	/>
{/if}

<style>
	.card {
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 1rem;
	}

	.detail {
		display: flex;
		gap: 1rem;
	}

	.cover {
		width: 120px;
		flex-shrink: 0;
		aspect-ratio: 2/3;
		object-fit: cover;
		border-radius: var(--radius);
		background: var(--surface2);
	}

	.cover.placeholder {
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--text-dim);
	}

	.meta {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
		min-width: 0;
	}

	.series,
	.rating,
	.release {
		font-size: 0.85rem;
	}

	.release {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		color: var(--text-dim);
	}

	.faint {
		color: var(--text-dim);
	}

	.hc {
		font-size: 0.85rem;
	}

	.section {
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--text-dim);
		margin: 1.5rem 0 0.5rem;
	}

	.formats {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.format {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 0.5rem 0.75rem;
		font-size: 0.875rem;
	}

	.format.missing {
		opacity: 0.65;
	}

	.type {
		font-weight: 500;
	}

	.narrator {
		color: var(--text-dim);
		font-size: 0.8rem;
	}

	.abs {
		margin-left: auto;
		font-size: 0.8rem;
	}

	.deferred {
		margin-top: 0.5rem;
		font-size: 0.78rem;
		color: var(--text-dim);
	}

	@media (max-width: 640px) {
		.cover {
			width: 90px;
		}
	}
</style>
