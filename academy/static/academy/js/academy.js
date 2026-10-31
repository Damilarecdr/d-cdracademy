document.addEventListener("DOMContentLoaded", function () {
    const toggle = document.getElementById("menuToggle");
    const nav = document.getElementById("mainNav");

    if (toggle && nav) {
        toggle.addEventListener("click", function () {
            nav.classList.toggle("open");
        });
    }

    document.querySelectorAll("[data-confirm]").forEach(function (element) {
        element.addEventListener("click", function (event) {
            const message = element.getAttribute("data-confirm");
            if (!window.confirm(message)) {
                event.preventDefault();
            }
        });
    });

    setTimeout(function () {
        document.querySelectorAll(".alert").forEach(function (alert) {
            alert.style.transition = "opacity .3s ease";
            alert.style.opacity = "0";
            setTimeout(() => alert.remove(), 300);
        });
    }, 5000);
});
