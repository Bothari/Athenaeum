<script lang="ts">
	import type { Snippet } from 'svelte';

	/**
	 * Two-stage confirm, ported from v1's confirmAction: the first click swaps the
	 * label, a second within the timeout runs the action, and it reverts on its own
	 * if ignored. v1 stored the pending flag in a dataset attribute on the DOM node.
	 */
	interface Props {
		confirmLabel?: string;
		timeoutMs?: number;
		danger?: boolean;
		onconfirm: () => void | Promise<void>;
		children: Snippet;
	}

	let {
		confirmLabel = 'Confirm?',
		timeoutMs = 4000,
		danger = false,
		onconfirm,
		children
	}: Props = $props();

	let pending = $state(false);
	let busy = $state(false);
	let timer: ReturnType<typeof setTimeout>;

	async function click() {
		if (!pending) {
			pending = true;
			timer = setTimeout(() => (pending = false), timeoutMs);
			return;
		}
		clearTimeout(timer);
		pending = false;
		busy = true;
		try {
			await onconfirm();
		} finally {
			busy = false;
		}
	}

	$effect(() => () => clearTimeout(timer));
</script>

<button type="button" class:pending class:danger disabled={busy} onclick={click}>
	{#if pending}{confirmLabel}{:else}{@render children()}{/if}
</button>

<style>
	button {
		padding: 0.15rem 0.5rem;
		font-size: 0.8rem;
		background: none;
		border: 1px solid transparent;
		border-radius: var(--radius);
		color: var(--text-dim);
		white-space: nowrap;
	}

	button:hover:not(:disabled) {
		color: var(--text);
		border-color: var(--border);
	}

	button.danger {
		color: var(--red);
	}

	button.pending {
		color: var(--yellow);
		border-color: var(--yellow);
	}

	button:disabled {
		opacity: 0.6;
	}
</style>
