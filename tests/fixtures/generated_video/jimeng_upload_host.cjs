'use strict';
// Exercise the shipped upload function in an offline browser realm.
const fs = require('node:fs');
const vm = require('node:vm');
const crypto = require('node:crypto');
const [workerPath, uploadHost, file] = process.argv.slice(2);
const source = fs.readFileSync(workerPath, 'utf8');
const moduleScope = {module: {exports: {}}, require, process, Buffer};
vm.runInNewContext(source + '\nmodule.exports.testUpload = upload;', moduleScope);
let binaryPosts = 0, commits = 0, route;
const payload = fs.readFileSync(file);
const realm = vm.createContext({crypto: crypto.webcrypto, TextEncoder, URL, URLSearchParams,
  Uint8Array, AbortSignal, Date, console,
  fetch: async (url, init) => {
    const value = String(url);
    if (value.includes('/__ai_video_jimeng_ref__/')) {
      return {ok: true, arrayBuffer: async () => payload};
    }
    if (value.includes('/get_upload_token')) return {ok: true, json: async () => ({ret: 0,
      data: {access_key_id: 'fixture-key', secret_access_key: 'fixture-secret',
        session_token: 'fixture-token', space_name: 'fixture-space'}})};
    if (value.includes('ApplyImageUpload')) return {ok: true, json: async () => ({Result: {
      UploadAddress: {UploadHosts: [uploadHost], SessionKey: 'fixture-session',
        StoreInfos: [{StoreUri: 'fixture-uri', Auth: 'fixture-auth'}]}}})};
    if (value.includes('/upload/v1/')) {
      binaryPosts++;
      if (!Buffer.from(init.body).equals(payload)) throw Error('changed bytes');
      return {ok: true, json: async () => ({code: 2000})};
    }
    if (value.includes('CommitImageUpload')) {
      commits++;
      return {ok: true, json: async () => ({Result: {Results: [{UriStatus: 2000, Uri: 'fixture-uri'}]}})};
    }
    throw Error('unexpected endpoint');
  }});
const page = {route: async (_, handler) => {route = handler;},
  unroute: async () => {route = null;},
  evaluate: async (fn, arg) => {
    realm.arg = arg;
    return vm.runInContext('(' + fn.toString() + ')(arg)', realm);
  }};
(async () => {
  let result, error;
  try {
    result = await moduleScope.module.exports.testUpload(page, {file, kind: 'image', mime_type: 'image/png',
      sha256: crypto.createHash('sha256').update(payload).digest('hex')}, {check: async () => ({})});
  } catch (caught) {error = caught.message;}
  console.log(JSON.stringify({ok: Boolean(result), result, error, binaryPosts, commits, cleaned: route === null}));
})().catch(error => {console.error(error.message);process.exitCode = 1;});
