function animateCounters() {
  const counters = document.querySelectorAll(".counter");
  counters.forEach((el) => {
    const targetRaw = el.getAttribute("data-target");
    if (targetRaw == null) return;
    const target = Number(targetRaw);
    if (!Number.isFinite(target)) return;

    const isFloat = targetRaw.includes(".");
    const start = 0;
    const duration = 800;
    const startTs = performance.now();

    function tick(ts) {
      const p = Math.min(1, (ts - startTs) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      const value = start + (target - start) * eased;
      el.textContent = isFloat ? value.toFixed(2) : Math.round(value).toString();
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  });
}

async function setupSamplePreview() {
  const btn = document.getElementById("btnSample");
  const useSample = document.getElementById("useSample");
  const preview = document.getElementById("samplePreview");
  const body = document.getElementById("samplePreviewBody");
  if (!btn || !useSample || !preview || !body) return;

  btn.addEventListener("click", async () => {
    useSample.checked = true;
    const res = await fetch("/api/sample_students");
    const data = await res.json();
    const students = (data.students || []).slice(0, 10);
    body.innerHTML = "";
    students.forEach((s) => {
      const tr = document.createElement("tr");
      tr.className = "bg-transparent";
      tr.innerHTML = `
        <td class="px-3 py-2 text-white/80">${escapeHtml(String(s.Student_ID ?? ""))}</td>
        <td class="px-3 py-2 text-white/80">${escapeHtml(String(s.Name ?? ""))}</td>
        <td class="px-3 py-2 text-white/80">${escapeHtml(String(s.Subject ?? ""))}</td>
      `;
      body.appendChild(tr);
    });
    preview.classList.remove("hidden");
  });
}

function escapeHtml(str) {
  return str
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setupFitnessChart() {
  if (!window.__GA_HISTORY__) return;
  const canvas = document.getElementById("fitnessChart");
  if (!canvas) return;

  const best = window.__GA_HISTORY__.best || [];
  const avg = window.__GA_HISTORY__.avg || [];
  const labels = best.map((_, i) => `G${i + 1}`);

  // eslint-disable-next-line no-undef
  new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Best Fitness",
          data: best,
          borderColor: "rgba(16,185,129,0.95)",
          backgroundColor: "rgba(16,185,129,0.15)",
          fill: true,
          tension: 0.35,
          pointRadius: 0,
        },
        {
          label: "Average Fitness",
          data: avg,
          borderColor: "rgba(56,189,248,0.9)",
          backgroundColor: "rgba(56,189,248,0.08)",
          fill: true,
          tension: 0.35,
          pointRadius: 0,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          labels: { color: "rgba(255,255,255,0.8)" },
        },
        tooltip: {
          mode: "index",
          intersect: false,
        },
      },
      scales: {
        x: {
          ticks: { color: "rgba(255,255,255,0.55)", maxTicksLimit: 8 },
          grid: { color: "rgba(255,255,255,0.06)" },
        },
        y: {
          ticks: { color: "rgba(255,255,255,0.55)" },
          grid: { color: "rgba(255,255,255,0.06)" },
        },
      },
    },
  });
}

document.addEventListener("DOMContentLoaded", () => {
  animateCounters();
  setupSamplePreview();
  setupFitnessChart();

  const gaForm = document.getElementById("gaForm");
  const loadingOverlay = document.getElementById("loadingOverlay");
  if (gaForm && loadingOverlay) {
    gaForm.addEventListener("submit", () => {
      loadingOverlay.classList.remove("hidden");
    });
  }
});

