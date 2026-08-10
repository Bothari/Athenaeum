<script lang="ts">
	import { untrack } from 'svelte';
	import { beforeNavigate } from '$app/navigation';
	import { page } from '$app/state';
	import { restoreScrollPosition, saveScroll, takeScroll } from '$lib/scroll';
	import DetailStats from '$lib/components/DetailStats.svelte';
	import ErrorState from '$lib/components/ErrorState.svelte';
	import HardcoverCard from '$lib/components/HardcoverCard.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import LoadingState from '$lib/components/LoadingState.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import MissingSection from '$lib/components/series/MissingSection.svelte';
	import SeriesBooks from '$lib/components/series/SeriesBooks.svelte';
	import SeriesPack from '$lib/components/series/SeriesPack.svelte';
	import { getSeries, getSeriesBooks } from '$lib/api/series';
	import { auth } from '$lib/stores/auth.svelte';
	import type { SeriesBook, SeriesDetail } from '$lib/types/series';

	const seriesId = $derived(page.params.id!);

	type View = 'list' | 'poster';
	/** Shared with author detail, as in v1. */
	const VIEW_KEY = 'detail_view';

	let series = $state<SeriesDetail | null>(null);
	let books = $state<SeriesBook[]>([]);
	let loading = $state(true);
	let failed = $state(false);
	let view = $state<View>('list');

	/** Filled in once the Hardcover lookup returns; null means still checking. */
	let missingCount = $state<number | null>(null);
	let upcomingCount = $state<number | null>(null);

	const inLibrary = $derived(series?.library_count ?? 0);
	const requested = $derived(series?.requested_count ?? 0);
	const total = $derived(
		missingCount == null ? null : inLibrary + missingCount + (upcomingCount ?? 0)
	);

	async function load() {
		loading = true;
		failed = false;
		missingCount = null;
		upcomingCount = null;
		try {
			const [b, s] = await Promise.all([getSeriesBooks(seriesId), getSeries(seriesId)]);
			books = b;
			series = s;
		} catch {
			failed = true;
		} finally {
			loading = false;
		}
	}

	// Not paginated, so only the position matters — but the page is empty until
	// the fetch resolves, which is why the browser's own restoration lands at the
	// top and this has to wait for the data.
	const scrollKey = untrack(() => page.url.pathname);
	let pendingRestore = takeScroll(scrollKey);

	beforeNavigate(() => saveScroll(scrollKey));

	$effect(() => {
		void seriesId;
		load().then(() => {
			if (!pendingRestore) return;
			const { y } = pendingRestore;
			pendingRestore = null;
			restoreScrollPosition(y);
		});
	});

	$effect(() => {
		const stored = localStorage.getItem(VIEW_KEY);
		if (stored === 'poster' || stored === 'list') view = stored;
	});

	function setView(next: View) {
		view = next;
		localStorage.setItem(VIEW_KEY, next);
	}

	/** Falls back to the series name carried on a book when the series row has none. */
	const name = $derived(
		series?.name ||
			books[0]?.series?.find((s) => s.id === seriesId)?.name ||
			books[0]?.series?.[0]?.name ||
			'Series'
	);
</script>

{#if failed}
	<ErrorState onretry={load} />
{:else if loading}
	<LoadingState />
{:else}
	<PageHeader title={name} icon="series">
		{#snippet actions()}
			<div class="view-toggle">
				<button
					type="button"
					class:active={view === 'poster'}
					onclick={() => setView('poster')}
					title="Poster"
					aria-label="Poster view">▦</button
				>
				<button
					type="button"
					class:active={view === 'list'}
					onclick={() => setView('list')}
					title="List"
					aria-label="List view">☰</button
				>
			</div>
		{/snippet}
	</PageHeader>

	<DetailStats
		{inLibrary}
		{requested}
		missing={missingCount}
		upcoming={upcomingCount}
		{total}
		missingTargetId="series-section-missing"
		upcomingTargetId="series-section-upcoming"
	/>

	<h2 class="heading">Books in Library</h2>
	<SeriesBooks {books} {view} />

	<MissingSection
		{seriesId}
		oncounts={(c) => {
			missingCount = c.missing;
			upcomingCount = c.upcoming;
		}}
	/>

	{#if auth.isAdmin}
		<SeriesPack {seriesId} />
	{/if}

	<HardcoverCard
		type="series"
		entityId={seriesId}
		hcId={series?.link?.hardcover_series_id}
		hcSlug={series?.link?.hardcover_series_slug}
	/>
{/if}

<style>
	.heading {
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--text-dim);
		margin: 1.5rem 0 0.5rem;
	}

	.view-toggle {
		display: flex;
		gap: 0.15rem;
	}

	.view-toggle button {
		background: none;
		border: 1px solid var(--border);
		border-radius: var(--radius);
		color: var(--text-dim);
		padding: 0.2rem 0.45rem;
		font-size: 0.9rem;
	}

	.view-toggle button.active {
		color: var(--accent);
		border-color: var(--accent);
	}
</style>
