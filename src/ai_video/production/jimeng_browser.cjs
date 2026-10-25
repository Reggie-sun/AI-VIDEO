// Jimeng's logged-in canvas owns credentials and the native commercial action.
// The host sends only bounded task data. This worker never prints session data.
'use strict';

const fs = require('node:fs');
const crypto = require('node:crypto');
const readline = require('node:readline');

let lines;
const nextLine = async () => {
  lines ??= readline.createInterface({input: process.stdin, crlfDelay: Infinity})[Symbol.asyncIterator]();
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
let nativeStarted = false;
let dispatchAnnounced = false;

// This function is serialized into the page, including its lexical helpers.
// Retain owners for ONE operation, then compare them with fresh React context.
function createSession(profile) {
  function locate() {
    if (location.href !== 'https://jimeng.jianying.com/ai-tool/ai-canvas/' + profile.project_id) {
      throw Error('canvas navigation changed');
    }
    const canvases = new Set(), clients = new Set(), accounts = new Set(), transports = new Set();
    const visited = new Set();
    for (const element of document.querySelectorAll('*')) {
      let fiber = element[Object.keys(element).find(key => key.startsWith('__reactFiber$'))];
      for (let i = 0; fiber && i < 240 && !visited.has(fiber); i++, fiber = fiber.return) {
        visited.add(fiber);
        const value = fiber.memoizedProps?.value;
        if (value?.generationRuntime && value?.controller && value.actions?.projectId === profile.project_id) canvases.add(value);
        if (typeof value?.client?.quoteActions === 'function') clients.add(value.client);
        if (value?.endpoints?.http?.postEnvelope) transports.add(value.endpoints.http);
        if (value && typeof value === 'object' && Object.keys(value).length === 1 && value.uid) accounts.add(String(value.uid));
      }
    }
    if (canvases.size !== 1 || accounts.size !== 1 || clients.size > 1 || transports.size > 1) {
      throw Error('native owner missing or ambiguous');
    }
    return {canvas: [...canvases][0], client: [...clients][0], http: [...transports][0], uid: [...accounts][0]};
  }
  const initial = locate();
  return {
    async check() {
      const current = locate();
      if (Object.keys(initial).some(key => initial[key] !== current[key])) throw Error('native owner changed');
      const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(current.uid));
      const digest = [...new Uint8Array(bytes)].map(x => x.toString(16).padStart(2, '0')).join('');
      // Hashing yields to the page. Recheck before returning any authority.
      const fresh = locate();
      if (digest !== profile.account_sha256 || Object.keys(current).some(key => current[key] !== fresh[key])) {
        throw Error('logged-in account or native owner changed');
      }
      return current;
    },
    claim(owner) {
      if (window.__aiVideoJimengFence) throw Error('native fence already active');
      const fence = {owner, used: false, closed: false, pending: false, expires: Date.now() + 120000};
      fence.release = () => {
        if (fence.pending) return; // Late native continuations must still hit a closed fence.
        clearTimeout(fence.timer);
        if (fence.proto && fence.proto.postEnvelope === fence.wrapper) fence.proto.postEnvelope = fence.original;
        if (fence.fetchWrapper && window.fetch === fence.fetchWrapper) window.fetch = fence.originalFetch;
        if (window.__aiVideoJimengFence === fence) window.__aiVideoJimengFence = null;
      };
      fence.close = () => {fence.closed = true; fence.release();};
      fence.timer = setTimeout(fence.close, 120000);
      window.__aiVideoJimengFence = fence;
    },
  };
}

async function connect(command) {
  const {chromium} = require(command.playwright_module);
  const port = fs.readFileSync(command.profile_dir + '/DevToolsActivePort', 'utf8').split('\n')[0];
  if (!/^[0-9]{2,5}$/.test(port)) throw Error('browser endpoint unavailable');
  const browser = await chromium.connectOverCDP('http://127.0.0.1:' + port);
  const target = origin + '/ai-tool/ai-canvas/' + command.profile.project_id;
  try {
    const pages = browser.contexts().flatMap(context => context.pages()).filter(p => p.url() === target);
    if (pages.length !== 1) throw Error('exact logged-in canvas missing or ambiguous');
    const page = pages[0];
    const session = await page.evaluateHandle(createSession, command.profile);
    await session.evaluate(value => value.check());
    return {browser, page, session};
  } catch (error) {
    await browser.close().catch(() => {});
    throw error;
  }
}

