document.addEventListener("click", function (e) {
    createPulse(e.clientX, e.clientY);
});

function createPulse(x, y) {
    const pulse = document.createElement("span");

    pulse.style.position = "fixed";
    pulse.style.left = x + "px";
    pulse.style.top = y + "px";
    pulse.style.width = "20px";
    pulse.style.height = "20px";
    pulse.style.borderRadius = "50%";
    pulse.style.background = "rgba(59,130,246,0.3)";
    pulse.style.boxShadow = "0 0 40px rgba(59,130,246,0.6)";
    pulse.style.pointerEvents = "none";
    pulse.style.transform = "translate(-50%, -50%)";
    pulse.style.zIndex = "9999999";

    document.body.appendChild(pulse);

    pulse.animate([
        { transform: "translate(-50%, -50%) scale(0.5)", opacity: 1 },
        { transform: "translate(-50%, -50%) scale(4)", opacity: 0 }
    ], {
        duration: 700,
        easing: "ease-out"
    });

    setTimeout(() => pulse.remove(), 700);
}