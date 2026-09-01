async function loadBackend() {
  const res = await fetch("/api/health");
  const data = await res.json();
  console.log(data);
}

window.addEventListener('DOMContentLoaded', loadBackend);