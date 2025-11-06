import os
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
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


# --- ĐỊNH NGHĨA REQUEST BODY MODEL ---
class StockRequest(BaseModel):
    """Model cho Request Body (JSON Payload)"""
    symbols: List[str] 
# ------------------------------------


# # Khởi tạo ứng dụng FastAPI
# app = FastAPI(
#     title="API Giá Cổ Phiếu Tách Biệt",
#     description="API lấy Giá Tham chiếu và Giá Mở cửa tại 2 endpoint riêng biệt.",
#     version="1.4.0"
# )

# # --- Hàm chung để xử lý và trích xuất dữ liệu ---
# def get_stock_data(symbols_list: List[str], data_column: tuple, output_key: str) -> List[Dict[str, Any]]:
#     """
#     Hàm này gọi trading.price_board và chỉ trích xuất cột dữ liệu được chỉ định.
    
#     Args:
#         symbols_list: Danh sách các mã cổ phiếu.
#         data_column: Tên cột đa cấp cần trích xuất (vd: ('listing', 'ref_price')).
#         output_key: Tên khóa JSON mong muốn (vd: 'ref_price').
        
#     Returns:
#         List[Dict[str, Any]]: Danh sách các object JSON chứa mã và giá trị.
#     """
    
#     if not symbols_list:
#         raise HTTPException(status_code=400, detail="Vui lòng cung cấp ít nhất một mã cổ phiếu.")
    
#     try:
#         # Lấy toàn bộ bảng giá
#         df = Trading(source ='VCI').price_board(symbols_list=symbols_list)
        
#         # Định nghĩa các cột cần thiết (symbol và cột data_column)
#         COLUMNS_TO_EXTRACT = [
#             ('listing', 'symbol'),     # Cột mã cổ phiếu
#             data_column                # Cột dữ liệu cần thiết
#         ]

#         # Kiểm tra sự tồn tại của các cột trước khi trích xuất
#         for col in COLUMNS_TO_EXTRACT:
#             if col not in df.columns:
#                  raise HTTPException(
#                     status_code=500, 
#                     detail=f"Cột {col} không tồn tại trong dữ liệu. Cấu trúc vnstock có thể đã thay đổi."
#                 )

#         # 1. Trích xuất các cột cần thiết
#         result_df = df[COLUMNS_TO_EXTRACT]

#         # 2. Đổi tên cột để làm phẳng cấu trúc JSON
#         result_df.columns = ['symbol', output_key]
        
#         # 3. Chuyển kết quả sang định dạng list of dictionaries (JSON)
#         return result_df.to_dict('records')

#     except HTTPException:
#         raise 
#     except Exception as e:
#         print(f"Lỗi chi tiết: {e}") 
#         raise HTTPException(
#             status_code=500, 
#             detail=f"Đã xảy ra lỗi khi xử lý dữ liệu: {type(e).__name__}"
#         )


# # --- ENDPOINT 1: Lấy Giá Tham chiếu (ref_price) ---
# @app.get("/stocks/ref-price", response_model=List[Dict[str, Any]])
# async def get_reference_price(symbols: str):
#     """
#     Lấy **Giá Tham chiếu** ('listing', 'ref_price').
    
#     - **symbols**: Mã cổ phiếu cách nhau bằng dấu phẩy (vd: VCB,ACB,BID).
#     """
#     symbols_list = [s.strip().upper() for s in symbols.split(',')]
#     symbols_list = [s for s in symbols_list if s]

#     # Sử dụng hàm chung để trích xuất dữ liệu
#     return get_stock_data(
#         symbols_list=symbols_list, 
#         data_column=('listing', 'ref_price'),
#         output_key='ref_price'
#     )


# # --- ENDPOINT 2: Lấy Giá Mở cửa (open_price) ---
# @app.get("/stocks/open-price", response_model=List[Dict[str, Any]])
# async def get_opening_price(symbols: str):
#     """
#     Lấy **Giá Mở cửa** ('match', 'open_price').
    
#     - **symbols**: Mã cổ phiếu cách nhau bằng dấu phẩy (vd: VCB,ACB,BID).
#     """
#     symbols_list = [s.strip().upper() for s in symbols.split(',')]
#     symbols_list = [s for s in symbols_list if s]

#     # Sử dụng hàm chung để trích xuất dữ liệu
#     return get_stock_data(
#         symbols_list=symbols_list, 
#         data_column=('match', 'open_price'),
#         output_key='open_price'
#     )

# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title="API Giá Cổ Phiếu Gộp Chung",
    description="API lấy Giá Tham chiếu và Giá Mở cửa trong một Request POST duy nhất.",
    version="1.6.0"
)

# --- Hàm chung để xử lý và trích xuất DỮ LIỆU GỘP CHUNG ---
def get_combined_stock_data(symbols_list: List[str]) -> List[Dict[str, Any]]:
    """
    Hàm gọi price_board và trích xuất ref_price và open_price.
    """
    
    if not symbols_list:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp ít nhất một mã cổ phiếu.")
    
    try:
        # Lấy toàn bộ bảng giá
        df = Trading(source='VCI').price_board(symbols_list=symbols_list)
        
        # Định nghĩa các cột đa cấp cần thiết
        COLUMNS_TO_EXTRACT = [
            ('listing', 'symbol'),     
            ('listing', 'ref_price'),  # Giá Tham chiếu
            ('match', 'open_price')    # Giá Mở cửa
        ]

        # 1. Trích xuất các cột cần thiết
        result_df = df[COLUMNS_TO_EXTRACT]

        # 2. Đổi tên cột để làm phẳng cấu trúc JSON
        result_df.columns = ['symbol', 'ref_price', 'open_price']
        
        # 3. Chuyển kết quả sang định dạng list of dictionaries (JSON)
        return result_df.to_dict('records')

    except Exception as e:
        print(f"Lỗi chi tiết: {e}") 
        # Sử dụng kiểm tra cụ thể để tránh lỗi MultiIndex không tồn tại
        if "not in index" in str(e):
             raise HTTPException(
                status_code=500, 
                detail="Cấu trúc dữ liệu trả về từ vnstock đã thay đổi. Vui lòng kiểm tra lại tên cột."
            )
        raise HTTPException(
            status_code=500, 
            detail=f"Đã xảy ra lỗi khi xử lý dữ liệu: {type(e).__name__}"
        )


# --- ENDPOINT CHUNG (POST): Lấy Cả ref-price và open-price ---
@app.post("/stocks/quotes", response_model=List[Dict[str, Any]])
async def get_combined_quotes(
    request: StockRequest, # Lấy dữ liệu từ Request Body
    api_key: str = Security(get_api_key) # Áp dụng bảo mật
):
    """
    Lấy cả Giá Tham chiếu và Giá Mở cửa cho danh sách mã chứng khoán được gửi qua Body.
    Body: {"symbols": ["VCB", "ACB", "BID"]}
    """
    # Xử lý danh sách mã chứng khoán từ Body
    symbols_list = [s.strip().upper() for s in request.symbols if s.strip()]

    # Sử dụng hàm gộp chung
    return get_combined_stock_data(symbols_list=symbols_list)

# (Bạn có thể giữ hoặc xóa các endpoint POST riêng lẻ cũ tùy nhu cầu)