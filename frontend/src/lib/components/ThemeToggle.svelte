<script lang="ts">
	import Icon from './Icon.svelte';
	import { theme } from '$lib/stores/theme.svelte';
</script>

<button
	class="theme-toggle"
	onclick={() => theme.toggle()}
	title="Toggle light/dark mode"
	aria-label="Toggle light/dark mode"
>
	<Icon name={theme.current === 'light' ? 'moon' : 'sun'} />
</button>

<style>
	.theme-toggle {
		background: none;
		border: none;
		color: var(--text-dim);
		padding: 0.3rem;
		border-radius: var(--radius);
		display: flex;
		align-items: center;
		justify-content: center;
		transition: color 0.15s;
	}

	.theme-toggle:hover {
		color: var(--text);
	}
</style>
