(function () {
  "use strict";
  var switcher = document.getElementById("langSwitcher");
  if (!switcher) return;

  document.addEventListener("click", function (e) {
    if (!switcher.contains(e.target)) {
      switcher.removeAttribute("open");
    }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && switcher.hasAttribute("open")) {
      switcher.removeAttribute("open");
    }
  });
})();
