 document.addEventListener("DOMContentLoaded", () => {

            // PLUS
            document.querySelectorAll(".plus-cart").forEach(button => {
                button.addEventListener("click", async () => {
                    const prodId = button.getAttribute("pid");

                    const response = await fetch(`/pluscart?prod_id=${prodId}`, {
                        headers: { "X-Requested-With": "XMLHttpRequest" }
                    });

                    const data = await response.json();

                    // quantity
                    const quantityEl = document.getElementById(`quantity-${prodId}`);
                    quantityEl.innerText = data.quantity;

                    // Find minus button
                    const minusBtn = document.querySelector(`.minus-cart[pid="${prodId}"]`);

                    // ENABLE if quantity > 1
                    if (data.quantity > 1 && minusBtn) {
                        minusBtn.style.pointerEvents = "auto";
                        minusBtn.style.opacity = "1";
                    }

                    // item total
                    const itemEl = document.querySelector(`.item-total[data-product="${prodId}"]`);
                    if (itemEl) {
                        itemEl.innerText = "EUR " + Number(data.item_total).toFixed(2);
                    }

                    // totals
                    document.getElementById("amount").innerText = "EUR " + Number(data.amount).toFixed(2);
                    document.getElementById("totalamount").innerText = "EUR " + Number(data.totalamount).toFixed(2);
                });
            });

            // MINUS
            document.querySelectorAll(".minus-cart").forEach(button => {
                button.addEventListener("click", async () => {
                    const prodId = button.getAttribute("pid");
                    const quantityEl = document.getElementById(`quantity-${prodId}`);
                    let currentQty = parseInt(quantityEl.innerText);

                    // STOP if Q = 1
                    if (currentQty <= 1) {
                        return;
                    }

                    const response = await fetch(`/minuscart?prod_id=${prodId}`, {
                        headers: { "X-Requested-With": "XMLHttpRequest" }
                    });

                    const data = await response.json();

                    // quantity
                    quantityEl.innerText = data.quantity;

                    // DISABLE if Q = 1
                    if (data.quantity <= 1) {
                        button.style.pointerEvents = "none";
                        button.style.opacity = "0.5";
                    }

                    // item total
                    const itemEl = document.querySelector(`.item-total[data-product="${prodId}"]`);
                    if (itemEl) {
                        itemEl.innerText = "EUR " + Number(data.item_total).toFixed(2);
                    }

                    // totals
                    document.getElementById("amount").innerText = "EUR " + Number(data.amount).toFixed(2);
                    document.getElementById("totalamount").innerText = "EUR " + Number(data.totalamount).toFixed(2);
                });
            });

            // REMOVE
            document.querySelectorAll(".remove-cart").forEach(button => {
                button.addEventListener("click", async (event) => {
                    event.preventDefault();
                    const prodId = button.getAttribute("pid");

                    const response = await fetch(`/removecart?prod_id=${prodId}`, {
                        headers: { "X-Requested-With": "XMLHttpRequest" }
                    });

                    if (response.ok) {
                        const data = await response.json();

                        document.getElementById("amount").innerText = `EUR ${data.amount}`;
                        document.getElementById("totalamount").innerText = `EUR ${data.totalamount}`;

                        // remove row
                        const row = button.closest(".row");
                        if (row) {
                            const nextHr = row.nextElementSibling;
                            row.remove();
                            if (nextHr && nextHr.tagName === "HR") nextHr.remove();
                        }

                        // empty cart
                        if (data.cart_count === 0) {
                            document.querySelector(".container").innerHTML = `
                                <h1 class="text-center mb-5">Your Cart is Empty.</h1>
                                <div class="d-flex justify-content-center">
                                    <a href="/" class="btn btn-success">Continue Shopping</a>
                                </div>
                            `;
                        }
                    }
                });
            });

        });