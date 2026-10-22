<script lang="ts">
	import { untrack } from 'svelte';
	import SettingField from './SettingField.svelte';
	import UsersManager from './UsersManager.svelte';
	import { saveSection } from '$lib/api/settings';
	import { verifyOidcProvider, type OidcVerifyResult } from '$lib/api/users';
	import type { AppSettings } from '$lib/types/settings';

	interface Props {
		settings: AppSettings;
	}

	let { settings }: Props = $props();

	// Seeded once, then owned locally — see SettingsForm.
	let values = $state<Record<string, unknown>>(untrack(() => ({ ...(settings.auth ?? {}) })));
	let saving = $state(false);
	let feedback = $state<{ ok: boolean; message: string } | null>(null);

	let verifying = $state(false);
	let verified = $state<OidcVerifyResult | null>(null);
	let verifyError = $state('');

	const oidcEnabled = $derived(values.oidc_enabled === true);

	/**
	 * The provider must be told where to send users back to. Built from
	 * general.public_url, which is why that field is required for OIDC.
	 */
	const redirectUri = $derived.by(() => {
		const publicUrl = (settings.general?.public_url as string | undefined)?.replace(/\/$/, '');
		return publicUrl
			? `${publicUrl}/api/auth/oidc/callback`
			: '(set General → Public URL first)';
	});

	async function verify() {
		const url = String(values.oidc_provider_url ?? '').trim();
		if (!url) return;
		verifying = true;
		verified = null;
		verifyError = '';
		try {
			const result = await verifyOidcProvider(url);
			if (result.ok === false) verifyError = 'Could not reach provider.';
			else verified = result;
		} catch (err) {
			verifyError = err instanceof Error ? err.message : String(err);
		} finally {
			verifying = false;
		}
	}

	async function save() {
		saving = true;
		feedback = null;
		try {
			await saveSection('auth', values);
			feedback = { ok: true, message: 'Saved' };
		} catch (err) {
			feedback = { ok: false, message: err instanceof Error ? err.message : String(err) };
		} finally {
			saving = false;
		}
	}
</script>

<UsersManager />

<h2 class="heading">Login methods</h2>

<SettingField
	spec={{
		key: 'form_enabled',
		label: 'Enable form login (username + password)',
		type: 'boolean'
	}}
	value={values.form_enabled}
	onchange={(v) => (values.form_enabled = v)}
/>

<SettingField
	spec={{
		key: 'oidc_enabled',
		label: 'Enable OIDC / SSO login',
		type: 'boolean',
		hint: 'When enabled, the login page redirects to your OIDC provider. Add ?force_local=1 to the login URL to bypass and use form login.'
	}}
	value={values.oidc_enabled}
	onchange={(v) => (values.oidc_enabled = v)}
/>

{#if values.form_enabled !== true && values.oidc_enabled !== true}
	<!-- Not a v1 behaviour, but disabling both is how you lock everyone out. -->
	<p class="warn">
		Both login methods are disabled. Saving this will leave no way to sign in.
	</p>
{/if}

{#if oidcEnabled}
	<h2 class="heading">OIDC settings</h2>

	<div class="provider">
		<div class="grow">
			<SettingField
				spec={{
					key: 'oidc_provider_url',
					label: 'Provider URL',
					placeholder: 'e.g. https://sso.example.com/application/o/athenaeum',
					hint: 'Issuer URL — Athenaeum auto-discovers all endpoints from here'
				}}
				value={values.oidc_provider_url}
				onchange={(v) => (values.oidc_provider_url = v)}
			/>
		</div>
		<button type="button" onclick={verify} disabled={verifying}>
			{verifying ? 'Verifying…' : 'Verify'}
		</button>
	</div>

	{#if verifyError}
		<p class="err">{verifyError}</p>
	{:else if verified}
		<div class="discovered">
			<div class="ok">Provider reachable</div>
			<dl>
				<dt>Issuer</dt>
				<dd>{verified.issuer || '—'}</dd>
				<dt>Authorization</dt>
				<dd>{verified.authorization_endpoint || '—'}</dd>
				<dt>Token</dt>
				<dd>{verified.token_endpoint || '—'}</dd>
				<dt>Userinfo</dt>
				<dd>{verified.userinfo_endpoint || '—'}</dd>
			</dl>
		</div>
	{/if}

	<SettingField
		spec={{ key: 'oidc_client_id', label: 'Client ID' }}
		value={values.oidc_client_id}
		onchange={(v) => (values.oidc_client_id = v)}
	/>
	<SettingField
		spec={{ key: 'oidc_client_secret', label: 'Client Secret', type: 'password' }}
		value={values.oidc_client_secret}
		onchange={(v) => (values.oidc_client_secret = v)}
	/>
	<SettingField
		spec={{ key: 'oidc_scopes', label: 'Scopes' }}
		value={values.oidc_scopes ?? 'openid email profile'}
		onchange={(v) => (values.oidc_scopes = v)}
	/>
	<SettingField
		spec={{ key: 'session_days', label: 'Session duration (days)', type: 'number', width: '120px' }}
		value={values.session_days ?? 30}
		onchange={(v) => (values.session_days = v)}
	/>

	<div class="redirect">
		<div class="label">Redirect URI <span class="dim">(register this with your provider)</span></div>
		<input type="text" readonly value={redirectUri} onclick={(e) => e.currentTarget.select()} />
	</div>
{/if}

<div class="actions">
	<button type="button" class="primary" onclick={save} disabled={saving}>
		{saving ? 'Saving…' : 'Save'}
	</button>
	{#if feedback}
		<span class="feedback" class:ok={feedback.ok} class:err={!feedback.ok}>
			{feedback.ok ? '✓' : '✗'}
			{feedback.message}
		</span>
	{/if}
</div>

<style>
	.heading {
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--text-dim);
		margin: 1.5rem 0 0.5rem;
	}

	.provider {
		display: flex;
		gap: 0.5rem;
		align-items: flex-start;
	}

	.grow {
		flex: 1;
		min-width: 0;
	}

	.discovered {
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		padding: 0.6rem 0.9rem;
		margin-bottom: 1rem;
		font-size: 0.82rem;
	}

	.discovered .ok {
		color: var(--green);
		margin-bottom: 0.35rem;
	}

	dl {
		display: grid;
		grid-template-columns: auto 1fr;
		gap: 0.15rem 0.75rem;
		margin: 0;
	}

	dt {
		color: var(--text-dim);
	}

	dd {
		margin: 0;
		overflow-wrap: anywhere;
	}

	.redirect {
		margin-bottom: 1rem;
	}

	.label {
		font-size: 0.85rem;
		color: var(--text-dim);
		margin-bottom: 0.35rem;
	}

	/* Height from padding; font-size stays >=16px or iOS zooms on focus. */
	input {
		width: 100%;
		max-width: 650px;
		padding: 0.4rem 0.6rem;
		background: var(--bg);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		font-family: ui-monospace, monospace;
		cursor: pointer;
	}

	.actions {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-top: 1rem;
	}

	button {
		padding: 0.4rem 0.9rem;
		font-size: 0.9rem;
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

	.warn {
		color: var(--yellow);
		font-size: 0.85rem;
		margin-bottom: 1rem;
	}

	.err {
		color: var(--red);
		font-size: 0.85rem;
		margin-bottom: 1rem;
	}

	.feedback.ok {
		color: var(--green);
		font-size: 0.85rem;
	}

	.feedback.err {
		color: var(--red);
		font-size: 0.85rem;
	}

	.dim {
		color: var(--text-dim);
	}
</style>
