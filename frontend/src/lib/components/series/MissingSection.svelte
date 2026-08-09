<script lang="ts">
	import LoadingState from '../LoadingState.svelte';
	import SearchCard from '../SearchCard.svelte';
	import { getMissing, linkLibraryBook, setShowSecondaryWorks } from '$lib/api/series';
	import { isUnreleased } from '$lib/release';
	import { toasts } from '$lib/stores/toast.svelte';
	import type { MissingItem, MissingResponse } from '$lib/types/series';

	interface Props {
		seriesId: string;
		/** Reports the computed counts up so the stats bar can fill in. */
		oncounts?: (counts: { missing: number; upcoming: number }) => void;
	}

	let { seriesId, oncounts }: Props = $props();

	let data = $state<MissingResponse | null>(null);
	let loading = $state(true);
	let failed = $state(false);
	let togglingSecondary = $state(false);
	let adding = $state<string | null>(null);

	/**
	 * Released items are "missing" — findable now. Unreleased ones are "upcoming"
	 * and are split out so the two are not conflated.
	 */
	const missing = $derived(
		(data?.items ?? []).filter((b) => !isUnreleased(b.release_date, b.release_date_fetched))
	);
	const upcoming = $derived(
		(data?.items ?? []).filter((b) => isUnreleased(b.release_date, b.release_date_fetched))
	);

	async function load() {
		loading = true;
		failed = false;
		try {
			data = await getMissing(seriesId);
			if (data.items && !data.error) {
				oncounts?.({ missing: missing.length, upcoming: upcoming.length });
			}
		} catch {
			failed = true;
		} finally {
			loading = false;
			togglingSecondary = false;
		}
	}

	$effect(() => {
		void seriesId;
		load();
	});

	async function toggleSecondary(value: boolean) {
		togglingSecondary = true;
		try {
			await setShowSecondaryWorks(seriesId, value);
			await load();
		} catch {
			toasts.error('Failed to update series setting');
			togglingSecondary = false;
		}
	}

	/** For a book we already hold that is not yet attached to this series. */
	async function addToSeries(item: MissingItem) {
		if (!item.book_id) return;
		adding = item.book_id;
		try {
			await linkLibraryBook(seriesId, item.book_id, item.series_position ?? null);
			await load();
		} catch {
			toasts.error('Failed to add book to series');
		} finally {
			adding = null;
		}
	}
</script>

{#snippet secondaryToggle()}
	<label class="secondary">
		<input
			type="checkbox"
			checked={data?.show_secondary_works ?? false}
			disabled={togglingSecondary}
			onchange={(e) => toggleSecondary(e.currentTarget.checked)}
		/>
		Non-primary works
	</label>
{/snippet}

{#snippet items(list: MissingItem[], heading: string, anchor: string)}
	<div class="heading-row" id={anchor}>
		<span class="heading">{heading} ({list.length}{data?.truncated ? '+' : ''})</span>
		{#if heading.startsWith('Missing')}{@render secondaryToggle()}{/if}
	</div>
	{#each list as item (item.book_id ?? item.metadata_id ?? item.title)}
		<div class="item">
			{#if item.series_position != null}
				<span class="pos">#{item.series_position}</span>
			{/if}
			<SearchCard result={item} />
			{#if item.in_library && item.book_id}
				<!-- Held already, just not attached to this series. -->
				<div class="add-row">
					<span class="label">Series</span>
					<button
						type="button"
						disabled={adding === item.book_id}
						onclick={() => addToSeries(item)}
					>
						{adding === item.book_id ? 'Adding…' : 'Add to this series'}
					</button>
				</div>
			{/if}
		</div>
	{/each}
{/snippet}

{#if loading}
	<div class="heading-row"><span class="heading">Missing from Series</span></div>
	<LoadingState compact />
{:else if failed || data?.error}
	<!-- v1 silently blanked this section on failure; saying so is more useful. -->
	<div class="heading-row"><span class="heading">Missing from Series</span></div>
	<p class="dim">Could not reach Hardcover to check for missing books.</p>
{:else if (data?.items?.length ?? 0) === 0}
	<div class="heading-row">
		<span class="heading">Missing from Series</span>
		{@render secondaryToggle()}
	</div>
	<p class="dim">All books accounted for.</p>
{:else}
	{#if missing.length}
		{@render items(missing, 'Missing from Series', 'series-section-missing')}
	{/if}
	{#if upcoming.length}
		{@render items(upcoming, 'Upcoming', 'series-section-upcoming')}
	{/if}
{/if}

<style>
	.heading-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		margin: 1.5rem 0 0.5rem;
		flex-wrap: wrap;
	}

	.heading {
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--text-dim);
	}

	.secondary {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		font-size: 0.8rem;
		color: var(--text-dim);
		white-space: nowrap;
		cursor: pointer;
	}

	.dim {
		color: var(--text-dim);
		padding: 0.5rem 0;
	}

	.item {
		position: relative;
	}

	.pos {
		position: absolute;
		top: 0.4rem;
		left: 0.4rem;
		z-index: 1;
		background: var(--surface2);
		color: var(--text-dim);
		font-size: 0.7rem;
		padding: 0.1rem 0.35rem;
		border-radius: 3px;
	}

	.add-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin: -0.25rem 0 0.75rem;
		padding-left: 0.75rem;
	}

	.label {
		font-size: 0.78rem;
		color: var(--text-dim);
	}

	.add-row button {
		padding: 0.2rem 0.6rem;
		font-size: 0.8rem;
		background: var(--accent);
		color: #fff;
		border: none;
		border-radius: var(--radius);
	}

	.add-row button:disabled {
		opacity: 0.6;
	}
</style>
