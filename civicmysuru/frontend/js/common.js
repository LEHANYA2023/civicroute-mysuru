const API_BASE = "http://127.0.0.1:8000";
document.addEventListener("DOMContentLoaded", () => {
  if (localStorage.getItem("civicTheme") === "light") document.body.classList.add("light");
  document.querySelectorAll("[data-theme-toggle]").forEach(b => b.onclick = () => {
    document.body.classList.toggle("light");
    localStorage.setItem("civicTheme", document.body.classList.contains("light") ? "light" : "dark")
  });
  const u = JSON.parse(localStorage.getItem("civicUser") || "null"),
    p = document.getElementById("userPill");
  if (p && u) p.textContent = u.name || u.email;
  const l = document.getElementById("logoutBtn");
  if (l) l.onclick = () => {
    localStorage.removeItem("civicUser");
    location.href = "login.html"
  }
});

function showToast(m) {
  const c = document.getElementById("toastContainer");
  if (!c) return;
  const t = document.createElement("div");
  t.className = "toast";
  t.textContent = m;
  c.appendChild(t);
  setTimeout(() => t.remove(), 3000)
}

function esc(v) {
  return String(v ?? "").replace(/[&<>"']/g, c => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  } [c]))
}