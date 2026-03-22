let currentDiscount = 0;

document.addEventListener('DOMContentLoaded', function() {
    // Lấy 2 ảnh QR
    const imgMomo = document.getElementById('qr-momo');
    const imgBanking = document.getElementById('qr-banking');

    // Lấy tất cả các radio button có name là 'payment_method'
    const radios = document.querySelectorAll('input[name="payment_method"]');

    // Lặp qua từng nút để gắn sự kiện 'change'
    radios.forEach(radio => {
        radio.addEventListener('change', function() {
            // Nếu người dùng chọn MoMo
            if (this.value === 'momo') {
                imgMomo.classList.remove('d-none'); // Hiện Momo
                imgBanking.classList.add('d-none'); // Ẩn Banking
            }
            // Nếu người dùng chọn Banking
            else if (this.value === 'banking') {
                imgBanking.classList.remove('d-none'); // Hiện Banking
                imgMomo.classList.add('d-none'); // Ẩn Momo
            }
        });
    });
});

function applyDiscount() {
    const code = document.getElementById('discount-code').value.trim();
    const msgBox = document.getElementById('discount-msg');

    if (code === "") {
        msgBox.innerHTML = "<span class='text-danger'>Vui lòng nhập mã giảm giá!</span>";
        return;
    }

    fetch('/api/apply-discount', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: code })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            msgBox.innerHTML = `<span class='text-success'>${data.message}</span>`;
            currentDiscount = data.discount_amount;
            updateFinalAmount();
        } else {
            msgBox.innerHTML = `<span class='text-danger'>${data.message}</span>`;
            currentDiscount = 0;
            updateFinalAmount();
        }
    })
    .catch(err => console.error(err));
}

function updateFinalAmount() {
    let subtotalStr = document.getElementById('subtotal').innerText.replace(/\./g, '').replace(/,/g, '');
    let subtotal = parseFloat(subtotalStr) || 0;

    let finalAmount = subtotal - currentDiscount;
    if (finalAmount < 0) finalAmount = 0;

    document.getElementById('discount-amount').innerText = currentDiscount.toLocaleString('vi-VN');
    document.getElementById('final-amount').innerText = finalAmount.toLocaleString('vi-VN');
}

function pay() {
    const paymentMethod = document.querySelector('input[name="payment_method"]:checked').value;
    const discountCode = document.getElementById('discount-code').value.trim();

    let methodName = (paymentMethod === 'momo') ? 'Ví MoMo' : 'Ngân hàng MB Bank';

    if(confirm(`Xác nhận bạn đã quét mã QR và thanh toán cho đơn hàng này qua ${methodName}?`)) {
        fetch('/api/pay', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                payment_method: paymentMethod,
                discount_code: discountCode
            })
        })
        .then(res => res.json())
        .then(data => {
            if(data.status === 'success') {
                alert("Thanh toán thành công! Mã thẻ đã được gửi vào lịch sử mua hàng.");
                window.location.href = '/';
            } else {
                alert("Lỗi thanh toán: " + data.message);
            }
        });
    }
}