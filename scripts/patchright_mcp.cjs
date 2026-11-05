#!/usr/bin/env node
'use strict';

// A separate MCP browser surface using an explicitly selected Patchright runtime.
// It attaches to the existing Chrome; it never launches or closes that browser.
const fs = require('node:fs');
const path = require('node:path');
const {createRequire} = require('node:module');
let initializationStage = 'configuration';
const localErrors = new Set([
  'Expected each supported path option exactly once',
  'Missing browser runtime path option',
  'Existing browser endpoint is unavailable',
  'Unexpected Patchright runtime version',
  'Existing browser context is ambiguous',
]);

function options(argv) {
  const allowed = new Set(['--runtime-dir', '--mcp-runtime-dir', '--profile-dir', '--output-dir']);
  const values = {};
  for (let i = 0; i < argv.length; i += 2) {
    if (!allowed.has(argv[i]) || !argv[i + 1] || Object.hasOwn(values, argv[i])) {
      throw new Error('Expected each supported path option exactly once');
    }
    values[argv[i]] = path.resolve(argv[i + 1]);
  }
  for (const key of allowed) if (!values[key]) throw new Error('Missing browser runtime path option');
  return values;
}

function endpoint(profileDir) {
  const port = fs.readFileSync(path.join(profileDir, 'DevToolsActivePort'), 'utf8').split('\n')[0];
  if (!/^\d{2,5}$/.test(port) || Number(port) > 65535) {
    throw new Error('Existing browser endpoint is unavailable');
  }
  return 'http://127.0.0.1:' + port;
}

async function main(argv) {
  const args = options(argv);
  initializationStage = 'runtime_modules';
  const runtimeRequire = createRequire(path.join(args['--runtime-dir'], 'package.json'));
  const mcpRequire = createRequire(path.join(args['--mcp-runtime-dir'], 'package.json'));
  const patchright = runtimeRequire('patchright');
  const version = JSON.parse(fs.readFileSync(path.join(args['--runtime-dir'],
    'node_modules/patchright/package.json'), 'utf8')).version;
  if (version !== '1.64.2') throw new Error('Unexpected Patchright runtime version');
  const {createConnection} = mcpRequire('@playwright/mcp');
  const {StdioServerTransport} = runtimeRequire('@modelcontextprotocol/sdk/server/stdio.js');
  initializationStage = 'existing_browser_endpoint';
  const cdpEndpoint = endpoint(args['--profile-dir']);
  initializationStage = 'cdp_connection';
  const browser = await patchright.chromium.connectOverCDP(cdpEndpoint);
  const contexts = browser.contexts();
  if (contexts.length !== 1) throw new Error('Existing browser context is ambiguous');
  const context = contexts[0];
  initializationStage = 'mcp_context_factory';
  const connection = await createConnection({
    browser: {browserName: 'chromium', isolated: false},
    outputDir: args['--output-dir'],
  }, async () => context);
  initializationStage = 'stdio_connection';
  await connection.connect(new StdioServerTransport());
  // Stop only this adapter process. The user's browser and all its pages survive.
  process.once('SIGTERM', () => process.exit(0));
  process.once('SIGINT', () => process.exit(0));
}

if (require.main === module) main(process.argv.slice(2)).catch(error => {
  const reason = localErrors.has(error.message) ? error.message : (error.code || error.name);
  process.stderr.write('Patchright MCP initialization failed [' + initializationStage + ']: ' + reason + '\n');
  process.exit(1);
});

module.exports = {options, endpoint};
