<script lang="ts">
	import Icon from './Icon.svelte';
	import { formatDate } from '$lib/format';
	import type { TaskStatus } from '$lib/types/status';

	interface Props {
		label: string;
		task: TaskStatus;
		busy?: boolean;
		onrun: () => void;
	}

	let { label, task, busy = false, onrun }: Props = $props();

	/** No schedule and not currently running means the task is switched off. The
	 *  dev instance has all cron expressions blanked, so this is the normal state
	 *  there. */
	const disabled = $derived(!task.next_run && !task.running);
</script>

<div class="task" class:disabled>
	<div class="head">
		<div class="label">{label}</div>
		<button type="button" onclick={onrun} disabled={busy || task.running}>
			<Icon name="spinner" size={12} />
			Run
		</button>
	</div>

	<div class="status">
		{#if disabled}
			Disabled
		{:else if task.running}
			<Icon name="spinner" size={12} /> running
		{:else if task.last_run}
			Last: {formatDate(task.last_run)}
		{:else}
			Never run
		{/if}
	</div>

	{#if !disabled && task.last_result}
		<div class="result" class:dim={task.running}>{task.last_result}</div>
	{/if}
</div>

<style>
	.task {
		flex: 1;
		min-width: 0;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 0.75rem 1rem;
	}

	.task.disabled {
		opacity: 0.55;
	}

	.head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.5rem;
	}

	.label {
		font-size: 0.9rem;
		font-weight: 600;
	}

	button {
		display: inline-flex;
		align-items: center;
		gap: 0.25rem;
		font-size: 0.78rem;
		padding: 0.15rem 0.5rem;
		white-space: nowrap;
		background: none;
		border: 1px solid var(--border);
		border-radius: var(--radius);
		color: var(--text-dim);
	}

	button:hover:not(:disabled) {
		color: var(--text);
		border-color: var(--accent);
	}

	button:disabled {
		opacity: 0.5;
	}

	.status {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		font-size: 0.78rem;
		color: var(--text-dim);
		margin-top: 0.35rem;
	}

	.result {
		font-size: 0.78rem;
		margin-top: 0.2rem;
		white-space: pre-line;
	}

	.result.dim {
		color: var(--text-dim);
	}
</style>
