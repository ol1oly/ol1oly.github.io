
function goTo(id) {
    document.getElementById(id).scrollIntoView({ behavior: 'smooth' });
}
var index = 0;


document.getElementById("buttonContact").addEventListener('click', function () {
    goTo("contactH1");
});

document.getElementById("buttonProjects").addEventListener('click', function () {
    goTo("projectsSection");
});


fetch("https://connect-4-game-solver.onrender.com/").then(res => console.log("connect4: " + res.status));
fetch("https://golfapp-1hsh.onrender.com/ping").then(res => console.log("golf app: " + res.status));









