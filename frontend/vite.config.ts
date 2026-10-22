import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

// In the dev container the FastAPI app is a separate service; locally it is on the
// host. API_PROXY_TARGET lets the same config serve both.
const API_TARGET = process.env.API_PROXY_TARGET ?? 'http://localhost:8741';

export default defineConfig({
	plugins: [
		sveltekit({
			compilerOptions: {
				// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
				runes: ({ filename }) =>
					filename.split(/[/\\]/).includes('node_modules') ? undefined : true
			},

			// SPA: Vite emits static assets that FastAPI serves from static/. No Node
			// server at runtime. `fallback` is index.html because app/main.py's
			// catch-all serve_spa already returns it for every unmatched path.
			adapter: adapter({
				pages: 'build',
				assets: 'build',
				fallback: 'index.html',
				precompress: false,
				strict: true
			})
		})
	],

	server: {
		host: '0.0.0.0',
		port: 5173,
		strictPort: true,
		// Reached from phones on the LAN by hostname/IP, not just localhost. Mobile
		// testing is mandatory here because of the focus-zoom rule (see CLAUDE.md).
		allowedHosts: ['localhost', 'marvin', '.bothari.com'],
		proxy: {
			// Session cookies are set by FastAPI, so the proxy must preserve them.
			// Same-origin through the dev server means no CORS and no cookie flags to
			// special-case.
			'/api': {
				target: API_TARGET,
				changeOrigin: false
			}
		}
	}
});
