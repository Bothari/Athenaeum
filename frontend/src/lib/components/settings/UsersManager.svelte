<script lang="ts">
	import Badge from '../Badge.svelte';
	import ConfirmButton from '../ConfirmButton.svelte';
	import ErrorState from '../ErrorState.svelte';
	import Icon from '../Icon.svelte';
	import LoadingState from '../LoadingState.svelte';
	import {
		createUser,
		deleteUser,
		listUsers,
		resetPassword,
		updateUser,
		type ManagedUser
	} from '$lib/api/users';
	import { auth } from '$lib/stores/auth.svelte';
	import { toasts } from '$lib/stores/toast.svelte';
	import type { Role } from '$lib/types/auth';

	let users = $state<ManagedUser[]>([]);
	let loading = $state(true);
	let failed = $state(false);
	let openId = $state<string | null>(null);

	// New-user form
	let username = $state('');
	let email = $state('');
	let password = $state('');
	let role = $state<Role>('user');
	let creating = $state(false);
	let createError = $state('');

	// Password reset, inline rather than v1's prompt()
	let resettingId = $state<string | null>(null);
	let newPassword = $state('');

	async function load() {
		loading = true;
		failed = false;
		try {
			users = (await listUsers()).users ?? [];
		} catch {
			failed = true;
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		load();
	});

	/** Guards against an admin removing their own access by accident. */
	function isSelf(u: ManagedUser): boolean {
		return u.id === auth.user?.user_id;
	}

	async function saveEmail(u: ManagedUser, value: string) {
		if ((u.email ?? '') === value.trim()) return;
		try {
			await updateUser(u.id, { email: value.trim() });
			toasts.success('Email updated.');
			u.email = value.trim();
		} catch (err) {
			toasts.error(err instanceof Error ? err.message : 'Failed to update email.');
		}
	}

	async function saveRole(u: ManagedUser, value: Role) {
		try {
			await updateUser(u.id, { role: value });
			toasts.success('Role updated.');
			u.role = value;
		} catch (err) {
			toasts.error(err instanceof Error ? err.message : 'Failed to update role.');
			await load();
		}
	}

	async function doReset(u: ManagedUser) {
		if (!newPassword) return;
		try {
			await resetPassword(u.id, newPassword);
			toasts.success('Password reset.');
			resettingId = null;
			newPassword = '';
			await load();
		} catch (err) {
			toasts.error(err instanceof Error ? err.message : 'Failed to reset password.');
		}
	}

	async function remove(u: ManagedUser) {
		try {
			await deleteUser(u.id);
			toasts.success('User deleted.');
			await load();
		} catch (err) {
			// The backend's message says why (e.g. "Cannot delete yourself"), which is
			// far more useful than a generic failure.
			toasts.error(err instanceof Error ? err.message : 'Failed to delete user.');
		}
	}

	async function add() {
		if (!username.trim() || !password) {
			createError = 'Username and password required.';
			return;
		}
		creating = true;
		createError = '';
		try {
			await createUser({
				username: username.trim(),
				password,
				role,
				email: email.trim() || undefined
			});
			toasts.success('User created.');
			username = '';
			email = '';
			password = '';
			role = 'user';
			await load();
		} catch (err) {
			createError = err instanceof Error ? err.message : String(err);
		} finally {
			creating = false;
		}
	}
</script>

<h2 class="heading">Users</h2>

