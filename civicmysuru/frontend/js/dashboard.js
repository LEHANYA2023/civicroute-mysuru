let complaints = [];
document.addEventListener("DOMContentLoaded", () => {
  load();
  ["searchComplaints", "statusFilter", "priorityFilter"].forEach(id => document.getElementById(id)?.addEventListener("input", render));
  document.getElementById("refreshBtn")?.addEventListener("click", load);
  document.getElementById("modalClose")?.addEventListener("click", close)
});
async function load() {
  try {
    const [a, b] = await Promise.all([fetch(API_BASE + "/api/complaints"), fetch(API_BASE + "/api/stats")]);
    if (!a.ok || !b.ok) throw 0;
    complaints = await a.json();
    const s = await b.json();
    ["total", "open", "in_progress", "resolved", "critical"].forEach((k, i) => document.getElementById(["totalComplaints", "openComplaints", "progressComplaints", "resolvedComplaints", "criticalComplaints"][i]).textContent = s[k]);
    render()
  } catch (e) {
    document.getElementById("complaintsList").innerHTML = '<div class="empty">Backend is not reachable.<br>Start FastAPI on http://127.0.0.1:8000</div>'
  }
}

function render() {
  const q = document.getElementById("searchComplaints").value.toLowerCase(),
    s = document.getElementById("statusFilter").value,
    p = document.getElementById("priorityFilter").value;
  const a = complaints.filter(c => (!q || `${c.id} ${c.area} ${c.issue_type} ${c.description}`.toLowerCase().includes(q)) && (!s || c.status === s) && (!p || c.priority === p));
  document.getElementById("complaintsList").innerHTML = a.length ? a.map(c => `<div class="complaint" onclick="openComplaint('${esc(c.id)}')"><span class="id">${esc(c.id)}</span><div><b>${esc(c.issue_type)}</b><small>${esc(c.area)} • ${esc(c.department)}</small></div><span class="badges"><em class="${c.priority.toLowerCase()}">${esc(c.priority)}</em><em>${esc(c.status)}</em></span></div>`).join("") : '<div class="empty">No complaints found.</div>'
}

function openComplaint(id) {
  const c = complaints.find(x => x.id === id);
  if (!c) return;
  document.getElementById("modalContent").innerHTML = `<div class="eyebrow">COMPLAINT DETAIL</div><h2>${esc(c.id)}</h2><p class="muted">${esc(c.description)}</p><div class="detail-grid">${d("Issue",c.issue_type)}${d("Area",c.area)}${d("Authority",c.authority)}${d("Department",c.department)}${d("Jurisdiction",c.jurisdiction)}${d("Priority",c.priority)}${d("Verification",c.verification_score+"% — "+c.verification_status)}${d("Status",c.status)}</div><div class="actions">${c.status!=="In Progress"&&c.status!=="Resolved"?`<button class="btn ghost" onclick="changeStatus('${esc(c.id)}','In Progress')">Start Work</button>`:""}${c.status!=="Resolved"?`<button class="btn primary" onclick="changeStatus('${esc(c.id)}','Resolved')">Mark Resolved</button>`:""}</div>`;
  document.getElementById("modal").classList.remove("hidden")
}

function d(a, b) {
  return `<div class="detail"><small>${esc(a)}</small><b>${esc(b)}</b></div>`
}

function close() {
  document.getElementById("modal").classList.add("hidden")
}
async function changeStatus(id, status) {
  try {
    const r = await fetch(API_BASE + "/api/complaints/" + encodeURIComponent(id) + "/status", {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        status
      })
    });
    if (!r.ok) throw 0;
    showToast("Complaint " + id + " → " + status);
    close();
    load()
  } catch (e) {
    showToast("Could not update complaint.")
  }
}