import os
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from vnstock import Trading
import pandas as pd
from typing import List, Dict, Any


# --- CẤU HÌNH BẢO MẬT ---
# 1. Khai báo Security Scheme: Yêu cầu người dùng gửi header 'X-Access-Token'
API_KEY_NAME = "X-Access-Token"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

# 2. Token bí mật của bạn (RẤT QUAN TRỌNG: Hãy thay đổi và lưu trong biến môi trường khi deploy!)
SECRET_TOKEN = os.environ.get("API_SECRET_TOKEN", "fallback_token") # Dùng dòng này

# 3. Hàm Dependency kiểm tra Token
async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == SECRET_TOKEN:
        return api_key
    # Tự động trả về HTTP 403 nếu token không hợp lệ
    raise HTTPException(
        status_code=403, 
        detail=f"Invalid API Key. Please provide the correct token in the '{API_KEY_NAME}' header."
    )
# -------------------------





# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title="API Giá Cổ Phiếu Tách Biệt",
    description="API lấy Giá Tham chiếu và Giá Mở cửa tại 2 endpoint riêng biệt.",
    version="1.4.0"
)

# --- Hàm chung để xử lý và trích xuất dữ liệu ---
def get_stock_data(symbols_list: List[str], data_column: tuple, output_key: str) -> List[Dict[str, Any]]:
    """
    Hàm này gọi trading.price_board và chỉ trích xuất cột dữ liệu được chỉ định.
    
    Args:
        symbols_list: Danh sách các mã cổ phiếu.
        data_column: Tên cột đa cấp cần trích xuất (vd: ('listing', 'ref_price')).
        output_key: Tên khóa JSON mong muốn (vd: 'ref_price').
        
    Returns:
        List[Dict[str, Any]]: Danh sách các object JSON chứa mã và giá trị.
    """
    
    if not symbols_list:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp ít nhất một mã cổ phiếu.")
    
    try:
        # Lấy toàn bộ bảng giá
        df = Trading(source ='VCI').price_board(symbols_list=symbols_list)
        
        # Định nghĩa các cột cần thiết (symbol và cột data_column)
        COLUMNS_TO_EXTRACT = [
            ('listing', 'symbol'),     # Cột mã cổ phiếu
            data_column                # Cột dữ liệu cần thiết
        ]

        # Kiểm tra sự tồn tại của các cột trước khi trích xuất
        for col in COLUMNS_TO_EXTRACT:
            if col not in df.columns:
                 raise HTTPException(
                    status_code=500, 
                    detail=f"Cột {col} không tồn tại trong dữ liệu. Cấu trúc vnstock có thể đã thay đổi."
                )

        # 1. Trích xuất các cột cần thiết
        result_df = df[COLUMNS_TO_EXTRACT]

        # 2. Đổi tên cột để làm phẳng cấu trúc JSON
        result_df.columns = ['symbol', output_key]
        
        # 3. Chuyển kết quả sang định dạng list of dictionaries (JSON)
        return result_df.to_dict('records')

    except HTTPException:
        raise 
    except Exception as e:
        print(f"Lỗi chi tiết: {e}") 
        raise HTTPException(
            status_code=500, 
            detail=f"Đã xảy ra lỗi khi xử lý dữ liệu: {type(e).__name__}"
        )


# --- ENDPOINT 1: Lấy Giá Tham chiếu (ref_price) ---
@app.get("/stocks/ref-price", response_model=List[Dict[str, Any]])
async def get_reference_price(symbols: str):
    """
    Lấy **Giá Tham chiếu** ('listing', 'ref_price').
    
    - **symbols**: Mã cổ phiếu cách nhau bằng dấu phẩy (vd: VCB,ACB,BID).
    """
    symbols_list = [s.strip().upper() for s in symbols.split(',')]
    symbols_list = [s for s in symbols_list if s]

    # Sử dụng hàm chung để trích xuất dữ liệu
    return get_stock_data(
        symbols_list=symbols_list, 
        data_column=('listing', 'ref_price'),
        output_key='ref_price'
    )


# --- ENDPOINT 2: Lấy Giá Mở cửa (open_price) ---
@app.get("/stocks/open-price", response_model=List[Dict[str, Any]])
async def get_opening_price(symbols: str):
    """
    Lấy **Giá Mở cửa** ('match', 'open_price').
    
    - **symbols**: Mã cổ phiếu cách nhau bằng dấu phẩy (vd: VCB,ACB,BID).
    """
    symbols_list = [s.strip().upper() for s in symbols.split(',')]
    symbols_list = [s for s in symbols_list if s]

    # Sử dụng hàm chung để trích xuất dữ liệu
    return get_stock_data(
        symbols_list=symbols_list, 
        data_column=('match', 'open_price'),
        output_key='open_price'
    )