async function readResource(page, profile, resourceId, session) {
  return page.evaluate(async ({projectId, resourceId, session}) => {
    await session.check();
    const response = await fetch('/octo_api/v1/resource/batch_get', {
      method: 'POST', credentials: 'include', redirect: 'error',
      headers: {'content-type': 'application/json'},
      body: JSON.stringify({project_id: projectId, resource_ids: [resourceId]}),
      signal: AbortSignal.timeout(20000),
    });
    const payload = await response.json();
    await session.check();
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
  }, {projectId: profile.project_id, resourceId, session});
}

async function readSavedCanvas(page, profile, resourceId, session) {
  for (let attempt = 0; attempt < 7; attempt++) {
    const result = await page.evaluate(async ({projectId, nodeId, resourceId, session}) => {
      await session.check();
      const response = await fetch('/octo_api/v1/project/draft/get', {
        method: 'POST', credentials: 'include', redirect: 'error',
        headers: {'content-type': 'application/json'},
        body: JSON.stringify({project_id: projectId}),
        signal: AbortSignal.timeout(20000),
      });
      const payload = await response.json();
      await session.check();
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
    }, {projectId: profile.project_id, nodeId: profile.node_id, resourceId, session});
    if (result.saved) return result;
    if (attempt < 6) await page.waitForTimeout(5000);
  }
  throw Error('submitted resource is not in server-saved canvas draft');
}

async function upload(page, command, session) {
  const bytes = fs.readFileSync(command.file);
  if (sha(bytes) !== command.sha256) throw Error('reference bytes changed');
  const localUrl = origin + '/__ai_video_jimeng_ref__/' + crypto.randomUUID();
  await page.route(localUrl, route => route.fulfill({
    status: 200, contentType: command.mime_type, body: bytes,
  }));
  try {
    return await page.evaluate(async ({kind, localUrl, session}) => {
      await session.check();
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
        await session.check();
        const response = await fetch(path, {method: 'POST', credentials: 'include', redirect: 'error',
          headers: {'content-type': 'application/json'}, body: JSON.stringify(body),
          signal: AbortSignal.timeout(20000)});
        const data = await response.json();
        await session.check();
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
      await session.check();
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
      await session.check();
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
      await session.check();
      const committed = await fetch(commitUrl, {method: 'POST', credentials: 'omit', redirect: 'error',
        headers: {...await sign('POST', commitUrl, commitBody), 'Content-Type': 'application/json'},
        body: commitBody, signal: AbortSignal.timeout(20000)});
      const commit = await committed.json();
      if (!committed.ok || commit.ResponseMetadata?.Error) throw Error('upload commit rejected');
      const result = commit.Result?.Results?.[0];
      if (kind === 'image' && result?.UriStatus !== 2000) throw Error('image commit unconfirmed');
      const storageId = kind === 'image' ? result?.Uri : result?.Vid;
      if (typeof storageId !== 'string' || !storageId) throw Error('upload identity missing');
      await session.check();
      return {storage_id: storageId};
    }, {kind: command.kind, localUrl, session});
  } finally {
    await page.unroute(localUrl);
  }
}

