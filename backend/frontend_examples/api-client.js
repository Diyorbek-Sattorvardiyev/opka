const API_BASE_URL = "http://localhost:8000/api";

function getToken() {
  return localStorage.getItem("access_token");
}

async function apiRequest(path, options = {}) {
  const headers = {
    ...(options.headers || {}),
  };

  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  const payload = await response.json();
  if (!response.ok || !payload.success) {
    throw new Error(payload.message || "API xatoligi");
  }
  return payload.data;
}

async function register(fullName, email, password) {
  const data = await apiRequest("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ full_name: fullName, email, password }),
  });
  localStorage.setItem("access_token", data.access_token);
  return data.user;
}

async function login(email, password) {
  const data = await apiRequest("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  localStorage.setItem("access_token", data.access_token);
  return data.user;
}

async function predictXray(file) {
  const formData = new FormData();
  formData.append("file", file);
  return apiRequest("/analysis/predict", {
    method: "POST",
    body: formData,
  });
}

async function predictAndRenderXray(file) {
  const data = await predictXray(file);

  const modelContainer = document.querySelector("#model-results");
  if (modelContainer) {
    modelContainer.innerHTML = data.models.map((model) => {
      if (!model.available) {
        return `<article><strong>${model.name}</strong><p>Model hali ulanmagan</p></article>`;
      }
      return `<article><strong>${model.name}</strong><p>${model.confidence}% (${model.risk_level})</p></article>`;
    }).join("");
  }

  document.querySelector("#ensemble-card").textContent =
    `Yakuniy: ${data.final_result.confidence}% (${data.final_result.risk_level})`;
  document.querySelector("#original-image").src = `http://localhost:8000${data.original_image_url}`;
  document.querySelector("#heatmap-image").src = `http://localhost:8000${data.heatmap_image_url}`;
  document.querySelector("#ai-summary").textContent = data.ai_summary;
  document.querySelector("#medical-disclaimer").textContent = data.medical_disclaimer;
  return data;
}

async function loadHistory() {
  return apiRequest("/analysis/history");
}

async function loadStats() {
  return apiRequest("/dashboard/stats");
}

function logout() {
  localStorage.removeItem("access_token");
  window.location.href = "login.html";
}
