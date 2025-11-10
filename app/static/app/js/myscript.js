
$('.plus-cart').click(function(){
    var id = $(this).attr("pid").toString();
    var eml = this.parentNode.children[2];
    console.log("pid =", id);

    $.ajax({
        type: "GET",
        url: "/pluscart/",
        data: { prod_id: id },
        success: function(data){
            console.log("data = ",data);
            eml.innerText = data.quantity;
            document.getElementById("amount").innerText = "EUR " + parseFloat(data.amount).toFixed(2);
            document.getElementById("totalamount").innerText = "EUR " + parseFloat(data.totalamount).toFixed(2);
        }
    });
});

$('.minus-cart').click(function(){
    var id = $(this).attr("pid").toString();
    var eml = this.parentNode.children[2];
    console.log("pid =", id);

    $.ajax({
        type: "GET",
        url: "/minuscart/",
        data: { prod_id: id },
        success: function(data){
            console.log("data =", data);
            if (data.quantity <= 0) {
                location.reload();  // reload page if item was removed
            } else {
                eml.innerText = data.quantity;
                document.getElementById("amount").innerText = "EUR " + data.amount.toFixed(2);
                document.getElementById("totalamount").innerText = "EUR " + data.totalamount.toFixed(2);
            }
        }
    });
});

$('.remove-cart').click(function(){
    var pid = $(this).attr("pid");
    console.log("pid =", pid);
    var eml = this

    $.ajax({
        type: "GET",
        url: "/removecart/",
        data: {
            prod_id: pid
        },
        success: function(data){
            console.log("data = ", data);

            // Remove product row from UI
            //document.getElementById("product-row-" + pid).remove();

            // Update cart totals
            document.getElementById("amount").innerText = "EUR " + parseFloat(data.amount).toFixed(2);
            document.getElementById("totalamount").innerText = "EUR " + parseFloat(data.totalamount).toFixed(2);
            eml.parentNode.parentNode.parentNode.parentNode.remove();
        }
    });
});

$('.plus-wishlist').click(function(){
    var id=$(this).attr("pid").toString();
    $.ajax({
        type: "GET",
        url:"/pluswishlist",
        data:{
            prod_id:id
        },
        success:function(data){
            //alert(data.message)
            window.location.href = `http://localhost:8000/product/${id}`;
        }
    });
});

$('.minus-wishlist').click(function(){
    var id=$(this).attr("pid").toString();
    $.ajax({
        type: "GET",
        url:"/minuswishlist",
        data:{
            prod_id:id
        },
        success:function(data){
            //alert(data.message)
            window.location.href = `http://localhost:8000/product/${id}`;
        }
    });
});





