document.addEventListener("DOMContentLoaded", () => {
  const u = JSON.parse(localStorage.getItem("civicUser") || "null");
  if (u?.name) document.getElementById("citizenName").value = u.name;

  // Prefill from an AI Detection handoff (detect.html -> report.html?issueType=...&description=...)
  const params = new URLSearchParams(location.search);
  const handoffIssue = params.get("issueType");
  const handoffDescription = params.get("description");
  if (handoffIssue) {
    const s = document.getElementById("issueType");
    const o = [...s.options].find(x => x.text === handoffIssue);
    if (o) s.value = handoffIssue;
  }
  if (handoffDescription) document.getElementById("description").value = handoffDescription;
  if (handoffIssue || handoffDescription) showToast("AI detection result transferred to this form.");

  ["area", "issueType", "description"].forEach(id => document.getElementById(id).addEventListener("input", preview));
  document.getElementById("complaintImage").onchange = e => {
    document.getElementById("imageName").textContent = e.target.files[0] ? `Selected: ${e.target.files[0].name}` : ""
  };
  document.getElementById("classifyBtn").onclick = classify;
  document.getElementById("complaintForm").onsubmit = submit;
  document.getElementById("detectLocation").onclick = detectLocation;
  preview()
});
let timer;

function preview() {
  clearTimeout(timer);
  timer = setTimeout(async () => {
    const area = document.getElementById("area").value.trim(),
      issue = document.getElementById("issueType").value.trim(),
      description = document.getElementById("description").value.trim();
    if (!area && !issue) return;
    try {
      const q = new URLSearchParams({
        area: area || "Other",
        issue_type: issue || "Other",
        description
      });
      const r = await fetch(API_BASE + "/api/route-preview?" + q);
      const d = await r.json();
      document.getElementById("previewAuthority").textContent = d.authority;
      document.getElementById("previewDepartment").textContent = d.department;
      document.getElementById("previewPriority").textContent = d.priority + " (" + d.priority_score + ")";
      document.getElementById("previewMode").textContent = d.routing_mode
    } catch (e) {
      document.getElementById("previewAuthority").textContent = "Backend offline";
      document.getElementById("previewDepartment").textContent = "Start FastAPI"
    }
  }, 350)
}
function detectLocation() {
  if (!navigator.geolocation) {
    showToast("Location detection is not supported.");
    return;
  }
  showToast("Detecting your location...");
  navigator.geolocation.getCurrentPosition(
    position => {
      const lat = position.coords.latitude.toFixed(5);
      const lng = position.coords.longitude.toFixed(5);
      document.getElementById("location").value = `GPS: ${lat}, ${lng}`;
      showToast("Location detected successfully.");
    },
    () => {
      showToast("Location permission was not granted.");
    }
  );
}

async function classify() {
  const f = document.getElementById("complaintImage").files[0],
    description = document.getElementById("description").value;
  try {
    const r = await fetch(API_BASE + "/api/classify-issue", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        filename: f?.name || "",
        description
      })
    });
    const d = await r.json();
    document.getElementById("aiText").textContent = `${d.issue_type} • ${(d.confidence*100).toFixed(0)}% demo confidence`;
    const s = document.getElementById("issueType"),
      o = [...s.options].find(x => x.text === d.issue_type);
    if (o) {
      s.value = d.issue_type;
      preview()
    }
  } catch (e) {
    document.getElementById("aiText").textContent = "AI service unavailable. Start FastAPI first."
  }
}
async function submit(e) {
  e.preventDefault();
  const f = document.getElementById("complaintImage").files[0],
    body = {
      citizen_name: document.getElementById("citizenName").value.trim(),
      area: document.getElementById("area").value.trim(),
      issue_type: document.getElementById("issueType").value.trim(),
      location: document.getElementById("location").value.trim(),
      description: document.getElementById("description").value.trim(),
      image_name: f?.name || null
    };
  try {
    const r = await fetch(API_BASE + "/api/complaints", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(body)
      }),
      d = await r.json();
    if (!r.ok) throw Error(d.detail || "Submission failed");
    showToast("Complaint " + d.id + " submitted");
    setTimeout(() => location.href = "dashboard.html", 900)
  } catch (x) {
    showToast(x.message)
  }
}