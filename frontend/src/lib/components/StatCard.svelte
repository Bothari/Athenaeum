<script lang="ts">
	interface Props {
		value: number | string;
		label: string;
		/** Renders as a link when set. */
		href?: string;
		tone?: 'default' | 'accent' | 'red' | 'green';
		disabled?: boolean;
	}

	let { value, label, href, tone = 'default', disabled = false }: Props = $props();
</script>

<!-- v1 used inline onclick="navigate(...)" on a div, which relied on a global
     function and gave no link affordances. An anchor is used when clickable. -->
<svelte:element
	this={href ? 'a' : 'div'}
	{href}
	class="stat-card"
	class:clickable={!!href}
	class:disabled
	role={href ? undefined : 'group'}
>
	<div class="value tone-{tone}">{value}</div>
	<div class="label">{label}</div>
</svelte:element>

<style>
	.stat-card {
		flex: 1;
		min-width: 0;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 0.75rem 1rem;
		text-align: center;
		color: inherit;
		text-decoration: none;
		display: block;
	}

	.stat-card.clickable {
		cursor: pointer;
		transition: border-color 0.15s;
	}

	.stat-card.clickable:hover {
		border-color: var(--accent);
		text-decoration: none;
	}

	.stat-card.disabled {
		opacity: 0.55;
	}

	.value {
		font-size: 1.4rem;
		font-weight: 700;
		letter-spacing: -0.02em;
	}

	.tone-accent {
		color: var(--accent);
	}

	.tone-red {
		color: var(--red);
	}

	.tone-green {
		color: var(--green);
	}

	.label {
		font-size: 0.78rem;
		color: var(--text-dim);
		margin-top: 0.15rem;
	}
</style>
