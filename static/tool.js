document.addEventListener("DOMContentLoaded", function () {
let btnReturn=document.querySelector("#return");

btnReturn.addEventListener("click",()=>{
window.location.href="/home";
})



let btnCreate=document.querySelector("#create");
let table = document.querySelector("#table");

btnCreate.addEventListener("click",function(){
    let newRow=document.createElement("tr");
    let defaultFilling=["Enter Task", "Enter Owner", "00/00/00", "Enter Status", "Enter Details"];

    defaultFilling.forEach(value=>{
        let newCell=document.createElement("td");
        newCell.textContent=value;
        newRow.appendChild(newCell);

    });

    table.appendChild(newRow);

    data = {
        "details": "this is the details",
    };
    fetch('/create', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
      console.log('Success:', data);
    })
    .catch(error => {
      console.error('Error:', error);
    });
})


document.querySelector("#header").addEventListener("click", function() {
    let header = document.querySelector("#header");
    let currentText = header.textContent;

    let input = document.createElement("input");
    input.type = "text";
    input.value = currentText;
    header.textContent = "";
    header.appendChild(input);
    input.focus();

    input.addEventListener("blur", function() {
        header.textContent = this.value || currentText;
    });

    input.addEventListener("keyup", function(event) {
        if (event.key === "Enter") {
            input.blur();
        }
    });
});

document.querySelector("#table").addEventListener("click", function(event){
 if (event.target.tagName === "TD") {
    let cell = event.target;
    let currentText = cell.textContent;

    let input = document.createElement("input");
    input.type="text";
    input.value=currentText;
    cell.textContent = "";
    cell.appendChild(input);
    input.focus();

    input.addEventListener("blur", function(){
        cell.textContent=this.value||currentText;
    })

    input.addEventListener("keyup", function(event){
        if(event.key==="Enter"){
           input.blur();
        }
    });
  }
})

});
