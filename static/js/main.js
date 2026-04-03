(function () {
  "use strict";

  var header = document.querySelector(".site-header");
  var navToggle = document.querySelector(".nav-toggle");
  var navMenu = document.querySelector(".nav-menu");
  var navLinks = document.querySelectorAll(".nav-menu a");
  var yearEl = document.getElementById("year");
  var form = document.getElementById("contact-form");
  var formStatus = document.getElementById("form-status");

  if (yearEl) {
    yearEl.textContent = String(new Date().getFullYear());
  }

  function setHeaderScrolled() {
    if (!header) return;
    header.classList.toggle("is-scrolled", window.scrollY > 24);
  }

  setHeaderScrolled();
  window.addEventListener("scroll", setHeaderScrolled, { passive: true });

  function closeNav() {
    if (!navToggle || !navMenu) return;
    navToggle.setAttribute("aria-expanded", "false");
    navMenu.classList.remove("is-open");
    document.body.classList.remove("nav-open");
  }

  function openNav() {
    if (!navToggle || !navMenu) return;
    navToggle.setAttribute("aria-expanded", "true");
    navMenu.classList.add("is-open");
    document.body.classList.add("nav-open");
  }

  if (navToggle && navMenu) {
    navToggle.addEventListener("click", function () {
      var expanded = navToggle.getAttribute("aria-expanded") === "true";
      if (expanded) closeNav();
      else openNav();
    });

    navLinks.forEach(function (link) {
      link.addEventListener("click", function () {
        if (window.matchMedia("(max-width: 899px)").matches) closeNav();
      });
    });

    window.addEventListener("resize", function () {
      if (window.matchMedia("(min-width: 900px)").matches) closeNav();
    });
  }

  /* Testimonial slider */
  var slider = document.querySelector("[data-slider]");
  if (slider) {
    var slides = slider.querySelectorAll("[data-slide]");
    var prevBtn = slider.querySelector("[data-prev]");
    var nextBtn = slider.querySelector("[data-next]");
    var dotsContainer = slider.querySelector("[data-dots]");
    var current = 0;
    var timer;

    function show(index) {
      current = (index + slides.length) % slides.length;
      slides.forEach(function (s, i) {
        s.classList.toggle("is-active", i === current);
      });
      if (dotsContainer) {
        var dots = dotsContainer.querySelectorAll(".slider-dot");
        dots.forEach(function (d, i) {
          d.classList.toggle("is-active", i === current);
        });
      }
    }

    function next() {
      show(current + 1);
    }

    function prev() {
      show(current - 1);
    }

    function startAuto() {
      clearInterval(timer);
      timer = setInterval(next, 6000);
    }

    if (dotsContainer && slides.length) {
      slides.forEach(function (_, i) {
        var dot = document.createElement("button");
        dot.type = "button";
        dot.className = "slider-dot" + (i === 0 ? " is-active" : "");
        dot.setAttribute("aria-label", "Go to testimonial " + (i + 1));
        dot.addEventListener("click", function () {
          show(i);
          startAuto();
        });
        dotsContainer.appendChild(dot);
      });
    }

    if (nextBtn) nextBtn.addEventListener("click", function () { next(); startAuto(); });
    if (prevBtn) prevBtn.addEventListener("click", function () { prev(); startAuto(); });

    startAuto();
  }

  /* Animated stats when in view */
  var stats = document.querySelectorAll(".stat__value[data-count]");
  var statsAnimated = false;

  function animateStat(el, target) {
    var duration = 1500;
    var start = performance.now();

    function frame(now) {
      var t = Math.min((now - start) / duration, 1);
      var eased = 1 - Math.pow(1 - t, 3);
      el.textContent = String(Math.round(eased * target));
      if (t < 1) requestAnimationFrame(frame);
    }

    requestAnimationFrame(frame);
  }

  function checkStats() {
    if (!stats.length || statsAnimated) return;
    var first = stats[0].closest(".stats");
    if (!first) return;
    var rect = first.getBoundingClientRect();
    if (rect.top < window.innerHeight * 0.85) {
      statsAnimated = true;
      stats.forEach(function (el) {
        var n = parseInt(el.getAttribute("data-count"), 10);
        if (!isNaN(n)) animateStat(el, n);
      });
    }
  }

  window.addEventListener("scroll", checkStats, { passive: true });
  checkStats();

  /* Scroll reveal */
  var revealEls = document.querySelectorAll(
    ".section-head, .card, .why-item, .about__content, .about__media, .contact__intro, .contact-form"
  );
  revealEls.forEach(function (el) {
    el.classList.add("reveal");
  });

  if (typeof IntersectionObserver !== "undefined") {
    var obs = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            obs.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -40px 0px", threshold: 0.08 }
    );

    revealEls.forEach(function (el) {
      obs.observe(el);
    });
  } else {
    revealEls.forEach(function (el) {
      el.classList.add("is-visible");
    });
  }

  /* Contact form — POST to Flask when data-contact-url is present */
  if (form && formStatus) {
    var contactUrl = form.getAttribute("data-contact-url");

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      formStatus.textContent = "";
      formStatus.classList.remove("is-success", "is-error");

      var name = form.elements.name.value.trim();
      var email = form.elements.email.value.trim();
      var message = form.elements.message.value.trim();

      if (!name || !email || !message) {
        formStatus.textContent = "Please fill in all fields.";
        formStatus.classList.add("is-error");
        return;
      }

      var emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
      if (!emailOk) {
        formStatus.textContent = "Please enter a valid email address.";
        formStatus.classList.add("is-error");
        return;
      }

      if (!contactUrl) {
        formStatus.textContent = "Thank you — we’ll get back to you shortly.";
        formStatus.classList.add("is-success");
        form.reset();
        return;
      }

      var btn = form.querySelector('button[type="submit"]');
      if (btn) btn.disabled = true;

      var csrfInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
      var csrfToken = csrfInput ? csrfInput.value : "";

      fetch(contactUrl, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ name: name, email: email, message: message }),
      })
        .then(function (r) {
          return r.json().then(function (data) {
            return { ok: r.ok, data: data };
          });
        })
        .then(function (result) {
          if (result.ok && result.data && result.data.ok) {
            formStatus.textContent = result.data.message || "Thank you.";
            formStatus.classList.add("is-success");
            form.reset();
          } else {
            var err =
              result.data && result.data.error
                ? result.data.error
                : "Something went wrong. Please try again.";
            formStatus.textContent = err;
            formStatus.classList.add("is-error");
          }
        })
        .catch(function () {
          formStatus.textContent = "Network error. Please try again.";
          formStatus.classList.add("is-error");
        })
        .finally(function () {
          if (btn) btn.disabled = false;
        });
    });
  }
})();
