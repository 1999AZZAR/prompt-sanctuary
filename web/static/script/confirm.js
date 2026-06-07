(function () {
  "use strict";
  document.addEventListener(
    "submit",
    function (e) {
      var form = e.target;
      if (form && form.matches && form.matches('form[data-confirm]')) {
        var message = form.getAttribute("data-confirm");
        if (message && !window.confirm(message)) {
          e.preventDefault();
        }
      }
    },
    true
  );
})();
