/* Live FHIR activity panel: polls /api/fhir-log every ~1s with a `since` cursor.
   Writes (POST/PUT/DELETE) are highlighted and link to the raw-resource viewer. */
(function () {
  var panel = document.getElementById('fhir-log');
  if (!panel) return;
  var entriesEl = document.getElementById('fhir-log-entries');
  var liveEl = document.getElementById('fhir-log-live');
  var toggle = document.getElementById('fhir-log-toggle');
  var writesOnly = document.getElementById('fhir-log-writes-only');
  var since = 0, failures = 0, MAX_ROWS = 200;

  if (localStorage.getItem('fhirLogCollapsed') === '1') panel.classList.add('collapsed');
  if (localStorage.getItem('fhirLogWritesOnly') === '1') {
    writesOnly.checked = true;
    panel.classList.add('writes-only');
  }
  toggle.addEventListener('click', function () {
    panel.classList.toggle('collapsed');
    localStorage.setItem('fhirLogCollapsed', panel.classList.contains('collapsed') ? '1' : '0');
  });
  writesOnly.addEventListener('change', function () {
    panel.classList.toggle('writes-only', writesOnly.checked);
    localStorage.setItem('fhirLogWritesOnly', writesOnly.checked ? '1' : '0');
  });

  function atBottom() {
    return entriesEl.scrollHeight - entriesEl.scrollTop - entriesEl.clientHeight < 40;
  }

  function render(e) {
    var isErr = e.status === null || e.status >= 400;
    var row = document.createElement(e.resource_id ? 'a' : 'div');
    row.className = 'fhir-row ' + e.kind + (isErr ? ' err' : '');
    if (e.resource_id) row.href = '/fhir/' + e.resource_id + '/raw';

    var tSpan = document.createElement('span');
    tSpan.className = 't';
    tSpan.textContent = new Date(e.ts).toLocaleTimeString([], { hour12: false });

    var mSpan = document.createElement('span');
    mSpan.className = 'm m-' + e.method.toLowerCase();  // class-only; no server data in innerHTML
    mSpan.textContent = e.method;

    var tgSpan = document.createElement('span');
    tgSpan.className = 'tg';
    tgSpan.textContent = e.target;

    row.appendChild(tSpan);
    row.appendChild(mSpan);
    row.appendChild(tgSpan);

    if (isErr) {
      var stSpan = document.createElement('span');
      stSpan.className = 'st';
      stSpan.textContent = String(e.status || 'net');
      row.appendChild(stSpan);
    }

    entriesEl.appendChild(row);
    while (entriesEl.children.length > MAX_ROWS) entriesEl.removeChild(entriesEl.firstChild);
  }

  function poll() {
    fetch('/api/fhir-log?since=' + since)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        failures = 0;
        liveEl.classList.remove('paused');
        var stick = atBottom();
        (data.entries || []).forEach(render);
        if (typeof data.latest === 'number') since = data.latest;
        if (stick) entriesEl.scrollTop = entriesEl.scrollHeight;
        schedule(1000);
      })
      .catch(function () {
        failures += 1;
        if (failures >= 5) liveEl.classList.add('paused');
        schedule(failures >= 5 ? 10000 : 1000);  // slow retry while paused, never give up
      });
  }

  function schedule(delay) {
    setTimeout(function () {
      if (document.hidden) { schedule(delay); return; }  // idle while tab is hidden
      poll();
    }, delay);
  }

  poll();
})();
