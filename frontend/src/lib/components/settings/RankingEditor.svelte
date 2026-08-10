<script lang="ts">
	import Icon from '../Icon.svelte';
	import { CRITERION_META } from './schemas';
	import type { RankingCriterion } from '$lib/types/settings';

	/**
	 * Ordered ranking criteria for auto-search. Results are filtered, then sorted
	 * by these top to bottom; inactive ones are ignored.
	 *
	 * v1 used HTML5 drag-and-drop, which is unusable on touch. Move up/down
	 * buttons work everywhere and are keyboard-accessible, which matters given
	 * how much of this app is used on a phone.
	 */
	interface Props {
		items: RankingCriterion[];
		onchange: (items: RankingCriterion[]) => void;
	}

	let { items, onchange }: Props = $props();

	function move(index: number, delta: number) {
		const next = [...items];
		const target = index + delta;
		if (target < 0 || target >= next.length) return;
		[next[index], next[target]] = [next[target], next[index]];
		onchange(next);
	}

	function update(index: number, patch: Partial<RankingCriterion>) {
		onchange(items.map((item, i) => (i === index ? { ...item, ...patch } : item)));
	}
</script>

<h3 class="heading">Result ranking</h3>
<p class="hint">
	Results are filtered then sorted top to bottom. Inactive criteria are ignored.
</p>

<div class="stack">
	{#each items as item, i (item.criterion)}
		{@const meta = CRITERION_META[item.criterion] ?? { label: item.criterion, desc: '' }}
		<div class="item">
			<div class="order">
				<button
					type="button"
					aria-label="Move {meta.label} up"
					disabled={i === 0}
					onclick={() => move(i, -1)}
				>
					<Icon name="arrow-up" size={12} />
				</button>
				<button
					type="button"
					aria-label="Move {meta.label} down"
					disabled={i === items.length - 1}
					onclick={() => move(i, 1)}
				>
					<Icon name="arrow-down" size={12} />
				</button>
			</div>

			<div class="body">
				<div class="label">{meta.label}</div>
				<div class="desc">{meta.desc}</div>
			</div>

			{#if meta.prefer}
				<select
					value={item.prefer ?? meta.prefer[0]}
					onchange={(e) => update(i, { prefer: e.currentTarget.value })}
				>
					{#each meta.prefer as option (option)}
						<option value={option}>Prefer {option}</option>
					{/each}
				</select>
			{/if}

			<label class="active">
				<input
					type="checkbox"
					checked={item.enabled !== false}
					onchange={(e) => update(i, { enabled: e.currentTarget.checked })}
				/>
				Active
			</label>
		</div>
	{/each}
</div>

<style>
	.heading {
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--text-dim);
		margin: 1.5rem 0 0.25rem;
	}

	.hint {
		font-size: 0.78rem;
		color: var(--text-dim);
		margin-bottom: 0.75rem;
	}

	.stack {
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
	}

	.item {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 0.5rem 0.75rem;
	}

	.order {
		display: flex;
		flex-direction: column;
		gap: 0.1rem;
		flex-shrink: 0;
	}

	.order button {
		background: none;
		border: 1px solid var(--border);
		border-radius: 3px;
		color: var(--text-dim);
		padding: 0 0.2rem;
		line-height: 1;
		display: flex;
	}

	.order button:hover:not(:disabled) {
		color: var(--accent);
		border-color: var(--accent);
	}

	.order button:disabled {
		opacity: 0.35;
	}

	.body {
		flex: 1;
		min-width: 0;
	}

	.label {
		font-size: 0.9rem;
		font-weight: 500;
	}

	.desc {
		font-size: 0.8rem;
		color: var(--text-dim);
	}

	select {
		padding: 0.2rem 0.5rem;
		background: var(--bg);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		flex-shrink: 0;
	}

	.active {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		font-size: 0.82rem;
		white-space: nowrap;
		flex-shrink: 0;
		cursor: pointer;
	}
</style>
