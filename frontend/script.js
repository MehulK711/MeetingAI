/* ═══════════════════════════════════════════════════════════
   MeetingOS v3 — script.js
   Full backend integration: tasks, analytics, workload,
   timeline, audit log, performance, modal, toast, polling
   ═══════════════════════════════════════════════════════════ */

'use strict';

// ── CONFIG ────────────────────────────────────────────────
const API           = 'http://localhost:8000/api';
const POLL_MS       = 9000;
const TOAST_LIFE_MS = 4200;

// ── STATE ─────────────────────────────────────────────────
const State = {
  tasks:      [],
  logs:       [],
  analytics:  null,
  activeView: 'dashboard',
  activeTask: null,
  sortMode:   'urgency',
  searchQ:    '',
  filterStatus:   '',
  filterPriority: '',
  pollerID:   null,
};

// ── DOM CACHE ─────────────────────────────────────────────
const $ = id => document.getElementById(id);
const $$ = sel => document.querySelectorAll(sel);

// ── BOOT ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  bindNav();
  bindDashboard();
  bindModal();
  bindHistory();
  bindSearch();
  checkHealth();
  loadAll();
  State.pollerID = setInterval(loadAll, POLL_MS);
});

// ── NAVIGATION ────────────────────────────────────────────
function bindNav() {
  $$('.snav-btn').forEach(btn => {
    btn.addEventListener('click', () => switchView(btn.dataset.view));
  });
}

function switchView(view) {
  State.activeView = view;
  $$('.snav-btn').forEach(b => b.classList.toggle('active', b.dataset.view === view));
  $$('.view').forEach(v => v.classList.toggle('active', v.id === 'view-' + view));

  const titles = {
    dashboard:   'Dashboard',
    analytics:   'Analytics',
    workload:    'Workload',
    timeline:    'Timeline',
    history:     'Audit Log',
    performance: 'Performance',
  };
  const crumbs = {
    dashboard:   'Overview · All Tasks',
    analytics:   'Insights · KPIs & Charts',
    workload:    'Team · Owner Assignment',
    timeline:    'Schedule · Deadline View',
    history:     'System · Full Audit Trail',
    performance: 'Team · Completion Metrics',
  };
  $('viewTitle').textContent = titles[view]  || view;
  $('breadcrumb').textContent = crumbs[view] || '';

  // Show/hide topbar filters only on dashboard
  const showFilters = view === 'dashboard';
  $('topbarFilters').style.display = showFilters ? 'flex' : 'none';

  // Render active section
  renderSection(view);
}

function renderSection(view) {
  if (view === 'analytics')   renderAnalytics();
  if (view === 'workload')    renderWorkload();
  if (view === 'timeline')    renderTimeline();
  if (view === 'history')     renderHistory();
  if (view === 'performance') renderPerformance();
}

// ── HEALTH CHECK ──────────────────────────────────────────
async function checkHealth() {
  try {
    const res  = await fetch(`${API}/health`);
    const data = await res.json();
    if (data.status === 'healthy') {
      $('connDot').className = 'conn-dot online';
      $('connLabel').textContent = 'ML Engine Ready';
    }
  } catch {
    $('connDot').className = 'conn-dot error';
    $('connLabel').textContent = 'Backend Offline';
    toast('Backend is offline', 'Run python main.py in the backend folder', 'error');
  }
}

// ── LOAD ALL ──────────────────────────────────────────────
async function loadAll() {
  await Promise.allSettled([fetchTasks(), fetchLogs(), fetchAnalytics()]);
  renderSection(State.activeView);
}

// ── FETCH TASKS ───────────────────────────────────────────
async function fetchTasks() {
  try {
    const res = await fetch(`${API}/tasks`);
    if (!res.ok) return;
    State.tasks = await res.json();
    renderDashboard();
  } catch {}
}

