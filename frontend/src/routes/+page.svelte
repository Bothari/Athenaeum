<script lang="ts">
	// Phase 1 scaffold smoke test. Proves the toolchain end to end: Svelte 5 runes
	// compile, the token stylesheet applies, and /api proxies through to FastAPI
	// with session cookies intact. Replaced in phase 2 by the real app shell.
	type Probe = { status: 'loading' } | { status: 'ok'; body: string } | { status: 'error'; message: string };

	let probe = $state<Probe>({ status: 'loading' });

	async function checkApi() {
		probe = { status: 'loading' };
		try {
			const res = await fetch('/api/auth/me');
			const text = await res.text();
			probe = { status: 'ok', body: `${res.status} ${text.slice(0, 200)}` };
		} catch (err) {
			probe = { status: 'error', message: err instanceof Error ? err.message : String(err) };
		}
	}

	$effect(() => {
		checkApi();
	});
</script>

<main>
	<h1>Athenaeum v2</h1>
	<p class="dim">Phase 1 scaffold. No UI ported yet.</p>

	<section>
		<h2>API proxy</h2>
		{#if probe.status === 'loading'}
			<p class="dim">Checking /api/auth/me...</p>
		{:else if probe.status === 'ok'}
			<p class="ok">Reached FastAPI: <code>{probe.body}</code></p>
		{:else}
			<p class="err">Failed: {probe.message}</p>
		{/if}
		<button onclick={checkApi}>Re-check</button>
	</section>

	<section>
		<h2>Zoom guard</h2>
		<p class="dim">Focus this on a phone. The page must not zoom.</p>
		<input type="text" placeholder="Type here" />
	</section>
</main>

<style>
	main {
		max-width: 40rem;
		margin: 0 auto;
		padding: 2rem 1rem;
	}

	h1 {
		color: var(--accent);
		font-size: 1.5rem;
	}

	h2 {
		font-size: 1rem;
		margin-bottom: 0.5rem;
	}

	section {
		margin-top: 2rem;
		padding: 1rem;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
	}

	.dim {
		color: var(--text-dim);
		font-size: 0.85rem;
	}

	.ok {
		color: var(--green);
	}

	.err {
		color: var(--red);
	}

	code {
		word-break: break-all;
	}

	button {
		margin-top: 0.75rem;
		padding: 0.4rem 0.8rem;
		background: var(--surface2);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
	}

	/* Padding, not font-size, controls the field's size. See CLAUDE.md. */
	input {
		width: 100%;
		padding: 0.4rem 0.6rem;
		background: var(--bg);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius);
	}
</style>
