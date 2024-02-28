console.clear();

const cardsContainer = document.querySelector(".cards");
const cardsContainerInner = document.querySelector(".cards__inner");
const cards = Array.from(document.querySelectorAll(".card"));
const overlayContainer = document.querySelector(".overlay");
const contentContainer = document.querySelector(".content-container");

const applyOverlayMask = (e) => {
    const overlayEl = overlayContainer;
    const x = e.pageX - cardsContainer.offsetLeft;
    const y = e.pageY - cardsContainer.offsetTop;

    overlayEl.style = `--opacity: 1; --x: ${x}px; --y:${y}px;`;
};

const createOverlayCta = (overlayCard, ctaEl) => {
    const overlayCta = document.createElement("div");
    overlayCta.classList.add("cta");
    overlayCta.textContent = ctaEl.textContent;
    overlayCta.setAttribute("aria-hidden", true);
    overlayCard.append(overlayCta);
};

const observer = new ResizeObserver((entries) => {
    entries.forEach((entry) => {
        const cardIndex = cards.indexOf(entry.target);
        let width = entry.borderBoxSize[0].inlineSize;
        let height = entry.borderBoxSize[0].blockSize;

        if (cardIndex >= 0) {
            overlayContainer.children[cardIndex].style.width = `${width}px`;
            overlayContainer.children[cardIndex].style.height = `${height}px`;
        }
    });
});

const initOverlayCard = (cardEl) => {
    const overlayCard = document.createElement("div");
    overlayCard.classList.add("card");
    createOverlayCta(overlayCard, cardEl.lastElementChild);
    overlayContainer.append(overlayCard);
    observer.observe(cardEl);
};

cards.forEach(initOverlayCard);
contentContainer.addEventListener("pointermove", applyOverlayMask);
