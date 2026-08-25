<script lang="ts">
	import { untrack } from 'svelte';
	import SettingField from './SettingField.svelte';
	import { TASK_DEFS } from './schemas';
	import { getNextRun, saveSection } from '$lib/api/settings';
	import { getSyncStatus, runSyncTask } from '$lib/api/status';
	import { formatDateTime } from '$lib/format';
	import { toasts } from '$lib/stores/toast.svelte';
	import type { SyncStatus } from '$lib/types/status';

	/**
	 * Cron schedules for the three background tasks, each with a Run now button
	 * and its last/next run.
	 */
	interface Props {
		initial: Record<string, string>;
	}

	let { initial }: Props = $props();

	// Seeded once, then owned locally — see SettingsForm for why this is untracked.
	let schedule = $state<Record<string, string>>(untrack(() => ({ ...initial })));
	let nextRuns = $state<Record<string, { next_run?: string | null }>>({});
	let status = $state<SyncStatus>({});
	let saving = $state(false);
	let running = $state<string | null>(null);

	async function refresh() {
		status = await getSyncStatus().catch(() => ({}));
	}

	$effect(() => {
		refresh();
	});

	/**
	 * Recomputes next-run whenever an expression changes, so the preview updates
	 * as you type. The endpoint evaluates the expression it is given rather than
	 * what is stored, and answers null for an invalid one — which makes it a
	 * validity check too.
	 */
	$effect(() => {
		for (const task of TASK_DEFS) {
			const expr = schedule[task.key];
			if (!expr) {
				nextRuns[task.key] = { next_run: null };
				continue;
			}
			getNextRun(expr)
				.then((r) => (nextRuns[task.key] = r))
				.catch(() => (nextRuns[task.key] = { next_run: null }));
		}
	});

	async function save() {
		saving = true;
		try {
			await saveSection('schedule', schedule);
			toasts.success('Schedule saved');
			// Next-run times change as soon as the cron does.
			await refresh();
		} catch (err) {
			// The backend validates cron expressions and rejects bad ones, so this
			// message is worth surfacing rather than a generic failure.
			toasts.error(err instanceof Error ? err.message : String(err));
		} finally {
			saving = false;
		}
	}

	async function run(key: string, label: string, endpoint: string) {
		running = key;
		try {
			await runSyncTask(endpoint);
			toasts.info(`${label} started`);
			await refresh();
		} catch (err) {
			toasts.error(`Failed: ${err instanceof Error ? err.message : String(err)}`);
		} finally {
			running = null;
		}
	}
</script>

<div class="cards">
	{#each TASK_DEFS as task (task.key)}
		{@const t = status[task.key] ?? {}}
		<div class="card">
			<div class="head">
				<strong>{task.label}</strong>
				<button
					type="button"
					onclick={() => run(task.key, task.label, task.endpoint)}
					disabled={running === task.key || t.running}
				>
					Run now
				</button>
			</div>

			<SettingField
				spec={{
					key: task.key,
					label: `Cron schedule — default: ${task.default}`,
					placeholder: 'disabled'
				}}
				value={schedule[task.key] ?? ''}
				onchange={(v) => (schedule[task.key] = v as string)}
			/>

			<div class="meta">
				<span>
					{#if !schedule[task.key]}
						Disabled
					{:else if nextRuns[task.key]?.next_run}
						Next: {formatDateTime(nextRuns[task.key].next_run)}
					{:else}
						<span class="invalid">Invalid cron expression</span>
					{/if}
				</span>
				<span>Last: {t.last_run ? formatDateTime(t.last_run) : '—'}</span>
				{#if t.last_result}
					<span class="result">{t.last_result}</span>
				{/if}
			</div>
		</div>
	{/each}
</div>

<div class="actions">
	<button type="button" class="primary" onclick={save} disabled={saving}>
		{saving ? 'Saving…' : 'Save'}
	</button>
</div>

<style>
	.cards {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.card {
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 0.75rem 1rem;
	}

	.head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
	}

	.meta {
		display: flex;
		flex-direction: column;
		gap: 0.1rem;
		font-size: 0.78rem;
		color: var(--text-dim);
	}

	.result {
		white-space: pre-line;
	}

	.invalid {
		color: var(--red);
	}

	.actions {
		margin-top: 1rem;
	}

	button {
		padding: 0.25rem 0.7rem;
		font-size: 0.8rem;
		background: var(--surface2);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		white-space: nowrap;
	}

	button.primary {
		padding: 0.4rem 0.9rem;
		font-size: 0.9rem;
		background: var(--accent);
		border-color: var(--accent);
		color: #fff;
	}

	button:disabled {
		opacity: 0.6;
	}
</style>
