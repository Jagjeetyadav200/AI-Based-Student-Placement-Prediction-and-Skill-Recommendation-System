document.addEventListener("DOMContentLoaded", function () {

  // ---- Navbar scroll state ----
  const navbar = document.getElementById("navbar");
  if (navbar) {
    const onScroll = () => {
      navbar.classList.toggle("scrolled", window.scrollY > 12);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  // ---- Mobile nav toggle ----
  const navToggle = document.getElementById("navToggle");
  const navCollapsible = document.getElementById("navLinks");
  if (navToggle && navCollapsible) {
    navToggle.addEventListener("click", () => {
      const isOpen = navCollapsible.classList.toggle("open");
      navToggle.classList.toggle("active", isOpen);
      navToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });
  }

  // ---- Scroll-reveal animations ----
  const revealEls = document.querySelectorAll(".reveal");
  if (revealEls.length && "IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("revealed");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    revealEls.forEach((el) => observer.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add("revealed"));
  }

  // ---- Progress bar animation (result page) ----
  const fill = document.querySelector(".progress-fill");
  if (fill) {
    const target = fill.getAttribute("data-width");
    setTimeout(() => { fill.style.width = target + "%"; }, 150);
  }

  // ---- Score ring animation (result page) ----
  const ring = document.querySelector(".score-ring");
  if (ring) {
    const pct = ring.getAttribute("data-pct");
    ring.style.setProperty("--pct", 0);
    setTimeout(() => { ring.style.setProperty("--pct", pct); }, 150);
  }

  // ---- Auto-dismiss flash messages ----
  document.querySelectorAll(".flash").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity 0.4s ease";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 400);
    }, 5000);
  });

  // ---- Disable submit button + show spinner (prevents double-submit) ----
  document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("submit", () => {
      const btn = form.querySelector('button[type="submit"]');
      if (btn && !btn.classList.contains("is-loading")) {
        if (!btn.querySelector(".btn-text")) {
          btn.innerHTML = `<span class="btn-text">${btn.innerHTML}</span>`;
        }
        btn.classList.add("is-loading");
      }
    });
  });

  // ---- Admin category chart (admin.html) ----
  const chartCanvas = document.getElementById("categoryChart");
  if (chartCanvas && window.Chart) {
    const high = parseInt(chartCanvas.dataset.high, 10);
    const medium = parseInt(chartCanvas.dataset.medium, 10);
    const low = parseInt(chartCanvas.dataset.low, 10);
    new Chart(chartCanvas, {
      type: "doughnut",
      data: {
        labels: ["High", "Medium", "Low"],
        datasets: [{
          data: [high, medium, low],
          backgroundColor: ["#34d399", "#fbbf24", "#f87171"],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: "bottom", labels: { font: { family: "Inter" }, color: "#99a1ba" } }
        }
      }
    });
  }
});
