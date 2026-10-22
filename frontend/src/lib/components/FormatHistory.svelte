<script lang="ts">
	import { getRequestHistory } from '$lib/api/requests';
	import type { FormatType } from '$lib/types/library';
	import type { HistoryEvent } from '$lib/types/requests';

	interface Props {
		bookId: string;
		type: FormatType;
	}

	let { bookId, type }: Props = $props();

	let events = $state<HistoryEvent[]>([]);

	$effect(() => {
		let cancelled = false;
		getRequestHistory(bookId)
			.then((all) => {
				if (cancelled) return;
				// A request's type comes from the live join when available, else from
				// the `created` event's detail. Ported from v1.
				const typeById = new Map<string, string>();
				for (const ev of all) {
					if (ev.request_type) typeById.set(ev.request_id, ev.request_type);
					else if (ev.event_type === 'created' && ev.detail?.type)
						typeById.set(ev.request_id, ev.detail.type);
				}
				events = all.filter((ev) => typeById.get(ev.request_id) === type);
			})
			.catch(() => {
				events = [];
			});
		return () => {
			cancelled = true;
		};
	});

	function label(ev: HistoryEvent): string {
		const d = ev.detail ?? {};
		switch (ev.event_type) {
			case 'created':
				return `Request created — ${d.status ?? ''}`;
			case 'state_change':
				return `Status: ${d.from ?? '?'} → ${d.to ?? '?'}${d.reason ? ` — ${d.reason}` : ''}`;
			case 'searched':
				return `Searched Prowlarr — ${d.results ?? '?'} result${d.results === 1 ? '' : 's'}`;
			case 'grabbed':
				return `Grabbed via ${d.indexer ?? '?'}${d.size ? ` ${(d.size / 1024 / 1024).toFixed(0)} MB` : ''}`;
			case 'cancelled':
				return 'Request cancelled';
			default:
				return ev.event_type;
		}
	}
</script>

{#if events.length > 0}
	<div class="history">
		<div class="heading">History</div>
		{#each events as ev, i (i)}
			<div class="row">
				<span class="label">
					{label(ev)}
					{#if ev.event_type === 'grabbed' && ev.detail?.title}
						{#if ev.detail.info_url}
							<a href={ev.detail.info_url} target="_blank" rel="noreferrer">{ev.detail.title}</a>
						{:else}
							<span>{ev.detail.title}</span>
						{/if}
					{/if}
				</span>
				<span class="ts">{ev.created_at ? new Date(ev.created_at).toLocaleString() : ''}</span>
			</div>
		{/each}
	</div>
{/if}

<style>
	.history {
		margin-top: 0.75rem;
	}

	.heading {
		font-size: 0.78rem;
		color: var(--text-dim);
		margin-bottom: 0.25rem;
	}

	.row {
		display: flex;
		justify-content: space-between;
		gap: 0.75rem;
		font-size: 0.78rem;
		padding: 0.15rem 0;
	}

	.label {
		min-width: 0;
	}

	.ts {
		color: var(--text-dim);
		white-space: nowrap;
	}
</style>
