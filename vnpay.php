<?php

header('Content-Type: application/json');

// Thiết lập múi giờ
date_default_timezone_set('Asia/Bangkok');

// Hàm xử lý thanh toán VNPay
function processVnPayPayment($orderId, $total)
{
    // Định nghĩa thông tin VNPay
    $vnp_TmnCode = '9FHQFJV7'; // TMN Code của bạn
    $vnp_HashSecret = '51CNF74EOXHO7VEELB0W6Z8P6PI8G4MZ'; // Hash Secret của bạn
    $vnp_Url = 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html'; // URL VNPay
    $vnp_Returnurl = 'http://localhost/index.html'; // URL trả về

    // Khởi tạo các tham số yêu cầu
    $vnp_TxnRef = $orderId; // Số tham chiếu giao dịch
    $vnp_OrderInfo = 'Thanh toán đơn hàng ' . $orderId; // Thông tin đơn hàng
    $vnp_OrderType = 'billpayment'; // Loại đơn hàng
    $vnp_Amount = $total * 100; // Chuyển đổi số tiền sang VND
    $vnp_Locale = 'vn'; // Ngôn ngữ
    $vnp_IpAddr = $_SERVER['REMOTE_ADDR']; // Địa chỉ IP của người dùng
    $date = new DateTime("now", new DateTimeZone('Asia/Bangkok'));
    $vnp_CreateDate = $date->format('YmdHis'); // Thời gian hiện tại

    // Tạo mảng dữ liệu yêu cầu
    $inputData = array(
        "vnp_Version" => "2.1.0",
        "vnp_TmnCode" => $vnp_TmnCode,
        "vnp_Amount" => $vnp_Amount,
        "vnp_Command" => "pay",
        "vnp_CreateDate" => $vnp_CreateDate,
        "vnp_CurrCode" => "VND",
        "vnp_IpAddr" => $vnp_IpAddr,
        "vnp_Locale" => $vnp_Locale,
        "vnp_OrderInfo" => $vnp_OrderInfo,
        "vnp_OrderType" => $vnp_OrderType,
        "vnp_ReturnUrl" => $vnp_Returnurl,
        "vnp_TxnRef" => $vnp_TxnRef,
    );

    // Sắp xếp mảng theo thứ tự từ điển
    ksort($inputData);
    $query = "";
    $i = 0;
    $hashdata = "";
    foreach ($inputData as $key => $value) {
        if ($i == 1) {
            $hashdata .= '&' . urlencode($key) . "=" . urlencode($value);
        } else {
            $hashdata .= urlencode($key) . "=" . urlencode($value);
            $i = 1;
        }
        $query .= urlencode($key) . "=" . urlencode($value) . '&';
    }

    // Tạo URL thanh toán
    $vnp_Url = $vnp_Url . "?" . rtrim($query, '&');
    if (isset($vnp_HashSecret)) {
        $vnpSecureHash = hash_hmac('sha512', $hashdata, $vnp_HashSecret);
        $vnp_Url .= '&vnp_SecureHash=' . $vnpSecureHash; // Thêm Secure Hash vào URL
    }

    return $vnp_Url; // Trả về URL thanh toán
}

// Nhận dữ liệu từ yêu cầu POST
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $data = json_decode(file_get_contents('php://input'), true);
    $orderId = isset($data['orderId']) ? $data['orderId'] : null; // Nhận orderId
    $total = isset($data['total']) ? $data['total'] : null; // Nhận tổng tiền

    if ($orderId && $total && is_numeric($total)) {
        $paymentUrl = processVnPayPayment($orderId, $total); // Gọi hàm và nhận URL thanh toán
        echo json_encode(['status' => 'success', 'paymentUrl' => $paymentUrl]); // Trả về URL thanh toán
    } else {
        echo json_encode(['error' => 'Thiếu trường orderId hoặc total không hợp lệ']);
    }
} else {
    echo json_encode(['error' => 'Phương thức không hợp lệ.']);
}
?>
