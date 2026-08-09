<script lang="ts">
	import Icon from './Icon.svelte';

	interface Props {
		/** Shrinks the reserved height for inline use inside a card or section. */
		compact?: boolean;
	}

	let { compact = false }: Props = $props();
</script>

<div class="state-loading" class:compact>
	<Icon name="spinner" />
</div>

<style>
	.state-loading {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 200px;
		color: var(--text-dim);
	}

	.compact {
		min-height: 4rem;
	}
</style>
