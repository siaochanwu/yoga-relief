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

// ---- 問卷（Task 11 實作）----
function renderQuestions() {}
async function submitAnswers() {}

// ---- 結果（Task 11 實作）----
function renderResult(res) {}

// ---- 紀錄（Task 12 實作）----
function renderHistory() {}
function clearHistory() {}

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
