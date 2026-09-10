import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { cp, mkdir, mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { promisify } from 'node:util';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const execFileAsync = promisify(execFile);
const root = fileURLToPath(new URL('../../', import.meta.url));

test('frontend build excludes backend secrets from environment and local env file', async () => {
  // Keep dependency resolution through the checkout's node_modules, but never
  // load the developer's .env or modify their dist/ output.
  const temporaryRoot = path.join(root, '.local');
  await mkdir(temporaryRoot, { recursive: true });
  const fixture = await mkdtemp(path.join(temporaryRoot, 'openai-build-'));
  const processKey = 'sk-FAKE-openai-process-build-canary';
  const localKey = 'sk-FAKE-openai-local-build-canary';
  try {
    await mkdir(path.join(fixture, 'scripts'));
    await cp(path.join(root, 'scripts/build.mjs'), path.join(fixture, 'scripts/build.mjs'));
    await cp(path.join(root, 'frontend/src'), path.join(fixture, 'frontend/src'), { recursive: true });
    const privateHost = 'http://private-ollama.example.test:11434';
    await writeFile(path.join(fixture, '.env'),
      `OPENAI_API_KEY=${localKey}\nAIG_STRATEGY_PROVIDER=ollama\nAIG_OLLAMA_BASE_URL=${privateHost}\n`);
    const environment = { ...process.env, PUBLIC_API_BASE_URL: 'https://api.example.test',
      AIG_STRATEGY_PROVIDER: 'openai', AIG_OLLAMA_BASE_URL: privateHost };
    delete environment.OPENAI_API_KEY;
    delete environment.AIG_OPENAI_API_KEY;
    for (const key of [undefined, processKey]) {
      if (key !== undefined) environment.OPENAI_API_KEY = key;
      const { stdout, stderr } = await execFileAsync(process.execPath, ['scripts/build.mjs'], {
        cwd: fixture, env: environment, timeout: 30000,
      });
      const output = path.join(fixture, 'dist');
      const files = await readdir(output, { recursive: true, withFileTypes: true });
      assert.ok(files.some((entry) => entry.name === 'main.js'));
      assert.ok(files.some((entry) => entry.name === 'index.html'));
      assert.ok((await readFile(path.join(output, 'assets/main.js'), 'utf8')).includes('https://api.example.test'));
      for (const entry of files.filter((entry) => entry.isFile())) {
        const contents = await readFile(path.join(entry.parentPath, entry.name));
        for (const secret of [processKey, localKey, 'OPENAI_API_KEY', 'AIG_STRATEGY_PROVIDER',
          privateHost, 'api.openai.com', '10.0.0.250', '/api/chat']) {
          assert.equal(contents.includes(Buffer.from(secret)), false, `Secret leaked in ${entry.name}`);
        }
      }
      for (const secret of [processKey, localKey]) {
        assert.equal((stdout + stderr).includes(secret), false, 'Secret leaked in build log');
      }
    }
  } finally {
    assert.equal(path.dirname(path.resolve(fixture)), path.resolve(temporaryRoot));
    await rm(fixture, { recursive: true, force: true });
  }
});
