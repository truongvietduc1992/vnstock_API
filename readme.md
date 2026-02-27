# VNStock API
API được thiết kế để kết nối và lấy dữ liệu chứng khoán Việt Nam qua thư viện `vnstock` v0.1.5 và đóng gói gọn dưới dạng Fast API. Thích hợp cho việc deploy nhanh qua Docker hoặc các dịch vụ PsaS như Koyeb/Render, v.v.

**Tính năng:**
* Fetch giá tham chiếu (ref_price), giá mở cửa (open_price) của nhiều mã chứng khoán cùng lúc.
* Lấy giá Crypto thông qua Binance API (Cập nhật real-time).
* Lấy giá Vàng trong và ngoài nước qua cổng GiavangNOW.
* Xác thực bằng **API Token Header**.
* Tối ưu bộ nhớ Cache 60s phù hợp cài đặt trên các VPS Free/Eco cấu hình yếu (Tránh nghẽn CPU và tránh bị block IP API nguồn).

---

## 1. Cài đặt môi trường Local và chạy thử (Run API Locally)

Để test ở dưới máy, mở Terminal / CMD và cài đặt môi trường. (Yêu cầu sẵn Python 3.10+):

1. Clone project: `git clone <your_github_repo_link>`
2. Cài đặt các thư viện yêu cầu: `pip install -r requirements.txt` (Nếu dùng máy cấu hình mạnh, có thể dùng `uvicorn main:app --reload` để chạy).
3. Thêm token tạm vào biến môi trường (Ví dụ: 1324) 
    * Windows: `set API_SECRET_TOKEN=1324`
    * Linux/Mac: `export API_SECRET_TOKEN=1324`
4. Khởi động server (Mặc định ở `http://localhost:8000`):
    `python -m uvicorn main:app --host 0.0.0.0 --port 8000`

---

## 2. Các Endpoint (API Docs)

Lưu ý: Bạn phải truyền **Header** bắt buộc là `X-Access-Token` với Token bạn đã setup (Mặc định nếu chưa set biến môi trường là `1324`)

### A. Lấy giá Chứng Khoán VN
* Cú pháp: `POST /stocks/quotes`
* Body json: 
```json
{
  "symbols": ["FPT", "TCB"]
}
```

### B. Lấy giá Hình thái Crypto (Tiền Mã Hóa) 
* Cú pháp: `POST /crypto/quotes`
* Body json: 
```json
{
  "symbols": ["BTCUSDT", "ETHUSDT"]
}
```

### C. Lấy giá Vàng
* Cú pháp: `GET /gold/quotes`
* Trả về kết quả JSON với Data Vàng thế giới, Vàng 9999, DOJI,...

---

## 3. Deployment (Deploy app lên Koyeb / Render)

Dự án này đã có đủ File `Dockerfile` cấu hình cực mịn theo chuẩn. Bạn chỉ cần:
1. Đăng ký/đăng nhập Koyeb hoặc Render
2. Tạo Service -> Kết nối tới tài khoản Github -> Chọn Repositories này.
3. Ở cấu hình Environment Variables của máy ảo Koyeb:
   -> Thêm Biến: KEY là `API_SECRET_TOKEN`, VALUE là `Mật_khẩu_bí_mật_của_bạn_tuỳ_thích`
   *Chú ý: Đừng để trống biến này để không ai truy cập vào phá API của bạn.*
4. Bấm `Deploy` và tận hưởng!
