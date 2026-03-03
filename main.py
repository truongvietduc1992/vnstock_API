import os
import urllib.request
import urllib.parse
import json
import ssl
import time
import pandas as pd
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from vnstock import Trading
from typing import List, Dict, Any

# --- CẤU HÌNH BẢO MẬT & CACHE (Tối ưu cho VPS nhỏ) ---
API_KEY_NAME = "X-Access-Token"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)
SECRET_TOKEN = os.environ.get("API_SECRET_TOKEN", "1324") 

CACHE_TTL = 60 # Lưu kết quả 60 giây để tránh nghẽn CPU/RAM
cache_quotes = {
    "stock": {},
    "crypto": {},
    "gold": {"time": 0, "data": None}
}

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
    
    symbols_list = [s.strip().upper() for s in request.symbols if s.strip()]
    cache_key = ",".join(sorted(symbols_list))
    
    # Kiểm tra cache
    now = time.time()
    if cache_key in cache_quotes["stock"]:
        if now - cache_quotes["stock"][cache_key]["time"] < CACHE_TTL:
            return cache_quotes["stock"][cache_key]["data"]

    try:
        # Gọi vnstock fetch dữ liệu
        df = Trading(source='VCI').price_board(symbols_list=symbols_list)
        
        # Xử lý làm phẳng cột nếu là MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            new_cols = []
            for col in df.columns:
                col_name = col[1] if isinstance(col, tuple) else col
                new_cols.append(col_name)
            df.columns = new_cols

        # Trích xuất các cột cần thiết (bao gồm khối lượng giao dịch)
        required_cols = ['symbol', 'ref_price', 'open_price']
        optional_cols = [
            'match_price',          # Giá khớp lệnh gần nhất
            'match_vol',            # KL khớp lệnh gần nhất
            'accumulated_volume',   # Tổng KL giao dịch trong phiên
            'accumulated_value',    # Tổng giá trị giao dịch (triệu VND)
            'highest',              # Giá cao nhất phiên
            'lowest',               # Giá thấp nhất phiên
            'foreign_buy_volume',   # KL mua của khối ngoại
            'foreign_sell_volume',  # KL bán của khối ngoại
        ]
        for col in required_cols:
            if col not in df.columns:
                raise Exception(f"Thiếu cột {col} trong dữ liệu vnstock. Cột hiện có: {list(df.columns)}")

        # Thêm các cột tùy chọn nếu có
        all_cols = required_cols + [c for c in optional_cols if c in df.columns]
        result_df = df[all_cols].copy()
        result = result_df.to_dict('records')
        
        # Lưu cache
        cache_quotes["stock"][cache_key] = {"time": now, "data": result}
        return result

    except Exception as e:
        print(f"Lỗi API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")

@app.post("/crypto/quotes", response_model=List[Dict[str, Any]])
def get_crypto_quotes(request: StockRequest, api_key: str = Security(get_api_key)):
    if not request.symbols:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp ít nhất một mã crypto (VD: BTCUSDT).")
    
    symbols_list = [s.strip().upper() for s in request.symbols if s.strip()]
    cache_key = ",".join(sorted(symbols_list))
    
    # Kiểm tra cache
    now = time.time()
    if cache_key in cache_quotes["crypto"]:
        if now - cache_quotes["crypto"][cache_key]["time"] < CACHE_TTL:
            return cache_quotes["crypto"][cache_key]["data"]

    try:
        symbols_json = json.dumps(symbols_list).replace(" ", "") # Xoá khoảng trắng để Binance không báo lỗi
        url = f"https://data-api.binance.vision/api/v3/ticker/price?symbols={urllib.parse.quote(symbols_json)}"

        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            # Convert response format to be similar to stock (symbol, ref_price, open_price - where open_price is not accurate, use price for all)
            result = []
            for item in data:
                result.append({
                    "symbol": item.get('symbol'),
                    "ref_price": float(item.get('price')),
                    "open_price": float(item.get('price')) 
                })
            
            # Lưu cache
            cache_quotes["crypto"][cache_key] = {"time": now, "data": result}
            return result
    except urllib.error.HTTPError as e:
        raise HTTPException(status_code=e.code, detail=f"Binance API lỗi: {e.reason}")
    except Exception as e:
        print(f"Lỗi hệ thống Crypto API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")

@app.get("/gold/quotes")
def get_gold_quotes(api_key: str = Security(get_api_key)):
    # Kiểm tra cache
    now = time.time()
    if cache_quotes["gold"]["data"] and (now - cache_quotes["gold"]["time"] < CACHE_TTL):
        return cache_quotes["gold"]["data"]

    try:
        url = "https://giavang.now/api/prices"
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
            data = json.loads(response.read())
            
            if not data.get("success"):
                raise HTTPException(status_code=500, detail="API giá vàng trả về lỗi.")
            
            prices_dict = data.get("prices", {})
            result = []
            for key, val in prices_dict.items():
                result.append({
                    "symbol": key,
                    "name": val.get("name"),
                    "buy_price": val.get("buy"),
                    "sell_price": val.get("sell"),
                    "currency": val.get("currency")
                })
            
            # Lưu cache
            cache_quotes["gold"] = {"time": now, "data": result}
            return result
    except urllib.error.HTTPError as e:
        raise HTTPException(status_code=e.code, detail=f"GiavangAPI lỗi: {e.reason}")
    except Exception as e:
        print(f"Lỗi hệ thống Gold API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")
