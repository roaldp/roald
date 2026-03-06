/* === Roald Companion Dashboard — Frontend Logic === */

const REFRESH_INTERVAL = 10; // seconds
let countdown = REFRESH_INTERVAL;
let refreshTimer = null;

// ── Tab Navigation ──────────────────────────────────────────────

document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    tab.classList.add('active');
    const target = document.getElementById('tab-' + tab.dataset.tab);
    if (target) target.classList.add('active');

    // Load tab-specific data
    if (tab.dataset.tab === 'mind') loadMind();
    if (tab.dataset.tab === 'knowledge') loadKnowledge();
    if (tab.dataset.tab === 'logs') loadLogs();
  });
});

// ── Clock ───────────────────────────────────────────────────────

function updateClock() {
  const el = document.getElementById('clock');
  if (el) el.textContent = new Date().toLocaleTimeString();
}
setInterval(updateClock, 1000);
updateClock();

// ── API Helpers ─────────────────────────────────────────────────

async function fetchJSON(url) {
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('Fetch error:', url, err);
    return null;
  }
}

// ── Escape HTML ─────────────────────────────────────────────────

function esc(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ── Overview Tab ────────────────────────────────────────────────

async function loadStatus() {
  const data = await fetchJSON('/api/status');
  if (!data) return;

  // Status badge
  const badge = document.getElementById('status-badge');
  if (data.locked) {
    badge.textContent = 'Pulsing';
    badge.className = 'badge badge-pulsing';
  } else if (data.running) {
    badge.textContent = 'Running';
    badge.className = 'badge badge-online';
  } else {
    badge.textContent = 'Offline';
    badge.className = 'badge badge-offline';
  }

  // Stats
  const s = data.stats || {};
  setText('stat-total-pulses', s.total_pulses ?? '—');
  setText('stat-full-pulses', s.full_pulses ?? '—');
  setText('stat-reactive-pulses', s.reactive_pulses ?? '—');
  setText('stat-tool-calls', s.tool_calls ?? '—');
  setText('stat-slack-sent', s.slack_messages_sent ?? '—');
  setText('stat-errors', s.errors ?? '—');

  // Status details
  setText('status-process', data.running ? 'Active' : 'Not running');
  setText('status-last-pulse', data.last_pulse || 'No pulses yet');
  setText('status-lock', data.locked ? 'Locked (pulse in progress)' : 'Unlocked');
  setText('status-mind', data.mind_exists ? 'Initialized' : 'Not created');

  // Sources
  renderSources(data.sources || []);

  // Active Context
  renderContentBlock('active-context', data.active_context);

  // Pending Tasks
  renderTasks(data.tasks || []);

  // Inbox
  renderContentBlock('inbox-tracker', data.inbox);

  // Recent Events
  renderEvents(data.events || []);

  // Config tab data
  renderConfig(data.config || {});
  renderContentBlock('next-instructions', data.next_instructions);
  renderContentBlock('preferences', data.preferences);

  // Footer
  document.getElementById('last-updated').textContent =
    'Updated: ' + new Date().toLocaleTimeString();
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function renderSources(sources) {
  const el = document.getElementById('sources-list');
  if (!sources.length) {
    el.innerHTML = '<p class="muted">No sources configured</p>';
    return;
  }
  el.innerHTML = sources.map(s => {
    let cls = 'pending';
    if (s.status === 'active') cls = 'active';
    else if (s.status === 'unavailable') cls = 'unavailable';
    else if (s.status.includes('awaiting')) cls = 'awaiting';
    return `<div class="source-item">
      <span class="source-name">${esc(s.name)}</span>
      <span class="source-status ${cls}">${esc(s.status)}</span>
    </div>`;
  }).join('');
}

function renderTasks(tasks) {
  const el = document.getElementById('pending-tasks');
  if (!tasks.length) {
    el.innerHTML = '<p class="muted">No pending tasks</p>';
    return;
  }
  el.innerHTML = tasks.map(t => `
    <div class="task-item">
      <div class="task-check ${t.done ? 'done' : ''}"></div>
      <span class="task-text ${t.done ? 'done' : ''}">${esc(t.text)}</span>
    </div>
  `).join('');
}

function renderEvents(events) {
  const el = document.getElementById('recent-events');
  if (!events.length) {
    el.innerHTML = '<p class="muted">No recent events</p>';
    return;
  }
  el.innerHTML = events.map(e =>
    `<div class="event-item">${esc(e)}</div>`
  ).join('');
}

function renderContentBlock(id, text) {
  const el = document.getElementById(id);
  if (!el) return;
  const clean = (text || '').trim();
  if (!clean || clean.startsWith('_No ') || clean.startsWith('_Not ')) {
    el.innerHTML = `<p class="muted">${esc(clean || 'Nothing yet')}</p>`;
  } else {
    el.innerHTML = `<div style="white-space:pre-wrap">${esc(clean)}</div>`;
  }
}

// ── Config Tab ──────────────────────────────────────────────────

function renderConfig(config) {
  const el = document.getElementById('config-display');
  if (!config || !Object.keys(config).length) {
    el.innerHTML = '<p class="muted">No configuration loaded</p>';
    return;
  }

  const items = [
    { key: 'Timezone', value: config.timezone || 'UTC' },
    { key: 'Full Pulse Interval', value: (config.full_pulse_interval_minutes || 30) + ' min' },
    { key: 'Slack Poll Interval', value: (config.slack_poll_interval_seconds || 1) + 's' },
    { key: 'Claude Model', value: config.claude_model || 'default' },
    { key: 'Slack User ID', value: config.slack_user_id_set ? 'Set' : 'Not set', cls: config.slack_user_id_set ? 'ok' : 'warn' },
    { key: 'Slack Channel ID', value: config.slack_channel_id_set ? 'Set' : 'Using default (self-DM)', cls: config.slack_channel_id_set ? 'ok' : '' },
  ];

  const sources = config.sources || {};
  Object.entries(sources).forEach(([name, enabled]) => {
    items.push({
      key: 'Source: ' + name,
      value: enabled ? 'Enabled' : 'Disabled',
      cls: enabled ? 'ok' : 'warn',
    });
  });

  el.innerHTML = items.map(i =>
    `<div class="config-item">
      <span class="config-key">${esc(i.key)}</span>
      <span class="config-value ${i.cls || ''}">${esc(i.value)}</span>
    </div>`
  ).join('');
}

// ── Mind Tab ────────────────────────────────────────────────────

async function loadMind() {
  const data = await fetchJSON('/api/mind/raw');
  const el = document.getElementById('mind-raw');
  if (data && data.content) {
    el.textContent = data.content;
  } else {
    el.textContent = 'mind.md not found — companion has not run yet.';
  }
}

document.getElementById('refresh-mind')?.addEventListener('click', loadMind);

// ── Knowledge Tab ───────────────────────────────────────────────

async function loadKnowledge() {
  const data = await fetchJSON('/api/knowledge');
  if (!data) return;

  renderFileList('knowledge-meetings', data.files?.meetings || []);
  renderFileList('knowledge-emails', data.files?.emails || []);
  renderFileList('knowledge-notes', data.files?.notes || []);

  const indexEl = document.getElementById('knowledge-index');
  if (data.index && data.index.length) {
    indexEl.innerHTML = data.index.map(e =>
      `<div class="event-item">${esc(e)}</div>`
    ).join('');
  } else {
    indexEl.innerHTML = '<p class="muted">No knowledge indexed yet</p>';
  }
}

function renderFileList(id, files) {
  const el = document.getElementById(id);
  if (!files.length) {
    el.innerHTML = '<p class="muted">No files yet</p>';
    return;
  }
  el.innerHTML = files.map(f =>
    `<div class="file-item" data-path="${esc(f.name)}" onclick="previewFile('${esc(f.name)}')">
      <span class="file-name">${esc(f.name)}</span>
      <span class="file-meta">${esc(f.modified)}</span>
    </div>`
  ).join('');
}

async function previewFile(name) {
  const card = document.getElementById('knowledge-preview-card');
  const title = document.getElementById('knowledge-preview-title');
  const content = document.getElementById('knowledge-preview');

  card.style.display = 'block';
  title.textContent = name;
  content.textContent = 'Loading...';

  const data = await fetchJSON('/api/knowledge/file?path=' + encodeURIComponent(name));
  if (data && data.content) {
    content.textContent = data.content;
  } else {
    content.textContent = 'Could not load file.';
  }
}

// Make previewFile available globally for onclick
window.previewFile = previewFile;

document.getElementById('close-preview')?.addEventListener('click', () => {
  document.getElementById('knowledge-preview-card').style.display = 'none';
});

// ── Logs Tab ────────────────────────────────────────────────────

async function loadLogs() {
  const lines = document.getElementById('log-lines')?.value || 100;
  const data = await fetchJSON(`/api/logs?lines=${lines}`);
  if (!data || !data.entries) return;

  const el = document.getElementById('log-output');
  el.innerHTML = data.entries.map(e => {
    let msgClass = '';
    const msg = e.message || '';
    if (msg.includes('error') || msg.includes('ERROR')) msgClass = 'error';
    else if (msg.includes('TOOL')) msgClass = 'tool';
    else if (msg.includes('SLACK')) msgClass = 'slack';
    else if (msg.includes('pulse')) msgClass = 'pulse';

    return `<div class="log-line">` +
      (e.timestamp ? `<span class="log-ts">[${esc(e.timestamp)}]</span> ` : '') +
      `<span class="log-msg ${msgClass}">${esc(msg)}</span></div>`;
  }).join('');

  if (document.getElementById('log-autoscroll')?.checked) {
    el.scrollTop = el.scrollHeight;
  }
}

document.getElementById('refresh-logs')?.addEventListener('click', loadLogs);
document.getElementById('log-lines')?.addEventListener('change', loadLogs);

// ── Auto-Refresh ────────────────────────────────────────────────

function startRefreshCycle() {
  countdown = REFRESH_INTERVAL;
  updateCountdown();

  if (refreshTimer) clearInterval(refreshTimer);
  refreshTimer = setInterval(() => {
    countdown--;
    updateCountdown();
    if (countdown <= 0) {
      loadStatus();
      // Reload active tab data
      const activeTab = document.querySelector('.tab.active');
      if (activeTab) {
        if (activeTab.dataset.tab === 'logs') loadLogs();
        if (activeTab.dataset.tab === 'mind') loadMind();
        if (activeTab.dataset.tab === 'knowledge') loadKnowledge();
      }
      countdown = REFRESH_INTERVAL;
    }
  }, 1000);
}

function updateCountdown() {
  const el = document.getElementById('refresh-countdown');
  if (el) el.textContent = countdown;
}

// ── Init ────────────────────────────────────────────────────────

loadStatus();
startRefreshCycle();
