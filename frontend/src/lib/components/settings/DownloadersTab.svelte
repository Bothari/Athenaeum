<script lang="ts">
	import { untrack } from 'svelte';
	import SettingField from './SettingField.svelte';
	import { DL_FIELDS, DL_TYPE_LABELS } from './schemas';
	import { saveSection, testService } from '$lib/api/settings';
	import { toasts } from '$lib/stores/toast.svelte';
	import type { DownloaderConfig } from '$lib/types/settings';

	/**
	 * Downloader list editor. Each entry is saved as part of the whole
	 * `downloaders` array, since that is what the backend stores.
	 */
	interface Props {
		initial: DownloaderConfig[];
	}

	let { initial }: Props = $props();

	/*
	 * Seeded once, then owned locally — see SettingsForm for why this is untracked.
	 *
	 * $state.snapshot, not structuredClone: `initial` comes from a $state object,
	 * so it is a reactive Proxy, and structuredClone throws DataCloneError on a
	 * proxy. That failure happens during setup, so it takes the whole tab down
	 * rather than degrading.
	 */
	let items = $state<DownloaderConfig[]>(untrack(() => $state.snapshot(initial ?? []) as DownloaderConfig[]));
	let openIndex = $state<number | null>(null);
	let saving = $state(false);
	let testingIndex = $state<number | null>(null);
	let testResult = $state<Record<number, { ok: boolean; message: string }>>({});

	function add(type: string) {
		items = [...items, { type, enabled: true }];
		openIndex = items.length - 1;
	}

	function remove(index: number) {
		items = items.filter((_, i) => i !== index);
		if (openIndex === index) openIndex = null;
	}

	function update(index: number, key: string, value: unknown) {
		items = items.map((item, i) => (i === index ? { ...item, [key]: value } : item));
	}

	async function save() {
		saving = true;
		try {
			await saveSection('downloaders', items);
			toasts.success('Downloaders saved');
		} catch (err) {
			toasts.error(err instanceof Error ? err.message : String(err));
		} finally {
			saving = false;
		}
	}

	async function test(index: number) {
		testingIndex = index;
		try {
			const result = await testService('downloader', items[index] as Record<string, unknown>);
			testResult[index] =
				result.ok === false
					? { ok: false, message: result.error || 'Connection failed' }
					: { ok: true, message: result.message || 'Connection OK' };
		} catch (err) {
			testResult[index] = { ok: false, message: err instanceof Error ? err.message : String(err) };
		} finally {
			testingIndex = null;
		}
	}
</script>

{#each items as item, i (i)}
	<div class="card">
		<div class="header">
			<button
				type="button"
				class="title"
				onclick={() => (openIndex = openIndex === i ? null : i)}
				aria-expanded={openIndex === i}
			>
				{DL_TYPE_LABELS[item.type] ?? item.type}
			</button>
			<label class="enabled">
				<input
					type="checkbox"
					checked={item.enabled !== false}
					onchange={(e) => update(i, 'enabled', e.currentTarget.checked)}
				/>
				Enabled
			</label>
		</div>

		{#if openIndex === i}
			<div class="body">
				{#each DL_FIELDS[item.type] ?? [] as spec (spec.key)}
					<SettingField {spec} value={item[spec.key]} onchange={(v) => update(i, spec.key, v)} />
				{/each}

				<div class="actions">
					<button type="button" onclick={() => test(i)} disabled={testingIndex === i}>
						{testingIndex === i ? 'Testing…' : 'Test Connection'}
					</button>
					<button type="button" class="danger" onclick={() => remove(i)}>Remove</button>
					{#if testResult[i]}
						<span class="feedback" class:ok={testResult[i].ok} class:err={!testResult[i].ok}>
							{testResult[i].ok ? '✓' : '✗'}
							{testResult[i].message}
						</span>
					{/if}
				</div>
			</div>
		{/if}
	</div>
{/each}

<div class="add">
	{#each Object.entries(DL_TYPE_LABELS) as [type, label] (type)}
		<button type="button" onclick={() => add(type)}>+ {label}</button>
	{/each}
</div>

<div class="actions save-row">
	<button type="button" class="primary" onclick={save} disabled={saving}>
		{saving ? 'Saving…' : 'Save'}
	</button>
	<span class="hint">Saves all downloaders together.</span>
</div>

<style>
	.card {
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		margin-bottom: 0.5rem;
	}

	.header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.6rem 0.9rem;
	}

	.title {
		flex: 1;
		text-align: left;
		background: none;
		border: none;
		color: inherit;
		font-weight: 600;
		font-size: 1rem;
		padding: 0;
	}

	.enabled {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		white-space: nowrap;
		cursor: pointer;
		font-size: 0.85rem;
		color: var(--text-dim);
	}

	.body {
		padding: 0 0.9rem 0.9rem;
	}

	.actions {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		flex-wrap: wrap;
	}

	.save-row {
		margin-top: 1rem;
	}

	.add {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
		margin-top: 0.75rem;
	}

	button {
		padding: 0.35rem 0.8rem;
		font-size: 0.85rem;
		background: var(--surface2);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
	}

	button.primary {
		background: var(--accent);
		border-color: var(--accent);
		color: #fff;
	}

	button.danger {
		color: var(--red);
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

	.hint {
		font-size: 0.78rem;
		color: var(--text-dim);
	}
</style>
