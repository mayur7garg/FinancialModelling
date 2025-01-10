function filterSymbols() {
    let td;
    let symFilter = document.getElementById("symbolSearch").value.toUpperCase();
    let trs = document.getElementById("symbolTable").getElementsByTagName("tr");

    for (let i = 1; i < trs.length; i++) {
        td = trs[i].getElementsByTagName("td")[0];
        if (td) {
            searchValue = td.textContent || td.innerText;
            if (searchValue.toUpperCase().indexOf(symFilter) > -1) {
                trs[i].style.display = "";
            } else {
                trs[i].style.display = "none";
            }
        }
    }
}