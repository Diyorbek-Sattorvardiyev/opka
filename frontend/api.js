const API_ORIGIN = window.location.protocol.startsWith("http") ? window.location.origin : "http://localhost:8000";
const API_BASE_URL = `${API_ORIGIN}/api`;
const MEDIA_BASE_URL = API_ORIGIN;

function getToken() {
    return localStorage.getItem("access_token");
}

function setToken(token) {
    localStorage.setItem("access_token", token);
}

function requireToken() {
    const token = getToken();
    if (!token) {
        window.location.href = "login.html";
        return null;
    }
    return token;
}

async function apiRequest(path, options = {}) {
    const headers = { ...(options.headers || {}) };
    const token = getToken();

    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers,
    });
    const contentType = response.headers.get("content-type") || "";
    const payload = contentType.includes("application/json")
        ? await response.json()
        : { success: response.ok, message: await response.text() };

    if (!response.ok || payload.success === false) {
        throw new Error(payload.message || payload.detail || "API xatoligi");
    }

    return payload.data ?? payload;
}

function absoluteMediaUrl(url) {
    if (!url) return "";
    if (url.startsWith("http")) return url;
    return `${MEDIA_BASE_URL}${url}`;
}

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
    }[char]));
}

function numberOrZero(value) {
    const number = Number(value);
    return Number.isFinite(number) ? number : 0;
}

function clampPercent(value) {
    return Math.max(0, Math.min(100, numberOrZero(value)));
}

function formatPercent(value, digits = 0) {
    return `${clampPercent(value).toFixed(digits)}%`;
}

function formatDate(value, options = {}) {
    if (!value) return "-";
    const date = new Date(value.includes("T") ? value : `${value}T00:00:00`);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleDateString("uz-UZ", options);
}

function getFinalResult(analysis) {
    return analysis?.final_result || analysis?.ensemble_result || analysis || {};
}

function riskLabel(riskLevel) {
    const risk = String(riskLevel || "").toUpperCase();
    if (risk === "NORMAL") return "Normal";
    if (risk === "RISK") return "Xavf";
    if (risk === "CRITICAL") return "Kritik";
    return riskLevel || "-";
}

function setButtonLoading(button, isLoading, loadingText) {
    if (!button) return;
    if (isLoading) {
        if (!button.dataset.originalHtml) button.dataset.originalHtml = button.innerHTML;
        button.disabled = true;
        button.style.opacity = "0.75";
        button.textContent = loadingText;
    } else {
        button.disabled = false;
        button.style.opacity = "";
        if (button.dataset.originalHtml) {
            button.innerHTML = button.dataset.originalHtml;
            delete button.dataset.originalHtml;
        }
    }
}

function wireNavigation() {
    document.querySelectorAll("a").forEach((link) => {
        const text = link.textContent.trim().toLowerCase();
        if (text === "home" || text === "bosh sahifa") link.href = "tahlil.html";
        if (text === "history" || text === "tarix") link.href = "tarix.html";
        if (text === "statistics" || text === "statistika") link.href = "statistika.html";
        if (text.includes("ro'yxatdan") || text.includes("ro'yhatdan")) link.href = "regstr.html";
        if (text.includes("log in") || text.includes("tizimga kiring")) link.href = "login.html";
    });

    document.querySelectorAll('[data-icon="logout"], .material-symbols-outlined').forEach((icon) => {
        if (icon.textContent.trim() === "logout") {
            icon.addEventListener("click", () => {
                localStorage.removeItem("access_token");
                window.location.href = "login.html";
            });
        }
    });
}

