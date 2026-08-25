/** Display formatting, ported verbatim from v1's helpers so output is identical. */

export function formatDate(iso?: string | null): string {
	if (!iso) return '—';
	return new Date(iso).toLocaleDateString(undefined, {
		year: 'numeric',
		month: 'short',
		day: 'numeric'
	});
}

export function formatDateTime(iso?: string | null): string {
	if (!iso) return '—';
	return new Date(iso).toLocaleString(undefined, {
		month: 'short',
		day: 'numeric',
		hour: 'numeric',
		minute: '2-digit'
	});
}

export function formatBytes(bytes?: number | null): string {
	if (!bytes) return '—';
	const gb = bytes / 1e9;
	if (gb >= 1) return `${gb.toFixed(1)} GB`;
	return `${(bytes / 1e6).toFixed(0)} MB`;
}

/**
 * Downloaders disagree about ETA: SABnzbd sends "H:MM:SS", qBittorrent sends
 * seconds and uses -1 for unavailable and 8640000 for infinite. Anything beyond
 * a day is treated as unknown, as in v1.
 */
export function formatEta(eta?: number | string | null): string | null {
	let secs: number | null | undefined;

	if (typeof eta === 'string') {
		const parts = eta.split(':').map(Number);
		if (parts.length === 3 && !parts.some(isNaN)) {
			secs = parts[0] * 3600 + parts[1] * 60 + parts[2];
		} else {
			return null;
		}
	} else {
		secs = eta;
	}

	if (secs == null || secs < 0 || secs > 86400) return null;
	if (secs < 60) return `${secs}s`;

	const h = Math.floor(secs / 3600);
	const m = Math.floor((secs % 3600) / 60);
	const s = secs % 60;
	if (h > 0) return `${h}h ${m}m`;
	return `${m}m ${s > 0 ? ` ${s}s` : ''}`.trim();
}
