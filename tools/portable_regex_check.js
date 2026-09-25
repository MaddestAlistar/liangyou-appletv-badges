// Common-body semantic check, not an implementation of a private player.
const fs = require('node:fs');
const { performance } = require('node:perf_hooks');
const request = JSON.parse(fs.readFileSync(0, 'utf8'));
const compiled = Object.fromEntries(Object.entries(request.configs).map(([name, config]) => [
  name, config.filters.map(f => {
    if (!f.pattern.startsWith('(?i)')) throw new Error(`Unexpected flags: ${f.id}`);
    return [f.id.slice(5), new RegExp(f.pattern.slice(4), 'i')];
  }),
]));
const results = Object.fromEntries(Object.entries(compiled).map(([name, rules]) => [
  name, request.texts.map(text => rules.filter(([, rx]) => rx.test(text)).map(([id]) => id).sort()),
]));
const start = performance.now();
for (const rules of Object.values(compiled)) {
  for (const text of request.noise) for (const [, rx] of rules) rx.test(text);
}
process.stdout.write(JSON.stringify({ results, noise_ms: Math.round(performance.now() - start) }));