function initLoginPage() {
    if (!location.pathname.endsWith("login.html")) return;

    const form = document.querySelector("form");
    const emailInput = document.querySelector("#username");
    const passwordInput = document.querySelector("#password");
    const submitButton = form?.querySelector('button[type="submit"]');
    const togglePasswordButton = document.querySelector('[data-action="toggle-password"]');

    togglePasswordButton?.addEventListener("click", () => {
        const isVisible = passwordInput.type === "text";
        passwordInput.type = isVisible ? "password" : "text";
        const icon = togglePasswordButton.querySelector(".material-symbols-outlined");
        if (icon) {
            icon.textContent = isVisible ? "visibility" : "visibility_off";
            icon.dataset.icon = icon.textContent;
        }
    });

    form?.addEventListener("submit", async (event) => {
        event.preventDefault();
        const email = emailInput.value.trim();
        const password = passwordInput.value;

        if (!email || !password) {
            alert("Email va parolni kiriting");
            return;
        }

        try {
            setButtonLoading(submitButton, true, "Kirilmoqda...");
            const data = await apiRequest("/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });
            setToken(data.access_token);
            window.location.href = "tahlil.html";
        } catch (error) {
            alert(error.message);
        } finally {
            setButtonLoading(submitButton, false);
        }
    });
}

function initRegisterPage() {
    if (!location.pathname.endsWith("regstr.html")) return;

    const form = document.querySelector("form");
    const submitButton = form?.querySelector('button[type="submit"]');
    const inputs = form ? Array.from(form.querySelectorAll("input")) : [];

    form?.addEventListener("submit", async (event) => {
        event.preventDefault();
        const fullName = inputs[0]?.value.trim();
        const email = inputs[2]?.value.trim();
        const password = inputs[3]?.value;
        const confirmPassword = inputs[4]?.value;
        const terms = document.querySelector("#terms");

        if (!fullName || !email || !password) {
            alert("Ism, email va parolni kiriting");
            return;
        }
        if (password !== confirmPassword) {
            alert("Parollar bir xil emas");
            return;
        }
        if (terms && !terms.checked) {
            alert("Shartlarga rozilik belgilang");
            return;
        }

        try {
            setButtonLoading(submitButton, true, "Yaratilmoqda...");
            const data = await apiRequest("/auth/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    full_name: fullName,
                    email,
                    password,
                }),
            });
            setToken(data.access_token);
            window.location.href = "tahlil.html";
        } catch (error) {
            alert(error.message);
        } finally {
            setButtonLoading(submitButton, false);
        }
    });
}

