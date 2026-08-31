async function loadBackend() {
  const res = await fetch("http://backend:8000/api/health");
  const data = await res.json();
  console.log(data);
}