function buildVideoAction(profile, materials) {
  if (!['seedance_2.5', 'seedance_2.0_mini', 'seedance_2.0_vip',
        'seedance_2.0_fast_vip'].includes(profile.model_id)) {
    throw Error('unsupported Jimeng model');
  }
  const inputMode = profile.input_mode || 'multimodal';
  const videoMode = {multimodal:'multi_modal',first_frame:'i2v',first_last_frame:'first_last_frame'}[inputMode];
  if (!videoMode) throw Error('unsupported Jimeng input mode');
  if (inputMode !== 'multimodal') {
    const roles = inputMode === 'first_frame' ? ['first_frame'] : ['first_frame','last_frame'];
    if (profile.model_id !== 'seedance_2.0_vip' || materials.length !== roles.length ||
        materials.some((item, index) => item.kind !== 'image' || item.image_role !== roles[index])) {
      throw Error('native frame conditioning differs from the sealed endpoint roles');
    }
  } else if (materials.some(item => item.image_role != null)) {
    throw Error('frame roles cannot use the multimodal commercial action');
  }
  const inputVideoMillis = materials.filter(x => x.kind === 'video')
    .reduce((sum, item) => sum + item.duration_millis, 0);
  if (profile.benefit_amount !== profile.duration_seconds + Math.round(inputVideoMillis / 1000)) {
    throw Error('sealed native benefit amount differs from material duration');
  }
  const kinds = ['image', 'video', 'audio'].filter(kind => materials.some(x => x.kind === kind));
  return {scene: 'video.generate', source: 'canvas_generation', options: {
    model: profile.model_id, resolution: profile.resolution,
    durationSeconds: profile.duration_seconds, outputCount: 1,
    videoMode, hasInputVideo: inputVideoMillis > 0,
    isLongVideo: false, materialTypes: kinds,
    ...(inputVideoMillis > 0 ? {
      benefitAmount: profile.benefit_amount,
      chargeInputVideoDuration: true,
      inputVideoDuration: Math.round(inputVideoMillis / 1000),
    } : {}),
  }};
}

function buildVideoCommerceContext(action, inputVideoMillis) {
  return {hasInputVideo: action.options.hasInputVideo,
    ...(action.options.hasInputVideo ? {inputVideoDurationMs: inputVideoMillis} : {})};
}

function buildVideoEditorDraft(previous, params) {
  if (previous && previous.kind !== 'video') throw Error('native editor kind changed');
  return {...previous, kind: 'video', parts: previous?.parts || [],
    references: previous?.references || [], outputCount: 1,
    contentSettings: {...previous?.contentSettings,
      mode: params.mode === 2 || params.mode === 3 ? 'firstLastFrame' : 'multiModal',
      modelName: params.model_name, aspectRatio: params.aspect_ratio,
      resolution: params.resolution, durationSeconds: params.duration_ms / 1000,
      isLongVideo: false}};
}

// Native commercial execution selects a benefit but can omit its optional
// server quote precondition. Bind our fresh bounded quote before admission;
// never replace a supplied precondition or change generation parameters.
function createVideoQuoteBinder() {
  return (body, profile, credits) => {
    const row = body.initial?.items?.[0];
    if (body.initial?.items?.length !== 1 ||
        row.commerce_selection?.benefit_type !== profile.benefit_type ||
        !Number.isSafeInteger(credits) || credits <= 0 || credits > profile.credit_upper_bound ||
        !Number.isSafeInteger(profile.benefit_amount) || profile.benefit_amount <= 0) {
      throw Error('native quote binding rejected');
    }
    const expected = {expected_benefit_amount: profile.benefit_amount,
      expected_credits_amount: credits};
    const supplied = row.commerce_selection.quote_precondition;
    if (supplied !== undefined && (supplied === null ||
        Object.keys(supplied).length !== 2 ||
        supplied.expected_benefit_amount !== expected.expected_benefit_amount ||
        supplied.expected_credits_amount !== expected.expected_credits_amount)) {
      throw Error('native quote precondition changed');
    }
    return {...body, initial: {...body.initial, items: [{...row,
      commerce_selection: {...row.commerce_selection, quote_precondition: expected}}]}};
  };
}

