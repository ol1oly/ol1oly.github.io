const PROJECTS = [
    {
        title: "GolfBro",
        image: "images/golfBroSmaller.png",
        featured: true,
        description: "A web app for golfers to meet and chat in real time.",
        skills: "web development, APIs, authentication, databases",
        stack: "nodeJs, EJS, express, MySQL, html, css, socket.IO, cloudinary",
        link: "https://golfapp-1hsh.onrender.com/",
        linkText: "View project",
        year: "2025",
        role: ""
    },
    {
        title: "Waypoints",
        image: "images/waypoints.webp",
        featured: true,
        description: "A Unity asset that lets developers make GameObjects follow custom paths.",
        skills: "software design, clean coding",
        stack: "Unity, C#",
        link: "https://assetstore.unity.com/packages/tools/level-design/waypoints-323240",
        linkText: "View project",
        year: "2025",
        role: ""
    },
    {
        title: "Connect4 AI",
        image: "images/connect4.png",
        featured: true,
        description: "Final project of the Accelerated introduction to Machine Learning course.",
        skills: "An application to play Connect 4 against an AI agent, applying core ML concepts in an interactive setting.",
        stack: "Python, Fastapi, React, Vite, DaisyUI, pytorch, numpy, Tailwind",
        link: "https://connect-4-game-solver.onrender.com/",
        linkText: "View project",
        year: "2023",
        role: ""
    },
    {
        title: "Abyssal Dive",
        image: "images/fish.png",
        description: "A game made for the GDM studios competition of winter 2026. Won best theme integration",
        skills: "Game/software design",
        stack: "Unity, C#",
        link: "https://o1loly.itch.io/abyssal-dive",
        linkText: "Play game",
        year: "2026",
        role: ""
    },
    {
        title: "Lost in Hell",
        image: "images/lostInHell.png",
        description: "A game made for the GDM studios competition of winter 2025.",
        skills: "Game/software design",
        stack: "Unity, C#",
        link: "https://acaciesong.itch.io/lostinhell",
        linkText: "Play game",
        year: "2025",
        role: ""
    },
    {
        title: "Rubik's Solver",
        image: "images/rubik.png",
        description: "Submission for McHacks13, McGill's largest hackathon.",
        skills: "An app that scans your rubik cube faces, determines the colors of the stickers via GeminiAI, and displays the solution with a 3d cube model.",
        stack: "Python, Fastapi, React, Vite, DaisyUI, Tailwind",
        link: "https://devpost.com/software/rubiksmagic",
        linkText: "View project",
        year: "2026",
        role: ""
    },
    {
        title: "Rush Hour",
        image: "images/rushHour.png",
        description: "Rush Hour remake during CEGEP with level selection, collision detection, and drag-and-drop gameplay.",
        skills: "reading files, JavaFX event handling",
        stack: "JavaFX, Java",
        link: "#",
        linkText: "Check it out",
        year: "2023",
        role: ""
    },
    {
        title: "Crossword Game",
        image: "images/mots.png",
        description: "A crossword game remake made during CEGEP, with level selection and three themes.",
        skills: "reading files, JavaFX event handling, UI design",
        stack: "JavaFX, Java",
        link: "#",
        linkText: "Check it out",
        year: "2023",
        role: ""
    },
    {
        title: "Aim Trainer",
        image: "images/Aimlab.png",
        description: "",
        skills: "",
        stack: "Unity, C#",
        link: "https://github.com/ol1oly/Chess-3D-Unity",
        linkText: "Check it out",
        year: "2024",
        role: ""
    },
    {
        title: "Chess Logic",
        image: "images/chessGame.png",
        description: "Chess logic implemented in unity, with local multiplayer play.",
        skills: "",
        stack: "Unity, C#",
        link: "https://github.com/ol1oly/Chess-3D-Unity",
        linkText: "Check it out",
        year: "2024",
        role: ""
    },
    {
        title: "Temperature Guesser",
        image: "images/guessTemp.png",
        description: "Minigame to guess the temperature of cities, with a favorites list.",
        skills: "Using an API, file writing/reading",
        stack: "Python, TKinter, OpenWeatherMapAPI",
        link: "https://github.com/ol1oly/Weather-Quiz",
        linkText: "Check it out",
        year: "2024",
        role: ""
    },
    {
        title: "Geographic Quiz",
        image: "images/countryQuiz.png",
        description: "Quiz on countries, cities, and capitals with maps and personalization.",
        skills: "Using an API, file writing/reading, geocoding",
        stack: "Python, TKinter, Geonames API",
        link: "https://github.com/ol1oly/Weather-Quiz",
        linkText: "Check it out",
        year: "2024",
        role: ""
    }
];

