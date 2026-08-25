<script lang="ts">
	import { untrack } from 'svelte';
	import Badge from './Badge.svelte';
	import type { BadgeVariant } from './Badge.svelte';
	import Icon from './Icon.svelte';
	import { cancelRequest, createRequest } from '$lib/api/requests';
	import { createBook } from '$lib/api/search';
	import { auth } from '$lib/stores/auth.svelte';
	import { toasts } from '$lib/stores/toast.svelte';
	import type { FormatType } from '$lib/types/library';
	import type { FormatMode, SearchResult } from '$lib/types/search';

	/**
	 * The request/cancel toggle on a search card. Port of v1's buildFormatRows.
	 *
	 * Each format is a pill: grey means not requested (click to request), coloured
	 * means requested (click to cancel), green means already in the library
	 * (disabled).
	 */
	interface Props {
		result: SearchResult;
		/** Fired after a request is created, so the card can start linking to the book. */
		onlinked?: (bookId: string) => void;
	}

	let { result, onlinked }: Props = $props();

	const TYPES: FormatType[] = ['ebook', 'audiobook'];

	interface FormatState {
		mode: FormatMode;
		reqStatus: string | null;
		reqId: string | null;
		reqOwnerId: string | null;
		libNarrator: string;
	}

	function initial(type: FormatType): FormatState {
		const lib = result.library_formats?.find((f) => f.type === type);
		const active = result.existing_requests?.find((r) => r.type === type && r.status !== 'failed');
		// A failed request still counts as "there is a request", but it is
		// actionable: clicking retries rather than cancels.
		const failed = active
			? null
			: result.existing_requests?.find((r) => r.type === type && r.status === 'failed');
		const req = active ?? failed;

		return {
			mode: lib ? 'in-library' : active ? 'requested' : failed ? 'failed' : 'unmonitored',
			reqStatus: req?.status ?? null,
			reqId: req?.id ?? null,
			reqOwnerId: req?.requested_by_user_id ?? null,
			libNarrator: lib?.narrator ?? ''
		};
	}

	let formats = $state<Record<FormatType, FormatState>>({
		ebook: initial('ebook'),
		audiobook: initial('audiobook')
	});
	// Seeded once from the incoming result, then owned by the input. Untracked so
	// the one-shot read is explicit rather than looking like a missed dependency —
	// a card is rebuilt when results change, so there is nothing to re-sync from.
	let narrator = $state(
		untrack(() => result.existing_requests?.find((r) => r.type === 'audiobook')?.narrator ?? '')
	);
	let busy = $state<FormatType | null>(null);

	/** Users may only cancel their own requests. */
	function canCancel(s: FormatState): boolean {
		if (s.mode !== 'requested') return true;
		return auth.isAdmin || !s.reqOwnerId || s.reqOwnerId === auth.user?.user_id;
	}

	function variant(s: FormatState): BadgeVariant {
		if (s.mode === 'in-library') return 'in_library';
		if (s.mode === 'failed') return 'failed';
		if (s.mode === 'requested') return (s.reqStatus ?? 'requested') as BadgeVariant;
		return 'neutral';
	}

	function tooltip(type: FormatType, s: FormatState): string {
		const name = type === 'audiobook' ? 'Audiobook' : 'Ebook';
		switch (s.mode) {
			case 'in-library':
				return `${name} — in library`;
			case 'requested':
				return canCancel(s) ? `${name} — click to cancel` : `${name} — requested by another user`;
			case 'failed':
				return `${name} — failed, click to retry`;
			default:
				return `${name} — click to request`;
		}
	}

	function disabled(s: FormatState): boolean {
		return s.mode === 'in-library' || (s.mode === 'requested' && !canCancel(s));
	}

	async function toggle(type: FormatType) {
		const s = formats[type];
		if (disabled(s)) return;
		busy = type;

		try {
			if (s.mode === 'unmonitored' || s.mode === 'failed') {
				// Always create the book, even when book_id is known: this is what
				// backfills series associations for books added before series data.
				const book = await createBook({
					title: result.title,
					authors: (result.authors ?? []).map((a) => ({ name: a.name, hc_id: a.id ?? null })),
					cover_url: result.cover_url ?? null,
					series_list: (result.series ?? []).map((s2) => ({
						name: s2.name,
						position: s2.position ?? null,
						hardcover_id: s2.hardcover_series_id ?? null
					})),
					metadata_source: result.metadata_source ?? null,
					metadata_id: result.metadata_id ?? null,
					metadata_url: result.metadata_url ?? null,
					hardcover_slug: result.slug ?? null
				});

				const req = await createRequest({
					book_id: book.id,
					type,
					narrator: type === 'audiobook' ? narrator.trim() || null : null
				});
				if (req.skipped) toasts.info('Already requested');

				formats[type] = {
					...s,
					mode: 'requested',
					reqId: req.id ?? null,
					reqStatus: 'requested'
				};
				onlinked?.(book.id);
			} else if (s.mode === 'requested') {
				if (!s.reqId) {
					toasts.error('Cannot cancel — unknown request ID');
					return;
				}
				await cancelRequest(s.reqId);
				formats[type] = { ...s, mode: 'unmonitored', reqId: null, reqStatus: null };
				narrator = '';
			}
		} catch (err) {
			toasts.error(`Failed: ${err instanceof Error ? err.message : String(err)}`);
		} finally {
			busy = null;
		}
	}
</script>

<div class="row">
	<span class="label">Request</span>

	{#each TYPES as type, i (type)}
		{#if i > 0}<span class="sep">|</span>{/if}
		<button
			type="button"
			class="pill"
			title={tooltip(type, formats[type])}
			disabled={disabled(formats[type]) || busy === type}
			onclick={() => toggle(type)}
		>
			<Badge variant={variant(formats[type])}>
				<Icon name={type === 'audiobook' ? 'audiobook' : 'ebook'} size={12} />
			</Badge>
		</button>
	{/each}

	{#if formats.audiobook.mode === 'unmonitored'}
		<input type="text" bind:value={narrator} placeholder="Narrator" />
	{:else if formats.audiobook.mode === 'in-library' && formats.audiobook.libNarrator}
		<span class="narrator">{formats.audiobook.libNarrator}</span>
	{:else if formats.audiobook.mode === 'requested' && narrator}
		<span class="narrator">{narrator}</span>
	{/if}
</div>

<style>
	.row {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		flex-wrap: wrap;
		padding-top: 0.5rem;
	}

	.label {
		font-size: 0.78rem;
		color: var(--text-dim);
	}

	.sep {
		color: var(--border);
	}

	.pill {
		background: none;
		border: none;
		padding: 0;
		cursor: pointer;
	}

	.pill:disabled {
		cursor: default;
	}

	.narrator {
		font-size: 0.78rem;
		color: var(--text-dim);
		font-style: italic;
	}

	/* Height from padding; font-size stays >=16px or iOS zooms on focus. */
	input {
		flex: 1;
		min-width: 7rem;
		padding: 0.1rem 0.4rem;
		background: var(--bg);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
	}

	input:focus {
		border-color: var(--accent);
		outline: none;
	}
</style>
