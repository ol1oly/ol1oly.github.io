
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
    "Made in school with JavaFX, recreation of the game Rush Hour",
    "Made in school with JavaFX, recreation of the Crossword game"
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
    goTo("tables");
});

document.getElementById("left-arrow").addEventListener('click', function () {
    arrowClick(-1);
});
document.getElementById("right-arrow").addEventListener('click', function () {
    arrowClick(1);
});


/*
for (let i = 0; i < rows.length; i++) {
    rows[i].addEventListener('click', function() {
        changeColor(rows[i]);
    });
    
  }*/