/* ---- helpers ---- */

function escapeHTML(str) {
    return String(str).replace(/[&<>"']/g, function (c) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
}

/* Compact card markup — matches the .project-card structure the CSS expects. */
function cardHTML(p, index) {
    return `
        <article class="project-card" data-index="${index}" tabindex="0" role="button"
                 aria-label="Open details for ${escapeHTML(p.title)}">
            <h2 class="project-title">${escapeHTML(p.title)}</h2>
            <img class="project-image" src="${escapeHTML(p.image)}" alt="${escapeHTML(p.title)}">
            ${p.description ? `<p class="project-text" data-type="description">${escapeHTML(p.description)}</p>` : ""}
            <a class="project-button" href="${escapeHTML(p.link)}" target="_blank" rel="noopener"
               data-external>${escapeHTML(p.linkText || "View project")}</a>
        </article>`;
}

function renderInto(selector, list) {
    const el = document.querySelector(selector);
    if (!el) return;
    el.innerHTML = list.map(function (p) {
        return cardHTML(p, PROJECTS.indexOf(p));
    }).join("");
}

/* ---- modal ---- */

let modalBackdrop;

function buildModal() {
    modalBackdrop = document.createElement("div");
    modalBackdrop.className = "modal-backdrop";
    modalBackdrop.innerHTML = `
        <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modalTitle">
            <button class="modal-close" type="button" aria-label="Close">&times;</button>
            <img class="modal-image" src="" alt="">
            <h2 class="modal-title" id="modalTitle"></h2>
            <p class="modal-desc"></p>
            <p class="modal-row modal-skills"></p>
            <p class="modal-row modal-meta"></p>
            <p class="modal-row modal-stack"></p>
            <a class="project-button modal-link" target="_blank" rel="noopener"></a>
        </div>`;
    document.body.appendChild(modalBackdrop);

    modalBackdrop.addEventListener("click", function (e) {
        if (e.target === modalBackdrop || e.target.classList.contains("modal-close")) {
            closeModal();
        }
    });
    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") closeModal();
    });
}

function setRow(el, label, value) {
    if (value) {
        el.innerHTML = label ? `<strong>${label}</strong> ${escapeHTML(value)}` : escapeHTML(value);
        el.style.display = "";
    } else {
        el.style.display = "none";
    }
}

function openModal(p) {
    const m = modalBackdrop;
    m.querySelector(".modal-image").src = p.image;
    m.querySelector(".modal-image").alt = p.title;
    m.querySelector(".modal-title").textContent = p.title;

    const desc = m.querySelector(".modal-desc");
    desc.textContent = p.description || "";
    desc.style.display = p.description ? "" : "none";

    setRow(m.querySelector(".modal-skills"), "Skills:", p.skills);
    const meta = [p.role, p.year].filter(Boolean).join(" · ");
    setRow(m.querySelector(".modal-meta"), "", meta);
    setRow(m.querySelector(".modal-stack"), "Made with:", p.stack);

    const link = m.querySelector(".modal-link");
    link.href = p.link;
    link.textContent = p.linkText || "View project";

    m.classList.add("open");
    document.body.style.overflow = "hidden";
}

function closeModal() {
    if (!modalBackdrop) return;
    modalBackdrop.classList.remove("open");
    document.body.style.overflow = "";
}

/* ---- wire up ---- */

function initProjects() {
    renderInto('[data-projects="featured"]', PROJECTS.filter(function (p) { return p.featured; }));
    renderInto('[data-projects="all"]', PROJECTS);

    buildModal();

    document.querySelectorAll(".projects-container").forEach(function (container) {
        container.addEventListener("click", function (e) {
            // Let the in-card link open the external URL without triggering the modal.
            if (e.target.closest("[data-external]")) return;
            const card = e.target.closest(".project-card");
            if (card) openModal(PROJECTS[card.dataset.index]);
        });
        container.addEventListener("keydown", function (e) {
            if (e.key !== "Enter" && e.key !== " ") return;
            const card = e.target.closest(".project-card");
            if (card && !e.target.closest("[data-external]")) {
                e.preventDefault();
                openModal(PROJECTS[card.dataset.index]);
            }
        });
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initProjects);
} else {
    initProjects();
}
