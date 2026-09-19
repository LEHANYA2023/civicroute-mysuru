document.addEventListener("DOMContentLoaded", () => {
  const f = document.getElementById("loginForm");
  if (!f) return;
  f.onsubmit = e => {
    e.preventDefault();
    const email = document.getElementById("email").value.trim(),
      password = document.getElementById("password").value;
    if (!email || password.length < 4) return;
    const name = email.split("@")[0].replace(/[._-]+/g, " ").replace(/\b\w/g, c => c.toUpperCase());
    localStorage.setItem("civicUser", JSON.stringify({
      email,
      name
    }));
    location.href = "dashboard.html"
  }
});