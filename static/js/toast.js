let toastTimer;
let toastHideTimer;

function hideToast() {
    const toast = document.getElementById("toast-component");
    if (!toast) return;

    toast.classList.remove("toast-show");
    toast.classList.add("toast-hidden");
    toastHideTimer = window.setTimeout(() => {
        if (toast.matches(":popover-open")) toast.hidePopover();
    }, 300);
}

function showToast(title, message, type = "normal", duration = 3000) {
    const toast = document.getElementById("toast-component");
    if (!toast) return;

    window.clearTimeout(toastTimer);
    window.clearTimeout(toastHideTimer);
    toast.classList.remove("toast-success", "toast-error", "toast-normal");
    toast.classList.add(`toast-${["success", "error"].includes(type) ? type : "normal"}`);
    document.getElementById("toast-title").textContent = String(title ?? "");
    document.getElementById("toast-message").textContent = String(message ?? "");

    if (!toast.matches(":popover-open")) toast.showPopover();
    void toast.offsetHeight;
    toast.classList.remove("toast-hidden");
    toast.classList.add("toast-show");
    toastTimer = window.setTimeout(hideToast, duration);
}

globalThis.showToast = showToast;

document.querySelector(".toast-close")?.addEventListener("click", () => {
    window.clearTimeout(toastTimer);
    window.clearTimeout(toastHideTimer);
    hideToast();
});
