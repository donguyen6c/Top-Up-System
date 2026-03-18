let currentPrice = 0;

function formatCurrency(number) {
    return new Intl.NumberFormat('vi-VN').format(number) + ' đ';
}

function updateTotal() {
    const qtyInput = document.getElementById('bill-quantity');
    if (!qtyInput) return;
    const qty = parseInt(qtyInput.value);
    const total = currentPrice * qty;
    document.getElementById('bill-total').innerText = formatCurrency(total);
}

const productBtns = document.querySelectorAll('.product-btn');
productBtns.forEach(btn => {
    btn.addEventListener('click', function() {
        productBtns.forEach(b => b.classList.remove('active'));
        this.classList.add('active');

        const id = this.getAttribute('data-id');
        const carrier = this.getAttribute('data-carrier');
        currentPrice = parseInt(this.getAttribute('data-price'));

        document.getElementById('bill-carrier').innerText = carrier;
        document.getElementById('bill-price').innerText = formatCurrency(currentPrice);
        document.getElementById('form-product-id').value = id;

        document.getElementById('bill-quantity').value = 1;
        updateTotal();

        document.getElementById('btn-buy').disabled = false;
    });
});

const btnPlus = document.getElementById('btn-plus');
const btnMinus = document.getElementById('btn-minus');

if (btnPlus && btnMinus) {
    btnPlus.addEventListener('click', function() {
        if(currentPrice > 0) {
            let qtyInput = document.getElementById('bill-quantity');
            let currentQty = parseInt(qtyInput.value);
            if(currentQty < 10) {
                qtyInput.value = currentQty + 1;
                updateTotal();
            }
        }
    });

    btnMinus.addEventListener('click', function() {
        if(currentPrice > 0) {
            let qtyInput = document.getElementById('bill-quantity');
            let currentQty = parseInt(qtyInput.value);
            if(currentQty > 1) {
                qtyInput.value = currentQty - 1;
                updateTotal();
            }
        }
    });
}