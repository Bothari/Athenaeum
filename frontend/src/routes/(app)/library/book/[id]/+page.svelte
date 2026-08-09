<script lang="ts">
	import { page } from '$app/state';
	import Badge from '$lib/components/Badge.svelte';
	import ErrorState from '$lib/components/ErrorState.svelte';
	import FormatRow from '$lib/components/FormatRow.svelte';
	import HardcoverCard from '$lib/components/HardcoverCard.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import LoadingState from '$lib/components/LoadingState.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import { getBook, hardcoverUrl } from '$lib/api/books';
	import type { FormatType } from '$lib/types/library';
	import type {
		BookDetail,
		BookFormatDetail,
		BookRequestDetail,
		BookSeriesRef
	} from '$lib/types/detail';

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

	/**
	 * One row per held format, then any request for a format/narrator combination
	 * not already held, then a placeholder for each type still missing entirely.
	 * Ported from v1's renderDetailFormats, keyed on type+narrator so a book held
	 * in two narrations shows both.
	 */
	const formatRows = $derived.by(() => {
		const rows: {
			key: string;
			type: FormatType;
			status: string;
			narrator: string | null;
			format: BookFormatDetail | null;
			request: BookRequestDetail | null;
		}[] = [];
		const seen = new Set<string>();
		const key = (t: string, n?: string | null) => `${t}::${n || ''}`;

		for (const f of book?.formats ?? []) {
			seen.add(key(f.type, f.narrator));
			rows.push({
				key: key(f.type, f.narrator),
				type: f.type,
				status: 'in_library',
				narrator: f.narrator || null,
				format: f,
				request: null
			});
		}

		for (const r of book?.requests ?? []) {
			if (seen.has(key(r.type, r.narrator))) continue;
			seen.add(key(r.type, r.narrator));
			rows.push({
				key: key(r.type, r.narrator),
				type: r.type,
				status: r.status,
				narrator: r.narrator || null,
				format: null,
				request: r
			});
		}

		for (const type of ['ebook', 'audiobook'] as FormatType[]) {
			if (!rows.some((r) => r.type === type)) {
				rows.push({
					key: key(type),
					type,
					status: 'missing',
					narrator: null,
					format: null,
					request: null
				});
			}
		}

		return rows;
	});
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
		{#each formatRows as fmtRow (fmtRow.key)}
			<FormatRow
				{bookId}
				type={fmtRow.type}
				status={fmtRow.status}
				narrator={fmtRow.narrator}
				format={fmtRow.format}
				request={fmtRow.request}
				onrefresh={load}
			/>
		{/each}
	</div>

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

	@media (max-width: 640px) {
		.cover {
			width: 90px;
		}
	}
</style>
