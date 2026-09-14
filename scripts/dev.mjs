/** One local command: owned Python process + existing esbuild watch/proxy. */
import { spawn } from 'node:child_process';
import { access } from 'node:fs/promises';
import { createServer } from 'node:net';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const python = fileURLToPath(new URL(process.platform === 'win32'
  ? '../.venv/Scripts/python.exe' : '../.venv/bin/python', import.meta.url));
const children = [];
let apiPort;
let stopping = false;
function stop(code = 0) {
  if (stopping) return;
  stopping = true;
  process.exitCode = code;
  for (const child of children) child.kill();
}
function start(executable, args, env = process.env) {
  const child = spawn(executable, args, { cwd: root, env, stdio: 'inherit', windowsHide: true });
  children.push(child);
  child.on('error', (error) => { console.error(error.message); stop(1); });
  child.on('exit', (code) => { if (!stopping) stop(code || 1); });
  return child;
}
process.once('SIGINT', () => stop());
process.once('SIGTERM', () => stop());
try {
  await access(python).catch(() => { throw new Error('Missing .venv. Run python -m venv .venv, then .venv\\Scripts\\python.exe -m pip install -e ".[test]" (Linux: .venv/bin/python).'); });
  for (const port of [0, 5173]) {
    await new Promise((resolve, reject) => {
      const probe = createServer();
      probe.once('error', (error) => reject(new Error(error.code === 'EADDRINUSE'
        ? `Port ${port} is in use. Stop the existing local server, then run npm run dev again.`
        : `Cannot listen on 127.0.0.1:${port}: ${error.code}. Check local socket permissions. ${error.message}`)));
      probe.listen(port, '127.0.0.1', () => {
        if (port === 0) apiPort = probe.address().port;
        probe.close(resolve);
      });
    });
  }
  start(python, ['-m', 'uvicorn', 'aig.control_web:create_app', '--factory', '--host', '127.0.0.1', '--port', String(apiPort)]);
  let ready = false;
  for (let attempt = 0; attempt < 100 && !stopping; attempt++) {
    try { ready = (await fetch(`http://127.0.0.1:${apiPort}/api/health`, { signal: AbortSignal.timeout(500) })).ok; } catch {}
    if (ready) break;
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  if (!ready) throw new Error('Python did not become ready. Check the startup error above; install dependencies with pip install -e ".[test]".');
  if (!stopping) {
    // Local preview always uses this process's API, regardless of deployment .env origins.
    start(process.execPath, ['scripts/build.mjs', '--serve'], {
      ...process.env, PUBLIC_API_BASE_URL: '', API_HOST: '127.0.0.1', API_PORT: String(apiPort), DEV_HOST: '127.0.0.1',
    });
  }
} catch (error) { console.error(error.message); stop(1); }
