<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import ErrorState from '$lib/components/ErrorState.svelte';
	import LoadingState from '$lib/components/LoadingState.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import DownloadersTab from '$lib/components/settings/DownloadersTab.svelte';
	import RankingEditor from '$lib/components/settings/RankingEditor.svelte';
	import SettingsForm from '$lib/components/settings/SettingsForm.svelte';
	import TasksTab from '$lib/components/settings/TasksTab.svelte';
	import {
		ABS_FIELDS,
		AUTO_SEARCH_FIELDS,
		DEFAULT_RANKING,
		GENERAL_FIELDS,
		HARDCOVER_FIELDS,
		NOTIFICATION_FIELDS,
		PROWLARR_FIELDS
	} from '$lib/components/settings/schemas';
	import { getSettings } from '$lib/api/settings';
	import { setSearchParam } from '$lib/url';
	import { auth } from '$lib/stores/auth.svelte';
	import type { AppSettings, RankingCriterion } from '$lib/types/settings';

	/** Auth is deliberately absent — it lands in phase 8b with user management. */
	const TABS = [
		'General',
		'ABS',
		'Prowlarr',
		'Downloads',
		'Hardcover',
		'Notifications',
		'Tasks'
	] as const;
	type Tab = (typeof TABS)[number];

	const tab = $derived.by<Tab>(() => {
		const value = page.url.searchParams.get('tab');
		return TABS.includes(value as Tab) ? (value as Tab) : 'General';
	});

	let settings = $state<AppSettings | null>(null);
	let failed = $state(false);

	/** Libraries returned by the ABS connection test, for the picker. */
	let absLibraries = $state<{ id: string; name: string }[]>([]);
	let selectedLibraries = $state<string[]>([]);
	let ranking = $state<RankingCriterion[]>([]);

	async function load() {
		failed = false;
		try {
			settings = await getSettings();
			const saved = settings.audiobookshelf?.library_id;
			selectedLibraries = Array.isArray(saved) ? (saved as string[]) : [];
			ranking = (settings.auto_search?.ranking ?? DEFAULT_RANKING) as RankingCriterion[];
		} catch {
			failed = true;
		}
	}

	$effect(() => {
		if (!auth.isAdmin) {
			goto('/', { replaceState: true });
			return;
		}
		load();
	});

	function setTab(next: Tab) {
		setSearchParam('tab', next === 'General' ? null : next);
	}

	function toggleLibrary(id: string, checked: boolean) {
		selectedLibraries = checked
			? [...selectedLibraries, id]
			: selectedLibraries.filter((x) => x !== id);
	}
</script>

<PageHeader title="Settings" icon="settings" />

<div class="tabs" role="tablist">
	{#each TABS as t (t)}
		<button
			type="button"
			role="tab"
			aria-selected={tab === t}
			class:active={tab === t}
			onclick={() => setTab(t)}
		>
			{t}
		</button>
	{/each}
</div>

{#if failed}
	<ErrorState onretry={load} />
{:else if !settings}
	<LoadingState />
{:else if tab === 'General'}
	<SettingsForm section="general" fields={GENERAL_FIELDS} initial={settings.general ?? {}} />
{:else if tab === 'ABS'}
	<SettingsForm
		section="audiobookshelf"
		fields={ABS_FIELDS}
		initial={settings.audiobookshelf ?? {}}
		test="abs"
		transform={(v) => ({ ...v, library_id: selectedLibraries })}
		ontested={(r) => {
			const libs = (r as { libraries?: { id: string; name: string }[] }).libraries;
			if (libs) absLibraries = libs;
		}}
	>
		{#snippet children()}
			<div class="libraries">
				<div class="label">Libraries</div>
				{#if absLibraries.length}
					{#each absLibraries as lib (lib.id)}
						<label class="lib">
							<input
								type="checkbox"
								checked={selectedLibraries.includes(lib.id)}
								onchange={(e) => toggleLibrary(lib.id, e.currentTarget.checked)}
							/>
							{lib.name}
						</label>
					{/each}
				{:else if selectedLibraries.length}
					<p class="hint">
						{selectedLibraries.length} library ID{selectedLibraries.length === 1 ? '' : 's'} saved — click
						Test Connection to reload.
					</p>
				{:else}
					<p class="hint">Click Test Connection to load available libraries.</p>
				{/if}
			</div>
		{/snippet}
	</SettingsForm>
{:else if tab === 'Prowlarr'}
	<SettingsForm
		section="prowlarr"
		fields={PROWLARR_FIELDS}
		initial={settings.prowlarr ?? {}}
		test="prowlarr"
	/>
{:else if tab === 'Downloads'}
	<DownloadersTab initial={settings.downloaders ?? []} />

	<h2 class="section">Auto-search</h2>
	<SettingsForm
		section="auto_search"
		fields={AUTO_SEARCH_FIELDS}
		initial={settings.auto_search ?? {}}
		transform={(v) => ({ ...v, ranking })}
	>
		{#snippet children()}
			<RankingEditor items={ranking} onchange={(next) => (ranking = next)} />
		{/snippet}
	</SettingsForm>
{:else if tab === 'Hardcover'}
	<SettingsForm
		section="hardcover"
		fields={HARDCOVER_FIELDS}
		initial={settings.hardcover ?? {}}
		test="hardcover"
	/>
{:else if tab === 'Notifications'}
	<SettingsForm
		section="notifications"
		fields={NOTIFICATION_FIELDS}
		initial={settings.notifications ?? {}}
		test="notifications"
	/>
{:else}
	<TasksTab initial={settings.schedule ?? {}} />
{/if}

<style>
	.tabs {
		display: flex;
		gap: 0.25rem;
		border-bottom: 1px solid var(--border);
		margin-bottom: 1rem;
		overflow-x: auto;
	}

	.tabs button {
		background: none;
		border: none;
		border-bottom: 2px solid transparent;
		color: var(--text-dim);
		padding: 0.4rem 0.7rem;
		font-size: 0.9rem;
		white-space: nowrap;
	}

	.tabs button:hover {
		color: var(--text);
	}

	.tabs button.active {
		color: var(--text);
		border-bottom-color: var(--accent);
	}

	.section {
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--text-dim);
		margin: 2rem 0 0.5rem;
		padding-top: 1.5rem;
		border-top: 1px solid var(--border);
	}

	.libraries {
		margin-bottom: 1rem;
	}

	.label {
		font-size: 0.85rem;
		color: var(--text-dim);
		margin-bottom: 0.35rem;
	}

	.lib {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.9rem;
		padding: 0.15rem 0;
		cursor: pointer;
	}

	.hint {
		font-size: 0.85rem;
		color: var(--text-dim);
	}
</style>
