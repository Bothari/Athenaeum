<script lang="ts">
	import { goto } from '$app/navigation';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import { auth } from '$lib/stores/auth.svelte';

	let signingOut = $state(false);

	async function signOut() {
		signingOut = true;
		await auth.signOut();
		await goto('/login', { replaceState: true });
	}
</script>

<div class="page">
	<PageHeader title="Profile" icon="author" />

	<div class="card">
		<div class="kv"><span class="label">Username</span><span>{auth.user?.username}</span></div>
		{#if auth.user?.email}
			<div class="kv"><span class="label">Email</span><span>{auth.user.email}</span></div>
		{/if}
		<div class="kv"><span class="label">Role</span><span>{auth.user?.role}</span></div>
	</div>

	<div class="actions">
		<a class="btn-link" href="/change-password">Change password</a>
		<button type="button" class="btn" onclick={signOut} disabled={signingOut}>Sign out</button>
	</div>
</div>

<style>
	.page {
		max-width: 400px;
	}

	.card {
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 1rem;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.kv {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
	}

	.label {
		color: var(--text-dim);
	}

	.actions {
		margin-top: 1rem;
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.btn {
		padding: 0.4rem 0.9rem;
		background: var(--surface2);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		font-size: 0.9rem;
	}

	.btn:disabled {
		opacity: 0.6;
	}

	.btn-link {
		font-size: 0.9rem;
	}
</style>