// ── FETCH LOGS ────────────────────────────────────────────
async function fetchLogs() {
  try {
    const res = await fetch(`${API}/logs?limit=200`);
    if (!res.ok) return;
    State.logs = await res.json();
    renderAuditFeed();
    $('logBadgeCount').textContent = State.logs.length;
  } catch {}
}

// ── FETCH ANALYTICS ───────────────────────────────────────
async function fetchAnalytics() {
  try {
    const res = await fetch(`${API}/analytics`);
    if (!res.ok) return;
    State.analytics = await res.json();
    renderMiniStats();
    renderMeter();
  } catch {}
}

// ── BIND DASHBOARD ────────────────────────────────────────
function bindDashboard() {
  $('btnProcess').addEventListener('click', processMeeting);
  $('btnEscalate').addEventListener('click', runEscalation);
  $('filterStatus').addEventListener('change', e => {
    State.filterStatus = e.target.value;
    renderTaskBoard();
  });
  $('filterPriority').addEventListener('change', e => {
    State.filterPriority = e.target.value;
    renderTaskBoard();
  });
  $('btnShowOverdue').addEventListener('click', () => {
    $('filterStatus').value = 'overdue';
    State.filterStatus = 'overdue';
    renderTaskBoard();
  });
  $$('.sort-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      $$('.sort-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      State.sortMode = btn.dataset.sort;
      renderTaskBoard();
    });
  });
}

// ── SEARCH ────────────────────────────────────────────────
function bindSearch() {
  const inp = $('searchInput');
  inp.addEventListener('input', () => {
    State.searchQ = inp.value.trim().toLowerCase();
    renderTaskBoard();
  });
  inp.addEventListener('keydown', e => {
    if (e.key === 'Escape') { inp.value = ''; State.searchQ = ''; renderTaskBoard(); }
  });
}

// ── PROCESS MEETING ───────────────────────────────────────
async function processMeeting() {
  const text = $('meetingText').value.trim();
  if (!text) { showAlert('Please paste meeting notes first.', 'error'); return; }
  if (text.length < 20) { showAlert('Notes are too short. Please add more detail.', 'error'); return; }

  setExtracting(true);
  hideAlert();

  try {
    const res  = await fetch(`${API}/process-meeting`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);

    showAlert(`✓ ${data.message}`, 'success');
    toast('Tasks Extracted', `${data.task_count} tasks from meeting ${data.meeting_id.slice(-8)}`, 'success');
    $('meetingText').value = '';
    await loadAll();
  } catch (err) {
    showAlert(`Error: ${err.message}`, 'error');
    toast('Extraction Failed', err.message, 'error');
  } finally {
    setExtracting(false);
  }
}

function setExtracting(on) {
  $('btnProcess').disabled = on;
  $('processSpinner').classList.toggle('hidden', !on);
  $('btnProcessText').textContent = on ? 'Extracting…' : 'Extract Tasks with AI';
}