function initAnalysisPage() {
    if (!location.pathname.endsWith("tahlil.html")) return;

    const uploadZone = document.querySelector(".border-dashed");
    const uploadButton = document.querySelector('[data-action="upload-image"]') || uploadZone?.querySelector("button");
    const viewer = document.querySelector(".diagnostic-viewer");
    const viewerImage = document.querySelector(".diagnostic-viewer img");
    const zoomButton = document.querySelector('[data-action="zoom-in"]');
    const fullscreenButton = document.querySelector('[data-action="fullscreen-viewer"]');
    const overlayButton = document.querySelector('[data-action="toggle-ai-overlay"]');
    const reanalyzeButton = document.querySelector('[data-action="reanalyze"]');
    const reportButton = document.querySelector('[data-action="download-report"]');
    const saveButton = document.querySelector('[data-action="save-analysis"]');
    const resultHeader = document.querySelector(".xl\\:col-span-5 .bg-error, .xl\\:col-span-5 .bg-emerald-600");
    const resultTitle = document.querySelector(".xl\\:col-span-5 h2");
    const scanId = document.querySelector(".xl\\:col-span-5 h2 + p");
    const badge = document.querySelector(".xl\\:col-span-5 .bg-white\\/20");
    const confidenceText = document.querySelector(".xl\\:col-span-5 .font-display-lg.text-display-lg");
    const progressBar = document.querySelector(".w-full.bg-slate-100.h-2 .h-full");
    const summaryText = document.querySelector(".border-l-4 p");
    const insightBox = document.querySelector(".bg-slate-50.border-l-4");

    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.accept = "image/png,image/jpeg";
    fileInput.style.display = "none";
    document.body.appendChild(fileInput);

    let currentZoom = 1;
    let overlayVisible = true;
    let lastFile = null;
    let lastAnalysis = null;

    function pickFile() {
        fileInput.click();
    }

    function updateOverlayButton() {
        if (!overlayButton) return;
        const iconName = overlayVisible ? "visibility" : "visibility_off";
        const label = overlayVisible ? "AI tahlilni yashirish" : "AI tahlilni ko'rsatish";
        overlayButton.innerHTML = `
            <span class="material-symbols-outlined text-emerald-400" data-icon="${iconName}" data-weight="fill">${iconName}</span>
            ${label}
        `;
    }

    function updateViewerImage() {
        if (!viewerImage) return;
        if (lastAnalysis) {
            const heatmapUrl = lastAnalysis.heatmap_image_url || lastAnalysis.heatmap_url;
            const originalUrl = lastAnalysis.original_image_url || lastAnalysis.original_url;
            const selectedUrl = overlayVisible ? (heatmapUrl || originalUrl) : (originalUrl || heatmapUrl);
            if (selectedUrl) viewerImage.src = absoluteMediaUrl(selectedUrl);
            viewerImage.style.opacity = "0.9";
        } else {
            viewerImage.style.opacity = overlayVisible ? "0.9" : "0.45";
        }
    }

    function updateResultView(data) {
        const finalResult = getFinalResult(data);
        const confidence = clampPercent(finalResult.confidence);
        const isNormal = !finalResult.pneumonia_detected;

        lastAnalysis = data;
        overlayVisible = true;
        updateViewerImage();
        updateOverlayButton();

        if (resultTitle) resultTitle.textContent = isNormal ? "Normal holatga yaqin" : "Pnevmoniya ehtimoli aniqlandi";
        if (scanId) scanId.textContent = `ID: SCAN-${data.analysis_id || data.id || "-"}`;
        if (badge) badge.textContent = riskLabel(finalResult.risk_level);
        if (confidenceText) {
            confidenceText.textContent = formatPercent(confidence);
            confidenceText.classList.toggle("text-error", !isNormal);
            confidenceText.classList.toggle("text-emerald-600", isNormal);
        }
        if (progressBar) {
            progressBar.style.width = `${confidence}%`;
            progressBar.classList.toggle("bg-error", !isNormal);
            progressBar.classList.toggle("bg-emerald-600", isNormal);
        }
        if (summaryText) summaryText.textContent = data.ai_summary || "AI izohi mavjud emas.";
        if (insightBox) {
            insightBox.classList.toggle("border-error", !isNormal);
            insightBox.classList.toggle("border-emerald-600", isNormal);
        }
        if (resultHeader) {
            resultHeader.classList.toggle("bg-error", !isNormal);
            resultHeader.classList.toggle("bg-emerald-600", isNormal);
        }

        const statCards = document.querySelectorAll(".grid.grid-cols-2.gap-4 .font-title-sm.text-title-sm.text-slate-800");
        const models = data.models || [];
        models.slice(0, statCards.length).forEach((model, index) => {
            if (!statCards[index]) return;
            statCards[index].textContent = model.available
                ? `${model.name} ${formatPercent(model.confidence)}`
                : `${model.name}: Model hali ulanmagan`;
        });
    }

    function buildReportText() {
        if (!lastAnalysis) return "";
        const finalResult = getFinalResult(lastAnalysis);
        const models = lastAnalysis.models || [];
        const lines = [
            "AI Lung Scan hisobot",
            `Tahlil ID: SCAN-${lastAnalysis.analysis_id || lastAnalysis.id || "-"}`,
            `Natija: ${finalResult.pneumonia_detected ? "Pnevmoniya ehtimoli" : "Normal"}`,
            `Xavf darajasi: ${riskLabel(finalResult.risk_level)}`,
            `Ishonch: ${formatPercent(finalResult.confidence, 1)}`,
            `Sana: ${formatDate(lastAnalysis.created_at, { year: "numeric", month: "2-digit", day: "2-digit" })}`,
            "",
            "AI izoh:",
            lastAnalysis.ai_summary || "Mavjud emas",
            "",
            "Model natijalari:",
            ...(models.length ? models.map((model) => `- ${model.name}: ${model.available ? formatPercent(model.confidence, 1) : "ulanmagan"}`) : ["- Model natijalari mavjud emas"]),
            "",
            lastAnalysis.medical_disclaimer || "Bu hisobot shifokor xulosasini almashtirmaydi.",
        ];
        return lines.join("\n");
    }

    async function uploadXray(file, loadingButton = uploadButton) {
        if (!file) return;
        if (!file.type.startsWith("image/")) {
            alert("Faqat JPG yoki PNG rasm yuklang");
            return;
        }

        lastFile = file;
        const formData = new FormData();
        formData.append("file", file);

        try {
            setButtonLoading(loadingButton, true, "Tahlil qilinmoqda...");
            const data = await apiRequest("/analysis/predict", {
                method: "POST",
                body: formData,
            });
            updateResultView(data);
            localStorage.setItem("latest_analysis", JSON.stringify(data));
        } catch (error) {
            alert(error.message);
        } finally {
            setButtonLoading(loadingButton, false);
        }
    }

    uploadZone?.addEventListener("click", pickFile);
    uploadButton?.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        pickFile();
    });

    uploadZone?.addEventListener("dragover", (event) => {
        event.preventDefault();
    });

    uploadZone?.addEventListener("drop", (event) => {
        event.preventDefault();
        const file = event.dataTransfer.files[0];
        if (file) uploadXray(file);
    });

    fileInput.addEventListener("change", () => {
        const file = fileInput.files[0];
        if (file) uploadXray(file);
        fileInput.value = "";
    });

    zoomButton?.addEventListener("click", () => {
        currentZoom = currentZoom >= 2 ? 1 : Number((currentZoom + 0.25).toFixed(2));
        if (viewerImage) {
            viewerImage.style.transform = `scale(${currentZoom})`;
            viewerImage.style.transition = "transform 150ms ease";
            viewerImage.style.cursor = currentZoom > 1 ? "zoom-out" : "default";
        }
    });

    fullscreenButton?.addEventListener("click", async () => {
        if (!viewer) return;
        try {
            if (document.fullscreenElement) {
                await document.exitFullscreen();
            } else {
                await viewer.requestFullscreen();
            }
        } catch (error) {
            alert("Fullscreen rejimini ochib bo'lmadi");
        }
    });

    overlayButton?.addEventListener("click", () => {
        overlayVisible = !overlayVisible;
        updateViewerImage();
        updateOverlayButton();
    });

    reanalyzeButton?.addEventListener("click", () => {
        if (lastFile) {
            uploadXray(lastFile, reanalyzeButton);
            return;
        }
        pickFile();
    });

    reportButton?.addEventListener("click", () => {
        const reportText = buildReportText();
        if (!reportText) {
            alert("Avval rasm yuklab tahlil qiling");
            return;
        }
        const blob = new Blob([reportText], { type: "text/plain;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `ai-lung-scan-${lastAnalysis.analysis_id || lastAnalysis.id || "report"}.txt`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    });

    saveButton?.addEventListener("click", () => {
        if (!lastAnalysis) {
            alert("Avval rasm yuklab tahlil qiling");
            return;
        }
        localStorage.setItem("latest_analysis", JSON.stringify(lastAnalysis));
        alert("Tahlil saqlandi. Serverdagi yozuv Tarix sahifasida ko'rinadi.");
    });

    updateOverlayButton();
}

function ensureAnalysisModal() {
    let modal = document.querySelector("#analysis-detail-modal");
    if (modal) return modal;

    document.body.insertAdjacentHTML("beforeend", `
        <div id="analysis-detail-modal" class="hidden fixed inset-0 z-[100] bg-slate-900/60 px-4 py-8 overflow-y-auto">
            <div class="min-h-full flex items-center justify-center">
                <div class="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-3xl overflow-hidden">
                    <div class="flex items-center justify-between p-5 border-b border-slate-200">
                        <h2 class="font-headline-md text-slate-900">Tahlil tafsilotlari</h2>
                        <button class="p-2 rounded-lg hover:bg-slate-100" data-action="close-modal" type="button">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                    <div class="p-6 space-y-5" data-modal-content></div>
                </div>
            </div>
        </div>
    `);

    modal = document.querySelector("#analysis-detail-modal");
    modal.addEventListener("click", (event) => {
        if (event.target === modal || event.target.closest('[data-action="close-modal"]')) {
            modal.classList.add("hidden");
        }
    });
    return modal;
}

function showAnalysisDetail(analysis) {
    const modal = ensureAnalysisModal();
    const content = modal.querySelector("[data-modal-content]");
    const finalResult = getFinalResult(analysis);
    const models = analysis.models || [];
    const imageUrl = absoluteMediaUrl(analysis.heatmap_image_url || analysis.original_image_url);

    content.innerHTML = `
        <div class="grid md:grid-cols-[220px_1fr] gap-6">
            <div class="bg-slate-900 rounded-lg overflow-hidden aspect-square flex items-center justify-center">
                ${imageUrl ? `<img class="w-full h-full object-contain" src="${escapeHtml(imageUrl)}" alt="Tahlil tasviri" />` : `<span class="text-slate-400">Rasm mavjud emas</span>`}
            </div>
            <div class="space-y-4">
                <div>
                    <p class="text-xs text-slate-500 uppercase font-bold tracking-wider">Tahlil ID</p>
                    <p class="text-xl font-bold text-slate-900">SCAN-${escapeHtml(analysis.analysis_id || analysis.id || "-")}</p>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div class="p-4 bg-slate-50 rounded-lg border border-slate-100">
                        <p class="text-xs text-slate-500 uppercase font-bold tracking-wider">Natija</p>
                        <p class="font-bold text-slate-900">${finalResult.pneumonia_detected ? "Pnevmoniya ehtimoli" : "Normal"}</p>
                    </div>
                    <div class="p-4 bg-slate-50 rounded-lg border border-slate-100">
                        <p class="text-xs text-slate-500 uppercase font-bold tracking-wider">Ishonch</p>
                        <p class="font-bold text-slate-900">${formatPercent(finalResult.confidence, 1)}</p>
                    </div>
                    <div class="p-4 bg-slate-50 rounded-lg border border-slate-100">
                        <p class="text-xs text-slate-500 uppercase font-bold tracking-wider">Xavf</p>
                        <p class="font-bold text-slate-900">${escapeHtml(riskLabel(finalResult.risk_level))}</p>
                    </div>
                    <div class="p-4 bg-slate-50 rounded-lg border border-slate-100">
                        <p class="text-xs text-slate-500 uppercase font-bold tracking-wider">Sana</p>
                        <p class="font-bold text-slate-900">${escapeHtml(formatDate(analysis.created_at, { year: "numeric", month: "2-digit", day: "2-digit" }))}</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="p-4 bg-cyan-50 rounded-lg border border-cyan-100 text-slate-700">
            ${escapeHtml(analysis.ai_summary || "AI izohi mavjud emas.")}
        </div>
        <div class="grid md:grid-cols-2 gap-3">
            ${models.length ? models.map((model) => `
                <div class="p-4 bg-slate-50 rounded-lg border border-slate-100">
                    <p class="font-bold text-slate-900">${escapeHtml(model.name || model.key || "Model")}</p>
                    <p class="text-sm text-slate-600">${model.available ? `${formatPercent(model.confidence, 1)} ishonch` : "Model ulanmagan"}</p>
                </div>
            `).join("") : `<div class="p-4 bg-slate-50 rounded-lg border border-slate-100 text-slate-600">Model natijalari mavjud emas.</div>`}
        </div>
    `;
    modal.classList.remove("hidden");
}

function showStaticHistoryDetail(card) {
    const title = card.querySelector(".text-title-sm.font-title-sm.text-primary")?.textContent.trim() || "Tahlil";
    const id = card.querySelector(".text-xs.text-slate-500")?.textContent.trim() || "";
    const status = card.querySelector("span.inline-flex")?.textContent.trim() || "-";
    const confidence = Array.from(card.querySelectorAll(".text-title-sm.font-title-sm.text-primary"))[1]?.textContent.trim() || "-";
    const date = Array.from(card.querySelectorAll(".text-body-md.font-body-md.text-primary"))[0]?.textContent.trim() || "-";
    showAnalysisDetail({
        id: id || title,
        created_at: date,
        ai_summary: `${title} bo'yicha demo tahlil ma'lumotlari. Real tafsilotlar backenddan yuklanganda to'liq ko'rsatiladi.`,
        final_result: {
            pneumonia_detected: status.toLowerCase().includes("pnevmoniya"),
            confidence: parseFloat(confidence) || 0,
            risk_level: status.toLowerCase().includes("pnevmoniya") ? "RISK" : "NORMAL",
        },
    });
}

function applyHistoryFilter(container, statusSelect, dateInput) {
    const cards = Array.from(container.querySelectorAll(".diagnostic-card"));
    const selectedStatus = (statusSelect?.value || "Barcha statuslar").toLowerCase();
    const dateQuery = (dateInput?.value || "").trim().toLowerCase();
    let visibleCount = 0;

    cards.forEach((card) => {
        const statusText = (card.dataset.status || card.querySelector("span.inline-flex")?.textContent || "").toLowerCase();
        const riskText = (card.dataset.risk || "").toLowerCase();
        const dateText = `${card.dataset.date || ""} ${card.textContent || ""}`.toLowerCase();
        const matchesStatus = selectedStatus.includes("barcha")
            || (selectedStatus.includes("normal") && statusText.includes("normal"))
            || (selectedStatus.includes("pnevmoniya") && statusText.includes("pnevmoniya"))
            || (selectedStatus.includes("kritik") && (riskText.includes("critical") || riskText.includes("kritik")));
        const matchesDate = !dateQuery || dateText.includes(dateQuery);
        const isVisible = matchesStatus && matchesDate;
        card.classList.toggle("hidden", !isVisible);
        if (isVisible) visibleCount += 1;
    });

    let emptyMessage = container.querySelector("[data-filter-empty]");
    if (!emptyMessage) {
        container.insertAdjacentHTML("beforeend", '<div class="hidden bg-white rounded-xl p-6 border border-slate-200 shadow-sm text-slate-500" data-filter-empty>Mos tahlil topilmadi.</div>');
        emptyMessage = container.querySelector("[data-filter-empty]");
    }
    emptyMessage.classList.toggle("hidden", visibleCount !== 0 || cards.length === 0);
}

function wireHistoryControls(container) {
    const statusSelect = document.querySelector("select");
    const dateInput = document.querySelector('input[type="text"]');
    const filterButton = document.querySelector('[data-action="filter-history"]');

    filterButton?.addEventListener("click", () => applyHistoryFilter(container, statusSelect, dateInput));
    statusSelect?.addEventListener("change", () => applyHistoryFilter(container, statusSelect, dateInput));
    dateInput?.addEventListener("input", () => applyHistoryFilter(container, statusSelect, dateInput));

    container.querySelectorAll('[data-action="show-static-detail"]').forEach((button) => {
        button.addEventListener("click", () => showStaticHistoryDetail(button.closest(".diagnostic-card")));
    });

    document.querySelectorAll(".flex.justify-center.mt-12 button").forEach((button) => {
        button.addEventListener("click", () => {
            const label = button.textContent.trim();
            if (!/^[0-9]+$/.test(label)) return;
            document.querySelectorAll(".flex.justify-center.mt-12 button").forEach((item) => {
                item.classList.remove("bg-secondary", "text-white");
                item.classList.add("border", "border-slate-200", "text-slate-600");
            });
            button.classList.add("bg-secondary", "text-white");
            button.classList.remove("border", "border-slate-200", "text-slate-600");
        });
    });
}

function renderHistoryItems(container, items) {
    container.innerHTML = "";

    if (!items.length) {
        container.innerHTML = '<div class="bg-white rounded-xl p-6 border border-slate-200 shadow-sm text-slate-500">Hozircha tahlillar mavjud emas.</div>';
        return;
    }

    items.forEach((item) => {
        const ensemble = getFinalResult(item);
        const confidence = clampPercent(ensemble.confidence);
        const statusText = ensemble.pneumonia_detected ? "Pnevmoniya ehtimoli" : "Normal";
        const statusClass = ensemble.pneumonia_detected
            ? "bg-error-container text-on-error-container"
            : "bg-tertiary-fixed text-on-tertiary-fixed-variant";
        const createdAt = new Date(item.created_at);
        const dateText = Number.isNaN(createdAt.getTime()) ? "-" : createdAt.toLocaleDateString("uz-UZ");
        const timeText = Number.isNaN(createdAt.getTime()) ? "" : createdAt.toLocaleTimeString("uz-UZ", { hour: "2-digit", minute: "2-digit" });
        const imageUrl = absoluteMediaUrl(item.heatmap_image_url || item.original_image_url);

        container.insertAdjacentHTML("beforeend", `
            <div class="diagnostic-card bg-white rounded-xl p-4 border border-slate-200 transition-all flex flex-col md:flex-row items-center gap-6 shadow-sm" data-status="${escapeHtml(statusText)}" data-risk="${escapeHtml(ensemble.risk_level || "")}" data-date="${escapeHtml(item.created_at || "")}">
                <div class="w-full md:w-32 h-32 bg-slate-900 rounded-lg overflow-hidden flex-shrink-0">
                    ${imageUrl ? `<img class="w-full h-full object-cover opacity-80 hover:opacity-100 transition-opacity" src="${escapeHtml(imageUrl)}" alt="X-ray heatmap" />` : ""}
                </div>
                <div class="flex-grow grid grid-cols-2 md:grid-cols-4 gap-4 w-full">
                    <div>
                        <p class="text-label-caps font-label-caps text-on-surface-variant uppercase tracking-wider mb-1">Tahlil ID</p>
                        <p class="text-title-sm font-title-sm text-primary">SCAN-${escapeHtml(item.analysis_id || item.id)}</p>
                        <p class="text-xs text-slate-500">${escapeHtml(item.model_name || "")}</p>
                    </div>
                    <div>
                        <p class="text-label-caps font-label-caps text-on-surface-variant uppercase tracking-wider mb-1">Status</p>
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${statusClass}">${statusText}</span>
                    </div>
                    <div>
                        <p class="text-label-caps font-label-caps text-on-surface-variant uppercase tracking-wider mb-1">Ishonch darajasi</p>
                        <div class="flex items-center gap-2">
                            <span class="text-title-sm font-title-sm text-primary">${formatPercent(confidence, 1)}</span>
                            <div class="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                <div class="h-full bg-cyan-600" style="width: ${confidence}%;"></div>
                            </div>
                        </div>
                    </div>
                    <div>
                        <p class="text-label-caps font-label-caps text-on-surface-variant uppercase tracking-wider mb-1">Sana</p>
                        <p class="text-body-md font-body-md text-primary">${escapeHtml(dateText)}</p>
                        <p class="text-xs text-slate-500">${escapeHtml(timeText)}</p>
                    </div>
                </div>
                <div class="flex-shrink-0 w-full md:w-auto flex flex-col gap-2">
                    <button class="w-full md:w-auto border border-secondary text-secondary px-6 py-2.5 rounded-lg text-body-sm font-bold hover:bg-secondary hover:text-white transition-all" data-detail-id="${escapeHtml(item.id)}">Batafsil</button>
                    <button class="w-full md:w-auto border border-error text-error px-6 py-2.5 rounded-lg text-body-sm font-bold hover:bg-error hover:text-white transition-all" data-delete-id="${escapeHtml(item.id)}">O'chirish</button>
                </div>
            </div>
        `);
    });

    container.querySelectorAll("[data-detail-id]").forEach((button) => {
        button.addEventListener("click", async () => {
            try {
                const item = await apiRequest(`/analysis/${button.dataset.detailId}`);
                showAnalysisDetail(item);
            } catch (error) {
                alert(error.message);
            }
        });
    });

    container.querySelectorAll("[data-delete-id]").forEach((button) => {
        button.addEventListener("click", async () => {
            if (!confirm("Tahlil o'chirilsinmi?")) return;
            try {
                await apiRequest(`/analysis/${button.dataset.deleteId}`, { method: "DELETE" });
                button.closest(".diagnostic-card")?.remove();
                if (!container.querySelector(".diagnostic-card")) {
                    container.innerHTML = '<div class="bg-white rounded-xl p-6 border border-slate-200 shadow-sm text-slate-500">Hozircha tahlillar mavjud emas.</div>';
                }
            } catch (error) {
                alert(error.message);
            }
        });
    });
}

function initHistoryPage() {
    if (!location.pathname.endsWith("tarix.html")) return;
    if (!requireToken()) return;

    const container = document.querySelector(".grid.grid-cols-1.gap-6");
    if (!container) return;

    wireHistoryControls(container);

    apiRequest("/analysis/history")
        .then((items) => {
            renderHistoryItems(container, items);
            const pagination = document.querySelector(".flex.justify-center.mt-12.gap-2");
            pagination?.classList.add("hidden");
        })
        .catch((error) => alert(error.message));
}

function setActiveRangeButton(activeButton) {
    document.querySelectorAll("[data-range]").forEach((button) => {
        const isActive = button === activeButton;
        button.classList.toggle("bg-slate-100", isActive);
        button.classList.toggle("text-slate-900", isActive);
        button.classList.toggle("text-slate-500", !isActive);
    });
}

function bucketChartItems(items, maxBuckets = 10) {
    if (!items.length || items.length <= maxBuckets) return items;
    const bucketSize = Math.ceil(items.length / maxBuckets);
    const buckets = [];
    for (let index = 0; index < items.length; index += bucketSize) {
        const chunk = items.slice(index, index + bucketSize);
        const first = chunk[0];
        const last = chunk[chunk.length - 1];
        buckets.push({
            date: first.date === last.date ? first.date : `${first.date} - ${last.date}`,
            count: chunk.reduce((sum, item) => sum + numberOrZero(item.count), 0),
        });
    }
    return buckets;
}

function renderStatsChart(items) {
    const chartContainer = document.querySelector(".relative.h-\\[300px\\].w-full.flex.items-end");
    if (!chartContainer) return;

    const buckets = bucketChartItems(items || []);
    const grid = chartContainer.querySelector(".absolute.inset-0");
    Array.from(chartContainer.children).forEach((child) => {
        if (child !== grid) child.remove();
    });

    const maxCount = Math.max(...buckets.map((item) => numberOrZero(item.count)), 1);
    buckets.forEach((item, index) => {
        const height = Math.max(8, Math.round((numberOrZero(item.count) / maxCount) * 100));
        const bar = document.createElement("div");
        bar.className = index === buckets.length - 1
            ? "relative w-full bg-cyan-500 rounded-t-sm hover:bg-cyan-600 transition-colors"
            : "relative w-full bg-cyan-100/50 rounded-t-sm hover:bg-cyan-200 transition-colors";
        bar.style.height = `${height}%`;
        bar.title = `${item.date}: ${item.count}`;
        chartContainer.appendChild(bar);
    });

    const labelContainer = chartContainer.nextElementSibling;
    if (labelContainer && buckets.length) {
        const first = buckets[0].date;
        const middle = buckets[Math.floor(buckets.length / 2)].date;
        const last = buckets[buckets.length - 1].date;
        labelContainer.innerHTML = [first, middle, last]
            .map((label) => `<span>${escapeHtml(label.includes(" - ") ? label : formatDate(label, { day: "numeric", month: "short" }))}</span>`)
            .join("");
    }
}

function renderDistribution(stats) {
    const cards = Array.from(document.querySelectorAll(".lg\\:col-span-4.bg-white"));
    const distributionCard = cards.find((card) => card.textContent.includes("Natijalar taqsimoti"));
    if (!distributionCard) return;

    const total = numberOrZero(stats.total_scans);
    const pneumonia = numberOrZero(stats.pneumonia_detected_count);
    const normal = numberOrZero(stats.normal_count ?? (total - pneumonia));
    const normalPercent = total ? Math.round((normal / total) * 100) : 0;
    const pneumoniaPercent = total ? Math.max(0, 100 - normalPercent) : 0;

    const centerPercent = distributionCard.querySelector(".absolute.inset-0 .text-2xl");
    if (centerPercent) centerPercent.textContent = `${normalPercent}%`;

    const circles = distributionCard.querySelectorAll("svg circle");
    if (circles[1]) circles[1].setAttribute("stroke-dasharray", `${normalPercent}, 100`);
    if (circles[2]) {
        circles[2].setAttribute("stroke-dasharray", `${pneumoniaPercent}, 100`);
        circles[2].setAttribute("stroke-dashoffset", `-${normalPercent}`);
    }

    const legendValues = distributionCard.querySelectorAll(".space-y-4 .text-sm.font-bold.text-slate-900");
    if (legendValues[0]) legendValues[0].textContent = normal;
    if (legendValues[1]) legendValues[1].textContent = pneumonia;
}

function renderStats(stats) {
    const metricValues = document.querySelectorAll(".text-4xl.font-extrabold.text-slate-900.tracking-tight");
    if (metricValues[0]) metricValues[0].textContent = stats.total_scans;
    if (metricValues[1]) metricValues[1].textContent = stats.pneumonia_detected_count;
    if (metricValues[2]) metricValues[2].textContent = formatPercent(stats.average_confidence, 1);

    renderStatsChart(stats.last_7_days_chart || stats.chart || []);
    renderDistribution(stats);
}

function initStatsPage() {
    if (!location.pathname.endsWith("statistika.html")) return;
    if (!requireToken()) return;

    const rangeButtons = Array.from(document.querySelectorAll("[data-range]"));

    async function loadStats(days, activeButton) {
        try {
            setActiveRangeButton(activeButton);
            const stats = await apiRequest(`/dashboard/stats?days=${days}`);
            renderStats(stats);
        } catch (error) {
            alert(error.message);
        }
    }

    rangeButtons.forEach((button) => {
        button.addEventListener("click", () => loadStats(Number(button.dataset.range || 30), button));
    });

    const activeButton = rangeButtons.find((button) => button.dataset.range === "30") || rangeButtons[0];
    loadStats(Number(activeButton?.dataset.range || 30), activeButton);
}

document.addEventListener("DOMContentLoaded", () => {
    wireNavigation();
    initLoginPage();
    initRegisterPage();
    initAnalysisPage();
    initHistoryPage();
    initStatsPage();
});
