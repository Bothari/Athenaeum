<script lang="ts">
	/**
	 * Progress bar and summary line for series/author detail pages.
	 *
	 * missing/upcoming/total arrive later than inLibrary (they need a Hardcover
	 * lookup), so null means "still checking" and is rendered as such rather than
	 * as zero.
	 */
	interface Props {
		inLibrary?: number | null;
		requested?: number | null;
		missing?: number | null;
		upcoming?: number | null;
		total?: number | null;
		/** Anchors the missing/upcoming links scroll to, when the page has them. */
		missingTargetId?: string;
		upcomingTargetId?: string;
	}

	let {
		inLibrary = 0,
		requested = 0,
		missing = null,
		upcoming = null,
		total = null,
		missingTargetId,
		upcomingTargetId
	}: Props = $props();

	const pending = $derived(missing == null);
	const percent = $derived(
		total && inLibrary != null ? Math.round(((inLibrary ?? 0) / total) * 100) : null
	);

	function scrollTo(id: string | undefined, event: MouseEvent) {
		if (!id) return;
		event.preventDefault();
		document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}
</script>

<div class="stats">
	{#if total != null}
		<div class="bar" title="{inLibrary} of {total} in library">
			<div class="fill" style="width:{percent}%"></div>
		</div>
	{:else}
		<div class="bar loading"></div>
	{/if}

	<div class="summary">
		<span>{inLibrary ?? 0} in library</span>

		{#if requested}
			<span class="sep">·</span>
			<span>{requested} requested</span>
		{/if}

		<span class="sep">·</span>
		{#if pending}
			<span class="dim">checking…</span>
		{:else if missing}
			<a class="missing" href="#{missingTargetId ?? ''}" onclick={(e) => scrollTo(missingTargetId, e)}>
				{missing} missing
			</a>
			{#if upcoming}
				<span class="sep">·</span>
				<a
					class="upcoming"
					href="#{upcomingTargetId ?? ''}"
					onclick={(e) => scrollTo(upcomingTargetId, e)}
				>
					{upcoming} upcoming
				</a>
			{/if}
		{:else if upcoming}
			<a
				class="upcoming"
				href="#{upcomingTargetId ?? ''}"
				onclick={(e) => scrollTo(upcomingTargetId, e)}
			>
				{upcoming} upcoming
			</a>
		{:else}
			<span class="complete">complete</span>
		{/if}
	</div>
</div>

<style>
	.stats {
		margin-bottom: 0.75rem;
	}

	.bar {
		height: 6px;
		border-radius: 3px;
		background: var(--surface2);
		margin-bottom: 0.5rem;
		overflow: hidden;
	}

	.bar.loading {
		opacity: 0.4;
	}

	.fill {
		height: 100%;
		background: var(--green);
		border-radius: 3px;
		transition: width 0.4s ease;
	}

	.summary {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 0.3rem;
		font-size: 0.85rem;
	}

	.sep {
		color: var(--text-dim);
	}

	.dim {
		color: var(--text-dim);
	}

	.missing {
		color: var(--red);
		font-weight: 500;
		text-decoration: none;
	}

	.upcoming {
		color: var(--yellow);
		font-weight: 500;
		text-decoration: none;
	}

	.missing:hover,
	.upcoming:hover {
		text-decoration: underline;
	}

	.complete {
		color: var(--green);
		font-weight: 500;
	}
</style>
