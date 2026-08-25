import { request } from '$lib/api/client';

/**
 * Cover aspect ratio, taken from the Audiobookshelf library's own setting
 * (coverAspectRatio: 1 = square, 0 = tall). Audiobook covers are usually square
 * while book covers are 2:3, so this follows whatever ABS is configured for
 * rather than guessing.
 *
 * Applied as a class on <body> so the rule can reach cover images inside any
 * component, matching v1.
 */
class CoverStore {
	square = $state(false);

	async init(): Promise<void> {
		try {
			const s = await request<{ cover_aspect_ratio?: number }>('/abs/library-settings');
			this.square = s.cover_aspect_ratio === 1;
		} catch {
			// The endpoint already defaults to 1 when ABS is unreachable; if the call
			// itself fails, leave covers at the 2:3 default rather than guessing.
			this.square = false;
		}
		document.body.classList.toggle('square-covers', this.square);
	}
}

export const covers = new CoverStore();
