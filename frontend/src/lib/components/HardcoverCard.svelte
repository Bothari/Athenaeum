<script lang="ts">
	import { untrack } from 'svelte';
	import TryLinkCandidates from './TryLinkCandidates.svelte';
	import { hardcoverUrl, refreshHardcover } from '$lib/api/books';
	import { getSettings } from '$lib/api/status';
	import { resolveHcUrl, setLink, tryLink, unlink } from '$lib/api/sync';
	import { toasts } from '$lib/stores/toast.svelte';
	import type { HcEntityType, TryLinkCandidate, TryLinkLog } from '$lib/types/detail';

	/**
	 * Hardcover link management, shared by book, author and series detail. Port of
	 * v1's setupHcCard, which re-rendered its own innerHTML and rebound handlers on
	 * every state change.
	 */
	interface Props {
		type: HcEntityType;
		entityId: string;
		hcId?: string | null;
		hcSlug?: string | null;
		/** Called after the link changes so the page can refresh derived data. */
		onchange?: (hcId: string | null, slug: string | null) => void;
	}

	let { type, entityId, hcId = null, hcSlug = null, onchange }: Props = $props();

	/**
	 * Seeded from props, then owned locally: this component is the only thing that
	 * changes the link, so it is uncontrolled after mount. untrack makes the
	 * one-shot read explicit rather than looking like a missed dependency.
	 *
	 * The consequence: a parent cannot push a new link in from outside. Parents
	 * that refetch on `onchange` get identical values back, so this does not
	 * currently matter — but a future caller wanting external control needs a key,
	 * not a prop change.
	 */
	let currentId = $state(untrack(() => hcId));
	let currentSlug = $state(untrack(() => hcSlug));
	let busy = $state(false);
	let searching = $state(false);
	let linking = $state<string | null>(null);
	let log = $state<TryLinkLog | null>(null);
	let showScores = $state(false);
	let idInput = $state('');
	let resolvedSlug = $state('');

	const url = $derived(hardcoverUrl(type, currentSlug));

	function applyLink(id: string | null, slug: string | null) {
		currentId = id;
		currentSlug = slug;
		log = null;
		onchange?.(id, slug);
	}

	async function doUnlink() {
		busy = true;
		try {
			await unlink(type, entityId);
			applyLink(null, null);
			toasts.success('Unlinked');
		} catch (err) {
			toasts.error(`Unlink failed: ${err instanceof Error ? err.message : String(err)}`);
		} finally {
			busy = false;
		}
	}

	async function doRefresh() {
		busy = true;
		try {
			const result = await refreshHardcover(entityId);
			applyLink(result.canonical_id ?? currentId, result.slug ?? currentSlug);
			toasts.success('HC data refreshed');
		} catch (err) {
			toasts.error(`Refresh failed: ${err instanceof Error ? err.message : String(err)}`);
		} finally {
			busy = false;
		}
	}

	async function find() {
		searching = true;
		try {
			const [result, settings] = await Promise.all([
				tryLink(type, entityId),
				getSettings().catch(() => ({}) as { general?: { debug_view?: boolean } })
			]);
			showScores = settings.general?.debug_view === true;
			log = result;
		} catch (err) {
			log = { result: 'error', error: err instanceof Error ? err.message : String(err) };
		} finally {
			searching = false;
		}
	}

	async function pick(candidate: TryLinkCandidate) {
		linking = candidate.hc_id;
		try {
			await setLink(type, entityId, candidate.hc_id, candidate.slug ?? '');
			applyLink(candidate.hc_id, candidate.slug ?? '');
			toasts.success('Linked');
		} catch (err) {
			toasts.error(`Failed: ${err instanceof Error ? err.message : String(err)}`);
		} finally {
			linking = null;
		}
	}

	/** Pasting a hardcover.app URL resolves it to an id in place, as in v1. */
	async function onInput() {
		if (!idInput.includes('hardcover.app/')) return;
		try {
			const resolved = await resolveHcUrl(idInput, type);
			if (resolved.hardcover_id) {
				idInput = resolved.hardcover_id;
				resolvedSlug = resolved.hardcover_slug ?? '';
				toasts.success(`URL resolved to HC ID ${resolved.hardcover_id}`);
			} else if (resolved.error) {
				toasts.error(resolved.error);
			}
		} catch {
			// Typing a partial URL will fail here; not worth surfacing.
		}
	}

	async function setManually() {
		let value = idInput.trim();
		if (!value) return;
		busy = true;
		let slug = resolvedSlug;
		try {
			if (value.includes('hardcover.app/')) {
				const resolved = await resolveHcUrl(value, type);
				if (!resolved.hardcover_id) {
					toasts.error(resolved.error || 'Could not resolve URL');
					return;
				}
				value = resolved.hardcover_id;
				slug = resolved.hardcover_slug ?? '';
			}
			await setLink(type, entityId, value, slug);
			applyLink(value, slug);
			toasts.success('Link updated');
		} catch (err) {
			toasts.error(`Failed: ${err instanceof Error ? err.message : String(err)}`);
		} finally {
			busy = false;
		}
	}
</script>

<h2 class="section">Hardcover</h2>
<div class="card">
	{#if currentId}
		<div class="linked">
			<span>Linked to Hardcover {type} #{currentId}</span>
			{#if url}
				<a href={url} target="_blank" rel="noreferrer">Open</a>
			{/if}
			<button type="button" onclick={doUnlink} disabled={busy}>Unlink</button>
			{#if type === 'book'}
				<button type="button" onclick={doRefresh} disabled={busy}>
					{busy ? 'Refreshing…' : 'Refresh HC data'}
				</button>
			{/if}
		</div>
	{:else}
		<button type="button" class="find" onclick={find} disabled={searching}>
			{searching ? 'Searching…' : 'Find Hardcover match'}
		</button>

		{#if log}
			<TryLinkCandidates {log} {type} {showScores} {linking} onpick={pick} />
		{/if}

		<div class="manual">
			<input
				type="text"
				bind:value={idInput}
				oninput={onInput}
				placeholder="Paste HC URL or ID"
			/>
			<button type="button" onclick={setManually} disabled={busy}>Set</button>
		</div>
	{/if}
</div>

<style>
	.section {
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
		padding: 0.75rem 1rem;
	}

	.linked {
		display: flex;
		align-items: center;
		gap: 0.625rem;
		flex-wrap: wrap;
		font-size: 0.875rem;
	}

	.manual {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		margin-top: 0.75rem;
	}

	/* Padding sets the height; font-size stays >=16px or iOS zooms on focus. */
	input {
		flex: 1;
		min-width: 0;
		padding: 0.35rem 0.6rem;
		background: var(--bg);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
	}

	input:focus {
		border-color: var(--accent);
		outline: none;
	}

	button {
		padding: 0.2rem 0.6rem;
		font-size: 0.8rem;
		background: var(--surface2);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		white-space: nowrap;
	}

	button:hover:not(:disabled) {
		border-color: var(--accent);
	}

	button:disabled {
		opacity: 0.6;
	}

	.find {
		font-size: 0.85rem;
		padding: 0.3rem 0.7rem;
	}
</style>
