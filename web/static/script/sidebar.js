(function () {
  "use strict";

  // ---------- MOBILE DRAWER ----------
  const drawer = document.getElementById("mobileDrawer");
  const openBtn = document.getElementById("mobileMenuBtn");
  const closeBtn = document.getElementById("mobileDrawerClose");

  function openDrawer() {
    if (!drawer) return;
    drawer.classList.add("is-open");
    drawer.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  }
  function closeDrawer() {
    if (!drawer) return;
    drawer.classList.remove("is-open");
    drawer.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }

  if (openBtn) openBtn.addEventListener("click", openDrawer);
  if (closeBtn) closeBtn.addEventListener("click", closeDrawer);
  if (drawer) {
    drawer.addEventListener("click", function (e) {
      if (e.target === drawer) closeDrawer();
    });
  }

  // ---------- COMMAND PALETTE (Cmd-K) ----------
  const cmdk = document.getElementById("cmdk");
  const cmdkInput = document.getElementById("cmdkInput");
  const cmdkList = document.getElementById("cmdkList");
  const cmdkTrigger = document.getElementById("cmdkTrigger");

  const COMMANDS = [
    { label: "Overview",       meta: "Dashboard",   href: "/home",          icon: "fa-house" },
    { label: "Generate",       meta: "Basic",       href: "/generate",      icon: "fa-wand-magic-sparkles" },
    { label: "Advanced",       meta: "Generator",   href: "/advance",       icon: "fa-sliders" },
    { label: "Refinement",     meta: "Workflow",    href: "/refinement",    icon: "fa-arrows-rotate" },
    { label: "My Library",     meta: "Saved",       href: "/mylib",         icon: "fa-book" },
    { label: "Community",      meta: "Shared",      href: "/library",       icon: "fa-users" },
    { label: "Profile",        meta: "Account",     href: "/profile",       icon: "fa-user" },
    { label: "Feedback",       meta: "Bug + ideas", href: "/feedback",      icon: "fa-comment-dots" },
    { label: "Sign out",       meta: "Auth",        href: "/logout",        icon: "fa-arrow-right-from-bracket" }
  ];

  let activeIdx = 0;
  let filtered = COMMANDS.slice();

  function renderList() {
    if (!cmdkList) return;
    if (filtered.length === 0) {
      cmdkList.innerHTML = '<div class="cmdk__empty">No matches</div>';
      return;
    }
    cmdkList.innerHTML = filtered.map(function (c, i) {
      return (
        '<button class="cmdk__item ' + (i === activeIdx ? "is-active" : "") + '" data-href="' + c.href + '">' +
        '<i class="fa-solid ' + c.icon + '" aria-hidden="true"></i>' +
        '<span>' + c.label + '</span>' +
        '<span class="cmdk__item-meta">' + c.meta + '</span>' +
        '</button>'
      );
    }).join("");
  }

  function openCmdK() {
    if (!cmdk) return;
    cmdk.classList.add("is-open");
    cmdk.setAttribute("aria-hidden", "false");
    if (cmdkInput) {
      cmdkInput.value = "";
      cmdkInput.focus();
    }
    filtered = COMMANDS.slice();
    activeIdx = 0;
    renderList();
  }
  function closeCmdK() {
    if (!cmdk) return;
    cmdk.classList.remove("is-open");
    cmdk.setAttribute("aria-hidden", "true");
  }

  function navigateTo(href) {
    closeCmdK();
    window.location.href = href;
  }

  if (cmdkTrigger) cmdkTrigger.addEventListener("click", openCmdK);
  if (cmdk) {
    cmdk.addEventListener("click", function (e) {
      if (e.target === cmdk) closeCmdK();
    });
  }
  if (cmdkList) {
    cmdkList.addEventListener("click", function (e) {
      const btn = e.target.closest(".cmdk__item");
      if (btn) navigateTo(btn.dataset.href);
    });
  }
  if (cmdkInput) {
    cmdkInput.addEventListener("input", function () {
      const q = cmdkInput.value.toLowerCase().trim();
      filtered = COMMANDS.filter(function (c) {
        return c.label.toLowerCase().indexOf(q) !== -1 || c.meta.toLowerCase().indexOf(q) !== -1;
      });
      activeIdx = 0;
      renderList();
    });
    cmdkInput.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        activeIdx = (activeIdx + 1) % Math.max(filtered.length, 1);
        renderList();
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        activeIdx = (activeIdx - 1 + filtered.length) % Math.max(filtered.length, 1);
        renderList();
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (filtered[activeIdx]) navigateTo(filtered[activeIdx].href);
      } else if (e.key === "Escape") {
        e.preventDefault();
        closeCmdK();
      }
    });
  }

  // Global keyboard shortcuts
  document.addEventListener("keydown", function (e) {
    const isModK = (e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k";
    if (isModK) {
      e.preventDefault();
      if (cmdk && cmdk.classList.contains("is-open")) closeCmdK();
      else openCmdK();
    } else if (e.key === "Escape") {
      if (drawer && drawer.classList.contains("is-open")) closeDrawer();
      if (cmdk && cmdk.classList.contains("is-open")) closeCmdK();
    }
  });

  // Expose for other scripts
  window.PromptSanctuaryUI = {
    openDrawer: openDrawer,
    closeDrawer: closeDrawer,
    openCmdK: openCmdK,
    closeCmdK: closeCmdK
  };
})();
