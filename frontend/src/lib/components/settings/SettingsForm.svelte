<script lang="ts">
	import { untrack } from 'svelte';
	import type { Snippet } from 'svelte';
	import SettingField from './SettingField.svelte';
	import { saveSection, testService } from '$lib/api/settings';
	import type { FieldSpec, SettingsSection, TestableService } from '$lib/types/settings';

	/**
	 * A schema-driven settings tab: fields, an optional Test Connection, and a
	 * Save that PUTs only this section.
	 */
	interface Props {
		section: SettingsSection;
		fields: FieldSpec[];
		/** Section values from GET /settings; edited locally until saved. */
		initial: Record<string, unknown>;
		test?: TestableService;
		/** Extra controls between the fields and the actions. */
		children?: Snippet<[Record<string, unknown>]>;
		/** Last chance to adjust the payload — used for ABS library selection. */
		transform?: (values: Record<string, unknown>) => Record<string, unknown>;
		ontested?: (result: unknown) => void;
	}

	let { section, fields, initial, test, children, transform, ontested }: Props = $props();

	/*
	 * Seeded once, then owned by this form. Untracked deliberately: if a prop
	 * change reset these, a settings reload landing mid-edit would silently throw
	 * away what you had typed. Switching tabs remounts the form, which is how
	 * fresh values get in.
	 */
	let values = $state<Record<string, unknown>>(untrack(() => ({ ...initial })));
	let saving = $state(false);
	let testing = $state(false);
	let feedback = $state<{ ok: boolean; message: string } | null>(null);

	const visible = $derived(fields.filter((f) => !f.visibleWhen || f.visibleWhen(values)));


	async function save() {
		saving = true;
		feedback = null;
		try {
			await saveSection(section, transform ? transform(values) : values);
			feedback = { ok: true, message: 'Saved' };
		} catch (err) {
			feedback = { ok: false, message: err instanceof Error ? err.message : String(err) };
		} finally {
			saving = false;
		}
	}

	async function runTest() {
		if (!test) return;
		testing = true;
		feedback = null;
		try {
			const result = await testService(test, values);
			ontested?.(result);
			feedback = result.ok === false
				? { ok: false, message: result.error || 'Connection failed' }
				: { ok: true, message: result.message || 'Connection OK' };
		} catch (err) {
			feedback = { ok: false, message: err instanceof Error ? err.message : String(err) };
		} finally {
			testing = false;
		}
	}
</script>

{#each visible as spec (spec.key)}
	<SettingField {spec} value={values[spec.key]} onchange={(v) => (values[spec.key] = v)} />
{/each}

{#if children}{@render children(values)}{/if}

<div class="actions">
	{#if test}
		<button type="button" class="secondary" onclick={runTest} disabled={testing}>
			{testing ? 'Testing…' : 'Test Connection'}
		</button>
	{/if}
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
	.actions {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		flex-wrap: wrap;
		margin-top: 1rem;
	}

	button {
		padding: 0.4rem 0.9rem;
		font-size: 0.9rem;
		border-radius: var(--radius);
		border: 1px solid var(--border);
		background: var(--surface2);
		color: var(--text);
	}

	button.primary {
		background: var(--accent);
		border-color: var(--accent);
		color: #fff;
	}

	button:disabled {
		opacity: 0.6;
	}

	.feedback {
		font-size: 0.85rem;
	}

	.feedback.ok {
		color: var(--green);
	}

	.feedback.err {
		color: var(--red);
	}
</style>
