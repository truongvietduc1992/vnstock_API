# VNStock API
API được thiết kế để kết nối và lấy dữ liệu chứng khoán Việt Nam qua thư viện `vnstock` v0.1.5 và đóng gói gọn dưới dạng Fast API. Thích hợp cho việc deploy nhanh qua Docker hoặc các dịch vụ PaaS như Koyeb/Render, v.v.

**Tính năng:**
* Fetch giá tham chiếu (ref_price), giá mở cửa (open_price), **khối lượng giao dịch** và nhiều chỉ số giao dịch khác của nhiều mã chứng khoán cùng lúc.
* Lấy giá Crypto thông qua Binance Data API (Cập nhật real-time).
* Lấy giá Vàng trong và ngoài nước qua cổng GiavangNOW.
* Xác thực bằng **API Token Header**.
* Tối ưu bộ nhớ Cache 60s phù hợp cài đặt trên các VPS Free/Eco cấu hình yếu (Tránh nghẽn CPU và tránh bị block IP API nguồn).

---

## 1. Cài đặt môi trường Local và chạy thử

Yêu cầu: Python 3.10+

```bash
git clone <your_github_repo_link>
cd vnstock_API
pip install -r requirements.txt
```

Thêm token vào biến môi trường (tuỳ chọn):
* Windows: `set API_SECRET_TOKEN=your_secret_token`
* Linux/Mac: `export API_SECRET_TOKEN=your_secret_token`

Khởi động server (Mặc định ở `http://localhost:8000`):
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 2. Các Endpoint (API Docs)

> **Header bắt buộc:** `X-Access-Token: <your_token>` (Mặc định: `1324`)

### A. Lấy giá Chứng Khoán VN
* **Endpoint:** `POST /stocks/quotes`
* **Body:**
```json
{
  "symbols": ["FPT", "TCB"]
}
```
* **Response mẫu:**
```json
[
  {
    "symbol": "FPT",
    "ref_price": 89600,
    "open_price": 90100,
    "match_price": 87400,
    "match_vol": 500,
    "accumulated_volume": 12281400,
    "accumulated_value": 1090594.1,
    "highest": 90900,
    "lowest": 87200,
    "foreign_buy_volume": 677585,
    "foreign_sell_volume": 1544060
  }
]
```

**Giải thích các trường dữ liệu:**

| Trường               | Ý nghĩa                                     |
|----------------------|----------------------------------------------|
| `symbol`             | Mã cổ phiếu                                 |
| `ref_price`          | Giá tham chiếu                               |
| `open_price`         | Giá mở cửa                                  |
| `match_price`        | Giá khớp lệnh gần nhất                      |
| `match_vol`          | Khối lượng khớp lệnh gần nhất               |
| `accumulated_volume` | **Tổng khối lượng giao dịch trong phiên**    |
| `accumulated_value`  | Tổng giá trị giao dịch (triệu VND)          |
| `highest`            | Giá cao nhất phiên                           |
| `lowest`             | Giá thấp nhất phiên                          |
| `foreign_buy_volume` | Khối lượng mua của khối ngoại                |
| `foreign_sell_volume`| Khối lượng bán của khối ngoại                |

### B. Lấy giá Crypto (Tiền Mã Hóa)
* **Endpoint:** `POST /crypto/quotes`
* **Body:**
```json
{
  "symbols": ["BTCUSDT", "ETHUSDT"]
}
```
* **Response mẫu:**
```json
[
  {
    "symbol": "BTCUSDT",
    "ref_price": 66744.45,
    "open_price": 66744.45
  }
]
```

### C. Lấy giá Vàng
* **Endpoint:** `GET /gold/quotes`
* **Response mẫu:**
```json
[
  {
    "symbol": "XAUUSD",
    "name": "World Gold (XAU/USD)",
    "buy_price": 5312.3,
    "sell_price": 0,
    "currency": "USD"
  },
  {
    "symbol": "DOJINHTV",
    "name": "DOJI Jewelry",
    "buy_price": 185200000,
    "sell_price": 188200000,
    "currency": "VND"
  }
]
```

---

## 3. Deployment (Deploy lên Koyeb / Render)

Dự án đã có sẵn `Dockerfile` chuẩn. Các bước:
1. Đăng ký/đăng nhập Koyeb hoặc Render
2. Tạo Service -> Kết nối tới GitHub -> Chọn Repository này
3. Cấu hình Environment Variables:
   - `API_SECRET_TOKEN` = `Mật_khẩu_bí_mật_của_bạn`
4. Bấm **Deploy** và tận hưởng!

> ⚠️ **Lưu ý:** Đừng để trống biến `API_SECRET_TOKEN` để bảo vệ API khỏi truy cập trái phép.
