
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
var currentImage = document.getElementById("contentImg");
var desc = document.getElementById("desc");
const images = ["images/Aimlab.png", "images/chessGame.png", "images/guessTemp.png", "images/countryQuiz.png", "images/mots.png", "images/rushHour.png"];
const description = [
    "Made in Unity, game where you can train your aim",
    "Made in Unity, fully functional chess game. Plans to make it multiplayer",
    "Made with Python and Tkinter, using OpenWeatherMap API. Guess the temperature of a city",
    "Made with Tkinter, using GeoNames API, an API with geographic data. Quiz about countries, cities and capitals.",
    "Made in school with JavaFX, recreation of the Crossword game",
    "Made in school with JavaFX, recreation of the game Rush Hour"
];
var index = 0;
/*
function changeColor(item){
    for (let i = 0; i < rows.length; i++) {
        rows[i].style.backgroundColor="white";
        rows[i].style.color="black";
        
      }
      item.style.backgroundColor="#0066ff";
      item.style.color="white";


      index=0;
      if(item == rows[0])  currentImage.src = "images/java.png";
      if(item == rows[1])  currentImage.src = "images/python.webp";
      if(item == rows[2])  currentImage.src = "images/uni.webp";
      
}*/


function arrowClick(change) {
    index += change;
    if (index < 0) index = images.length - 1;
    currentImage.src = images[index % images.length];
    desc.innerHTML = description[index % images.length];
}



document.getElementById("buttonContact").addEventListener('click', function () {
    goTo("contactH1");
});

document.getElementById("buttonProjects").addEventListener('click', function () {
    goTo("projects");
});

document.getElementById("left-arrow").addEventListener('click', function () {
    arrowClick(-1);
});
document.getElementById("right-arrow").addEventListener('click', function () {
    arrowClick(1);
});

fetch("https://golfapp-1hsh.onrender.com/ping").then(res => console.log(res.status));








