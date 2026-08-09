<script lang="ts">
	// Placeholder home. The real search page lands in phase 4 — this exists so the
	// shell, guard and nav have somewhere to land.
	import { auth } from '$lib/stores/auth.svelte';
</script>

<h1>Athenaeum</h1>
<p class="dim">
	Signed in as <strong>{auth.user?.username}</strong> ({auth.user?.role}). Search lands in a later
	phase.
</p>

<style>
	h1 {
		font-size: 1.5rem;
		font-weight: 700;
		letter-spacing: -0.02em;
		margin-bottom: 0.5rem;
	}

	.dim {
		color: var(--text-dim);
		font-size: 0.9rem;
	}
</style>
