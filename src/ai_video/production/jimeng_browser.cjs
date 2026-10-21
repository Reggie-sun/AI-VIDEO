// Jimeng's logged-in canvas owns credentials and the native commercial action.
// The host sends only bounded task data. This worker never prints session data.
'use strict';

const fs = require('node:fs');
const crypto = require('node:crypto');
const readline = require('node:readline');

const lines = readline.createInterface({input: process.stdin, crlfDelay: Infinity})[Symbol.asyncIterator]();
const nextLine = async () => {
  const item = await lines.next();
  if (item.done) throw Error('host disconnected');
  return JSON.parse(item.value);
};
const emit = value => process.stdout.write(JSON.stringify(value) + '\n');
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const ordered = value => Array.isArray(value) ? value.map(ordered)
  : value && typeof value === 'object'
    ? Object.fromEntries(Object.keys(value).sort().map(k => [k, ordered(value[k])])) : value;
const canon = value => JSON.stringify(ordered(value));
const origin = 'https://jimeng.jianying.com';

async function connect(command) {
  const {chromium} = require(command.playwright_module);
  const port = fs.readFileSync(command.profile_dir + '/DevToolsActivePort', 'utf8').split('\n')[0];
  if (!/^[0-9]{2,5}$/.test(port)) throw Error('browser endpoint unavailable');
  const browser = await chromium.connectOverCDP('http://127.0.0.1:' + port);
  const target = origin + '/ai-tool/ai-canvas/' + command.profile.project_id;
  const page = browser.contexts().flatMap(context => context.pages()).find(p => p.url() === target);
  if (!page) throw Error('exact logged-in canvas unavailable');
  const account = await page.evaluate(async () => {
    const scan = () => {
      let uid;
      for (const element of document.querySelectorAll('span')) {
        let fiber = element[Object.keys(element).find(key => key.startsWith('__reactFiber$'))];
        for (let i = 0; fiber && i < 240; i++, fiber = fiber.return) {
          const value = fiber.memoizedProps?.value;
          if (value && typeof value === 'object' && Object.keys(value).length === 1 && value.uid) {
            uid = String(value.uid);
            return uid;
          }
        }
      }
      return uid;
    };
    const uid = scan();
    if (!uid) throw Error('account identity unavailable');
    const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(uid));
    return [...new Uint8Array(bytes)].map(x => x.toString(16).padStart(2, '0')).join('');
  });
  if (account !== command.profile.account_sha256) throw Error('logged-in account mismatch');
  return {browser, page};
}

async function readResource(page, profile, resourceId) {
  return page.evaluate(async ({projectId, resourceId}) => {
    const response = await fetch('/octo_api/v1/resource/batch_get', {
      method: 'POST', credentials: 'include', redirect: 'error',
      headers: {'content-type': 'application/json'},
      body: JSON.stringify({project_id: projectId, resource_ids: [resourceId]}),
      signal: AbortSignal.timeout(20000),
    });
    const payload = await response.json();
    if (!response.ok || String(payload.ret) !== '0') throw Error('resource read rejected');
    const row = payload.data?.resources?.find(x => x.resource_id === resourceId);
    if (!row) throw Error('resource not found');
    const vid = row.video?.vid;
    const media = vid ? payload.data.media_urls?.[vid] : undefined;
    return {
      resource_id: row.resource_id, submit_id: row.submit_id,
      task_id: row.task_id == null ? null : String(row.task_id),
      status: row.status, project_id: projectId,
      video: {gen: row.video?.gen, vid},
      download_url: media?.download_url || media?.resolution_urls?.origin || media?.url,
    };
  }, {projectId: profile.project_id, resourceId});
}

async function readSavedCanvas(page, profile, resourceId) {
  for (let attempt = 0; attempt < 7; attempt++) {
    const result = await page.evaluate(async ({projectId, nodeId, resourceId}) => {
      const response = await fetch('/octo_api/v1/project/draft/get', {
        method: 'POST', credentials: 'include', redirect: 'error',
        headers: {'content-type': 'application/json'},
        body: JSON.stringify({project_id: projectId}),
        signal: AbortSignal.timeout(20000),
      });
      const payload = await response.json();
      if (!response.ok || String(payload.ret) !== '0' ||
          payload.data?.project?.project_id !== projectId ||
          typeof payload.data?.draft_json !== 'string') {
        throw Error('saved canvas read rejected');
      }
      const draft = JSON.parse(payload.data.draft_json);
      const matching = Array.isArray(draft.nodes) ? draft.nodes.filter(node =>
        node?.id === nodeId && node?.data?.resourceId === resourceId) : [];
      return {saved: matching.length === 1,
        draft_version: payload.data.draft_version,
        head_draft_version: payload.data.head_draft_version,
        draft_json: matching.length === 1 ? payload.data.draft_json : undefined};
    }, {projectId: profile.project_id, nodeId: profile.node_id, resourceId});
    if (result.saved) return result;
    if (attempt < 6) await page.waitForTimeout(5000);
  }
  throw Error('submitted resource is not in server-saved canvas draft');
}

