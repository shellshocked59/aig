import { copyFile, mkdir } from 'node:fs/promises';
import { watchFile, unwatchFile } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { build, context } from 'esbuild';
import { createServer, request } from 'node:http';

const root = fileURLToPath(new URL('../', import.meta.url));
const htmlSource = new URL('../frontend/src/index.html', import.meta.url);
const htmlOutput = new URL('../dist/index.html', import.meta.url);
const serving = process.argv.includes('--serve');
const watching = serving || process.argv.includes('--watch');

await mkdir(new URL('../dist/', import.meta.url), { recursive: true });
await copyFile(htmlSource, htmlOutput);

const options = {
  absWorkingDir: root,
  entryPoints: ['frontend/src/js/main.js'],
  bundle: true,
  platform: 'browser',
  // Preserve the existing plain-JavaScript bundle format.
  format: 'iife',
  target: ['es2022'],
  outfile: 'dist/assets/main.js',
  loader: { '.png': 'file' },
  assetNames: '[name]-[hash]',
  logLevel: 'info',
};

if (watching) {
  const buildContext = await context(options);
  await buildContext.watch();
  watchFile(htmlSource, { interval: 250 }, async () => {
    try {
      await copyFile(htmlSource, htmlOutput);
      console.log('Updated dist/index.html');
    } catch (error) {
      console.error('HTML copy failed:', error.message);
    }
  });
  let server;
  if (serving) {
    const staticServer = await buildContext.serve({ host: '127.0.0.1', port: 0, servedir: 'dist' });
    // Same-origin browser requests, with just /api forwarded to Python.
    server = createServer((incoming, outgoing) => {
      const isApi = incoming.url === '/api' || incoming.url.startsWith('/api/');
      const proxy = request({
        hostname: '127.0.0.1', port: isApi ? 8000 : staticServer.port,
        path: incoming.url, method: incoming.method,
        headers: { ...incoming.headers, host: `127.0.0.1:${isApi ? 8000 : staticServer.port}` },
      }, (response) => {
        outgoing.writeHead(response.statusCode, { ...response.headers, 'cache-control': 'no-store' });
        response.pipe(outgoing);
      });
      proxy.on('error', () => {
        if (outgoing.headersSent) { outgoing.destroy(); return; }
        outgoing.writeHead(502, { 'content-type': 'application/json' });
        outgoing.end(JSON.stringify({ error: 'backend_unavailable', message: 'Cannot reach Python. Start the backend on port 8000, then retry.' }));
      });
      incoming.pipe(proxy);
    });
    server.listen(5173, '127.0.0.1', () => console.log('Game: http://127.0.0.1:5173 · API proxy: 127.0.0.1:8000'));
    server.on('error', async (error) => { console.error(error.message); await buildContext.dispose(); process.exit(1); });
  }
  console.log('Watching HTML, JavaScript, CSS, and imported sprites. Refresh the browser after changes.');

  const stop = async () => {
    unwatchFile(htmlSource);
    server?.closeAllConnections();
    server?.close();
    await buildContext.dispose();
  };
  process.once('SIGINT', stop);
  process.once('SIGTERM', stop);
} else {
  await build(options);
  console.log('Built dist/index.html. Use npm run dev for the playable application.');
}
