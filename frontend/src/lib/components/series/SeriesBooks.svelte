<script lang="ts">
	import Badge from '../Badge.svelte';
	import type { BadgeVariant } from '../Badge.svelte';
	import BookCard from '../BookCard.svelte';
	import Icon from '../Icon.svelte';
	import type { SeriesBook } from '$lib/types/series';

	interface Props {
		books: SeriesBook[];
		view: 'list' | 'poster';
	}

	let { books, view }: Props = $props();

	/** Requests are only shown for formats not already held, as elsewhere. */
	function pendingRequests(b: SeriesBook) {
		return (b.requests ?? []).filter((r) => !(b.formats ?? []).some((f) => f.type === r.type));
	}
</script>

{#if books.length === 0}
	<p class="bare">The shelves are bare.</p>
{:else if view === 'list'}
	<div class="table-wrap">
		<table>
			<thead>
				<tr>
					<th class="num">#</th>
					<th>Title</th>
					<th class="fmt">Formats</th>
				</tr>
			</thead>
			<tbody>
				{#each books as b (b.id)}
					<tr>
						<td class="dim">{b.series_position ?? '—'}</td>
						<td><a href="/library/book/{b.id}">{b.title}</a></td>
						<td>
							{#if (b.formats?.length ?? 0) + pendingRequests(b).length === 0}
								<span class="dim">—</span>
							{:else}
								<div class="badges">
									{#each b.formats ?? [] as f (f.id)}
										<Badge
											variant="in_library"
											title={f.narrator ? `${f.type} — ${f.narrator}` : f.type}
										>
											<Icon name={f.type === 'audiobook' ? 'audiobook' : 'ebook'} size={12} />
										</Badge>
									{/each}
									{#each pendingRequests(b) as r (r.id)}
										<Badge variant={r.status as BadgeVariant} title="{r.type} — {r.status}">
											<Icon name={r.type === 'audiobook' ? 'audiobook' : 'ebook'} size={12} />
										</Badge>
									{/each}
								</div>
							{/if}
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
{:else}
	<div class="grid">
		{#each books as b (b.id)}
			<div class="cell">
				<BookCard book={b} />
				{#if b.series_position != null}
					<span class="pos">#{b.series_position}</span>
				{/if}
			</div>
		{/each}
	</div>
{/if}

<style>
	.bare {
		color: var(--text-dim);
		padding: 0.5rem 0;
	}

	.table-wrap {
		overflow-x: auto;
	}

	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.875rem;
	}

	th {
		text-align: left;
		font-weight: 600;
		color: var(--text-dim);
		padding: 0.5rem;
		border-bottom: 1px solid var(--border);
		white-space: nowrap;
	}

	th.num {
		width: 3rem;
	}

	th.fmt {
		width: 100px;
	}

	td {
		padding: 0.5rem;
		border-bottom: 1px solid var(--border);
		vertical-align: top;
	}

	.dim {
		color: var(--text-dim);
	}

	/* Flex on a wrapper, never on the td — see DataTable's cell styles. */
	.badges {
		display: flex;
		gap: 0.25rem;
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
		gap: 1rem;
	}

	/*
	 * v1 achieved this by reaching into the rendered card, replacing the cover
	 * element with a wrapper and appending a badge. Positioning it from outside
	 * keeps BookCard unaware of series context.
	 */
	.cell {
		position: relative;
	}

	.pos {
		position: absolute;
		top: 0.3rem;
		left: 0.3rem;
		background: rgb(0 0 0 / 0.65);
		color: #fff;
		font-size: 0.7rem;
		font-weight: 600;
		padding: 0.15rem 0.4rem;
		border-radius: 3px;
		pointer-events: none;
		line-height: 1.3;
	}
</style>
