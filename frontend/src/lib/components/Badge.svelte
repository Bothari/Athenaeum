<script lang="ts">
	import type { Snippet } from 'svelte';

	/** Status vocabulary from v1's badge-* classes. Kept as a union so a typo in a
	 *  route is a compile error rather than an unstyled badge. */
	export type BadgeVariant =
		| 'pending'
		| 'requested'
		| 'sso'
		| 'snatched'
		| 'downloading'
		| 'downloaded'
		| 'merging'
		| 'organizing'
		| 'completed'
		| 'in_library'
		| 'failed'
		| 'missing'
		| 'upcoming'
		| 'warn'
		| 'neutral';

	interface Props {
		variant: BadgeVariant;
		title?: string;
		small?: boolean;
		children: Snippet;
	}

	let { variant, title, small = false, children }: Props = $props();
</script>

<span class="badge badge-{variant}" class:small {title}>{@render children()}</span>

<style>
	.badge {
		display: inline-flex;
		align-items: center;
		gap: 0.25rem;
		font-size: 0.72rem;
		padding: 0.2rem 0.5rem;
		border-radius: 999px;
		font-weight: 500;
		white-space: nowrap;
	}

	/* v1 applied this inline on series cards. */
	.small {
		font-size: 0.75rem;
	}

	/* Dark (default) */
	.badge-pending {
		background: #2a2600;
		color: #c8a020;
	}
	.badge-requested {
		background: #1a2a40;
		color: #60a0d8;
	}
	.badge-sso {
		background: #183828;
		color: #50a060;
	}
	.badge-snatched {
		background: #3a2000;
		color: #e07020;
	}
	.badge-downloading,
	.badge-downloaded {
		background: #382800;
		color: #d09020;
	}
	.badge-merging,
	.badge-organizing {
		background: #281848;
		color: #9060d8;
	}
	.badge-completed,
	.badge-in_library {
		background: #183828;
		color: #50a060;
	}
	.badge-failed {
		background: #3a1818;
		color: #c04040;
	}
	.badge-missing {
		background: #3a2010;
		color: #d05828;
	}
	.badge-upcoming {
		background: #181e40;
		color: #6078d0;
	}
	.badge-warn {
		background: #2a2200;
		color: #e0b820;
	}
	.badge-neutral {
		background: var(--surface2);
		color: var(--text-dim);
		opacity: 0.6;
	}

	/* Light. :global on the html selector because it lives outside this component,
	   so Svelte would otherwise scope it away as unused. */
	:global(html.light) .badge-pending {
		background: #fff8d0;
		color: #7a6000;
	}
	:global(html.light) .badge-requested {
		background: #d8eaf8;
		color: #185080;
	}
	:global(html.light) .badge-sso {
		background: #d8eedc;
		color: #185828;
	}
	:global(html.light) .badge-snatched {
		background: #feecd8;
		color: #8a3800;
	}
	:global(html.light) .badge-downloading,
	:global(html.light) .badge-downloaded {
		background: #fef0d0;
		color: #7a5000;
	}
	:global(html.light) .badge-merging,
	:global(html.light) .badge-organizing {
		background: #ece0ff;
		color: #502898;
	}
	:global(html.light) .badge-completed,
	:global(html.light) .badge-in_library {
		background: #d8eedc;
		color: #185828;
	}
	:global(html.light) .badge-failed {
		background: #fcd8d8;
		color: #881818;
	}
	:global(html.light) .badge-missing {
		background: #fde8d8;
		color: #883010;
	}
	:global(html.light) .badge-upcoming {
		background: #dde0f8;
		color: #283898;
	}
	:global(html.light) .badge-warn {
		background: #fffbe0;
		color: #7a5e00;
	}
	:global(html.light) .badge-neutral {
		background: var(--surface2);
		color: var(--text-dim);
		opacity: 1;
	}
</style>
