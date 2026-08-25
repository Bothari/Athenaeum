<script lang="ts">
	import type { Snippet } from 'svelte';
	import Icon from './Icon.svelte';
	import type { IconName } from './Icon.svelte';

	interface Props {
		title: string;
		icon?: IconName;
		/** Right-aligned actions. */
		actions?: Snippet;
	}

	let { title, icon, actions }: Props = $props();
</script>

<div class="page-header">
	<span class="page-title">
		{#if icon}<Icon name={icon} />{/if}
		{title}
	</span>
	{#if actions}<div class="actions">{@render actions()}</div>{/if}
</div>

<style>
	.page-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.page-title {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 1.15rem;
		font-weight: 600;
		letter-spacing: -0.01em;
	}

	.actions {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
</style>