{#if loading}
	<LoadingState compact />
{:else if failed}
	<ErrorState message="Failed to load users." onretry={load} />
{:else if users.length === 0}
	<p class="dim">No users yet.</p>
{:else}
	{#each users as u (u.id)}
		<div class="card">
			<button
				type="button"
				class="head"
				onclick={() => (openId = openId === u.id ? null : u.id)}
				aria-expanded={openId === u.id}
			>
				<span class="name">
					{u.username}
					{#if isSelf(u)}<span class="you">you</span>{/if}
				</span>
				{#if u.force_password_change}<Badge variant="warn">PW change</Badge>{/if}
				{#if u.oidc_linked}<Badge variant="sso">SSO</Badge>{/if}
				<span class="chevron" class:open={openId === u.id}><Icon name="chevron-down" size={14} /></span>
			</button>

			{#if openId === u.id}
				<div class="body">
					<label class="label" for="email-{u.id}">Email</label>
					<input
						id="email-{u.id}"
						type="email"
						value={u.email ?? ''}
						placeholder="—"
						onblur={(e) => saveEmail(u, e.currentTarget.value)}
						onkeydown={(e) => {
							if (e.key === 'Enter') e.currentTarget.blur();
						}}
					/>

					<label class="label" for="role-{u.id}">Role</label>
					<select
						id="role-{u.id}"
						value={u.role}
						disabled={isSelf(u)}
						onchange={(e) => saveRole(u, e.currentTarget.value as Role)}
					>
						<option value="user">user</option>
						<option value="admin">admin</option>
					</select>
					{#if isSelf(u)}
						<p class="hint">You cannot change your own role — ask another admin.</p>
					{/if}

					<div class="actions">
						{#if resettingId === u.id}
							<input
								type="password"
								bind:value={newPassword}
								placeholder="New temporary password"
								onkeydown={(e) => {
									if (e.key === 'Enter') doReset(u);
								}}
							/>
							<button type="button" class="primary" onclick={() => doReset(u)}>Set</button>
							<button type="button" onclick={() => ((resettingId = null), (newPassword = ''))}>
								Cancel
							</button>
						{:else}
							<button type="button" onclick={() => ((resettingId = u.id), (newPassword = ''))}>
								Reset password
							</button>
							{#if !isSelf(u)}
								<ConfirmButton danger onconfirm={() => remove(u)}>
									Delete
								</ConfirmButton>
							{:else}
								<span class="hint">Deleting your own account is not offered.</span>
							{/if}
						{/if}
					</div>
				</div>
			{/if}
		</div>
	{/each}
{/if}

<h2 class="heading">Add user</h2>
<div class="add">
	<div class="field">
		<label class="label" for="new-username">Username</label>
		<input id="new-username" type="text" bind:value={username} />
	</div>
	<div class="field">
		<label class="label" for="new-email">Email <span class="dim">(optional)</span></label>
		<input id="new-email" type="email" bind:value={email} />
	</div>
	<div class="field">
		<label class="label" for="new-password">Temp password</label>
		<input id="new-password" type="password" bind:value={password} />
	</div>
	<div class="field narrow">
		<label class="label" for="new-role">Role</label>
		<select id="new-role" bind:value={role}>
			<option value="user">User</option>
			<option value="admin">Admin</option>
		</select>
	</div>
	<button type="button" class="primary" onclick={add} disabled={creating}>
		{creating ? 'Adding…' : 'Add user'}
	</button>
</div>
{#if createError}<p class="err">{createError}</p>{/if}

<style>
	.heading {
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--text-dim);
		margin: 1.5rem 0 0.5rem;
	}

	.card {
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		margin-bottom: 0.35rem;
	}

	.head {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		width: 100%;
		background: none;
		border: none;
		color: inherit;
		padding: 0.6rem 0.9rem;
		text-align: left;
		font-size: 0.95rem;
	}

	.name {
		font-weight: 500;
	}

	.you {
		font-size: 0.72rem;
		color: var(--text-dim);
		margin-left: 0.3rem;
	}

	.chevron {
		margin-left: auto;
		display: flex;
		color: var(--text-dim);
		transition: transform 0.15s;
	}

	.chevron.open {
		transform: rotate(180deg);
	}

	.body {
		padding: 0 0.9rem 0.9rem;
	}

	.label {
		display: block;
		font-size: 0.85rem;
		color: var(--text-dim);
		margin-bottom: 0.35rem;
	}

	/* Height from padding; font-size stays >=16px or iOS zooms on focus. */
	input,
	select {
		width: 100%;
		max-width: 420px;
		padding: 0.4rem 0.6rem;
		margin-bottom: 0.75rem;
		background: var(--bg);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
	}

	input:focus,
	select:focus {
		border-color: var(--accent);
		outline: none;
	}

	select:disabled {
		opacity: 0.6;
	}

	.actions {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.actions input {
		margin-bottom: 0;
		width: auto;
		flex: 1;
		min-width: 12rem;
	}

	button {
		padding: 0.3rem 0.7rem;
		font-size: 0.85rem;
		background: var(--surface2);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		white-space: nowrap;
	}

	button.primary {
		background: var(--accent);
		border-color: var(--accent);
		color: #fff;
	}

	button:disabled {
		opacity: 0.6;
	}

	.add {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
		align-items: flex-end;
	}

	.field {
		flex: 1;
		min-width: 140px;
	}

	.field.narrow {
		flex: 0 0 auto;
	}

	.field input,
	.field select {
		margin-bottom: 0;
	}

	.dim,
	.hint {
		color: var(--text-dim);
	}

	.hint {
		font-size: 0.78rem;
		margin-bottom: 0.5rem;
	}

	.err {
		color: var(--red);
		font-size: 0.85rem;
		margin-top: 0.5rem;
	}
</style>