async function upload(page, command) {
  const bytes = fs.readFileSync(command.file);
  if (sha(bytes) !== command.sha256) throw Error('reference bytes changed');
  const localUrl = origin + '/__ai_video_jimeng_ref__/' + crypto.randomUUID();
  await page.route(localUrl, route => route.fulfill({
    status: 200, contentType: command.mime_type, body: bytes,
  }));
  try {
    return await page.evaluate(async ({kind, localUrl}) => {
      const encode = new TextEncoder();
      const hex = data => [...new Uint8Array(data)].map(x => x.toString(16).padStart(2, '0')).join('');
      const hash = async data => hex(await crypto.subtle.digest('SHA-256', typeof data === 'string' ? encode.encode(data) : data));
      const hmac = async (key, value) => crypto.subtle.sign('HMAC',
        await crypto.subtle.importKey('raw', typeof key === 'string' ? encode.encode(key) : key,
          {name: 'HMAC', hash: 'SHA-256'}, false, ['sign']), encode.encode(value));
      const safeUpload = url => {
        const parsed = new URL(url);
        if (parsed.protocol !== 'https:' ||
            !/(^|\.)(bytedanceapi\.com|byteimg\.com|bytecdn\.cn|bytedance\.com|bytedance\.net|bytecdn\.com|douyinvod\.com|vod\.com|snssdk\.com|volces\.com|bytescm\.com|ibytedtos\.com|bytetos\.com|tos-cn\.com)$/.test(parsed.hostname)) {
          throw Error('upload destination invalid');
        }
      };
      const post = async (path, body) => {
        const response = await fetch(path, {method: 'POST', credentials: 'include', redirect: 'error',
          headers: {'content-type': 'application/json'}, body: JSON.stringify(body),
          signal: AbortSignal.timeout(20000)});
        const data = await response.json();
        if (!response.ok || String(data.ret) !== '0') throw Error('upload ticket rejected');
        return data.data;
      };
      const source = await fetch(localUrl, {credentials: 'omit', redirect: 'error'});
      if (!source.ok) throw Error('local reference unavailable');
      const payload = await source.arrayBuffer();
      const ticket = await post('/mweb/v1/get_upload_token', {scene: kind === 'image' ? 2 : 1});
      if (!ticket.access_key_id || !ticket.secret_access_key || !ticket.session_token || !ticket.space_name) {
        throw Error('upload ticket incomplete');
      }
      const service = kind === 'image' ? 'imagex' : 'vod';
      const region = ticket.region || 'cn-north-1';
      let host = kind === 'image' ? ticket.upload_domain || 'imagex.bytedanceapi.com' : 'vod.bytedanceapi.com';
      if (!host.startsWith('https://')) host = 'https://' + host;
      safeUpload(host);
      const sign = async (method, url, body = '') => {
        const parsed = new URL(url);
        const date = new Date().toISOString().replace(/[:-]/g, '').replace(/\.\d{3}Z$/, 'Z');
        const headers = {'x-amz-date': date, 'x-amz-security-token': ticket.session_token};
        const payloadHash = await hash(body);
        if (method === 'POST') headers['x-amz-content-sha256'] = payloadHash;
        const keys = Object.keys(headers).sort();
        const query = [...parsed.searchParams].sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0)
          .map(([key, value]) => key + '=' + value).join('&');
        const canonical = [method, parsed.pathname, query,
          keys.map(key => key + ':' + headers[key] + '\n').join(''),
          keys.join(';'), payloadHash].join('\n');
        const scope = date.slice(0, 8) + '/' + region + '/' + service + '/aws4_request';
        let key = await hmac('AWS4' + ticket.secret_access_key, date.slice(0, 8));
        key = await hmac(key, region);
        key = await hmac(key, service);
        key = await hmac(key, 'aws4_request');
        headers.Authorization = 'AWS4-HMAC-SHA256 Credential=' + ticket.access_key_id + '/' + scope +
          ', SignedHeaders=' + keys.join(';') + ', Signature=' +
          hex(await hmac(key, ['AWS4-HMAC-SHA256', date, scope, await hash(canonical)].join('\n')));
        return headers;
      };
      const query = kind === 'image'
        ? new URLSearchParams({Action: 'ApplyImageUpload', Version: '2018-08-01',
            ServiceId: ticket.space_name, FileSize: String(payload.byteLength),
            s: crypto.randomUUID().replaceAll('-', '').slice(0, 10)})
        : new URLSearchParams({Action: 'ApplyUploadInner', Version: '2020-11-19',
            SpaceName: ticket.space_name, FileType: 'video', IsInner: '1',
            FileSize: String(payload.byteLength),
            s: crypto.randomUUID().replaceAll('-', '').slice(0, 10)});
      const applyUrl = host + '/?' + query;
      const applied = await fetch(applyUrl, {headers: await sign('GET', applyUrl),
        credentials: 'omit', redirect: 'error', signal: AbortSignal.timeout(20000)});
      const apply = await applied.json();
      if (!applied.ok || apply.ResponseMetadata?.Error) throw Error('upload apply rejected');
      const address = kind === 'image' ? apply.Result?.UploadAddress
        : apply.Result?.InnerUploadAddress?.UploadNodes?.[0];
      const store = address?.StoreInfos?.[0];
      const uploadHost = kind === 'image' ? address?.UploadHosts?.[0] : address?.UploadHost;
      if (!store?.StoreUri || !store.Auth || !address?.SessionKey || !uploadHost) {
        throw Error('upload apply incomplete');
      }
      const uploadUrl = 'https://' + uploadHost + '/upload/v1/' + store.StoreUri;
      safeUpload(uploadUrl);
      let crc = 0xffffffff;
      for (const byte of new Uint8Array(payload)) {
        crc ^= byte;
        for (let i = 0; i < 8; i++) crc = (crc >>> 1) ^ ((crc & 1) ? 0xedb88320 : 0);
      }
      const uploaded = await fetch(uploadUrl, {method: 'POST', credentials: 'omit', redirect: 'error',
        headers: {Authorization: store.Auth, 'Content-CRC32': ((crc ^ 0xffffffff) >>> 0).toString(16).padStart(8, '0'),
          'Content-Type': 'application/octet-stream'}, body: payload,
        signal: AbortSignal.timeout(120000)});
      const uploadResult = await uploaded.json();
      if (!uploaded.ok || uploadResult.code !== 2000) throw Error('upload binary rejected');
      const commitUrl = host + '/?' + new URLSearchParams(kind === 'image'
        ? {Action: 'CommitImageUpload', Version: '2018-08-01', ServiceId: ticket.space_name}
        : {Action: 'CommitUploadInner', Version: '2020-11-19', SpaceName: ticket.space_name});
      const commitBody = JSON.stringify(kind === 'image'
        ? {SessionKey: address.SessionKey}
        : {SessionKey: address.SessionKey, Functions: []});
      const committed = await fetch(commitUrl, {method: 'POST', credentials: 'omit', redirect: 'error',
        headers: {...await sign('POST', commitUrl, commitBody), 'Content-Type': 'application/json'},
        body: commitBody, signal: AbortSignal.timeout(20000)});
      const commit = await committed.json();
      if (!committed.ok || commit.ResponseMetadata?.Error) throw Error('upload commit rejected');
      const result = commit.Result?.Results?.[0];
      if (kind === 'image' && result?.UriStatus !== 2000) throw Error('image commit unconfirmed');
      const storageId = kind === 'image' ? result?.Uri : result?.Vid;
      if (typeof storageId !== 'string' || !storageId) throw Error('upload identity missing');
      return {storage_id: storageId};
    }, {kind: command.kind, localUrl});
  } finally {
    await page.unroute(localUrl);
  }
}

