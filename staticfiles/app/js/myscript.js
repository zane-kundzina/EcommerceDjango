$(document).ready(function(){
    
   /*  $('.plus-cart').click(function(){
        var id = $(this).attr("pid").toString();

        $.ajax({
            type: "GET",
            url: "/pluscart/",
            data: { prod_id: id },
            success: function(data){
                console.log("data =", data);

                // quantity
                let qtyEl = document.getElementById("quantity-" + data.product_id);
                if (qtyEl) {
                    qtyEl.innerText = data.quantity;
                }

                // item total
                let itemEl = document.querySelector(
                    `.item-total[data-product="${data.product_id}"]`
                );
                if (itemEl) {
                    itemEl.innerText = "EUR " + data.item_total.toFixed(2);
                }

                // amount
                let amountEl = document.getElementById("amount");
                if (amountEl) {
                    amountEl.innerText = "EUR " + data.amount.toFixed(2);
                }

                // total
                let totalEl = document.getElementById("totalamount");
                if (totalEl) {
                    totalEl.innerText = "EUR " + data.totalamount.toFixed(2);
                }
            }
        });
    }); */

   /*  $('.minus-cart').click(function(){
        var id = $(this).attr("pid").toString();

        $.ajax({
            type: "GET",
            url: "/minuscart/",
            data: { prod_id: id },
            success: function(data){
                console.log("data =", data);

                if (data.quantity <= 0) {
                    location.reload();
                } else {
                    // quantity
                    let qtyEl = document.getElementById("quantity-" + data.product_id);
                    if (qtyEl) {
                        qtyEl.innerText = data.quantity;
                    }

                    // item total
                    let itemEl = document.getElementById("item-total-" + data.product_id);
                    if (itemEl) {
                        itemEl.innerText = "EUR " + data.item_total.toFixed(2);
                    }

                    // amount
                    let amountEl = document.getElementById("amount");
                    if (amountEl) {
                        amountEl.innerText = "EUR " + data.amount.toFixed(2);
                    }

                    // total
                    let totalEl = document.getElementById("totalamount");
                    if (totalEl) {
                        totalEl.innerText = "EUR " + data.totalamount.toFixed(2);
                    }
                }
            }
        });
    }); */

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
                    window.location.href = `/product/${id}/`;
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
                 window.location.href = `/product/${id}/`;
            }
        });
    });

    // Global JS function to update product rating display
    function updateProductRatingDisplay(avgRating, reviewCount) {
        const rounded = Math.round(avgRating);

        const stars = '★'.repeat(rounded) + '☆'.repeat(5 - rounded);

        $('#product-rating-display').html(`
            <span class="text-warning">${stars}</span>
            <strong>(${avgRating.toFixed(1)})</strong>
            <small class="text-muted">based on ${reviewCount} review/s</small>
        `);
    }

    // Clickable Star Rating for Review Form
    const $reviewStars = $("#review-star-rating span");
    const $reviewRatingInput = $("#review-rating-input");

    if ($reviewStars.length && $reviewRatingInput.length) {
        $reviewStars.hover(
            function() { highlightReviewStars($(this).data("value")); },
            function() { highlightReviewStars($reviewRatingInput.val()); }
        );

        $reviewStars.click(function() {
            const value = $(this).data("value");
            $reviewRatingInput.val(value);
            highlightReviewStars(value);
        });

        function highlightReviewStars(rating) {
            $reviewStars.each(function() {
                $(this).text($(this).data("value") <= rating ? "★" : "☆");
            });
        }

        highlightReviewStars($reviewRatingInput.val() || 0);
    }

    // Remove old handlers to prevent duplicates
    $(document).off('submit', '#review-form');

    // SUBMIT review form
    $(document).on('submit', '#review-form', function(e) {
        e.preventDefault(); // STOP normal form submission

        const rating = parseInt($('#review-rating-input').val()) || 0;
        const comment = $('textarea[name="comment"]').val();
        const url = window.location.pathname;

        if (rating < 1 || rating > 5) {
            alert('Please select at least 1 star before submitting your review.');
            return;
        }

        $.ajax({
            url: url,
            type: "POST",
            data: {
                comment: comment,
                rating: rating,
                csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                if (response.success) {
                    location.reload();
                }
            },
            error: function(xhr) {
                alert(xhr.responseJSON?.error || "Something went wrong.");

                // If it's the "one review only" error → reset form
                if (xhr.responseJSON?.error === "You can only submit one review per product.") {

                    // Clear textarea
                    $('textarea[name="comment"]').val("");

                    // Reset hidden rating input
                    $('#review-rating-input').val(0);

                    // Reset stars visually
                    $("#review-star-rating span")                        
                        .addClass("text-warning")
                        .text("☆");
                }
            }
        });
    });

    // DELETE review
   // DELETE review - single binding
    $(function() {
        $(document).off('click', '.delete-review-btn'); // remove any old duplicate bindings

        $(document).on('click', '.delete-review-btn', function(e) {
            e.preventDefault();
            e.stopPropagation(); // avoid double triggers

            const $btn = $(this);
            const $reviewDiv = $btn.closest('.review-block');
            const reviewId = $btn.data('review-id');

            if (!reviewId) {
                alert("Error: review ID not found");
                return;
            }

            if (!window.confirm("Are you sure you want to delete this review?")) {
                return;
            }

            $.ajax({
                type: 'POST',
                url: `/review/${reviewId}/delete/`,
                headers: {
                    'X-CSRFToken': $('#csrf-token').val()
                },
                success: function(data) {
                    if (data.success) {
                        $reviewDiv.remove();

                        // Show placeholder if no reviews left
                        if ($('.review-block').length === 0) {
                            $('.mt-5:has(h3:contains("Reviews"))').append(
                                '<p>No reviews yet. Be the first to review this product!</p>'
                            );
                        }

                        // Update product rating display
                        $('#product-rating-display').html(`
                            <span class="text-warning">
                                ${'★'.repeat(Math.round(data.product_rating))}
                                ${'☆'.repeat(5 - Math.round(data.product_rating))}
                            </span>
                            <strong>(${data.product_rating.toFixed(1)})</strong>
                            <small class="text-muted">based on ${data.review_count} review/s</small>
                        `);
                    } else {
                        alert("Error deleting review");
                    }
                },
                error: function(xhr) {
                    console.error(xhr.responseText);
                    alert("Error deleting review");
                }
            });
        });
    });


    // EDIT review
    $(document).on('click', '.edit-review-btn', function() {
        const $reviewDiv = $(this).closest('.border');

        // Prevent adding multiple edit forms
        if ($reviewDiv.find('.save-edit-btn').length) {
            return;
        }

        const reviewId = $reviewDiv.data('review-id');
        const currentComment = $reviewDiv.find('p').text();
        const currentRating = $reviewDiv.find('span.text-warning').text().split('★').length - 1;

        // Hide the Edit & Delete buttons
        $reviewDiv.find('.review-actions').hide();

        // Build edit form
        const editFormHtml = `
            <textarea class="form-control mb-2" rows="3">${currentComment}</textarea>
            <div class="mb-2">
                ${[1,2,3,4,5].map(i =>
                    `<span class="edit-star text-warning" data-value="${i}"
                        style="font-size: 1.5rem; cursor:pointer;">
                        ${i <= currentRating ? '★' : '☆'}
                    </span>`
                ).join('')}
                <input type="hidden" class="edit-rating" value="${currentRating}">
            </div>
            <button class="btn btn-success btn-sm save-edit-btn">Save</button>
            <button class="btn btn-secondary btn-sm cancel-edit-btn">Cancel</button>
        `;

        $reviewDiv.append(editFormHtml);
    });  

    // STAR click in EDIT form
    $(document).on('click', '.edit-star', function() {
        const $reviewDiv = $(this).closest('.border');
        const val = $(this).data('value');
        $reviewDiv.find('.edit-star').each(function() {
            $(this).text($(this).data('value') <= val ? '★' : '☆');
        });
        $reviewDiv.find('.edit-rating').val(val);
    });

    // CANCEL on Edit mode
    $(document).on('click', '.cancel-edit-btn', function() {
        const $reviewDiv = $(this).closest('.border');
        $reviewDiv.find('textarea, .edit-star, .edit-rating, .save-edit-btn, .cancel-edit-btn').remove();

        $reviewDiv.find('p, span.text-warning, small, .d-flex').show();
    });


    // SAVE on EDIT mode
    $(document).off('click', '.save-edit-btn').on('click', '.save-edit-btn', function() {
        const $reviewDiv = $(this).closest('.border');
        const reviewId = $reviewDiv.data('review-id');
        const newComment = $reviewDiv.find('textarea').val();
        const newRating = parseInt($reviewDiv.find('.edit-rating').val());

        if (!newRating || newRating < 1 || newRating > 5) {
        alert("Please select a star rating before saving your changes.");
        return; // Stop execution
        }

        $.ajax({
            type: 'POST',
            url: `/review/${reviewId}/edit/`,
            data: {
                'csrfmiddlewaretoken': $('#csrf-token').val(),
                'comment': newComment,
                'rating': newRating
            },
            success: function(data) {
                const validRating = Math.min(Math.max(parseInt(data.rating), 1), 5); 
                // Update this review visually
                $reviewDiv.find('p').text(data.comment);
                $reviewDiv.find('span.text-warning').html('★'.repeat(validRating) + '☆'.repeat(5 - validRating));
               // Remove edit form
                $reviewDiv.find('textarea, .edit-star, .edit-rating, .save-edit-btn, .cancel-edit-btn').remove();
                $reviewDiv.find('p, span.text-warning, small, .d-flex').show();

                // Update product average rating
                updateProductRatingDisplay(data.product_rating, data.review_count);
            },
            error: function(xhr) {
                console.log(xhr.responseText);
                alert("Error updating review:\n" + xhr.responseText);
            }
        });
    });

});