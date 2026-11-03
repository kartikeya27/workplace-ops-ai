const $ = id => document.getElementById(id);
let currentProposal = null;
let lastEvidenceId = null;
function escapeHtml(v) {
  return String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
}
function show(id, html) { $(id).innerHTML = html; }
function fmt(obj) { return `<pre>${escapeHtml(JSON.stringify(obj, null, 2))}</pre>`; }
async function request(path, options = {}) {
  const r = await fetch(path, {headers:{'Content-Type':'application/json'}, ...options});
  const data = await r.json();
  if (!r.ok) throw Error(data.detail || `HTTP ${r.status}`);
  return data;
}
async function perform(targetId, work) {
  try { await work(); } catch(e) { show(targetId, `<span class="bad">${escapeHtml(e.message)}</span>`); }
}
async function refresh() {
  const [stats, tickets, events] = await Promise.all([
    request('/api/summary'), request('/api/tickets'), request('/api/audit/events')]);
  const cards = [['Managed devices', stats.devices], ['Noncompliant devices', stats.noncompliant_devices],
    ['Open tickets', stats.open_tickets], ['Awaiting approval', stats.pending_approvals]];
  show('metrics', cards.map(([label,num]) => `<div class="metric"><span>${escapeHtml(label)}</span><strong>${escapeHtml(num)}</strong></div>`).join(''));
  const old = $('ticket').value;
  $('ticket').innerHTML = tickets.map(t => `<option value="${escapeHtml(t.id)}">${escapeHtml(t.id)} · ${escapeHtml(t.title)} (${escapeHtml(t.status)})</option>`).join('');
  if (tickets.some(t => t.id === old)) $('ticket').value = old;
  show('audit', events.length ? events.map(e => `${escapeHtml(e.occurred_at)}  ·  <strong>${escapeHtml(e.action)}</strong>  ·  ${escapeHtml(e.subject)}  ·  ${escapeHtml(e.actor)}`).join('\n') : 'No events yet.');
}
$('triage').addEventListener('click', () => perform('triage-result', async () => {
  const result = await request(`/api/tickets/${encodeURIComponent($('ticket').value)}/triage`, {method:'POST'});
  const p = result.proposal;
  currentProposal = p.status === 'pending' ? p.id : null;
  show('triage-result', `<strong>Suggested team:</strong> ${escapeHtml(p.team)}\n<strong>On-duty owner:</strong> ${escapeHtml(p.owner || 'unassigned: human queue')}\n<strong>Explanation:</strong> ${escapeHtml(p.reason)}\n<strong>Knowledge article:</strong> ${escapeHtml(result.explanation.knowledge_id)}\n<strong>Guidance:</strong> ${escapeHtml(result.explanation.guidance)}\n<strong>Device facts:</strong>\n${escapeHtml(result.explanation.device_facts.join('\n') || 'No device linked')}\n<strong>Proposed action:</strong> ${escapeHtml(p.status)}`);
  $('approve-panel').classList.toggle('hidden', !currentProposal || !p.owner);
  await refresh();
}));
$('ai-summary').addEventListener('click', () => perform('triage-result', async () => {
  const result = await request(`/api/tickets/${encodeURIComponent($('ticket').value)}/ai-summary`, {method:'POST'});
  currentProposal = null; $('approve-panel').classList.add('hidden');
  show('triage-result', `<strong>Handoff draft</strong> · ${escapeHtml(result.mode)} · <strong>Human review required</strong>\n\n${escapeHtml(result.draft)}\n\nKnowledge: ${escapeHtml(result.knowledge_id)}\nTools: ${escapeHtml(result.trace.join(' → '))}`);
}));
$('approve').addEventListener('click', () => perform('triage-result', async () => {
  if (!currentProposal) return;
  const response = await request(`/api/proposals/${encodeURIComponent(currentProposal)}/approve`, {
    method:'POST', body:JSON.stringify({reviewer:$('reviewer').value.trim()})});
  show('triage-result', `<span class="good"><strong>Simulation approved.</strong></span>\nLocal ticket assigned to: ${escapeHtml(response.assigned_to)}\nNo external ticketing system was contacted.`);
  currentProposal=null; $('approve-panel').classList.add('hidden'); await refresh();
}));
$('evidence').addEventListener('click', () => perform('evidence-result', async () => {
  const result = await request('/api/evidence/runs', {method:'POST'});
  lastEvidenceId = result.run_id; $('verify').disabled=false;
  show('evidence-result', `<span class="good">Evidence package created.</span>\n${fmt(result)}`);
  await refresh();
}));
$('verify').addEventListener('click', () => perform('evidence-result', async () => {
  const result=await request(`/api/evidence/runs/${encodeURIComponent(lastEvidenceId)}/verify`);
  show('evidence-result', `<strong>${result.verified ? 'Integrity check passed' : 'Integrity check failed'}</strong>\n${fmt(result)}`);
}));
$('patches').addEventListener('click', () => perform('patch-result', async () => {
  show('patch-result', fmt(await request('/api/patches/plan')));
}));
$('meetings').addEventListener('click', () => perform('meeting-result', async () => {
  show('meeting-result', fmt(await request('/api/meetings/plan')));
}));
$('refresh').addEventListener('click', () => perform('audit', refresh));
perform('audit', refresh);

