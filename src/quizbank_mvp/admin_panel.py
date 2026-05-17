"""Minimal browser shell for the MVP admin control surface."""

ADMIN_PANEL_HTML = """<!doctype html>
<html lang="uk">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>API Quiz Bank Admin</title>
  <style>
    :root { color-scheme: light; font-family: Arial, sans-serif; }
    body { margin: 0; background: #f5f7fa; color: #18202a; }
    header { background: #18202a; color: white; padding: 16px 24px; }
    main { display: grid; gap: 16px; padding: 16px; max-width: 1200px; margin: auto; }
    section, dialog { background: white; border: 1px solid #d7dde5; border-radius: 6px; padding: 16px; }
    label { display: grid; gap: 6px; font-size: 13px; font-weight: 700; }
    input, select, textarea, button { font: inherit; border-radius: 4px; border: 1px solid #b8c2cf; padding: 8px; }
    button { cursor: pointer; background: #1f6feb; color: white; border-color: #1f6feb; }
    button.secondary { background: white; color: #18202a; border-color: #b8c2cf; }
    .toolbar { display: grid; grid-template-columns: repeat(5, minmax(120px, 1fr)); gap: 12px; align-items: end; }
    .consumer-form { display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 12px; align-items: end; }
    .metrics { display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 12px; }
    .metric { background: #eef3f8; border-radius: 6px; padding: 12px; }
    table { border-collapse: collapse; width: 100%; font-size: 14px; }
    th, td { border-bottom: 1px solid #e3e8ef; padding: 8px; text-align: left; vertical-align: top; }
    tr:hover { background: #f8fafc; }
    .actions { display: flex; flex-wrap: wrap; gap: 6px; }
    .error { color: #b42318; font-weight: 700; }
    @media (max-width: 800px) { .toolbar, .consumer-form, .metrics { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <header><h1>API Quiz Bank Admin</h1></header>
  <main>
    <section class="toolbar">
      <label>Admin password <input id="adminPassword" type="password" autocomplete="current-password"></label>
      <label>Status <select id="status"><option value="">Any</option></select></label>
      <label>CEFR <select id="level"><option value="">Any</option><option>A1</option><option>A2</option><option>B1</option><option>B2</option><option>C1</option><option>C2</option></select></label>
      <label>Theme <input id="theme" placeholder="T10"></label>
      <button id="load">Load</button>
    </section>
    <section>
      <div class="metrics" id="metrics"></div>
    </section>
    <section>
      <p class="error" id="error"></p>
      <table>
        <thead><tr><th>ID</th><th>Status</th><th>Level</th><th>Theme</th><th>Question</th><th>Actions</th></tr></thead>
        <tbody id="items"></tbody>
      </table>
    </section>
    <section>
      <h2>Consumers</h2>
      <div class="consumer-form">
        <label>ID <input id="consumerId" placeholder="telegram_channel_a1"></label>
        <label>Name <input id="consumerName" placeholder="A1 Telegram Channel"></label>
        <label>Kind <select id="consumerKind"><option>api_client</option><option>telegram_channel</option><option>telegram_bot</option><option>teacher</option><option>school</option></select></label>
        <label>API key <input id="consumerApiKey" type="password" autocomplete="new-password"></label>
        <label>Quota <input id="consumerQuota" type="number" min="0" value="10"></label>
        <label>CEFR <input id="consumerLevels" placeholder="A2"></label>
        <label>Themes <input id="consumerThemes" placeholder="T10"></label>
        <label>Reason <input id="consumerReason" placeholder="owner-created access"></label>
        <button id="createConsumer">Create access</button>
      </div>
      <table>
        <thead><tr><th>ID</th><th>Name</th><th>Kind</th><th>Status</th><th>Usage</th><th>Allowed</th><th>Actions</th></tr></thead>
        <tbody id="consumers"></tbody>
      </table>
    </section>
  </main>
  <dialog id="actionDialog">
    <form method="dialog">
      <h2 id="dialogTitle"></h2>
      <label>Reason <textarea id="reason" rows="4" required></textarea></label>
      <menu>
        <button class="secondary" value="cancel">Cancel</button>
        <button id="confirmAction" value="confirm">Confirm</button>
      </menu>
    </form>
  </dialog>
  <script>
    const statuses = ['draft','imported','normalized','needs_review','approved','published','monitored','retired','blocked'];
    const statusSelect = document.getElementById('status');
    statuses.forEach(status => statusSelect.append(new Option(status, status)));
    let pending = null;
    const headers = () => ({'X-QuizBank-Admin-Key': document.getElementById('adminPassword').value});
    async function api(path, options = {}) {
      const response = await fetch(path, {...options, headers: {...headers(), ...(options.headers || {})}});
      if (!response.ok) throw await response.json();
      return response.json();
    }
    async function load() {
      document.getElementById('error').textContent = '';
      try {
        const params = new URLSearchParams();
        if (status.value) params.set('status', status.value);
        if (level.value) params.set('cefr_level', level.value);
        if (theme.value) params.set('theme_id', theme.value);
        const [dashboard, items] = await Promise.all([
          api('/v1/admin/dashboard'),
          api('/v1/admin/quiz-items?' + params.toString())
        ]);
        renderMetrics(dashboard);
        renderItems(items.data);
        await loadConsumers();
      } catch (error) {
        document.getElementById('error').textContent = error.detail || error.title || 'Admin request failed';
      }
    }
    function renderMetrics(data) {
      const visual = data.visual_metrics || {};
      const visualEvents = visual.event_counts || {};
      document.getElementById('metrics').innerHTML = [
        ['Approved + Published', data.approved_published_count],
        ['Deliveries', data.delivery_log_count],
        ['Audit Events', data.audit_log_count],
        ['Blocked', data.corpus_status_counts.blocked || 0],
        ['Visual Cache Hit Rate', `${Math.round((visual.cache_hit_rate || 0) * 100)}%`],
        ['Visual Fallback Rate', `${Math.round((visual.fallback_rate || 0) * 100)}%`],
        ['Visual Generations', visualEvents.generation_requested || 0]
      ].map(([label, value]) => `<div class="metric"><strong>${value}</strong><br>${label}</div>`).join('');
    }
    function renderItems(items) {
      document.getElementById('items').innerHTML = items.map(item => `
        <tr>
          <td>${escapeHtml(item.item_id)}</td><td>${escapeHtml(item.status)}</td>
          <td>${escapeHtml(item.cefr_level)}</td><td>${escapeHtml(item.theme_id)}</td>
          <td>${escapeHtml(item.stem_text)}</td><td class="actions">${actionButtons(item.item_id)}</td>
        </tr>`).join('');
    }
    async function loadConsumers() {
      const consumers = await api('/v1/admin/consumers');
      renderConsumers(consumers.data);
    }
    function renderConsumers(consumers) {
      document.getElementById('consumers').innerHTML = consumers.map(consumer => `
        <tr>
          <td>${escapeHtml(consumer.consumer_id)}</td>
          <td>${escapeHtml(consumer.display_name)}</td>
          <td>${escapeHtml(consumer.consumer_kind)}</td>
          <td>${escapeHtml(consumer.status)}</td>
          <td>${consumer.today_quota_used}/${consumer.daily_quota_limit}<br>${consumer.delivery_count} total</td>
          <td>${escapeHtml(consumer.allowed_cefr_levels.join(','))}<br>${escapeHtml(consumer.allowed_theme_ids.join(','))}</td>
          <td class="actions">${consumerActionButtons(consumer.consumer_id)}</td>
        </tr>`).join('');
    }
    function consumerActionButtons(consumerId) {
      const safeConsumerId = escapeHtml(consumerId);
      return ['suspend','activate','block']
        .map(action => `<button data-consumer="${safeConsumerId}" data-consumer-action="${action}">${action}</button>`).join('');
    }
    function actionButtons(itemId) {
      const safeItemId = escapeHtml(itemId);
      return ['approve','publish','retire','block']
        .map(action => `<button data-item="${safeItemId}" data-action="${action}">${action}</button>`).join('');
    }
    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, character => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
      }[character]));
    }
    function openAction(itemId, action) {
      pending = {itemId, action};
      dialogTitle.textContent = `${action} ${itemId}`;
      reason.value = '';
      actionDialog.showModal();
    }
    confirmAction.addEventListener('click', async event => {
      event.preventDefault();
      if (!pending || !reason.value.trim()) return;
      await api(`/v1/admin/quiz-items/${pending.itemId}/${pending.action}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({reason: reason.value.trim()})
      });
      actionDialog.close();
      await load();
    });
    async function createConsumer() {
      await api('/v1/admin/consumers', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          consumer_id: consumerId.value.trim(),
          display_name: consumerName.value.trim(),
          consumer_kind: consumerKind.value,
          daily_quota_limit: Number(consumerQuota.value),
          allowed_cefr_levels: csvValues(consumerLevels.value),
          allowed_theme_ids: csvValues(consumerThemes.value),
          api_key: consumerApiKey.value,
          reason: consumerReason.value.trim()
        })
      });
      consumerApiKey.value = '';
      await loadConsumers();
    }
    function csvValues(value) {
      return value.split(',').map(part => part.trim()).filter(Boolean);
    }
    document.getElementById('load').addEventListener('click', load);
    document.getElementById('createConsumer').addEventListener('click', createConsumer);
    document.getElementById('items').addEventListener('click', event => {
      if (event.target.dataset && event.target.dataset.action) {
        openAction(event.target.dataset.item, event.target.dataset.action);
      }
    });
    document.getElementById('consumers').addEventListener('click', async event => {
      if (event.target.dataset && event.target.dataset.consumerAction) {
        const reason = window.prompt('Reason');
        if (!reason) return;
        await api(`/v1/admin/consumers/${event.target.dataset.consumer}/${event.target.dataset.consumerAction}`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({reason})
        });
        await loadConsumers();
      }
    });
  </script>
</body>
</html>
"""
