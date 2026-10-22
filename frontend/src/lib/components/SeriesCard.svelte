<script lang="ts">
	import EntityCard from './EntityCard.svelte';
	import Badge from './Badge.svelte';
	import type { SeriesCardData } from '$lib/types/library';

	interface Props {
		series: SeriesCardData;
	}

	let { series }: Props = $props();

	/** show_secondary_works picks which pair of counts applies. Ported from v1's
	 *  seriesStatusBadge. */
	const missing = $derived(
		series.show_secondary_works ? series.missing_all : series.missing_primary
	);
	const upcoming = $derived(
		series.show_secondary_works ? series.upcoming_all : series.upcoming_primary
	);
	/** Both null means the counts have not been computed yet — show no badge at all
	 *  rather than claiming the series is complete. */
	const known = $derived(missing != null || upcoming != null);
</script>

<EntityCard href="/library/series/{series.id}" name={series.name}>
	{#snippet meta()}
		<Badge variant="in_library">{series.library_count ?? 0}</Badge>
		{#if (series.requested_count ?? 0) > 0}
			<Badge variant="requested">+{series.requested_count}</Badge>
		{/if}
		{#if known}
			{#if (missing ?? 0) > 0}
				<Badge variant="missing" small>{missing} missing</Badge>
			{:else if (upcoming ?? 0) > 0}
				<Badge variant="upcoming" small>{upcoming} upcoming</Badge>
			{:else}
				<Badge variant="completed" small>Complete</Badge>
			{/if}
		{/if}
	{/snippet}
</EntityCard>
