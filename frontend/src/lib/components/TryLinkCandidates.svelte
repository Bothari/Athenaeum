<script lang="ts">
	import { hardcoverUrl } from '$lib/api/books';
	import type { HcEntityType, TryLinkCandidate, TryLinkLog } from '$lib/types/detail';

	interface Props {
		log: TryLinkLog;
		type: HcEntityType;
		/** Match scores are only meaningful with debug_view on. */
		showScores?: boolean;
		onpick: (candidate: TryLinkCandidate) => void;
		linking?: string | null;
	}

	let { log, type, showScores = false, onpick, linking = null }: Props = $props();

	const MESSAGES: Partial<Record<TryLinkLog['result'], { text: string; tone: string }>> = {
		no_match: { text: 'No confident match found.', tone: 'dim' },
		no_results: { text: 'No confident match found.', tone: 'dim' },
		error: { text: '', tone: 'error' },
		no_api_key: { text: 'No Hardcover API key configured.', tone: 'error' },
		conflict: {
			text: 'Conflict: this HC item is already linked to another entry.',
			tone: 'warn'
		}
	};

	const message = $derived(MESSAGES[log.result]);

	function label(c: TryLinkCandidate): string {
		return (type === 'book' ? c.title : c.name) ?? '';
	}

	function score(c: TryLinkCandidate): string {
		if (c.score != null) return String(c.score);
		if (c.t_score != null) return `t:${c.t_score} a:${c.a_score}`;
		return '';
	}
</script>

{#if message}
	<p class="message {message.tone}">
		{message.text || log.error || 'Error'}
	</p>
{/if}

{#if log.candidates?.length}
	<div class="candidates">
		{#each log.candidates as candidate (candidate.hc_id)}
			{@const url = hardcoverUrl(type, candidate.slug)}
			<div class="candidate" class:best={candidate.is_best}>
				<div class="info">
					<div class="label">
						{label(candidate)}
						{#if showScores && score(candidate)}
							<span class="score">{score(candidate)}</span>
						{/if}
					</div>
					{#if type === 'book' && candidate.author}
						<div class="sub">{candidate.author}</div>
					{/if}
				</div>
				<div class="actions">
					<button
						type="button"
						onclick={() => onpick(candidate)}
						disabled={linking === candidate.hc_id}
					>
						{linking === candidate.hc_id ? 'Linking…' : 'Link'}
					</button>
					{#if url}
						<a href={url} target="_blank" rel="noreferrer" title="Open on Hardcover">Open</a>
					{/if}
				</div>
			</div>
		{/each}
	</div>
{/if}

<style>
	/*
	 * v1 styled this with --color-success / --color-error / --color-warning /
	 * --color-text-dim / --color-surface-raised, none of which are defined
	 * anywhere in its stylesheet — so these colours silently fell back to
	 * inherited values and the states were visually indistinguishable. Using the
	 * real tokens here.
	 */
	.message {
		margin: 0.5rem 0 0;
		font-size: 0.875rem;
	}

	.message.dim {
		color: var(--text-dim);
	}

	.message.error {
		color: var(--red);
	}

	.message.warn {
		color: var(--yellow);
	}

	.candidates {
		margin-top: 0.5rem;
		border: 1px solid var(--border);
		border-radius: var(--radius);
		overflow: hidden;
	}

	.candidate {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.75rem;
		padding: 0.5rem 0.75rem;
		border-bottom: 1px solid var(--border);
	}

	.candidate:last-child {
		border-bottom: none;
	}

	.candidate.best {
		background: var(--surface2);
	}

	.info {
		min-width: 0;
	}

	.label {
		font-size: 0.9rem;
	}

	.score {
		font-size: 0.75rem;
		color: var(--text-dim);
		margin-left: 0.375rem;
	}

	.sub {
		font-size: 0.8rem;
		color: var(--text-dim);
		margin-top: 1px;
	}

	.actions {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		flex-shrink: 0;
	}

	button {
		padding: 0.15rem 0.6rem;
		font-size: 0.8rem;
		background: var(--accent);
		color: #fff;
		border: none;
		border-radius: var(--radius);
	}

	button:disabled {
		opacity: 0.6;
	}

	a {
		font-size: 0.8rem;
	}
</style>
