<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { login, OIDC_START_URL } from '$lib/api/auth';
	import { isForceLocal, setForceLocal, FORCE_LOCAL_KEY } from '$lib/api/client';
	import { auth } from '$lib/stores/auth.svelte';

	const next = $derived(page.url.searchParams.get('next') ?? '/');

	let username = $state('');
	let password = $state('');
	let feedback = $state('');
	let busy = $state(false);
	/** Held true until the SSO decision is made, so the form never flashes before
	 *  an automatic redirect. */
	let deciding = $state(true);
	let showSsoLink = $state(false);

	let usernameInput = $state<HTMLInputElement | null>(null);

	$effect(() => {
		// ?force_local=1 pins local login for the rest of the tab session, which is
		// the only way in when OIDC is enabled and misbehaving.
		if (page.url.searchParams.has(FORCE_LOCAL_KEY)) setForceLocal();

		decide();
	});

	async function decide() {
		if (!auth.resolved) return;

		if (auth.isAuthenticated) {
			await goto(auth.mustChangePassword ? '/change-password' : next, { replaceState: true });
			return;
		}

		const forceLocal = isForceLocal();
		const hasOidc = auth.modes.includes('oidc');

		// v1 sent the user straight to SSO whenever OIDC was available and local
		// login had not been forced — including when a form was also on offer.
		if (hasOidc && !forceLocal) {
			window.location.href = OIDC_START_URL;
			return;
		}

		showSsoLink = hasOidc && !forceLocal;
		deciding = false;
		usernameInput?.focus();
	}

	async function submit(event?: Event) {
		event?.preventDefault();
		if (!username.trim() || !password) {
			feedback = 'Enter username and password.';
			return;
		}

		busy = true;
		feedback = '';
		try {
			const result = await login(username.trim(), password);
			await auth.completeLogin();
			await goto(result.force_password_change ? '/change-password' : next, { replaceState: true });
		} catch {
			feedback = 'Invalid credentials.';
			busy = false;
		}
	}
</script>

<div class="page">
	{#if deciding}
		<p class="dim">Signing in...</p>
	{:else}
		<h1>Sign in</h1>
		<form class="card" onsubmit={submit}>
			<div class="form-group">
				<label class="form-label" for="username">Username</label>
				<input
					id="username"
					bind:this={usernameInput}
					bind:value={username}
					type="text"
					autocomplete="username"
				/>
			</div>
			<div class="form-group">
				<label class="form-label" for="password">Password</label>
				<input
					id="password"
					bind:value={password}
					type="password"
					autocomplete="current-password"
				/>
			</div>
			<div class="form-actions">
				<button type="submit" class="btn" disabled={busy}>Sign in</button>
				<span class="feedback">{feedback}</span>
			</div>
		</form>

		{#if showSsoLink}
			<p class="sso"><a href={OIDC_START_URL}>Sign in with SSO</a></p>
		{/if}
	{/if}
</div>

<style>
	.page {
		max-width: 400px;
		margin: 4rem auto 0;
		padding: 0 1rem;
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

	.form-group {
		margin-bottom: 1rem;
	}

	.form-label {
		display: block;
		font-size: 0.85rem;
		color: var(--text-dim);
		margin-bottom: 0.35rem;
	}

	/* Size comes from padding, never font-size: dropping below 16px makes iOS
	   zoom the page on focus. See CLAUDE.md. */
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

	.dim {
		color: var(--text-dim);
		font-size: 0.9rem;
		text-align: center;
	}

	.sso {
		margin-top: 1rem;
		text-align: center;
		font-size: 0.85rem;
	}
</style>
