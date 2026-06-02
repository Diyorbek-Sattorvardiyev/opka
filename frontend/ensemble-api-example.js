const API_BASE_URL = "http://localhost:8000/api";
const MEDIA_BASE_URL = "http://localhost:8000";

function mediaUrl(path) {
    if (!path) return "";
    return path.startsWith("http") ? path : `${MEDIA_BASE_URL}${path}`;
}

async function uploadXrayWithDynamicEnsemble(file) {
    const formData = new FormData();
    formData.append("file", file);

    const token = localStorage.getItem("access_token");
    const headers = token ? { Authorization: `Bearer ${token}` } : {};

    showLoading(true);
    try {
        const response = await fetch(`${API_BASE_URL}/analysis/predict`, {
            method: "POST",
            headers,
            body: formData,
        });

        const payload = await response.json();
        if (!response.ok || !payload.success) {
            throw new Error(payload.message || "Tahlilda xatolik yuz berdi");
        }

        renderAnalysisResult(payload.data);
        return payload.data;
    } finally {
        showLoading(false);
    }
}

function renderAnalysisResult(data) {
    const finalResult = data.final_result;

    setImage("#original-image", data.original_image_url);
    setImage("#heatmap-image", data.heatmap_image_url);

    setText("#final-confidence", `${Number(finalResult.confidence).toFixed(1)}%`);
    setText("#final-risk", finalResult.risk_level);
    setText("#final-status", finalResult.pneumonia_detected ? "Pnevmoniya ehtimoli bor" : "Normal holatga yaqin");
    setText("#ensemble-method", finalResult.method);

    renderModelCards("#model-results", data.models || []);

    setText("#ai-summary", data.ai_summary);
    setText("#medical-disclaimer", data.medical_disclaimer);
}

function renderModelCards(containerSelector, models) {
    const container = document.querySelector(containerSelector);
    if (!container) return;

    container.innerHTML = models.map((model) => {
        if (!model.available) {
            return `
                <article class="model-card unavailable">
                    <h3>${model.name}</h3>
                    <p>Model hali ulanmagan</p>
                    <small>${model.message || "Model fayli topilmadi"}</small>
                </article>
            `;
        }

        return `
            <article class="model-card">
                <h3>${model.name}</h3>
                <p>${model.pneumonia_detected ? "Pnevmoniya ehtimoli" : "Normal"}</p>
                <strong>${Number(model.confidence).toFixed(1)}%</strong>
                <span>${model.risk_level}</span>
            </article>
        `;
    }).join("");
}

function setImage(selector, url) {
    const image = document.querySelector(selector);
    if (image && url) image.src = mediaUrl(url);
}

function setText(selector, value) {
    const element = document.querySelector(selector);
    if (element) element.textContent = value ?? "";
}

function showLoading(isLoading) {
    document.querySelectorAll("[data-loading]").forEach((element) => {
        element.hidden = !isLoading;
    });
}
