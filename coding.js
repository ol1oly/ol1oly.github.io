var row1 = document.getElementById("row1");
var row2 = document.getElementById("row2");
var row3 = document.getElementById("row3");
var row4 = document.getElementById("row4");

var currentImage = document.getElementById("contentImg");

const rows = [row1, row2, row3,row4];
var index=0;
const images=["images/anthony.jpg","images/king.jpg","images/ches.png","images/mbappe.jpg","images/java.png","images/skeletons.jpg"];
/*Solution: make three images, 1 active, 1 left and 1 right. when arrow pressed, the correct image slides into the middle, while the middle one
            goes to be outside view. After transition, middle changes its src to be the new one, while right and left changes their src to be 
            correct with the middle one. 

            might have to change the language selector to be on top, rather than on the left
*/ 
/*  MAYBE, include blender
To put in content: aimlab, chess
                    calculator, weather app, quizapp, logo detection
                    traffic, mot cachés, caveVin
                    simulation motor
*/

function goTo(id) {
    document.getElementById(id).scrollIntoView({ behavior: 'smooth' });
}

function changeColor(item){
    for (let i = 0; i < rows.length; i++) {
        rows[i].style.backgroundColor="white";
      }
      item.style.backgroundColor="yellow";
      index=0;
      if(item == rows[0])  currentImage.src = "images/java.png";
      if(item == rows[1])  currentImage.src = "images/python.webp";
      if(item == rows[2])  currentImage.src = "images/uni.webp";
      if(item == rows[3])  currentImage.src = "images/godo.png";
}


function arrowClick(change){
    index+=change;
    currentImage.src = images[index % images.length];
}



document.getElementById("buttonContact").addEventListener('click', function() {
    goTo("contactH1");
});

document.getElementById("buttonProjects").addEventListener('click', function() {
    goTo("tables");
});

document.getElementById("left-arrow").addEventListener('click', function() {
    arrowClick(1);
});
document.getElementById("right-arrow").addEventListener('click', function() {
    arrowClick(-1);
});


for (let i = 0; i < rows.length; i++) {
    rows[i].addEventListener('click', function() {
        changeColor(rows[i]);
    });
  }








