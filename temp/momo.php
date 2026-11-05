<?php

header('Content-Type: application/json');

function momoPayment($amount) {
    $partnerCode = 'MOMO';
    $accessKey = 'F8BBA842ECF85';
    $secretKey = 'K951B6PE1waDMi640xX08PD3vg6EkVlz';
    
    // Tạo requestId và orderId
    $requestId = $partnerCode . time();
    $orderId = $requestId;
    $orderInfo = 'pay with MoMo';
    $redirectUrl = 'http://localhost/index.html'; // URL chuyển hướng sau khi thanh toán
    $ipnUrl = 'https://callback.url/notify'; // URL nhận thông báo IPN
    $requestType = 'captureWallet';
    $extraData = ''; // Có thể để trống

    // Tạo rawSignature
    $rawSignature = "accessKey=$accessKey&amount=$amount&extraData=$extraData&ipnUrl=$ipnUrl&orderId=$orderId&orderInfo=$orderInfo&partnerCode=$partnerCode&redirectUrl=$redirectUrl&requestId=$requestId&requestType=$requestType";

    // Tạo chữ ký
    $signature = hash_hmac('sha256', $rawSignature, $secretKey);

    // Tạo đối tượng JSON gửi đến MoMo
    $requestBody = json_encode([
        'partnerCode' => $partnerCode,
        'accessKey' => $accessKey,
        'requestId' => $requestId,
        'amount' => $amount,
        'orderId' => $orderId,
        'orderInfo' => $orderInfo,
        'redirectUrl' => $redirectUrl,
        'ipnUrl' => $ipnUrl,
        'extraData' => $extraData,
        'requestType' => $requestType,
        'signature' => $signature,
        'lang' => 'en'
    ]);

    // Cấu hình cURL
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, "https://test-payment.momo.vn/v2/gateway/api/create");
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        'Content-Length: ' . strlen($requestBody)
    ]);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $requestBody);

    // Gửi yêu cầu và nhận phản hồi
    $response = curl_exec($ch);
    curl_close($ch);

    return json_decode($response, true);
}

// Nhận dữ liệu từ yêu cầu Post
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Lấy dữ liệu số tiền từ body của yêu cầu
    $data = json_decode(file_get_contents('php://input'), true);
    $amount = isset($data['amount']) ? $data['amount'] : null;

    if ($amount) {
        $response = momoPayment($amount);
        echo json_encode($response);
    } else {
        echo json_encode(['error' => 'Thiếu trường amount']);
    }
} else {
    echo json_encode(['error' => 'Phương thức không hợp lệ.']);
}
?>
