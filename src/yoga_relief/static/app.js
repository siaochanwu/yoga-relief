'use strict';

// ---- 常數與狀態 ----
const LABELS = {
  severity: { mild: '輕微', moderate: '中等', severe: '嚴重' },
  duration: { today: '今天才開始', days: '幾天', week_plus: '一週以上', month_plus: '一個月以上' },
  cause: { sedentary: '久坐久站', exertion: '運動或勞動後', sleep: '睡姿或落枕', injury: '受傷或跌倒', unknown: '不確定' },
};
const QUESTIONS = [
  { key: 'severity', title: '疼痛程度' },
  { key: 'duration', title: '持續多久' },
  { key: 'cause', title: '可能原因' },
];
const GENERIC_SUMMARY = '以下是常用於緩解此部位不適的動作，請依自身狀況量力而為。';

const state = {
  view: 'front',
  part: null,          // body part id
  partName: '',
  answers: { severity: null, duration: null, cause: null },
  result: null,        // /api/advice 的回應
  bodyParts: [],
};

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

// ---- 畫面切換 ----
function showScreen(name) {
  $$('.screen').forEach((el) => el.classList.toggle('hidden', el.id !== `screen-${name}`));
  hideError();
  window.scrollTo(0, 0);
}
function showError(msg) { const el = $('#error'); el.textContent = msg; el.classList.remove('hidden'); }
function hideError() { $('#error').classList.add('hidden'); }

// ---- 選部位 ----
async function loadBodyMap() {
  const [partsRes, svgRes] = await Promise.all([fetch('/api/body-parts'), fetch('/static/body.svg')]);
  if (!partsRes.ok || !svgRes.ok) throw new Error('load failed');
  state.bodyParts = await partsRes.json();
  // body.svg 是我們自己的同源靜態檔，不是使用者輸入，所以直接注入是安全的
  $('#body-map').innerHTML = await svgRes.text();
  $$('#body-map .part').forEach((el) => el.addEventListener('click', () => selectPart(el.dataset.part)));
  setView(state.view);
}

function setView(view) {
  state.view = view;
  $$('.tab').forEach((t) => t.classList.toggle('active', t.dataset.view === view));
  $('#view-front').classList.toggle('hidden', view !== 'front');
  $('#view-back').classList.toggle('hidden', view !== 'back');
}

function selectPart(id) {
  state.part = id;
  const part = state.bodyParts.find((p) => p.id === id);
  state.partName = part ? part.name_zh : id;
  $$('#body-map .part').forEach((el) => el.classList.toggle('selected', el.dataset.part === id));
  $('#selected-name').textContent = state.partName;
  $('#btn-next').disabled = false;
}

function resetSelection() {
  state.part = null;
  state.partName = '';
  state.answers = { severity: null, duration: null, cause: null };
  state.result = null;
  $$('#body-map .part').forEach((el) => el.classList.remove('selected'));
  $('#selected-name').textContent = '尚未選擇';
  $('#btn-next').disabled = true;
}

// ---- 問卷 ----
function renderQuestions() {
  $('#q-title').textContent = `${state.partName}：告訴我們一些狀況`;
  const container = $('#questions');
  container.innerHTML = '';
  for (const q of QUESTIONS) {
    const block = document.createElement('div');
    block.className = 'question';
    const title = document.createElement('p');
    title.textContent = q.title;
    block.appendChild(title);
    const options = document.createElement('div');
    options.className = 'options';
    for (const [value, label] of Object.entries(LABELS[q.key])) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'option' + (state.answers[q.key] === value ? ' selected' : '');
      btn.textContent = label;
      btn.addEventListener('click', () => {
        state.answers[q.key] = value;
        options.querySelectorAll('.option').forEach((o) => o.classList.toggle('selected', o === btn));
        updateSubmitState();
      });
      options.appendChild(btn);
    }
    block.appendChild(options);
    container.appendChild(block);
  }
  updateSubmitState();
}

function updateSubmitState() {
  const done = QUESTIONS.every((q) => state.answers[q.key] !== null);
  $('#btn-submit').disabled = !done;
}

