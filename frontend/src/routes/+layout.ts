// SPA mode: no server-side rendering, no prerendering. FastAPI owns auth and data;
// the client fetches everything from /api after load.
export const ssr = false;
export const prerender = false;
export const trailingSlash = 'never';
