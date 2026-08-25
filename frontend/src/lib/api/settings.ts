import { request } from './client';
import type { AppSettings, SettingsSection, TestableService } from '$lib/types/settings';

export function getSettings(): Promise<AppSettings> {
	return request<AppSettings>('/settings');
}

/**
 * Saves one section at a time. v1 did the same, and it matters: a whole-document
 * save would let a tab that loaded earlier clobber changes made in another.
 */
export function saveSection(
	section: SettingsSection,
	values: Record<string, unknown> | unknown[]
): Promise<unknown> {
	return request<unknown>('/settings', { method: 'PUT', body: { [section]: values } });
}

export interface TestResult {
	ok?: boolean;
	error?: string | null;
	message?: string | null;
	/** ABS returns the library list so it can be picked from. */
	libraries?: { id: string; name: string }[];
	[key: string]: unknown;
}

/**
 * Tests use the values on screen rather than what is saved, so an untested
 * change can be checked before committing it.
 */
export function testService(
	service: TestableService,
	values: Record<string, unknown>
): Promise<TestResult> {
	return request<TestResult>(`/settings/test/${service}`, { method: 'POST', body: values });
}

/**
 * Next fire time for a single cron expression. The backend evaluates whatever
 * expression is passed rather than what is saved, so this doubles as a live
 * preview while editing. Returns next_run: null for an invalid expression.
 */
export function getNextRun(expr: string): Promise<{ next_run?: string | null }> {
	return request<{ next_run?: string | null }>(
		`/schedule/next-run?expr=${encodeURIComponent(expr)}`
	);
}