async function syncVideoEditor(page, profile, params, session) {
  const previousDraft = await page.evaluate(async ({profile, session}) => {
    const {canvas} = await session.check();
    const node = canvas.mutableFeaturesApi.canvas.getObjectSnapshot(profile.node_id);
    if (node?.type !== 'video') throw Error('native editor node unavailable');
    return node.data.generationDraft || null;
  }, {profile, session});
  const editorDraft = buildVideoEditorDraft(previousDraft, params);
  await page.evaluate(async ({profile, params, previousDraft, editorDraft, session}) => {
    const {canvas} = await session.check();
    if (!canvas || canvas.generationRuntime.videoGenerationConfigStore.validate(params).status !== 'valid') {
      throw Error('native editor or parameters unavailable');
    }
    function normalize(value) {
      return Array.isArray(value) ? value.map(normalize)
        : value && typeof value === 'object'
          ? Object.fromEntries(Object.keys(value).sort().map(key => [key, normalize(value[key])]))
          : value;
    }
    const api = canvas.mutableFeaturesApi.canvas;
    const canCommit = () => {
      const node = api.getObjectSnapshot(profile.node_id);
      const current = canvas.generationRuntime.actions.getVideoSubmissionSnapshot(profile.node_id);
      return node?.type === 'video' && !node.data.resourceId &&
        !(node.data.resourceBatches || []).some(batch => batch.resourceIds.length) &&
        current.state === 'idle' && current.acceptedResourceIds.length === 0 &&
        JSON.stringify(normalize(node.data.generationDraft || null)) === JSON.stringify(normalize(previousDraft));
    };
    if (!canCommit()) throw Error('native editor changed before synchronization');
    const written = await api.actions.setNodeGenerationDraft.execute(
      profile.node_id, editorDraft, {canCommit, merge: false});
    if (!written.ok || JSON.stringify(normalize(api.getObjectSnapshot(profile.node_id)?.data.generationDraft))
        !== JSON.stringify(normalize(editorDraft))) throw Error('native editor synchronization unconfirmed');
  }, {profile, params, previousDraft, editorDraft, session});
  return editorDraft;
}

