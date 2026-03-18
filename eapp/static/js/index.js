let currentPrice = 0;
let currentInventory = 0;

function resetPaymentInfo() {
    currentPrice = 0;
    currentInventory = 0;

    document.getElementById('bill-carrier').innerText = "---";
    document.getElementById('bill-price').innerText = "0 đ";
    document.getElementById('bill-total').innerText = "0 đ";

    const qtyInput = document.getElementById('bill-quantity');
    if (qtyInput) {
        qtyInput.value = 1;
        qtyInput.setAttribute('data-max', 1);
        qtyInput.setAttribute('data-inventory', 1);
    }

    const formProductId = document.getElementById('form-product-id');
    if (formProductId) formProductId.value = "";

    const btnBuy = document.getElementById('btn-buy');
    if (btnBuy) btnBuy.disabled = true;

    document.querySelectorAll('.product-btn').forEach(btn => btn.classList.remove('active'));
}

const categoryTabs = document.querySelectorAll('.nav-pills .nav-link');
categoryTabs.forEach(tab => {
    tab.addEventListener('click', function() {
        resetPaymentInfo();
    });
});

function formatCurrency(number) {
    return new Intl.NumberFormat('vi-VN').format(number) + ' đ';
}

function updateTotal() {
    const qtyInput = document.getElementById('bill-quantity');
    if (!qtyInput || currentPrice === 0) return;

    const qty = parseInt(qtyInput.value);
    const total = currentPrice * qty;
    document.getElementById('bill-total').innerText = formatCurrency(total);
}

const productBtns = document.querySelectorAll('.product-btn');
productBtns.forEach(btn => {
    btn.addEventListener('click', function() {
        if (this.hasAttribute('disabled')) return; // Chặn nhấp nếu hết hàng

        productBtns.forEach(b => b.classList.remove('active'));
        this.classList.add('active');

        const id = this.getAttribute('data-id');
        const carrier = this.getAttribute('data-carrier');
        currentPrice = parseInt(this.getAttribute('data-price'));
        currentInventory = parseInt(this.getAttribute('data-inventory')); // Lấy tồn kho

        document.getElementById('bill-carrier').innerText = carrier;
        document.getElementById('bill-price').innerText = formatCurrency(currentPrice);
        document.getElementById('form-product-id').value = id;

        const qtyInput = document.getElementById('bill-quantity');
        qtyInput.value = 1; // Luôn reset về 1 khi chọn mệnh giá mới

        // Tính toán maxLimit dựa trên quy định hệ thống
        let systemLimit = 1;
        if (currentPrice <= 30000) systemLimit = 10;
        else if (currentPrice <= 300000) systemLimit = 5;
        else systemLimit = 3;

        // Giới hạn thực tế là con số NHỎ NHẤT giữa System Limit và Inventory
        let actualMaxLimit = Math.min(systemLimit, currentInventory);

        qtyInput.setAttribute('data-max', actualMaxLimit);
        qtyInput.setAttribute('data-inventory', currentInventory); // Lưu lại để dùng khi alert

        updateTotal();
        document.getElementById('btn-buy').disabled = false;
    });
});

const btnPlus = document.getElementById('btn-plus');
const btnMinus = document.getElementById('btn-minus');

if (btnPlus && btnMinus) {
    btnPlus.addEventListener('click', function() {
        if (currentPrice > 0) {
            const qtyInput = document.getElementById('bill-quantity');
            let currentQty = parseInt(qtyInput.value);

            const maxLimit = parseInt(qtyInput.getAttribute('data-max')) || 1;
            const inventory = parseInt(qtyInput.getAttribute('data-inventory')) || 1;

            if (currentQty < maxLimit) {
                qtyInput.value = currentQty + 1;
                updateTotal();
            } else {
                // Hiển thị alert phù hợp nguyên nhân
                if (currentQty >= inventory) {
                    alert(`Rất tiếc, kho chỉ còn ${inventory} thẻ mệnh giá này!`);
                } else {
                    alert(`Theo quy định, mệnh giá ${formatCurrency(currentPrice)} chỉ được mua tối đa ${maxLimit} thẻ/đơn.`);
                }
            }
        } else {
            alert("Vui lòng chọn mệnh giá trước!");
        }
    });

    btnMinus.addEventListener('click', function() {
        if (currentPrice > 0) {
            const qtyInput = document.getElementById('bill-quantity');
            let currentQty = parseInt(qtyInput.value);
            if (currentQty > 1) {
                qtyInput.value = currentQty - 1;
                updateTotal();
            }
        }
    });
}

function addToCart(id, name, price, quantity = 1) {
    fetch("/api/carts", {
        method: "post",
        body: JSON.stringify({
            "id": id,
            "name": name,
            "price": price,
            "quantity": quantity
        }),
        headers: {
            "Content-Type": "application/json"
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "error") {
            alert(data.message);
        } else {
            alert(data.message);

            let elems = document.getElementsByClassName("cart-counter");
            for (let e of elems) {
                e.innerText = data.total_quantity;
            }
        }
    })
    .catch(err => {
        console.error("Lỗi:", err);
        alert("Có lỗi xảy ra, vui lòng thử lại sau!");
    });
}