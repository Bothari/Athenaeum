/**
 * Settings sections the backend accepts on PUT /settings. Sending an unknown
 * key is a 400, so this union is the contract, not a convenience.
 */
export type SettingsSection =
	| 'general'
	| 'audiobookshelf'
	| 'prowlarr'
	| 'downloaders'
	| 'hardcover'
	| 'notifications'
	| 'schedule'
	| 'auto_search'
	| 'auth';

/** Services with a /settings/test/* endpoint. */
export type TestableService = 'abs' | 'prowlarr' | 'downloader' | 'hardcover' | 'notifications';

export interface RankingCriterion {
	criterion: string;
	enabled: boolean;
	prefer?: string;
}

export interface DownloaderConfig {
	id?: string;
	type: 'qbittorrent' | 'sabnzbd' | 'deluge' | string;
	name?: string;
	enabled?: boolean;
	url?: string;
	username?: string;
	password?: string;
	api_key?: string;
	category?: string;
	download_dir?: string;
	remove_completed?: boolean;
	[key: string]: unknown;
}

export interface AppSettings {
	general?: Record<string, unknown>;
	audiobookshelf?: Record<string, unknown>;
	prowlarr?: Record<string, unknown>;
	hardcover?: Record<string, unknown>;
	notifications?: Record<string, unknown>;
	schedule?: Record<string, string>;
	auto_search?: Record<string, unknown> & { ranking?: RankingCriterion[] };
	auth?: Record<string, unknown>;
	downloaders?: DownloaderConfig[];
}

/**
 * The backend replaces secrets with this on GET and ignores it on PUT, so a
 * value left untouched keeps whatever is stored. Never send it back as a real
 * value, and never treat it as one.
 */
export const MASKED = '********';

/** One editable field in a schema-driven tab. */
export interface FieldSpec {
	key: string;
	label: string;
	type?: 'text' | 'password' | 'number' | 'boolean' | 'textarea' | 'csv';
	hint?: string;
	placeholder?: string;
	min?: number;
	max?: number;
	width?: string;
	rows?: number;
	/** Hides the field unless the predicate passes — used for the prefix fields,
	 *  which only apply when directories are separated by type. */
	visibleWhen?: (values: Record<string, unknown>) => boolean;
}