async function submit(page, command) {
  const profile = command.profile;
  const params = command.video_params;
  const materials = command.materials;
  const inputVideoMillis = materials.filter(x => x.kind === 'video')
    .reduce((sum, item) => sum + item.duration_millis, 0);
  if (profile.benefit_amount !== profile.duration_seconds + Math.round(inputVideoMillis / 1000)) {
    throw Error('sealed native benefit amount differs from material duration');
  }
  const kinds = ['image', 'video', 'audio'].filter(kind => materials.some(x => x.kind === kind));
  const action = {scene: 'video.generate', source: 'canvas_generation', options: {
    model: 'seedance_2.5', resolution: profile.resolution,
    durationSeconds: profile.duration_seconds, outputCount: 1,
    videoMode: 'multi_modal', hasInputVideo: inputVideoMillis > 0,
    isLongVideo: false, materialTypes: kinds,
    benefitAmount: profile.benefit_amount,
    chargeInputVideoDuration: inputVideoMillis > 0,
    inputVideoDuration: Math.round(inputVideoMillis / 1000),
  }};
  let admitted = false;
  let ids;
  const admissionName = '__aiVideoJimengAdmit_' + crypto.randomUUID().replaceAll('-', '');
  const resultName = '__aiVideoJimengResult_' + crypto.randomUUID().replaceAll('-', '');
  await page.exposeFunction(admissionName, async value => {
    if (admitted) throw Error('duplicate native dispatch');
    admitted = true;
    ids = value;
    emit({event: 'dispatch', submit_id: value.submit_id, resource_id: value.resource_id});
    const approval = await nextLine();
    if (approval.approved !== true) throw Error('durable admission rejected');
    return true;
  });
  const expectedHash = sha(canon(params));
  let dispatched = false;
  const routePattern = '**/octo_api/v1/node_generate';
  const routeHandler = async route => {
    const request = route.request();
    try {
      const body = request.postDataJSON();
      if (body.initial?.node_id !== profile.node_id) {
        await route.continue();
        return;
      }
      if (dispatched || !admitted || !ids || request.method() !== 'POST' ||
          body.project_id !== profile.project_id ||
          body.initial.node_id !== profile.node_id ||
          body.initial?.submit_id !== ids.submit_id ||
          body.initial?.items?.length !== 1 ||
          body.initial.items[0].resource_id !== ids.resource_id ||
          sha(canon(body.initial.items[0].params?.video_params)) !== expectedHash) {
        throw Error('network identity mismatch');
      }
      dispatched = true;
      await route.continue();
    } catch (_) {
      await route.abort('blockedbyclient');
    }
  };
  await page.route(routePattern, routeHandler);
  try {
    await page.evaluate(({profile, params, action, inputVideoMillis, admissionName, resultName}) => {
      const locate = () => {
        let canvas, client, uid, http;
        for (const element of document.querySelectorAll('span')) {
          let fiber = element[Object.keys(element).find(key => key.startsWith('__reactFiber$'))];
          for (let i = 0; fiber && i < 240; i++, fiber = fiber.return) {
            const value = fiber.memoizedProps?.value;
            if (value?.generationRuntime && value?.controller) canvas = value;
            if (typeof value?.client?.quoteActions === 'function') client = value.client;
            if (value?.endpoints?.http?.postEnvelope) http = value.endpoints.http;
            if (value && typeof value === 'object' && Object.keys(value).length === 1 && value.uid) uid = String(value.uid);
          }
          if (canvas && client && http && uid) break;
        }
        if (!canvas || !client || !http || !uid) throw Error('native owner unavailable');
        return {canvas, client, http, uid};
      };
      const {canvas, client, http} = locate();
      const quote = client.quoteActions([{id: 'ai-video-jimeng', action}]);
      const state = client.getActionState(action);
      const balance = client.getSnapshot().data?.localCredit;
      const validQuote = value => Number.isSafeInteger(value) && value > 0 &&
        value <= profile.credit_upper_bound;
      if (quote.status !== 'available' || state.status !== 'allowed' ||
          !validQuote(quote.credits) || quote.credits !== state.quote?.credits ||
          !Number.isSafeInteger(balance) || balance < quote.credits) {
        throw Error('native quote or balance rejected');
      }
      if (canvas.generationRuntime.videoGenerationConfigStore.validate(params).status !== 'valid') {
        throw Error('native parameters rejected');
      }
      const snapshot = canvas.generationRuntime.actions.getVideoSubmissionSnapshot(profile.node_id);
      if (snapshot.state !== 'idle' || snapshot.acceptedResourceIds.length !== 0) {
        throw Error('native node is already submitting');
      }
      const normalize = value => Array.isArray(value) ? value.map(normalize)
        : value && typeof value === 'object'
          ? Object.fromEntries(Object.keys(value).sort().map(key => [key, normalize(value[key])]))
          : value;
      const proto = Object.getPrototypeOf(http);
      const original = proto.postEnvelope;
      if (window.__aiVideoJimengFence) throw Error('native fence already active');
      const fence = {owner: admissionName, used: false, closed: false,
        expires: Date.now() + 120000};
      window.__aiVideoJimengFence = fence;
      fence.restore = () => {
        if (fence.closed) return;
        fence.closed = true;
        if (window.__aiVideoJimengFence === fence) {
          proto.postEnvelope = original;
          window.__aiVideoJimengFence = null;
        }
      };
      setTimeout(() => {
        if (window.__aiVideoJimengFence === fence) fence.restore();
      }, 120000);
      proto.postEnvelope = async function(path, body, options) {
        if (path !== '/octo_api/v1/node_generate') return original.call(this, path, body, options);
        if (body.initial?.node_id !== profile.node_id) return original.call(this, path, body, options);
        if (fence.closed || fence.used || Date.now() >= fence.expires) throw Error('native fence closed');
        fence.used = true;
        const row = body.initial?.items?.[0];
        if (body.project_id !== profile.project_id || body.op !== 1 ||
            body.initial?.node_id !== profile.node_id ||
            body.initial?.items?.length !== 1 || row.type !== 2 ||
            JSON.stringify(normalize(row.params?.video_params)) !== JSON.stringify(normalize(params)) ||
            row.commerce_selection?.benefit_type !== profile.benefit_type ||
            (row.reference_sources?.length || 0) !== 0) throw Error('native request changed');
        const approved = await window[admissionName]({
          submit_id: body.initial.submit_id, resource_id: row.resource_id,
        });
        if (!approved || fence.closed || Date.now() >= fence.expires) throw Error('durable admission unavailable');
        const current = locate().client;
        const fresh = current.quoteActions([{id: 'ai-video-jimeng-fresh', action}]);
        const freshState = current.getActionState(action);
        const freshBalance = current.getSnapshot().data?.localCredit;
        if (fresh.status !== 'available' || !validQuote(fresh.credits) ||
            freshState.status !== 'allowed' ||
            freshState.quote?.credits !== fresh.credits ||
            !Number.isSafeInteger(freshBalance) || freshBalance < fresh.credits) {
          throw Error('native quote changed');
        }
        return original.call(this, path, body, options);
      };
      window[resultName] = {state: 'running'};
      Promise.resolve(canvas.generationRuntime.actions.submitVideo({
        targetId: profile.node_id, outputCount: 1, videoGenParams: params,
        referenceSources: [],
        commerceContext: {hasInputVideo: action.options.hasInputVideo,
          inputVideoDurationMs: inputVideoMillis},
      })).then(value => {
        window[resultName] = {state: 'settled', status: value?.status};
      }, () => {
        window[resultName] = {state: 'error'};
      }).finally(() => {
        fence.restore();
      });
      return true;
    }, {profile, params, action, inputVideoMillis, admissionName, resultName});
    for (let i = 0; i < 120; i++) {
      const result = await page.evaluate(name => window[name], resultName);
      if (result?.state !== 'running') break;
      await page.waitForTimeout(1000);
    }
    if (!admitted || !ids) throw Error('native dispatch was not durably admitted');
    const resource = await readResource(page, profile, ids.resource_id);
    if (resource.submit_id !== ids.submit_id || !/^\d+$/.test(resource.task_id || '')) {
      throw Error('accepted resource identity unavailable');
    }
    return {submit_id: ids.submit_id, resource_id: ids.resource_id, task_id: resource.task_id};
  } finally {
    await page.evaluate(({owner, resultName}) => {
      const fence = window.__aiVideoJimengFence;
      if (fence?.owner === owner) fence.restore();
      delete window[resultName];
    }, {owner: admissionName, resultName}).catch(() => {});
    await page.unroute(routePattern, routeHandler);
  }
}

async function main() {
  const command = await nextLine();
  const {browser, page} = await connect(command);
  try {
    if (command.operation === 'upload') {
      emit({ok: true, ...await upload(page, command)});
    } else if (command.operation === 'read') {
      emit({ok: true, resource: await readResource(page, command.profile, command.resource_id)});
    } else if (command.operation === 'canvas') {
      emit({ok: true, canvas: await readSavedCanvas(page, command.profile, command.resource_id)});
    } else if (command.operation === 'submit') {
      emit({ok: true, ...await submit(page, command)});
    } else {
      throw Error('operation unavailable');
    }
  } finally {
    await browser.close();
  }
}

main().catch(() => {
  emit({ok: false});
  process.exitCode = 1;
});
