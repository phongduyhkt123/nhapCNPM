function addToDetail(id){
    fetch('/api/detail', {
        'method': 'post',
        'body': JSON.stringify({
            'id': id

        }),
        'headers': {
            'Content-Type': 'application/json'

        }

    }).then(res =>res.json()).then(data =>{
            console.log(data);
    });
}
function addToCart(id){
    if (confirm("Bạn chắc chắn lưu vé chưa?") == true)
        var price = document.getElementById('price');
        fetch('api/cart', {
            'method': 'post',
            'body': JSON.stringify({
                'id': id,
                'price': price.value

            }),
             'headers': {
                'Content-Type': 'application/json',
                'Accept': 'application/json'

            }
        }).then(res =>res.json()).then(data =>{
            console.log(data);
            alert(data.message);
        });

}
function pay(){
    if (confirm("Bạn chắc chắn thanh toán chưa?") == true)
        fetch('api/pay', {
            'method': 'post',
             'headers': {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        }).then(res =>res.json()).then(data =>{
            alert(data.message);
            location.reload();
        }).catch(err => console.log(err));

}

function checkBooking(maxE, maxB){
    const economy = document.getElementById('noEconomy')
    const business = document.getElementById('noBusiness')
    var valid = false
    if (isNaN(economy.value) || parseInt(economy.value) < 0){
        economy.setCustomValidity("not valid")
    }
    else if(isNaN(business.value)|| parseInt(business.value) < 0){
        business.setCustomValidity("not valid")
    }
    else if(parseInt(business.value) + parseInt(economy.value) == 0){
        economy.setCustomValidity("pick number of ticket")
    }
    else if(parseInt(business.value) > maxB){
        business.setCustomValidity("not enough tickets")
    }
    else if(parseInt(economy.value) > maxE){
        economy.setCustomValidity("not enough tickets")
    }
    else {
        business.setCustomValidity("")
        economy.setCustomValidity("")
        valid = true
    }
    economy.reportValidity()
    business.reportValidity()
    return valid
}


function getTotalPrice(Eprice, Bprice){
    try {
        let nE = parseInt(document.getElementById('noEconomy').value) // số lượng vé Economy
        let nB = parseInt(document.getElementById('noBusiness').value) // số lượng vé Business
        if(nE >= 0 && nB >=0) {
            let total = nE * Eprice + nB * Bprice
            document.getElementById('total').value = total.toString()
        }
    }catch (err){
    }
}

function prebook(takeOffTime, dateRule, id, nextUrl) {
    var now = new Date()
    var difference = Math.abs(takeOffTime - now)
    days = difference/(1000 * 3600 * 24)
    if (days < parseInt(dateRule)) {
        alert('You must book before ' + dateRule.toString() + ' days')
    }
    else{
        location.replace(nextUrl);
    }
}


function addDays(date, number) {
    const newDate = new Date(date);
    return new Date(newDate.setDate(date.getDate() + number));
}

function showImage(event){
    let imgCon = document.getElementById('avt')
    let files = event.target.files[0]
    if(files){
        imgCon.src = URL.createObjectURL(files)
    }
}

function nextPage(page_cur){
    var nextTag = document.getElementById("page"+(page_cur+1).toString())
    window.location.href = nextTag.href;
}
function previousPage(page_cur){
    var nextTag = document.getElementById("page"+(page_cur-1).toString())
    window.location.href = nextTag.href;
}

function loadCustomer(customers){
    var cid = document.getElementById("sl1").value
    for (let i =0; i< customers.length; i++){
        if (customers[i]['id'].toString() == cid){
            document.getElementById("phone").value = customers[i]["phone"]
            document.getElementById("idNo").value = customers[i]["idNo"]
            break;
        }
    }
}