async function submitAnswers() {
  const payload = { body_part: state.part, ...state.answers };
  $('#btn-submit').disabled = true;
  try {
    const res = await fetch('/api/advice', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    state.result = await res.json();
    saveHistory(payload, state.result);
    renderResult(state.result);
    showScreen('result');
  } catch (e) {
    showError('暫時無法取得資料，請稍後再試。');
  } finally {
    updateSubmitState();
  }
}

// ---- 結果 ----
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderResult(res) {
  const root = $('#result');
  root.innerHTML = '';
  root.appendChild(el('h2', null, `${res.body_part.name_zh}的緩解動作`));

  if (res.seek_medical) {
    root.appendChild(el('div', 'banner',
      '你的狀況建議先由醫師或物理治療師評估。以下只列出最溫和的動作，若做了更痛請立即停止。'));
  }
  root.appendChild(el('div', 'summary', res.advice ? res.advice.summary : GENERIC_SUMMARY));

  res.poses.forEach((pose, index) => {
    const card = el('div', 'card');
    card.appendChild(el('h3', null, `${index + 1}. ${pose.name_zh}`));
    card.appendChild(el('div', 'en', pose.name_en));
    if (pose.image) {
      const img = document.createElement('img');
      img.className = 'pose-image';
      img.src = pose.image;
      img.alt = `${pose.name_zh}示意圖`;
      img.loading = 'lazy';
      img.addEventListener('error', () => img.remove());   // 圖缺了就拿掉，版面不破
      card.appendChild(img);
    }
    card.appendChild(el('div', 'duration', `建議時長：${pose.duration}`));

    const steps = el('ol');
    pose.steps.forEach((s) => steps.appendChild(el('li', null, s)));
    card.appendChild(steps);

    const cautions = [...pose.cautions, ...pose.contraindications.map((c) => `避免：${c}`)];
    if (cautions.length) {
      const ul = el('ul', 'caution');
      cautions.forEach((c) => ul.appendChild(el('li', null, c)));
      card.appendChild(ul);
    }
    if (pose.why) card.appendChild(el('div', 'why', `為什麼適合你：${pose.why}`));
    root.appendChild(card);
  });
}

// ---- 紀錄（localStorage）----
const HISTORY_KEY = 'yoga_relief_history';
const HISTORY_MAX = 20;

function isValidEntry(item) {
  // 半壞的資料（null、數字、缺 result、poses 不是陣列）直接丟掉，不讓一筆壞資料拖垮整頁
  return !!item && typeof item === 'object'
    && typeof item.ts === 'string'
    && !!item.result && typeof item.result === 'object'
    && Array.isArray(item.result.poses)
    && !!item.result.body_part;
}

function safeParse(text) {
  try {
    const data = JSON.parse(text);
    return Array.isArray(data) ? data.filter(isValidEntry) : [];
  } catch (e) {
    return [];
  }
}

function loadHistory() {
  try {
    return safeParse(localStorage.getItem(HISTORY_KEY) || '[]');
  } catch (e) {          // localStorage 被封鎖（隱私模式等）
    return [];
  }
}

function saveHistory(payload, result) {
  const entry = {
    ts: new Date().toISOString(),
    body_part: payload.body_part,
    body_part_name: result.body_part.name_zh,
    severity: payload.severity,
    duration: payload.duration,
    cause: payload.cause,
    result,
  };
  try {
    const list = [entry, ...loadHistory()].slice(0, HISTORY_MAX);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(list));
  } catch (e) {          // 配額滿或被封鎖：不記錄，功能照常
  }
}

function formatTs(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}/${pad(d.getMonth() + 1)}/${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function renderHistory() {
  const ul = $('#history-list');
  ul.innerHTML = '';
  const list = loadHistory();
  $('#btn-clear-history').classList.toggle('hidden', list.length === 0);
  if (list.length === 0) {
    ul.appendChild(el('li', 'history-empty', '還沒有紀錄。'));
    return;
  }
  for (const item of list) {
    const li = el('li');
    li.appendChild(el('div', 'ts', formatTs(item.ts)));
    li.appendChild(el('div', null,
      `${item.body_part_name || item.result.body_part.name_zh || item.body_part}・${LABELS.severity[item.severity] || item.severity || ''}`));
    li.addEventListener('click', () => {
      try {
        state.result = item.result;
        renderResult(item.result);
        showScreen('result');
      } catch (e) {
        showError('這筆紀錄無法顯示，請重新查詢。');
      }
    });
    ul.appendChild(li);
  }
}

function clearHistory() {
  if (!confirm('確定要清除全部紀錄？')) return;
  try { localStorage.removeItem(HISTORY_KEY); } catch (e) {}
  renderHistory();
}

// ---- 事件綁定與啟動 ----
function bindEvents() {
  $$('.tab').forEach((t) => t.addEventListener('click', () => setView(t.dataset.view)));
  $('#btn-next').addEventListener('click', () => { renderQuestions(); showScreen('questions'); });
  $('#btn-back-select').addEventListener('click', () => showScreen('select'));
  $('#btn-submit').addEventListener('click', submitAnswers);
  $('#btn-restart').addEventListener('click', () => { resetSelection(); showScreen('select'); });
  $('#btn-home').addEventListener('click', () => showScreen('select'));
  $('#btn-history').addEventListener('click', () => { renderHistory(); showScreen('history'); });
  $('#btn-clear-history').addEventListener('click', clearHistory);
}

async function init() {
  bindEvents();
  try {
    await loadBodyMap();
  } catch (e) {
    showError('暫時無法取得資料，請稍後再試。');
    const retry = document.createElement('button');
    retry.className = 'btn';
    retry.textContent = '重試';
    retry.addEventListener('click', () => location.reload());
    $('#error').appendChild(retry);
  }
}

document.addEventListener('DOMContentLoaded', init);