let currentProvisioning = null;
perform('provisioning-result', async () => {
  const devices = await request('/api/devices');
  $('provisioning-device').innerHTML = devices
    .map(d => `<option value="${escapeHtml(d.id)}">${escapeHtml(d.id)} · ${escapeHtml(d.model)} (${escapeHtml(d.platform)})</option>`).join('');
});
$('provisioning-check').addEventListener('click', () => perform('provisioning-result', async () => {
  const id = encodeURIComponent($('provisioning-device').value);
  const data = await request(`/api/provisioning/devices/${id}/readiness`);
  currentProvisioning = null;
  $('provisioning-approve-panel').classList.add('hidden');
  show('provisioning-result', fmt(data));
}));
$('provisioning-request').addEventListener('click', () => perform('provisioning-result', async () => {
  const id = encodeURIComponent($('provisioning-device').value);
  const data = await request(`/api/provisioning/devices/${id}/request`, {method:'POST'});
  currentProvisioning = data.request.status === 'pending' ? data.request.id : null;
  $('provisioning-approve-panel').classList.toggle('hidden', !currentProvisioning);
  show('provisioning-result', fmt(data));
  await refresh();
}));
$('provisioning-approve').addEventListener('click', () => perform('provisioning-result', async () => {
  if (!currentProvisioning) return;
  const result = await request(`/api/provisioning/requests/${encodeURIComponent(currentProvisioning)}/approve`, {
    method:'POST', body:JSON.stringify({reviewer:$('provisioning-reviewer').value.trim()})
  });
  show('provisioning-result', fmt(result));
  currentProvisioning = null;
  $('provisioning-approve-panel').classList.add('hidden');
  await refresh();
}));


// End-to-end local onboarding workflow; only SQLite changes, no external API calls.
let activeOnboardingRun = null;
async function loadOnboardingDevices() {
  const devices = await request('/api/devices');
  $('onboarding-device').innerHTML = devices.map(d =>
    '<option value="' + escapeHtml(d.id) + '">' + escapeHtml(d.id) +
    ' · ' + escapeHtml(d.model) + ' (' + escapeHtml(d.platform) + ')</option>').join('');
}
function renderOnboarding(run) {
  activeOnboardingRun = run.id;
  const ended = ['blocked', 'completed', 'completed_limited'].includes(run.status);
  $('onboarding-advance').disabled = ended || run.status === 'awaiting_privilege_approval';
  $('onboarding-privilege-panel').classList.toggle('hidden', run.status !== 'awaiting_privilege_approval');
  const steps = run.timeline.map(e => escapeHtml(e.time) + ' · <strong>' +
    escapeHtml(e.action) + '</strong> · ' + escapeHtml(e.actor));
  const apps = run.application_plan && run.application_plan.apps ?
    run.application_plan.apps.map(a => a.name + ': ' + a.state).join('\n') : 'Not planned yet';
  const priv = run.privilege_request ?
    run.privilege_request.scope + ' · ' + run.privilege_request.state : 'Not requested';
  show('onboarding-result',
    '<strong>Employee:</strong> ' + escapeHtml(run.employee_id) + '\n' +
    '<strong>Device:</strong> ' + escapeHtml(run.device_id) + '\n' +
    '<strong>Status:</strong> ' + escapeHtml(run.status) + '\n' +
    '<strong>Identity:</strong> ' + escapeHtml(run.identity_plan ? run.identity_plan.state : 'Not provisioned') + '\n' +
    '<strong>Applications:</strong>\n' + escapeHtml(apps) + '\n' +
    '<strong>Privilege:</strong> ' + escapeHtml(priv) + '\n' +
    '<strong>Simulated privilege valid:</strong> ' +
    (run.simulated_privilege_currently_valid ? 'yes (local record only)' : 'no') + '\n' +
    '<strong>Real external writes:</strong> ' + escapeHtml(run.external_writes) +
    '\n\n<strong>Audit timeline</strong>\n' + steps.join('\n'));
}
$('onboarding-create').addEventListener('click', () => perform('onboarding-result', async () => {
  const result = await request('/api/onboarding', {
    method: 'POST', body: JSON.stringify({
      employee_id: $('onboarding-employee').value.trim(),
      device_id: $('onboarding-device').value,
      profile: $('onboarding-profile').value
    })
  });
  renderOnboarding(result.run);
  await refresh();
}));
$('onboarding-advance').addEventListener('click', () => perform('onboarding-result', async () => {
  if (!activeOnboardingRun) return;
  const result = await request('/api/onboarding/' + encodeURIComponent(activeOnboardingRun) + '/advance', {method: 'POST'});
  renderOnboarding(result.run);
  await refresh();
}));
for (const [button, decision] of [['onboarding-approve', 'approve'], ['onboarding-deny', 'deny']]) {
  $(button).addEventListener('click', () => perform('onboarding-result', async () => {
    if (!activeOnboardingRun) return;
    const result = await request('/api/onboarding/' + encodeURIComponent(activeOnboardingRun) + '/privilege-decision', {
      method: 'POST', body: JSON.stringify({reviewer: $('onboarding-reviewer').value.trim(), decision})
    });
    renderOnboarding(result.run);
    await refresh();
  }));
}
perform('onboarding-result', loadOnboardingDevices);
