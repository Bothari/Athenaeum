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
	/*
	 * A real button, not a link. It previously had no background and a transparent
	 * border, so the first click armed it and the 4s timeout disarmed it — which
	 * from the outside is indistinguishable from the button doing nothing.
	 *
	 * Sizing matches the app's small-button convention so it lines up with
	 * siblings; it was visibly shorter than the buttons beside it.
	 */
	button {
		padding: 0.3rem 0.7rem;
		font-size: 0.85rem;
		background: var(--surface2);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		white-space: nowrap;
	}

	button.danger {
		color: var(--red);
		border-color: color-mix(in srgb, var(--red) 40%, transparent);
	}

	button:hover:not(:disabled) {
		border-color: currentColor;
	}

	/* Armed: unmistakably different, and the label says what a second tap does. */
	button.pending {
		background: var(--red);
		border-color: var(--red);
		color: #fff;
	}

	button:disabled {
		opacity: 0.6;
	}
</style>
