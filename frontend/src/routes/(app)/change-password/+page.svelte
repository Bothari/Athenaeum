<script lang="ts">
	import { goto } from '$app/navigation';
	import { changePassword } from '$lib/api/auth';
	import { auth } from '$lib/stores/auth.svelte';
	import { toasts } from '$lib/stores/toast.svelte';

	let current = $state('');
	let next = $state('');
	let confirm = $state('');
	let feedback = $state('');
	let busy = $state(false);

	async function submit(event: Event) {
		event.preventDefault();
		if (!current || !next) {
			feedback = 'All fields required.';
			return;
		}
		if (next !== confirm) {
			feedback = 'Passwords do not match.';
			return;
		}

		busy = true;
		feedback = '';
		try {
			await changePassword(current, next);
			// Re-read the session so force_password_change clears and the app-shell
			// guard stops redirecting back here.
			await auth.load();
			toasts.success('Password updated.');
			await goto('/', { replaceState: true });
		} catch {
			feedback = 'Failed to change password.';
			busy = false;
		}
	}
</script>

<div class="page">
	<h1>Set new password</h1>
	<form class="card" onsubmit={submit}>
		{#if auth.mustChangePassword}
			<p class="dim">Your password must be changed before continuing.</p>
		{/if}

		<div class="form-group">
			<label class="form-label" for="cp-current">Current password</label>
			<input id="cp-current" bind:value={current} type="password" autocomplete="current-password" />
		</div>
		<div class="form-group">
			<label class="form-label" for="cp-new">New password</label>
			<input id="cp-new" bind:value={next} type="password" autocomplete="new-password" />
		</div>
		<div class="form-group">
			<label class="form-label" for="cp-confirm">Confirm new password</label>
			<input id="cp-confirm" bind:value={confirm} type="password" autocomplete="new-password" />
		</div>
		<div class="form-actions">
			<button type="submit" class="btn" disabled={busy}>Save password</button>
			<span class="feedback">{feedback}</span>
		</div>
	</form>
</div>

<style>
	.page {
		max-width: 400px;
		margin: 2rem auto 0;
	}

	h1 {
		font-size: 1.25rem;
		font-weight: 600;
		margin-bottom: 1rem;
	}

	.card {
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 1rem;
	}

	.dim {
		color: var(--text-dim);
		font-size: 0.85rem;
		margin-bottom: 1rem;
	}

	.form-group {
		margin-bottom: 1rem;
	}

	.form-label {
		display: block;
		font-size: 0.85rem;
		color: var(--text-dim);
		margin-bottom: 0.35rem;
	}

	/* Padding controls size, not font-size — see CLAUDE.md. */
	input {
		width: 100%;
		padding: 0.4rem 0.6rem;
		background: var(--bg);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
	}

	input:focus {
		border-color: var(--accent);
		outline: none;
	}

	.form-actions {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.btn {
		padding: 0.4rem 0.9rem;
		background: var(--accent);
		color: #fff;
		border: none;
		border-radius: var(--radius);
		font-size: 0.9rem;
	}

	.btn:disabled {
		opacity: 0.6;
	}

	.feedback {
		font-size: 0.85rem;
		color: var(--red);
	}
</style>
