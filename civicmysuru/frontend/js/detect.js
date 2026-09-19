document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("detectImage");
  const description = document.getElementById("detectDescription");
  const fileNameEl = document.getElementById("detectFileName");
  const result = document.getElementById("detectionResult");

  input.addEventListener("change", () => {
    const file = input.files[0];
    if (!file) return;

    fileNameEl.textContent = `Selected: ${file.name}`;
    showScanning();
    setTimeout(() => runDetection(file), 900);
  });

  description.addEventListener("input", () => {
    if (input.files[0]) {
      clearTimeout(description._t);
      description._t = setTimeout(() => runDetection(input.files[0]), 500);
    }
  });

  function showScanning() {
    result.innerHTML = `
      <div style="text-align:center;padding:60px 20px">
        <div class="ai-icon" style="margin:auto">◌</div>
        <h3 style="font-family:'Space Grotesk';margin-top:20px">Analyzing image...</h3>
        <p class="muted" style="margin-top:8px;font-size:12px">Running the rule-based classifier</p>
      </div>`;
  }

  async function runDetection(file) {
    try {
      const r = await fetch(API_BASE + "/api/classify-issue", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filename: file.name,
          description: description.value.trim()
        })
      });
      if (!r.ok) throw 0;
      const d = await r.json();
      renderResult(d);
    } catch (e) {
      result.innerHTML = `
        <div class="detection-placeholder">
          <span>⚠</span>
          <p>Backend is not reachable.<br>Start FastAPI on ${API_BASE}</p>
        </div>`;
    }
  }

  function renderResult(d) {
    const keywordChips = (d.matched_keywords || [])
      .map(k => `<em>${esc(k)}</em>`)
      .join("");

    result.innerHTML = `
      <span class="section-label" style="color:var(--a);font-size:10px;letter-spacing:.14em;font-weight:700">AI ANALYSIS COMPLETE</span>
      <h3 style="font-family:'Space Grotesk';font-size:27px;margin:10px 0 20px">${esc(d.issue_type)}</h3>
      <div class="ai-result-grid">
        <div class="ai-result-item"><span>Detected Issue</span><strong>${esc(d.issue_type)}</strong></div>
        <div class="ai-result-item"><span>Confidence</span><strong>${Math.round(d.confidence * 100)}%</strong></div>
        <div class="ai-result-item"><span>Evidence</span><strong>Image Uploaded</strong></div>
        <div class="ai-result-item"><span>Suggested Action</span><strong>Create Complaint</strong></div>
      </div>
      ${keywordChips ? `<div class="ai-keywords">${keywordChips}</div>` : ""}
      <p class="ai-note">${esc(d.note || "Demo classifier.")}</p>
      <button class="btn primary" style="margin-top:18px" id="useResultBtn">Use Result to Report →</button>
    `;

    document.getElementById("useResultBtn").onclick = () => {
      const params = new URLSearchParams({
        issueType: d.issue_type,
        description: description.value.trim() ||
          `AI-assisted report: possible ${d.issue_type.toLowerCase()} detected in uploaded evidence.`
      });
      location.href = "report.html?" + params.toString();
    };
  }
});
