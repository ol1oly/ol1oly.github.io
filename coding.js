
/*Solution: make three images, 1 active, 1 left and 1 right. when arrow pressed, the correct image slides into the middle, while the middle one
            goes to be outside view. After transition, middle changes its src to be the new one, while right and left changes their src to be 
            correct with the middle one. 

            might have to change the language selector to be on top, rather than on the left
*/
/*  MAYBE, include blender
To put in content: aimlab, chess
                    calculator, weather app, quizapp, logo detection
                    traffic, mot cachés
                    simulation motor
*/

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









