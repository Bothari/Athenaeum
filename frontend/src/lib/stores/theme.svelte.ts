export type Theme = 'light' | 'dark';

const STORAGE_KEY = 'theme';
/** v1 shipped index.html with class="light" and defaulted to light. Preserved. */
const DEFAULT: Theme = 'light';

class ThemeStore {
	current = $state<Theme>(DEFAULT);

	/** Reads the stored preference and applies it. Called from the root layout. */
	init(): void {
		const stored = localStorage.getItem(STORAGE_KEY);
		this.apply(stored === 'dark' || stored === 'light' ? stored : DEFAULT);
	}

	toggle(): void {
		this.apply(this.current === 'light' ? 'dark' : 'light');
		localStorage.setItem(STORAGE_KEY, this.current);
	}

	private apply(theme: Theme): void {
		this.current = theme;
		// Tokens for dark live on :root and light overrides them via html.light,
		// so the class is the switch. See app.css.
		document.documentElement.classList.toggle('light', theme === 'light');
	}
}

export const theme = new ThemeStore();
