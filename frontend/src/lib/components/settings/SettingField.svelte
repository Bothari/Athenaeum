<script lang="ts">
	import { MASKED, type FieldSpec } from '$lib/types/settings';

	/**
	 * One field in a schema-driven settings tab. v1 had the same idea in miniature
	 * — a field() helper emitting data-key attributes that the save handler read
	 * back out of the DOM — so this formalises an existing pattern rather than
	 * inventing one, and keeps values in state instead of the document.
	 */
	interface Props {
		spec: FieldSpec;
		value: unknown;
		onchange: (value: unknown) => void;
	}

	let { spec, value, onchange }: Props = $props();

	const type = $derived(spec.type ?? 'text');

	/** Comma-separated lists are stored as arrays but edited as text. */
	const text = $derived.by(() => {
		if (type === 'csv') return Array.isArray(value) ? value.join(', ') : ((value as string) ?? '');
		return value == null ? '' : String(value);
	});

	const isMasked = $derived(text === MASKED);

	function commit(raw: string) {
		if (type === 'csv') {
			onchange(
				raw
					.split(',')
					.map((s) => s.trim().toLowerCase())
					.filter(Boolean)
			);
		} else if (type === 'number') {
			onchange(raw === '' ? '' : Number(raw));
		} else {
			onchange(raw);
		}
	}
</script>

{#if type === 'boolean'}
	<div class="group">
		<label class="check">
			<input
				type="checkbox"
				checked={value === true}
				onchange={(e) => onchange(e.currentTarget.checked)}
			/>
			<span>{spec.label}</span>
		</label>
		{#if spec.hint}<div class="hint">{spec.hint}</div>{/if}
	</div>
{:else}
	<div class="group">
		<label class="label" for="set-{spec.key}">{spec.label}</label>

		{#if type === 'textarea'}
			<textarea
				id="set-{spec.key}"
				rows={spec.rows ?? 5}
				placeholder={spec.placeholder}
				value={text}
				oninput={(e) => commit(e.currentTarget.value)}
			></textarea>
		{:else}
			<input
				id="set-{spec.key}"
				type={type === 'password' ? 'password' : type === 'number' ? 'number' : 'text'}
				placeholder={spec.placeholder}
				min={spec.min}
				max={spec.max}
				style={spec.width ? `width:${spec.width}` : undefined}
				value={text}
				oninput={(e) => commit(e.currentTarget.value)}
			/>
		{/if}

		{#if isMasked}
			<div class="hint">Stored value hidden. Leave as-is to keep it, or type a new one.</div>
		{:else if spec.hint}
			<div class="hint">{spec.hint}</div>
		{/if}
	</div>
{/if}

<style>
	.group {
		margin-bottom: 1rem;
	}

	.label {
		display: block;
		font-size: 0.85rem;
		color: var(--text-dim);
		margin-bottom: 0.35rem;
	}

	.check {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		cursor: pointer;
	}

	/* Height from padding; font-size stays >=16px or iOS zooms on focus. */
	input[type='text'],
	input[type='password'],
	input[type='number'],
	textarea {
		width: 100%;
		max-width: 650px;
		padding: 0.4rem 0.6rem;
		background: var(--bg);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
	}

	textarea {
		font-family: ui-monospace, monospace;
		resize: vertical;
	}

	input:focus,
	textarea:focus {
		border-color: var(--accent);
		outline: none;
	}

	.hint {
		font-size: 0.78rem;
		color: var(--text-dim);
		margin-top: 0.25rem;
	}
</style>
