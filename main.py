import os
import pandas as pd
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from vnstock import Trading
from typing import List, Dict, Any

# --- CẤU HÌNH BẢO MẬT ---
API_KEY_NAME = "X-Access-Token"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)
SECRET_TOKEN = os.environ.get("API_SECRET_TOKEN", "1324") 

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == SECRET_TOKEN:
        return api_key
    raise HTTPException(
        status_code=403, 
        detail=f"Invalid API Key. Please provide the correct token in the '{API_KEY_NAME}' header."
    )

# --- MODELS ---
class StockRequest(BaseModel):
    symbols: List[str]

app = FastAPI(title="VNStock API v2.0.3", version="2.0.3")

@app.get("/")
async def root():
    return {"status": "alive", "message": "VNStock API is online", "token_hint": "X-Access-Token required for quotes"}

@app.post("/stocks/quotes", response_model=List[Dict[str, Any]])
async def get_combined_quotes(request: StockRequest, api_key: str = Security(get_api_key)):
    if not request.symbols:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp ít nhất một mã cổ phiếu.")
    
    try:
        symbols_list = [s.strip().upper() for s in request.symbols if s.strip()]
        # Gọi vnstock fetch dữ liệu
        df = Trading(source='VCI').price_board(symbols_list=symbols_list)
        
        # Xử lý làm phẳng cột nếu là MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            # Cấu trúc mới thường là ('listing', 'symbol'), ('listing', 'ref_price'), ('match', 'open_price')
            # Chúng ta sẽ tìm dựa trên level 1 của cột
            new_cols = []
            for col in df.columns:
                col_name = col[1] if isinstance(col, tuple) else col
                new_cols.append(col_name)
            df.columns = new_cols

        # Trích xuất các cột cần thiết
        required_cols = ['symbol', 'ref_price', 'open_price']
        for col in required_cols:
            if col not in df.columns:
                raise Exception(f"Thiếu cột {col} trong dữ liệu vnstock. Cột hiện có: {list(df.columns)}")

        result_df = df[required_cols].copy()
        return result_df.to_dict('records')

    except Exception as e:
        print(f"Lỗi API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")
