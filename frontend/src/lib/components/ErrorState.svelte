<script lang="ts">
	interface Props {
		message?: string;
		/** Omit to hide the retry affordance entirely. */
		onretry?: () => void;
	}

	let { message = 'Failed to load.', onretry }: Props = $props();
</script>

<div class="state-error">
	<span>{message}</span>
	{#if onretry}
		<button type="button" class="retry" onclick={onretry}>Retry</button>
	{/if}
</div>

<style>
	.state-error {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 200px;
		color: var(--text-dim);
		gap: 0.5rem;
	}

	/* v1 used an <a href="#"> with a click handler; a button is the honest element
	   and gets keyboard behaviour for free. Styled to read as a link. */
	.retry {
		background: none;
		border: none;
		padding: 0;
		color: var(--accent);
		font-size: inherit;
		text-decoration: none;
	}

	.retry:hover {
		text-decoration: underline;
	}
</style>
