import type { FieldSpec } from '$lib/types/settings';

/**
 * Field definitions for the schema-driven tabs. Labels and hints are v1's,
 * verbatim — see docs/V2_SETTINGS_INVENTORY.md §2, which is the checklist this
 * was built against.
 *
 * Deliberately absent: the five settings keys nothing reads
 * (audiobookshelf.square_book_covers, general.group_series_in_search,
 * prowlarr.tags, auto_search.enabled, pushover.*) and auth.session_secret,
 * which must never be editable. See the inventory §3.
 */

export const GENERAL_FIELDS: FieldSpec[] = [
	{ key: 'output_dir', label: 'Output directory' },
	{ key: 'separate_type_dirs', label: 'Separate directories by type (audiobooks/ebooks)', type: 'boolean' },
	{
		key: 'audiobook_prefix',
		label: 'Audiobook directory prefix',
		visibleWhen: (v) => v.separate_type_dirs === true
	},
	{
		key: 'ebook_prefix',
		label: 'Ebook directory prefix',
		visibleWhen: (v) => v.separate_type_dirs === true
	},
	{
		key: 'public_url',
		label: 'Public URL',
		hint: 'Externally reachable URL for this app, e.g. https://athenaeum.example.com — required for OIDC'
	},
	{ key: 'merge_multifile_audiobooks', label: 'Merge multi-file audiobooks into single M4B', type: 'boolean' },
	{ key: 'debug_view', label: 'Debug view', type: 'boolean' },
	{
		key: 'allowed_audiobook_formats',
		label: 'Allowed audiobook formats',
		type: 'csv',
		hint: 'Comma-separated — Prowlarr results with other recognised formats are hidden. e.g. m4b, mp3, flac'
	},
	{
		key: 'allowed_ebook_formats',
		label: 'Allowed ebook formats',
		type: 'csv',
		hint: 'Comma-separated — e.g. epub, pdf, mobi, azw3'
	}
];

export const ABS_FIELDS: FieldSpec[] = [
	{ key: 'url', label: 'ABS URL', hint: 'e.g. http://192.168.1.10:13378 — used for browser links' },
	{
		key: 'internal_url',
		label: 'Internal ABS URL',
		hint: 'Optional — Docker internal URL e.g. http://abs:13378'
	},
	{ key: 'api_key', label: 'API Key', type: 'password' }
];

export const PROWLARR_FIELDS: FieldSpec[] = [
	{ key: 'url', label: 'URL' },
	{ key: 'api_key', label: 'API Key', type: 'password' },
	{
		key: 'tags',
		label: 'Indexer tag filter',
		type: 'csv',
		hint: 'Comma-separated — only search indexers carrying any of these tags. e.g. books, audiobooks. Leave empty to search all indexers.'
	}
];

export const HARDCOVER_FIELDS: FieldSpec[] = [
	{ key: 'api_key', label: 'API Key', type: 'password' },
	{ key: 'preferred_language', label: 'Preferred language' }
];

export const NOTIFICATION_FIELDS: FieldSpec[] = [
	{
		key: 'urls',
		label: 'Notification URLs',
		type: 'textarea',
		rows: 5,
		placeholder: 'One Apprise URL per line\ne.g. pover://token/userkey\ne.g. mailto://user:pass@smtp.example.com',
		hint: 'Supports 60+ services via Apprise URL syntax.'
	},
	{
		key: 'batch_window',
		label: 'Batch window (seconds)',
		type: 'number',
		min: 10,
		max: 3600,
		width: '120px',
		hint: 'Notifications within this window are grouped into a single message.'
	}
];

export const AUTO_SEARCH_FIELDS: FieldSpec[] = [
	{
		key: 'search_on_request',
		label: 'Search immediately on request',
		type: 'boolean',
		hint: 'Trigger a search as soon as a request is created or approved. The scheduled task (configured in Tasks) controls periodic bulk searches.'
	},
	{
		key: 'min_seeders',
		label: 'Minimum seeders',
		type: 'number',
		min: 0,
		width: '80px',
		hint: 'Torrent results below this are excluded. Set to 0 to disable.'
	},
	{
		key: 'max_attempts',
		label: 'Max search attempts',
		type: 'number',
		min: 1,
		width: '80px',
		hint: 'Stop retrying a request after this many failed searches.'
	}
];

/** Ranking criteria metadata, from v1's CRITERION_META. */
export const CRITERION_META: Record<
	string,
	{ label: string; desc: string; prefer?: string[] }
> = {
	format: {
		label: 'Format',
		desc: 'Prefers results matching your allowed formats order — first listed is most preferred'
	},
	seeders: {
		label: 'Seeders',
		desc: 'Prefers results with more seeders (torrent only; NZB results are unaffected)'
	},
	size: { label: 'Size', desc: 'Prefer larger or smaller files', prefer: ['larger', 'smaller'] },
	age: { label: 'Age', desc: 'Prefer newer or older indexed releases', prefer: ['newer', 'older'] },
	indexer_priority: {
		label: 'Indexer priority',
		desc: 'Prefer results from higher-priority indexers (as configured in Prowlarr)'
	}
};

export const DEFAULT_RANKING = [
	{ criterion: 'format', enabled: true },
	{ criterion: 'seeders', enabled: true },
	{ criterion: 'size', enabled: true, prefer: 'larger' },
	{ criterion: 'age', enabled: false, prefer: 'newer' },
	{ criterion: 'indexer_priority', enabled: false }
];

export const TASK_DEFS = [
	{ key: 'library_sync', label: 'Library sync', default: '0 2 * * *', endpoint: '/sync/library' },
	{ key: 'cache_refresh', label: 'Cache refresh', default: '0 3 * * *', endpoint: '/sync/cache-refresh' },
	{ key: 'auto_search', label: 'Auto-search', default: '0 */6 * * *', endpoint: '/sync/auto-search' }
] as const;

export const DL_TYPE_LABELS: Record<string, string> = {
	qbittorrent: 'qBittorrent',
	sabnzbd: 'SABnzbd',
	deluge: 'Deluge'
};

/** Per-downloader-type field sets, from v1's dlTypeFields. */
export const DL_FIELDS: Record<string, FieldSpec[]> = {
	qbittorrent: [
		{ key: 'url', label: 'URL' },
		{ key: 'username', label: 'Username' },
		{ key: 'password', label: 'Password', type: 'password' },
		{ key: 'download_dir', label: 'Download directory' }
	],
	sabnzbd: [
		{ key: 'url', label: 'URL' },
		{ key: 'api_key', label: 'API Key', type: 'password' },
		{ key: 'category', label: 'Category' },
		{
			key: 'remove_completed',
			label: 'Remove completed downloads from SABnzbd history',
			type: 'boolean',
			hint: 'Files are kept — only the history entry is removed.'
		}
	],
	deluge: [
		{ key: 'url', label: 'URL' },
		{ key: 'password', label: 'Password', type: 'password' },
		{ key: 'download_dir', label: 'Download directory' }
	]
};
