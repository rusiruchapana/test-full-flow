async function loadBackend() {
  const res = await fetch("http://localhost:8000/api/health");
  const data = await res.json();
  console.log(data);
}

window.addEventListener('DOMContentLoaded', loadBackend);