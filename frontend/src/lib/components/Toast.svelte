<script lang="ts">
	import { toasts } from '$lib/stores/toast.svelte';
</script>

<div class="toast-container">
	{#each toasts.items as toast (toast.id)}
		<div class="toast toast-{toast.type}" role="status">{toast.message}</div>
	{/each}
</div>

<style>
	.toast-container {
		position: fixed;
		bottom: 1.5rem;
		right: 1.5rem;
		z-index: 999;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.toast {
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 0.65rem 1rem;
		font-size: 0.875rem;
		min-width: 240px;
		max-width: 360px;
		animation: slide-in 0.2s ease;
	}

	.toast-success {
		border-left: 3px solid var(--green);
	}

	.toast-error {
		border-left: 3px solid var(--red);
	}

	.toast-info {
		border-left: 3px solid var(--accent);
	}

	@keyframes slide-in {
		from {
			opacity: 0;
			transform: translateX(1rem);
		}
		to {
			opacity: 1;
			transform: translateX(0);
		}
	}
</style>
