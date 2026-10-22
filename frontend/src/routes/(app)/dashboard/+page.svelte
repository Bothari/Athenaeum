<script lang="ts">
	import ActiveDownloads from '$lib/components/ActiveDownloads.svelte';
	import Badge from '$lib/components/Badge.svelte';
	import type { BadgeVariant } from '$lib/components/Badge.svelte';
	import ErrorState from '$lib/components/ErrorState.svelte';
	import LoadingState from '$lib/components/LoadingState.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import StatCard from '$lib/components/StatCard.svelte';
	import TaskCard from '$lib/components/TaskCard.svelte';
	import { getSettings, getStatus, getSyncStatus, runSyncTask, SYNC_TASKS } from '$lib/api/status';
	import { toasts } from '$lib/stores/toast.svelte';
	import type { StatusCounts, SyncStatus } from '$lib/types/status';

	const TASK_POLL_MS = 2000;

	/** Shown only when general.debug_view is on. Reference for what each status
	 *  pill looks like. */
	const LEGEND: { heading: string; pills: { variant: BadgeVariant; label: string }[] }[] = [
		{
			heading: 'Request states',
			pills: [
				{ variant: 'pending', label: 'Pending' },
				{ variant: 'requested', label: 'Requested' },
				{ variant: 'snatched', label: 'Snatched' },
				{ variant: 'downloading', label: 'Downloading' },
				{ variant: 'downloaded', label: 'Downloaded' },
				{ variant: 'merging', label: 'Merging' },
				{ variant: 'organizing', label: 'Organizing' },
				{ variant: 'completed', label: 'Completed' },
				{ variant: 'in_library', label: 'In Library' },
				{ variant: 'failed', label: 'Failed' }
			]
		},
		{
			heading: 'Misc',
			pills: [
				{ variant: 'upcoming', label: 'Upcoming' },
				{ variant: 'missing', label: 'Missing' },
				{ variant: 'sso', label: 'SSO' },
				{ variant: 'neutral', label: 'Neutral' }
			]
		}
	];

	let status = $state<StatusCounts | null>(null);
	let sync = $state<SyncStatus>({});
	let debugView = $state(false);
	let failed = $state(false);
	let running = $state<string | null>(null);

	/** Sums the states that mean "a download is in flight". */
	const active = $derived.by(() => {
		const r = status?.requests ?? {};
		return (
			(r.snatched ?? 0) +
			(r.downloading ?? 0) +
			(r.downloaded ?? 0) +
			(r.merging ?? 0) +
			(r.organizing ?? 0)
		);
	});

	const anyTaskRunning = $derived(Object.values(sync).some((t) => t.running));

	async function loadAll() {
		failed = false;
		try {
			const [s, sy, settings] = await Promise.all([getStatus(), getSyncStatus(), getSettings()]);
			status = s;
			sync = sy;
			debugView = settings.general?.debug_view === true;
		} catch {
			failed = true;
		}
	}

	$effect(() => {
		loadAll();
	});

	/**
	 * Polls task status only while something is running. v1 started an interval per
	 * button press and cleared it from inside the callback; keying off the running
	 * flag means at most one poller, stopped automatically on unmount.
	 */
	$effect(() => {
		if (!anyTaskRunning) return;
		const timer = setInterval(async () => {
			try {
				sync = await getSyncStatus();
			} catch {
				// Leave the previous snapshot in place on a transient failure.
			}
		}, TASK_POLL_MS);
		return () => clearInterval(timer);
	});

	async function run(key: string, label: string, endpoint: string) {
		running = key;
		try {
			await runSyncTask(endpoint);
			toasts.info(`${label} started`);
			sync = await getSyncStatus();
		} catch (err) {
			toasts.error(`Failed: ${err instanceof Error ? err.message : String(err)}`);
		} finally {
			running = null;
		}
	}
</script>

<PageHeader title="Dashboard" />

{#if failed}
	<ErrorState onretry={loadAll} />
{:else if !status}
	<LoadingState />
{:else}
	<h2 class="section">Library</h2>
	<div class="row">
		<StatCard value={status.books ?? 0} label="Books" href="/library/books" />
		<StatCard value={status.authors ?? 0} label="Authors" href="/library/authors" />
		<StatCard value={status.series ?? 0} label="Series" href="/library/series" />
	</div>
	<div class="row">
		<StatCard value={status.audiobooks ?? 0} label="Audiobooks" />
		<StatCard value={status.ebooks ?? 0} label="Ebooks" />
	</div>

	<h2 class="section">Queue</h2>
	<div class="row">
		<StatCard value={status.requests?.requested ?? 0} label="Requested" href="/requests" />
		<StatCard
			value={active}
			label="Downloading"
			href="/requests?tab=downloads"
			tone={active ? 'accent' : 'default'}
		/>
		<StatCard
			value={status.requests?.failed ?? 0}
			label="Failed"
			tone={status.requests?.failed ? 'red' : 'default'}
		/>
	</div>

	<ActiveDownloads />

	<h2 class="section">Hardcover Links</h2>
	<div class="row">
		{#each [{ key: 'unlinked_books', label: 'Books unlinked', href: '/library/books' }, { key: 'unlinked_authors', label: 'Authors unlinked', href: '/library/authors' }, { key: 'unlinked_series', label: 'Series unlinked', href: '/library/series' }] as tile (tile.key)}
			{@const count = (status[tile.key as keyof StatusCounts] as number) ?? 0}
			<StatCard
				value={count}
				label={tile.label}
				href={count ? `${tile.href}?unlinked=1` : undefined}
				tone={count ? 'default' : 'green'}
			/>
		{/each}
	</div>

	<h2 class="section">Scheduled Tasks</h2>
	<div class="row">
		{#each SYNC_TASKS as task (task.key)}
			<TaskCard
				label={task.label}
				task={sync[task.key] ?? {}}
				busy={running === task.key}
				onrun={() => run(task.key, task.label, task.endpoint)}
			/>
		{/each}
	</div>

	{#if debugView}
		<h2 class="section">Status Pill Legend</h2>
		<div class="legend">
			{#each LEGEND as group (group.heading)}
				<div>
					<div class="legend-heading">{group.heading}</div>
					<div class="legend-pills">
						{#each group.pills as pill (pill.variant)}
							<Badge variant={pill.variant}>{pill.label}</Badge>
						{/each}
					</div>
				</div>
			{/each}
		</div>
	{/if}
{/if}

<style>
	.section {
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--text-dim);
		margin: 1.5rem 0 0.5rem;
	}

	.row {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
		flex-wrap: wrap;
	}

	.legend {
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 0.75rem 1rem;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.legend-heading {
		font-size: 0.72rem;
		color: var(--text-dim);
		text-transform: uppercase;
		letter-spacing: 0.06em;
		margin-bottom: 0.35rem;
	}

	.legend-pills {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
	}
</style>
