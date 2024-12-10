let i = 0;
let txt = "";
let txt2= ""
let speed = 100;
let inp1 = document.querySelector("#userInput");
let clear_text=document.querySelector(".clear_response");

inp1.addEventListener("keydown", (event) => {
    if (event.keyCode === 13 || event.key === "Enter") {
        getText();
    }
});

clear_text.addEventListener("click",(event)=>{
    let attachElement = document.querySelector('.attach');
        attachElement.remove()
})

function getText() {
    let userInput = document.querySelector("#userInput");
    if (userInput.value != '') {
        let txt = userInput.value; // Get the value of the input field
        recordHistory(txt);
        let txt2 = getResult(); // Assuming getResult() is defined elsewhere

        // Clear the text input after getting its value
        userInput.value = '';
        // Clear the display area before appending new text
        let attachElement = document.querySelector('.attach');
        attachElement.innerHTML = '';
        // Add styles dynamically to h3 (if needed)
        addStyeToh3(attachElement)
        // Call the typeWriter function to display the text
        typeWriter(txt, attachElement); // Assuming typeWriter function exists and modified to accept attachElement
    }
}


function addStyeToh3(elem){
    elem.style.border = "2px solid #ffcc66";
    elem.style.padding = "20px";
    elem.style.borderRadius = "10px";
    elem.style.boxShadow = "0 4px 6px rgba(0, 0, 0, 0.1)";
    elem.style.backgroundColor = "white";
    elem.style.margin = "20px";
}


function getResult()
{
//asynchronosly handle the api and get the data and then assign it to the string that we want to be displayed on the screen 





//we get the result from the back end and we assign it to the txt and finllay display it according to the user format 
 var str= "Hello my frind"
}


function deleteEntry(event){
    const div_to_be_deleted=event.target.parentElement
    div_to_be_deleted.remove()
}

function typeWriter(text) {
    let i = 0;
    let d = document.querySelector('.attach');
    let speed = 5;

    function type() {
        if (i < text.length) {
            if (i % 52 == 0 && i > 0) {
                d.innerHTML += "<br>";
            }
            if (text.charAt(i) == " ") {
                d.textContent += " ";
            }
            d.textContent += text.charAt(i);
            i++;
            setTimeout(type, speed);
        }
    }
    // Start typing the text
    type();
}



function recordHistory(txt) {
    const d1 = document.querySelector('.history');
    const userInputShortened = txt.substring(0, 10); // Limiting to first 10 characters
    const h3 = document.createElement('h3');
    h3.appendChild(document.createTextNode(userInputShortened));
    h3.style.width="50%"
    //Creating the div element in order to attach it to the history tab=
    const div = document.createElement('div');
    div.appendChild(h3);
    div.style.display="flex"
    div.style.justifyContent="center"
    div.className="smooth-border"
    //creating button and adding it to the div which shows history this will delete the entry when i want it to be deleted
    const button = document.createElement("button");
    button.innerText="X"
    button.className="delete-btn";
    button.addEventListener("click",(event)=>{
        deleteEntry(event)
    })
    div.appendChild(button)
    d1.appendChild(div); // Append created div to '.histor' element to display user input history
    list_btn=d1.querySelectorAll('.delete-btn')
}