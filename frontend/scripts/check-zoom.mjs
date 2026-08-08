#!/usr/bin/env node
/**
 * Guards the mobile-zoom rule: iOS Safari zooms the page when a focused text
 * field's computed font-size is under 16px.
 *
 * Scans .svelte and .css sources for CSS rules that (a) target a text input and
 * (b) declare a font-size below 16px. Catches the exact regression v1 kept
 * hitting, where a smaller font-size crept into an input-ish class and silently
 * beat the global rule.
 *
 * Heuristic by design — it errs toward flagging. Suppress a genuine false
 * positive with a `/* zoom-safe: <reason> *\/` comment inside the rule body.
 */
import { readFileSync } from 'node:fs';
import { globSync } from 'node:fs';

const MIN_PX = 16;
const INPUT_SELECTOR = /\b(input|select|textarea)\b|\binput\b/i;

/** Resolve a CSS length to px. Returns null if not statically resolvable. */
function toPx(value) {
	const m = value.trim().match(/^(-?[\d.]+)(px|rem|em|pt|%)?$/);
	if (!m) return null;
	const n = parseFloat(m[1]);
	switch (m[2]) {
		case 'px':
		case undefined:
			return m[2] === 'px' ? n : null;
		case 'rem':
		case 'em':
			return n * 16;
		case 'pt':
			return n * (96 / 72);
		case '%':
			return (n / 100) * 16;
		default:
			return null;
	}
}

const files = globSync('src/**/*.{svelte,css}', { cwd: process.cwd() });
const violations = [];

for (const file of files) {
	const text = readFileSync(file, 'utf8');
	// Match `selector { ...body... }` — non-nested, which covers plain CSS.
	const ruleRe = /([^{}]+)\{([^{}]*)\}/g;
	let m;
	while ((m = ruleRe.exec(text)) !== null) {
		const [, selector, body] = m;
		if (!INPUT_SELECTOR.test(selector)) continue;
		if (/zoom-safe:/.test(body)) continue;

		const fs = body.match(/(?:^|[;{\s])font-size\s*:\s*([^;}]+)/i);
		if (!fs) continue;

		const px = toPx(fs[1]);
		if (px !== null && px < MIN_PX) {
			const line = text.slice(0, m.index).split('\n').length;
			violations.push({
				file,
				line,
				selector: selector.trim().replace(/\s+/g, ' '),
				value: fs[1].trim(),
				px
			});
		}
	}
}

if (violations.length === 0) {
	console.log(`OK zoom check: no input font-size under ${MIN_PX}px`);
	process.exit(0);
}

console.error(`\nFAIL zoom check - ${violations.length} rule(s) will zoom on iOS focus:\n`);
for (const v of violations) {
	console.error(`  ${v.file}:${v.line}`);
	console.error(`    ${v.selector} { font-size: ${v.value} }  -> ${v.px}px`);
}
console.error(`
Fix: keep font-size at >=${MIN_PX}px on focusable fields. To make a field look
smaller, reduce padding/height instead. See src/app.css.
`);
process.exit(1);