// ── ESCALATION ────────────────────────────────────────────
async function runEscalation() {
  const btn = $('btnEscalate');
  btn.disabled = true;
  btn.querySelector('span:last-child').textContent = 'Running…';
  try {
    const res  = await fetch(`${API}/escalate`, { method: 'POST' });
    const data = await res.json();
    toast('Escalation Complete',
      `${data.newly_overdue} newly overdue · ${data.escalated} escalated`,
      data.errors?.length ? 'warning' : 'success');
    await loadAll();
  } catch (err) {
    toast('Escalation Failed', err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.querySelector('span:last-child').textContent = 'Run Escalation';
  }
}

// ── RENDER DASHBOARD ──────────────────────────────────────
function renderDashboard() {
  renderMiniStats();
  renderTaskBoard();
  renderSidebarKpis();
}

function renderSidebarKpis() {
  const d = State.analytics;
  if (!d) return;
  $('skTotal').textContent = d.total_tasks;
  $('skDone').textContent  = d.completed;
  $('skOver').textContent  = d.overdue;
}

function renderMiniStats() {
  const d = State.analytics;
  if (!d) return;
  const total = Math.max(d.total_tasks, 1);
  $('statTotal').textContent      = d.total_tasks;
  $('statCompleted').textContent  = d.completed;
  $('statInProgress').textContent = d.in_progress;
  $('statOverdue').textContent    = d.overdue;
  $('stFillDone').style.width     = (d.completed   / total * 100) + '%';
  $('stFillActive').style.width   = (d.in_progress / total * 100) + '%';
  $('stFillOverdue').style.width  = (d.overdue     / total * 100) + '%';
}

function renderMeter() {
  const d = State.analytics;
  if (!d) return;
  const rate     = d.completion_rate || 0;
  const overRate = d.overdue_rate    || 0;
  $('ringPct').textContent       = rate + '%';
  $('completionRing').style.strokeDashoffset = 314 - (rate / 100 * 314);
  $('mCompletion').textContent   = rate + '%';
  $('mFillCompletion').style.width = Math.min(rate, 100) + '%';
  $('mOverdue').textContent      = overRate + '%';
  $('mFillOverdue').style.width  = Math.min(overRate, 100) + '%';
  $('mEscalated').textContent    = d.escalated || 0;
}

// ── TASK BOARD ────────────────────────────────────────────
function renderTaskBoard() {
  let tasks = filterTasks(State.tasks);
  tasks = sortTasks(tasks, State.sortMode);

  const overdue = State.tasks.filter(t => t.status === 'overdue');
  if (overdue.length) {
    $('overdueAlert').classList.remove('hidden');
    $('overdueAlertText').textContent =
      `${overdue.length} task${overdue.length > 1 ? 's are' : ' is'} overdue and escalated`;
  } else {
    $('overdueAlert').classList.add('hidden');
  }

  $('taskBadgeCount').textContent = tasks.length;

  if (!tasks.length) {
    $('taskBoard').innerHTML = `
      <div class="empty-board">
        <div class="eb-icon">◈</div>
        <div class="eb-title">${State.tasks.length ? 'No matching tasks' : 'No tasks yet'}</div>
        <div class="eb-sub">${State.tasks.length ? 'Try adjusting filters or search' : 'Paste meeting notes and extract tasks'}</div>
      </div>`;
    return;
  }

  $('taskBoard').innerHTML = tasks.map(buildTaskCard).join('');
  $$('.task-card').forEach(el => {
    el.addEventListener('click', () => openModal(State.tasks.find(t => t.id === parseInt(el.dataset.id))));
  });
}

function filterTasks(tasks) {
  return tasks.filter(t => {
    if (State.filterStatus   && t.status   !== State.filterStatus)   return false;
    if (State.filterPriority && t.priority !== State.filterPriority) return false;
    if (State.searchQ) {
      const q = State.searchQ;
      if (!t.task.toLowerCase().includes(q) &&
          !t.owner.toLowerCase().includes(q) &&
          !t.priority.toLowerCase().includes(q) &&
          !t.status.toLowerCase().includes(q)) return false;
    }
    return true;
  });
}

function sortTasks(tasks, mode) {
  const statusOrder = { overdue: 0, 'in-progress': 1, pending: 2, completed: 3 };
  const prioOrder   = { high: 0, medium: 1, low: 2 };
  if (mode === 'urgency') {
    return [...tasks].sort((a, b) =>
      (statusOrder[a.status] - statusOrder[b.status]) ||
      (prioOrder[a.priority] - prioOrder[b.priority]) ||
      new Date(a.deadline) - new Date(b.deadline)
    );
  }
  if (mode === 'deadline') {
    return [...tasks].sort((a, b) => new Date(a.deadline) - new Date(b.deadline));
  }
  if (mode === 'owner') {
    return [...tasks].sort((a, b) => a.owner.localeCompare(b.owner));
  }
  return tasks;
}

function buildTaskCard(task) {
  const dl  = daysLabel(task);
  const prioClass = 'pr-' + task.priority;
  const statClass = 'st-' + task.status;
  return `
    <div class="task-card ${prioClass} ${statClass}" data-id="${task.id}">
      <div class="tc-top">
        <div class="tc-title">${esc(task.task)}</div>
        <span class="tc-badge tb-${task.priority}">${task.priority}</span>
      </div>
      <div class="tc-meta">
        <span class="tc-meta-item">👤 ${esc(task.owner)}</span>
        <span class="tc-meta-item">📅 ${fmtDate(task.deadline)}</span>
      </div>
      <div class="tc-footer">
        <span class="status-pill sp-${task.status}">${task.status}</span>
        <span class="tc-days ${dl.cls}">${dl.text}</span>
        ${task.escalated ? '<span class="tc-esc-tag">⚡ Escalated</span>' : ''}
      </div>
    </div>`;
}

// ── AUDIT FEED ────────────────────────────────────────────
function renderAuditFeed() {
  const logs = State.logs.slice(0, 60);
  if (!logs.length) {
    $('auditFeed').innerHTML = '<div class="empty-feed">No events yet</div>';
    return;
  }
  $('auditFeed').innerHTML = logs.map(log => `
    <div class="audit-entry ae-${log.event_type}">
      <div class="ae-type aet-${log.event_type}">${log.event_type.replace(/_/g,' ')}</div>
      <div class="ae-desc">${esc(log.description)}</div>
      <div class="ae-time">${fmtDateTime(log.created_at)} · ${log.actor}</div>
    </div>`).join('');
}

// ── ANALYTICS SECTION ─────────────────────────────────────
function renderAnalytics() {
  const d = State.analytics;
  if (!d) return;
  const total = Math.max(d.total_tasks, 1);

  $('aTotal').textContent      = d.total_tasks;
  $('aCompleted').textContent  = d.completed;
  $('aInProgress').textContent = d.in_progress;
  $('aOverdue').textContent    = d.overdue;
  $('aEscalated').textContent  = d.escalated || 0;
  $('aCompRate').textContent   = d.completion_rate + '% rate';
  $('aOverRate').textContent   = d.overdue_rate   + '% rate';
  $('aActiveRate').textContent = Math.round(d.in_progress / total * 100) + '% of total';

  // Donut chart
  const CIRC = 377;
  const segs = [
    { id:'ds-pending',    n: d.pending     || 0 },
    { id:'ds-inprogress', n: d.in_progress || 0 },
    { id:'ds-completed',  n: d.completed   || 0 },
    { id:'ds-overdue',    n: d.overdue     || 0 },
  ];
  let off = 0;
  segs.forEach(seg => {
    const len = (seg.n / total) * CIRC;
    const el  = $(seg.id);
    if (!el) return;
    el.setAttribute('stroke-dasharray', `${len} ${CIRC - len}`);
    el.setAttribute('stroke-dashoffset', -off);
    off += len;
  });
  $('dctNum').textContent       = d.total_tasks;
  $('dl-pending').textContent    = d.pending     || 0;
  $('dl-inprogress').textContent = d.in_progress || 0;
  $('dl-completed').textContent  = d.completed   || 0;
  $('dl-overdue').textContent    = d.overdue     || 0;

  // Priority bars
  const pb = d.priority_breakdown || {};
  const maxP = Math.max(pb.high||0, pb.medium||0, pb.low||0, 1);
  $('hbHigh').style.width = ((pb.high||0)   / maxP * 100) + '%';
  $('hbMed').style.width  = ((pb.medium||0) / maxP * 100) + '%';
  $('hbLow').style.width  = ((pb.low||0)    / maxP * 100) + '%';
  $('hvHigh').textContent = pb.high   || 0;
  $('hvMed').textContent  = pb.medium || 0;
  $('hvLow').textContent  = pb.low    || 0;

  // Owner bars
  const ob = d.owner_breakdown || {};
  const maxO = Math.max(...Object.values(ob).map(o => o.total || 0), 1);
  const colors = ['#818cf8','#22d3ee','#4ade80','#fb923c','#f87171','#facc15','#f472b6'];
  $('ownerBars').innerHTML = Object.entries(ob).slice(0, 8).map(([name, data], i) => `
    <div class="ob-row">
      <span class="ob-name" title="${esc(name)}">${esc(name)}</span>
      <div class="ob-track"><div class="ob-fill" style="width:${(data.total/maxO*100)}%;background:${colors[i%colors.length]}"></div></div>
      <span class="ob-val">${data.total}</span>
    </div>`).join('');
}

// ── WORKLOAD SECTION ──────────────────────────────────────
function renderWorkload() {
  const tasks = State.tasks;
  if (!tasks.length) {
    $('workloadGrid').innerHTML = '<div class="empty-view"><div class="ev-icon">◎</div><p>Process a meeting to see workload</p></div>';
    return;
  }

  const owners = {};
  tasks.forEach(t => {
    if (!owners[t.owner]) owners[t.owner] = { total:0, completed:0, overdue:0, active:0, high:0 };
    owners[t.owner].total++;
    if (t.status === 'completed')   owners[t.owner].completed++;
    if (t.status === 'overdue')     owners[t.owner].overdue++;
    if (t.status === 'in-progress') owners[t.owner].active++;
    if (t.priority === 'high')      owners[t.owner].high++;
  });

  const palette = [
    'linear-gradient(135deg,#818cf8,#4f46e5)',
    'linear-gradient(135deg,#22d3ee,#0891b2)',
    'linear-gradient(135deg,#4ade80,#16a34a)',
    'linear-gradient(135deg,#fb923c,#ea580c)',
    'linear-gradient(135deg,#f87171,#dc2626)',
    'linear-gradient(135deg,#facc15,#ca8a04)',
    'linear-gradient(135deg,#f472b6,#be185d)',
    'linear-gradient(135deg,#a78bfa,#7c3aed)',
  ];
  const barColors = ['#818cf8','#22d3ee','#4ade80','#fb923c','#f87171','#facc15'];

  $('workloadGrid').innerHTML = Object.entries(owners).map(([name, d], i) => {
    const rate     = Math.round(d.completed / Math.max(d.total, 1) * 100);
    const overload = d.total > 5 || d.high > 2 || d.overdue > 1;
    const initials = name.split(' ').map(w => w[0] || '').join('').slice(0, 2).toUpperCase();
    const grad     = palette[i % palette.length];
    const barCol   = barColors[i % barColors.length];
    return `
      <div class="wl-card">
        <div class="wl-head">
          <div class="wl-avatar" style="background:${grad}">${initials}</div>
          <div>
            <div class="wl-name">${esc(name)}</div>
            <div class="wl-sub">${d.total} task${d.total !== 1 ? 's' : ''} assigned</div>
          </div>
        </div>
        <div class="wl-stats">
          <div class="wl-stat"><div class="wl-sn" style="color:var(--cyan)">${d.total}</div><div class="wl-sl">Total</div></div>
          <div class="wl-stat"><div class="wl-sn" style="color:var(--green)">${d.completed}</div><div class="wl-sl">Done</div></div>
          <div class="wl-stat"><div class="wl-sn" style="color:var(--red)">${d.overdue}</div><div class="wl-sl">Overdue</div></div>
        </div>
        <div class="wl-bar-label">
          <span>Completion Rate</span><span style="color:${barCol};font-weight:600">${rate}%</span>
        </div>
        <div class="wl-bar">
          <div class="wl-fill" style="width:${rate}%;background:${barCol}"></div>
        </div>
        ${overload ? '<div class="overload-warn">⚠ High Workload — Consider Redistributing</div>' : ''}
      </div>`;
  }).join('');
}

// ── TIMELINE SECTION ──────────────────────────────────────
function renderTimeline() {
  const active = State.tasks
    .filter(t => t.status !== 'completed')
    .sort((a, b) => new Date(a.deadline) - new Date(b.deadline));

  if (!active.length) {
    $('timelineContainer').innerHTML = '<div class="empty-view"><div class="ev-icon">◐</div><p>No active tasks scheduled</p></div>';
    return;
  }

  const nodeColors = { high: '#f87171', medium: '#facc15', low: '#4ade80' };
  $('timelineContainer').innerHTML = active.map((task, idx) => {
    const dl  = daysLabel(task);
    const nc  = task.status === 'overdue' ? '#f87171' : (nodeColors[task.priority] || '#818cf8');
    const isLast = idx === active.length - 1;
    return `
      <div class="tl-item">
        <div class="tl-date-col">
          <div class="tl-dt">${fmtDate(task.deadline)}</div>
          <div class="tl-rel ${dl.cls}">${dl.text}</div>
        </div>
        <div class="tl-connector">
          <div class="tl-node" style="background:${nc};box-shadow:0 0 8px ${nc}66"></div>
          ${!isLast ? '<div class="tl-line"></div>' : ''}
        </div>
        <div class="tl-card" data-id="${task.id}">
          <div class="tl-card-title">${esc(task.task)}</div>
          <div class="tl-card-meta">
            <span>👤 ${esc(task.owner)}</span>
            <span><span class="status-pill sp-${task.status}">${task.status}</span></span>
            <span><span class="tc-badge tb-${task.priority}">${task.priority}</span></span>
            ${task.escalated ? '<span class="tc-esc-tag">⚡</span>' : ''}
          </div>
        </div>
      </div>`;
  }).join('');

  // Timeline cards also open modal
  $$('.tl-card').forEach(el => {
    el.addEventListener('click', () => openModal(State.tasks.find(t => t.id === parseInt(el.dataset.id))));
  });
}

// ── HISTORY SECTION ───────────────────────────────────────
function bindHistory() {
  $('histEventFilter').addEventListener('change', renderHistory);
  $('btnRefreshHistory').addEventListener('click', async () => {
    await fetchLogs();
    renderHistory();
    toast('Refreshed', 'Audit log updated', 'info');
  });
}

function renderHistory() {
  const filter = $('histEventFilter').value;
  const logs   = filter ? State.logs.filter(l => l.event_type === filter) : State.logs;
  $('histResultCount').textContent = `${logs.length} event${logs.length !== 1 ? 's' : ''}`;

  if (!logs.length) {
    $('histTableBody').innerHTML = '<tr><td colspan="5" class="empty-row">No audit events recorded yet.</td></tr>';
    return;
  }

  $('histTableBody').innerHTML = logs.map(log => `
    <tr>
      <td class="he-time">${fmtDateTime(log.created_at)}</td>
      <td><span class="he-tag he-${log.event_type}">${log.event_type.replace(/_/g,' ')}</span></td>
      <td style="font-family:var(--f-mono);font-size:11px;color:var(--text-2)">${log.entity_type}:${log.entity_id}</td>
      <td class="he-actor">${log.actor}</td>
      <td>${esc(log.description)}</td>
    </tr>`).join('');
}

// ── PERFORMANCE SECTION ───────────────────────────────────
function renderPerformance() {
  const tasks = State.tasks;
  if (!tasks.length) {
    $('perfGrid').innerHTML = '<div class="empty-view"><div class="ev-icon">◒</div><p>Process meetings to generate data</p></div>';
    $('perfSummary').innerHTML = '';
    return;
  }

  const owners = {};
  tasks.forEach(t => {
    if (!owners[t.owner]) owners[t.owner] = { total:0, completed:0, overdue:0, active:0 };
    owners[t.owner].total++;
    if (t.status === 'completed')   owners[t.owner].completed++;
    if (t.status === 'overdue')     owners[t.owner].overdue++;
    if (t.status === 'in-progress') owners[t.owner].active++;
  });

  const ranked = Object.entries(owners)
    .map(([name, d]) => ({
      name, ...d,
      rate: Math.round(d.completed / Math.max(d.total, 1) * 100),
    }))
    .sort((a, b) => b.rate - a.rate || b.completed - a.completed);

  // Summary bar
  const topPerformer = ranked[0];
  $('perfSummary').innerHTML = ranked.slice(0, 3).map(r => `
    <div class="ps-item"><b>${esc(r.name)}</b> — ${r.rate}% done</div>`).join('');

  const medals  = ['🥇 #1', '🥈 #2', '🥉 #3'];
  const rankCls = [
    'background:rgba(250,204,21,0.12);color:var(--yellow);border:1px solid rgba(250,204,21,0.25)',
    'background:rgba(148,163,184,0.12);color:#94a3b8;border:1px solid rgba(148,163,184,0.25)',
    'background:rgba(251,146,60,0.12);color:var(--amber);border:1px solid rgba(251,146,60,0.25)',
  ];
  const barGrads = [
    'linear-gradient(90deg,#facc15,#fde68a)',
    'linear-gradient(90deg,#94a3b8,#cbd5e1)',
    'linear-gradient(90deg,#fb923c,#fdba74)',
    'linear-gradient(90deg,#818cf8,#a5b4fc)',
  ];

  $('perfGrid').innerHTML = ranked.map((owner, i) => {
    const medal   = medals[i]   || `#${i+1}`;
    const rankS   = rankCls[i]  || 'background:var(--surface2);color:var(--text-2);border:1px solid var(--border)';
    const barGrad = barGrads[i] || barGrads[3];
    return `
      <div class="perf-card">
        <div class="pc-header">
          <div class="pc-name">${esc(owner.name)}</div>
          <span class="pc-rank" style="${rankS}">${medal}</span>
        </div>
        <div class="pc-metrics">
          <div class="pm-box"><div class="pm-n" style="color:var(--cyan)">${owner.total}</div><div class="pm-l">Assigned</div></div>
          <div class="pm-box"><div class="pm-n" style="color:var(--green)">${owner.completed}</div><div class="pm-l">Done</div></div>
          <div class="pm-box"><div class="pm-n" style="color:var(--red)">${owner.overdue}</div><div class="pm-l">Overdue</div></div>
        </div>
        <div class="pc-rate-row">
          <span>Completion Rate</span>
          <span style="font-family:var(--f-mono);font-weight:700;color:${i===0?'var(--yellow)':i===1?'#94a3b8':'var(--amber)'}">${owner.rate}%</span>
        </div>
        <div class="pc-rate-bar">
          <div class="pc-rate-fill" style="width:${owner.rate}%;background:${barGrad}"></div>
        </div>
      </div>`;
  }).join('');
}

// ── MODAL ─────────────────────────────────────────────────
function bindModal() {
  $('modalClose').addEventListener('click', closeModal);
  $('modalBackdrop').addEventListener('click', e => { if (e.target === $('modalBackdrop')) closeModal(); });
  $('btnModalSave').addEventListener('click', saveModalStatus);
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
}

function openModal(task) {
  if (!task) return;
  State.activeTask = task;

  const prioColors = {
    high:   'background:rgba(248,113,113,0.15);color:var(--red);border:1px solid rgba(248,113,113,0.3)',
    medium: 'background:rgba(250,204,21,0.12);color:var(--yellow);border:1px solid rgba(250,204,21,0.3)',
    low:    'background:rgba(74,222,128,0.12);color:var(--green);border:1px solid rgba(74,222,128,0.3)',
  };
  $('modalTag').textContent = task.priority.toUpperCase();
  $('modalTag').style.cssText = (prioColors[task.priority] || '') + ';font-family:var(--f-mono);font-size:10px;font-weight:600;padding:3px 10px;border-radius:5px;letter-spacing:.05em';
  $('modalTitle').textContent   = task.task;
  $('mOwner').textContent       = task.owner;
  $('mDeadline').textContent    = `${fmtDate(task.deadline)} — ${daysLabel(task).text}`;
  $('mStatus').innerHTML        = `<span class="status-pill sp-${task.status}">${task.status}</span>`;
  $('mPriority').innerHTML      = `<span class="tc-badge tb-${task.priority}">${task.priority}</span>`;
  $('mSla').textContent         = `${task.sla_hours}h SLA window`;
  $('mEscalated').textContent   = task.escalated ? '⚡ Yes — reassignment suggested' : 'No';
  $('mCreated').textContent     = fmtDateTime(task.created_at);
  $('mMeetingId').textContent   = task.meeting_id;
  $('mStatusSelect').value      = task.status;
  $('modalAlert').classList.add('hidden');
  $('modalBackdrop').classList.remove('hidden');
}

function closeModal() {
  $('modalBackdrop').classList.add('hidden');
  State.activeTask = null;
}

async function saveModalStatus() {
  if (!State.activeTask) return;
  const newStatus = $('mStatusSelect').value;
  $('btnModalSave').disabled = true;
  try {
    const res = await fetch(`${API}/update-task-status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_id: State.activeTask.id, status: newStatus, actor: 'user' }),
    });
    if (!res.ok) { const e = await res.json(); throw new Error(e.detail || `HTTP ${res.status}`); }
    showModalAlert(`Status updated to "${newStatus}"`, 'success');
    toast('Status Updated', `Task marked as ${newStatus}`, 'success');
    await loadAll();
    setTimeout(closeModal, 900);
  } catch (err) {
    showModalAlert(`Error: ${err.message}`, 'error');
  } finally {
    $('btnModalSave').disabled = false;
  }
}

function showModalAlert(msg, type) {
  const el = $('modalAlert');
  el.textContent = msg;
  el.className   = `modal-alert ${type}`;
  el.classList.remove('hidden');
}

// ── ALERT BOX ─────────────────────────────────────────────
function showAlert(msg, type = 'success') {
  const el = $('alertBox');
  el.textContent = msg;
  el.className   = `alert-box ${type}`;
  el.classList.remove('hidden');
  if (type === 'success') setTimeout(hideAlert, 5000);
}
function hideAlert() { $('alertBox').classList.add('hidden'); }

// ── TOAST SYSTEM ──────────────────────────────────────────
const toastIcons = { success:'✓', error:'✕', warning:'⚠', info:'ℹ' };

function toast(title, msg, type = 'info') {
  const stack = $('toastStack');
  const el    = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `
    <div class="toast-icon">${toastIcons[type] || 'ℹ'}</div>
    <div class="toast-body">
      <div class="toast-title">${esc(title)}</div>
      <div class="toast-msg">${esc(msg)}</div>
    </div>`;
  stack.appendChild(el);
  setTimeout(() => {
    el.classList.add('out');
    setTimeout(() => el.remove(), 350);
  }, TOAST_LIFE_MS);
}

// ── HELPERS ───────────────────────────────────────────────
function daysLabel(task) {
  const d = task.days_until_deadline;
  if (d === null || d === undefined) return { text: '', cls: 'ok' };
  if (task.status === 'completed')   return { text: '✓ Done', cls: 'ok' };
  if (d < 0)   return { text: `${Math.abs(d)}d overdue`, cls: 'danger' };
  if (d === 0) return { text: 'Due today',  cls: 'danger' };
  if (d <= 3)  return { text: `${d}d left`, cls: 'warn' };
  return             { text: `${d}d left`, cls: 'ok' };
}

function esc(str) {
  return String(str || '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function fmtDate(d) {
  if (!d) return '—';
  try {
    const [y,m,day] = d.split('-');
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    return `${months[parseInt(m,10)-1]} ${parseInt(day,10)}, ${y}`;
  } catch { return d; }
}

function fmtDateTime(dt) {
  if (!dt) return '—';
  try {
    const d = new Date(dt.includes('T') ? dt : dt + 'Z');
    return d.toLocaleString('en-US', {
      month:'short', day:'numeric',
      hour:'2-digit', minute:'2-digit',
    });
  } catch { return dt; }
}