async function submit(page, command, session) {
  const profile = command.profile;
  const params = command.video_params;
  const materials = command.materials;
  const inputVideoMillis = materials.filter(x => x.kind === 'video')
    .reduce((sum, item) => sum + item.duration_millis, 0);
  const action = buildVideoAction(profile, materials);
  const commerceContext = buildVideoCommerceContext(action, inputVideoMillis);
  let admitted = false;
  let ids;
  let approvedCredits;
  const admissionName = '__aiVideoJimengAdmit_' + crypto.randomUUID().replaceAll('-', '');
  const resultName = '__aiVideoJimengResult_' + crypto.randomUUID().replaceAll('-', '');
  await session.evaluate(async (value, owner) => {await value.check(); value.claim(owner);}, admissionName);
  let admissionBinding, routed = false, routeHandler;
  let quoteBinder;
  const routePattern = '**/octo_api/v1/node_generate{,?*}';
  try {
    const editorDraft = await syncVideoEditor(page, profile, params, session);
    quoteBinder = await page.evaluateHandle(createVideoQuoteBinder);
    admissionBinding = await page.exposeFunction(admissionName, async value => {
      if (admitted) throw Error('duplicate native dispatch');
      admitted = true;
      ids = value;
    approvedCredits = value.quote_credits;
      dispatchAnnounced = true;
      emit({event: 'dispatch', submit_id: value.submit_id, resource_id: value.resource_id});
      const approval = await nextLine();
      if (approval.approved !== true) throw Error('durable admission rejected');
      return true;
    });
    if (typeof admissionBinding?.dispose !== 'function') throw Error('Playwright disposable binding unavailable');
    const expectedHash = sha(canon(params));
    let dispatched = false;
    routeHandler = async route => {
      const request = route.request();
      try {
        const body = request.postDataJSON();
        if (body.initial?.node_id !== profile.node_id) {
          await route.continue();
          return;
        }
        await session.evaluate(value => value.check());
        const fence = await page.evaluate(owner => {
          const value = window.__aiVideoJimengFence;
          return value?.owner === owner && !value.closed && Date.now() < value.expires;
        }, admissionName);
        if (!fence || dispatched || !admitted || !ids || request.method() !== 'POST' ||
            body.project_id !== profile.project_id || body.op !== 1 ||
            body.initial.items?.[0]?.type !== 2 ||
            body.initial.items?.[0]?.commerce_selection?.benefit_type !== profile.benefit_type ||
          body.initial.items?.[0]?.commerce_selection?.quote_precondition?.expected_benefit_amount !== profile.benefit_amount ||
          body.initial.items?.[0]?.commerce_selection?.quote_precondition?.expected_credits_amount !== approvedCredits ||
          !Number.isSafeInteger(approvedCredits) || approvedCredits <= 0 || approvedCredits > profile.credit_upper_bound ||
            (body.initial.items?.[0]?.reference_sources?.length || 0) !== 0 ||
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
    routed = true;
    nativeStarted = true;
    await page.evaluate(async ({profile, params, action, commerceContext, editorDraft, admissionName, resultName, session, quoteBinder}) => {
      const {canvas, client, http} = await session.check();
      if (!client || !http) throw Error('native commercial owner unavailable');
      const fence = window.__aiVideoJimengFence;
      if (!fence || fence.owner !== admissionName || fence.closed) throw Error('native lease changed');
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
      function normalize(value) {
        return Array.isArray(value) ? value.map(normalize)
          : value && typeof value === 'object'
            ? Object.fromEntries(Object.keys(value).sort().map(key => [key, normalize(value[key])]))
            : value;
      }
      const editorMatches = () => JSON.stringify(normalize(
        canvas.mutableFeaturesApi.canvas.getObjectSnapshot(profile.node_id)?.data.generationDraft))
          === JSON.stringify(normalize(editorDraft));
      if (!editorMatches()) throw Error('native editor changed after synchronization');
      const proto = Object.getPrototypeOf(http);
      const original = proto.postEnvelope;
      fence.proto = proto;
      fence.original = original;
      // The current native HTTP client calls the page's fetch. Keep the
      // one-request guard there too: a dead CDP client loses its routes, and
      // a replacement HTTP owner must not bypass durable admission.
      fence.originalFetch = window.fetch;
      fence.fetchWrapper = async function(input, init = {}) {
        const url = new URL(input?.url ?? String(input), location.href);
        if (url.origin !== location.origin || url.pathname !== '/octo_api/v1/node_generate') {
          return fence.originalFetch.call(this, input, init);
        }
        const raw = typeof init.body === 'string' ? init.body : await input.clone().text();
        const body = JSON.parse(raw);
        const target = body.initial?.node_id ?? body.retry?.node_id ?? body.detached?.source_node_id ?? body.post_edit?.source_node_id;
        if (target && target !== profile.node_id) return fence.originalFetch.call(this, input, init);
        await session.check();
        if (fence.closed || fence.wireUsed || Date.now() >= fence.expires ||
            (init.method || input.method) !== 'POST' ||
            !fence.approvedBody || JSON.stringify(normalize(body)) !== fence.approvedBody) {
          throw Error('native network fence rejected');
        }
        fence.wireUsed = true;
        return fence.originalFetch.call(this, input, init);
      };
      window.fetch = fence.fetchWrapper;
      fence.wrapper = async function(path, body, options) {
        if (path !== '/octo_api/v1/node_generate') return original.call(this, path, body, options);
        if (body.initial?.node_id !== profile.node_id) return original.call(this, path, body, options);
        if (fence.closed || fence.used || Date.now() >= fence.expires) throw Error('native fence closed');
        fence.used = true;
        await session.check();
        if (!editorMatches()) throw Error('native editor changed before dispatch');
        body = quoteBinder(body, profile, quote.credits);
        const row = body.initial?.items?.[0];
        if (body.project_id !== profile.project_id || body.op !== 1 ||
            body.initial?.node_id !== profile.node_id ||
            body.initial?.items?.length !== 1 || row.type !== 2 ||
            JSON.stringify(normalize(row.params?.video_params)) !== JSON.stringify(normalize(params)) ||
            row.commerce_selection?.benefit_type !== profile.benefit_type ||
            row.commerce_selection?.quote_precondition?.expected_benefit_amount !== profile.benefit_amount ||
            (row.reference_sources?.length || 0) !== 0) throw Error('native request changed');
        const approved = await window[admissionName]({
          submit_id: body.initial.submit_id, resource_id: row.resource_id,
          quote_credits: row.commerce_selection.quote_precondition?.expected_credits_amount,
        });
        if (!approved || fence.closed || Date.now() >= fence.expires) throw Error('durable admission unavailable');
        const freshOwners = await session.check();
        if (freshOwners.http !== http || proto.postEnvelope !== fence.wrapper || !editorMatches()) throw Error('native owner changed before send');
        const current = freshOwners.client;
        const fresh = current.quoteActions([{id: 'ai-video-jimeng-fresh', action}]);
        const freshState = current.getActionState(action);
        const freshBalance = current.getSnapshot().data?.localCredit;
        if (fresh.status !== 'available' || !validQuote(fresh.credits) ||
            freshState.status !== 'allowed' ||
            freshState.quote?.credits !== fresh.credits ||
            row.commerce_selection.quote_precondition?.expected_credits_amount !== fresh.credits ||
            !Number.isSafeInteger(freshBalance) || freshBalance < fresh.credits) {
          throw Error('native quote changed');
        }
        if (!editorMatches()) throw Error('native editor changed before transport');
        fence.approvedBody = JSON.stringify(normalize(body));
        return original.call(this, path, body, options);
      };
      proto.postEnvelope = fence.wrapper;
      fence.pending = true;
      window[resultName] = {state: 'running'};
      Promise.resolve().then(() => canvas.generationRuntime.actions.submitVideo({
        targetId: profile.node_id, outputCount: 1, videoGenParams: params,
        referenceSources: [],
        commerceContext,
      })).then(value => {
        window[resultName] = {state: 'settled', status: value?.status};
      }, () => {
        window[resultName] = {state: 'error'};
      }).finally(() => {
        fence.pending = false;
        fence.close();
      });
      return true;
    }, {profile, params, action, commerceContext, editorDraft, admissionName, resultName, session, quoteBinder});
    for (let i = 0; i < 120; i++) {
      const result = await page.evaluate(name => window[name], resultName);
      if (result?.state !== 'running') break;
      await page.waitForTimeout(1000);
    }
    if (!dispatched || !admitted || !ids) throw Error('native dispatch was not durably admitted and sent');
    const resource = await readResource(page, profile, ids.resource_id, session);
    if (resource.submit_id !== ids.submit_id || !/^[0-9]{1,32}$/.test(resource.task_id || '') ||
        sha(canon(resource.video?.gen)) !== expectedHash) {
      throw Error('accepted resource identity unavailable');
    }
    return {submit_id: ids.submit_id, resource_id: ids.resource_id, task_id: resource.task_id};
  } finally {
    await page.evaluate(({owner, resultName}) => {
      const fence = window.__aiVideoJimengFence;
      if (fence?.owner === owner) fence.close();
      delete window[owner];
      delete window[resultName];
    }, {owner: admissionName, resultName}).catch(() => {});
    if (routed) await page.unroute(routePattern, routeHandler);
    if (admissionBinding) await admissionBinding.dispose();
    if (quoteBinder) await quoteBinder.dispose();
  }
}

async function main() {
  const command = await nextLine();
  const {browser, page, session} = await connect(command);
  try {
    if (command.operation === 'upload') {
      emit({ok: true, ...await upload(page, command, session)});
    } else if (command.operation === 'read') {
      emit({ok: true, resource: await readResource(page, command.profile, command.resource_id, session)});
    } else if (command.operation === 'canvas') {
      emit({ok: true, canvas: await readSavedCanvas(page, command.profile, command.resource_id, session)});
    } else if (command.operation === 'submit') {
      emit({ok: true, ...await submit(page, command, session)});
    } else {
      throw Error('operation unavailable');
    }
  } finally {
    await session.dispose().catch(() => {});
    await browser.close();
  }
}

module.exports = {createSession, buildVideoAction, buildVideoCommerceContext, buildVideoEditorDraft, createVideoQuoteBinder, syncVideoEditor};
if (require.main === module) {
  main().catch(() => {
    emit({ok: false, no_effect: !nativeStarted && !dispatchAnnounced});
    process.exitCode = 1;
    process.stdin.destroy();
  });
}
