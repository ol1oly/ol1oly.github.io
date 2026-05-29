/* Single source of truth for the "Programming experience" section (index.html).
   Add a skill = add one line to the right group below.
   Each skill is ONE of:
     { name, img }        -> a logo image in images/
     { name, fa }         -> a Font Awesome icon class (Font Awesome is already loaded)
     { name, wordmark:1 } -> a text pill, for tech with no local logo
   Add `link:"..."` to any skill to make it clickable. */

const SKILL_GROUPS = [
    {
        label: "Languages",
        skills: [
            { name: "Java", img: "images/java2.png", link: "https://www.mcgill.ca/study/2024-2025/courses/comp-251" },
            { name: "C", img: "images/C.png" },
            { name: "C++", img: "images/c++.png" },
            { name: "C#", img: "images/cSharp.png" },
            { name: "Python", img: "images/python.webp", link: "https://github.com/ol1oly/Weather-Quiz" },
            { name: "JavaScript", img: "images/javascript.webp" },
            { name: "SQL", wordmark: 1 }
        ]
    },
    {
        label: "Web & Backend",
        skills: [
            { name: "React", img: "images/React.png" },
            { name: "Node.js", img: "images/nodeJs.png" },
            { name: "FastAPI", img: "images/fastapi.webp" },
            { name: "Next.js", wordmark: 1 },
            { name: "Express", wordmark: 1 },
        ]
    },
    {
        label: "Databases",
        skills: [
            { name: "PostgreSQL", img: "images/postgre.png"},
            { name: "Supabase", img: "images/supabase.png" }
        ]
    },
    {
        label: "Game development",
        skills: [
            { name: "Unity", img: "images/uni.webp", link: "https://o1loly.itch.io/abyssal-dive" },
            { name: "Godot", img: "images/godo.png" }
        ]
    },
    {
        label: "Tools",
        skills: [
            { name: "GitHub", fa: "fa-brands fa-github", link: "https://github.com/ol1oly" },
            { name: "Bash", img: "images/bash.png" },
            { name: "Claude Code", img: "images/claudecode.png" }
        ]
    }
];

function skillEscape(str) {
    return String(str).replace(/[&<>"']/g, function (c) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
}

function skillInner(s) {
    const name = skillEscape(s.name);
    if (s.img) return `<img src="${skillEscape(s.img)}" alt="${name}"><figcaption>${name}</figcaption>`;
    if (s.fa) return `<i class="${skillEscape(s.fa)}" aria-hidden="true"></i><figcaption>${name}</figcaption>`;
    return `<span class="skill-pill">${name}</span>`;
}

function skillHTML(s) {
    const cls = s.wordmark ? "skill skill--pill" : "skill";
    if (s.link) {
        return `<a class="${cls}" href="${skillEscape(s.link)}" target="_blank" rel="noopener">${skillInner(s)}</a>`;
    }
    return `<span class="${cls}">${skillInner(s)}</span>`;
}

function renderSkills() {
    const root = document.querySelector("[data-skills]");
    if (!root) return;
    // Each group is a native <details> accordion — click the header to expand
    // just the categories you care about. First group is open by default.
    root.innerHTML = SKILL_GROUPS.map(function (g, i) {
        return `
        <details class="skill-group"${i === 0 ? " open" : ""}>
            <summary class="skill-group-label">
                <span class="skill-caret" aria-hidden="true"></span>
                <span>${skillEscape(g.label)}</span>
                <span class="skill-count">${g.skills.length}</span>
            </summary>
            <div class="skill-row">${g.skills.map(skillHTML).join("")}</div>
        </details>`;
    }).join("");
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderSkills);
} else {
    renderSkills();
}
