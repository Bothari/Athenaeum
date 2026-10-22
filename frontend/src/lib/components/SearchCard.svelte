<script lang="ts">
	import Badge from './Badge.svelte';
	import FormatPills from './FormatPills.svelte';
	import Icon from './Icon.svelte';
	import { releaseBadge } from '$lib/release';
	import type { SearchResult } from '$lib/types/search';

	interface Props {
		result: SearchResult;
		/** Hides the request pills, for contexts that only display. */
		showPills?: boolean;
	}

	let { result, showPills = true }: Props = $props();

	/** Set once a request is made, so the card starts linking to the local book. */
	let linkedBookId = $state<string | null>(null);

	/**
	 * Only link to the local book page when there is something there to see —
	 * a held format or a live request. v1 applied the same rule, since a bare
	 * search result has no detail page worth visiting.
	 */
	const hasLocal = $derived(
		!!(result.library_formats?.length ||
			result.existing_requests?.some((r) => r.status !== 'failed'))
	);
	const bookId = $derived(linkedBookId ?? (hasLocal ? result.book_id : null));
	const href = $derived(bookId ? `/library/book/${bookId}` : null);

	function positionOf(pos?: string | null): string {
		if (!pos) return '';
		const n = parseFloat(pos);
		if (isNaN(n)) return pos;
		return n % 1 === 0 ? String(Math.floor(n)) : String(n);
	}

	const series = $derived(result.series?.[0]);
	const seriesLabel = $derived(
		series ? `${series.name}${positionOf(series.position) ? ` #${positionOf(series.position)}` : ''}` : ''
	);

	/** Searching by hardcover id pivots to that author/series; falling back to a
	 *  name search keeps the link useful when no id exists. */
	const seriesHref = $derived(
		series
			? series.hardcover_series_id
				? `/?hc_series_id=${encodeURIComponent(series.hardcover_series_id)}&advanced=1`
				: `/?series=${encodeURIComponent(series.name)}&advanced=1`
			: null
	);

	const authors = $derived(
		(result.authors?.length
			? result.authors
			: result.author
				? [{ name: result.author, id: result.author_id ?? '' }]
				: []
		).filter((a) => a.name)
	);

	/** published_year covers results that have no release_date at all. */
	const badge = $derived.by(() => {
		const fromDate = releaseBadge(result.release_date, result.release_date_fetched);
		if (fromDate) return fromDate;
		if (
			!result.release_date &&
			result.published_year &&
			String(result.published_year) > String(new Date().getFullYear())
		) {
			return { label: 'Unreleased', title: `Expected ${result.published_year}` };
		}
		return null;
	});
</script>

<div class="card">
	<svelte:element this={href ? 'a' : 'div'} {href} class="cover-link">
		{#if result.cover_url}
			<img class="cover" src={result.cover_url} alt="" loading="lazy" />
		{:else}
			<div class="cover placeholder"><Icon name="ebook" size={28} /></div>
		{/if}
	</svelte:element>

	<div class="body">
		<div class="title-row">
			<svelte:element this={href ? 'a' : 'span'} {href} class="title">{result.title}</svelte:element>
			{#if result.hardcover_url}
				<a
					class="hc"
					href={result.hardcover_url}
					target="_blank"
					rel="noreferrer"
					title="Open on Hardcover">HC</a
				>
			{/if}
		</div>

		{#if authors.length}
			<div class="authors">
				{#each authors as author, i (author.name + i)}
					{#if i > 0}<span>, </span>{/if}
					{#if author.id}
						<a href="/?hc_author_id={encodeURIComponent(author.id)}&advanced=1">{author.name}</a>
					{:else}
						<span>{author.name}</span>
					{/if}
				{/each}
			</div>
		{/if}

		{#if series && seriesHref}
			<div class="series"><a href={seriesHref}>{seriesLabel}</a></div>
		{/if}

		<div class="meta">
			{#if result.rating}
				<span class="rating">{result.rating.toFixed(1)} <span class="faint">({result.rating_count ?? 0})</span></span>
			{/if}
			{#if badge}
				<Badge variant="neutral" title={badge.title}>{badge.label}</Badge>
			{/if}
		</div>

		{#if showPills}
			<FormatPills {result} onlinked={(id) => (linkedBookId = id)} />
		{/if}
	</div>
</div>

<style>
	.card {
		display: flex;
		gap: 0.75rem;
		max-width: 100%;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 0.75rem;
		margin-bottom: 0.5rem;
	}

	.cover-link {
		flex-shrink: 0;
		display: block;
		/* Without this the flex row stretches the link past the cover, making the
		   click target taller than what it looks like. */
		align-self: flex-start;
	}

	.cover {
		width: 60px;
		aspect-ratio: 2/3;
		object-fit: cover;
		border-radius: var(--radius);
		background: var(--surface2);
		display: block;
	}

	.cover.placeholder {
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--text-dim);
	}

	.body {
		min-width: 0;
		flex: 1;
		/*
		 * Hardcover occasionally returns junk titles — a whole CSV row, including
		 * comma-joined URLs with no spaces. That is a single unbreakable token whose
		 * min-content width exceeds the viewport, and a flex item will not shrink
		 * below min-content, so it dragged the entire results column wider than the
		 * screen and squashed every other card. Wrap anywhere rather than trust the
		 * data to be sane.
		 */
		overflow-wrap: anywhere;
	}

	.title-row {
		display: flex;
		align-items: baseline;
		gap: 0.4rem;
		min-width: 0;
	}

	.title {
		font-weight: 600;
		font-size: 0.95rem;
		color: inherit;
		min-width: 0;
		/* Absurd titles wrap, but stop after a sensible number of lines. */
		display: -webkit-box;
		-webkit-line-clamp: 4;
		line-clamp: 4;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	a.title:hover {
		color: var(--accent);
	}

	.hc {
		font-size: 0.7rem;
		color: var(--text-dim);
		flex-shrink: 0;
	}

	.authors,
	.series {
		font-size: 0.82rem;
		color: var(--text-dim);
		margin-top: 0.1rem;
	}

	.meta {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		margin-top: 0.25rem;
		font-size: 0.8rem;
	}

	.faint {
		opacity: 0.6;
	}
</style>
