import json
import logging
import os
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_handler")

DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "NasdaqStockPredictions")
REGION = os.environ.get("AWS_REGION", "ap-southeast-1")

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(DYNAMODB_TABLE)


# Helpers

def decimal_to_float(obj):
    """Chuyển Decimal (DynamoDB) sang float để JSON serialise được"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


def response(status_code, body, cache_seconds=60):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Cache-Control": f"public, max-age={cache_seconds}",
        },
        "body": json.dumps(body, default=decimal_to_float),
    }


def error_response(status_code, message):
    return response(status_code, {"error": message}, cache_seconds=0)


# Route Handlers

def get_latest_predictions(query_params: dict):
    """
    GET /predictions/latest
    Tham số tuỳ chọn:
      - limit  : số lượng kết quả trả về (default 100)
      - filter : "bullish" | "bearish" | "all" (default "all")
    """
    limit  = int(query_params.get("limit", 100))
    filter_ = query_params.get("filter", "all").lower()

    # Lấy ngày mới nhất từ GSI (LatestDateIndex)
    # Query GSI để lấy tất cả record theo Date mới nhất
    # Dùng scan + filter bằng attribute LatestFlag = 1 (được set bởi Lambda predictor)
    result = table.query(
        IndexName="LatestFlag-Probability-index",
        KeyConditionExpression=Key("LatestFlag").eq(1),
        ScanIndexForward=False,  # giảm dần theo Probability
        Limit=limit * 2  # lấy dư để sau filter
    )

    items = result.get("Items", [])

    # Filter nếu cần
    if filter_ == "bullish":
        items = [i for i in items if int(i.get("Prediction", 0)) == 1]
    elif filter_ == "bearish":
        items = [i for i in items if int(i.get("Prediction", 0)) == 0]

    return response(200, {
        "date": items[0]["Date"] if items else None,
        "total": len(items[:limit]),
        "predictions": items[:limit]
    })


def get_symbol_history(symbol: str, query_params: dict):
    """
    GET /predictions/{symbol}
    Tham số tuỳ chọn:
      - days : số ngày lịch sử muốn lấy (default 30)
    """
    days = int(query_params.get("days", 30))

    result = table.query(
        KeyConditionExpression=Key("Symbol").eq(symbol.upper()),
        ScanIndexForward=False,   # ngày mới nhất trước
        Limit=days
    )

    items = result.get("Items", [])
    if not items:
        return error_response(404, f"Không tìm thấy dữ liệu cho mã {symbol}")

    # Tính thêm accuracy gần đây nếu có trường ActualLabel
    correct = sum(
        1 for i in items
        if "ActualLabel" in i and int(i["ActualLabel"]) == int(i.get("Prediction", -1))
    )
    has_actual = sum(1 for i in items if "ActualLabel" in i)
    accuracy_recent = correct / has_actual if has_actual > 0 else None

    return response(200, {
        "symbol": symbol.upper(),
        "days": len(items),
        "accuracy_recent": accuracy_recent,
        "history": list(reversed(items))  # trả theo thứ tự thời gian tăng dần
    })


def get_symbol_stats(symbol: str):
    """
    GET /predictions/{symbol}/stats
    Thống kê tổng hợp: accuracy, bullish_rate, avg_probability
    """
    result = table.query(
        KeyConditionExpression=Key("Symbol").eq(symbol.upper()),
        ScanIndexForward=False,
        Limit=90  # lấy 90 ngày
    )

    items = result.get("Items", [])
    if not items:
        return error_response(404, f"Không tìm thấy dữ liệu cho mã {symbol}")

    bullish = [i for i in items if int(i.get("Prediction", 0)) == 1]
    probs = [float(i.get("Probability", 0.5)) for i in items]
    has_actual = [i for i in items if "ActualLabel" in i]
    correct = [i for i in has_actual if int(i["ActualLabel"]) == int(i["Prediction"])]

    return response(200, {
        "symbol": symbol.upper(),
        "total_predictions": len(items),
        "bullish_rate": len(bullish) / len(items) if items else 0,
        "avg_probability": sum(probs) / len(probs) if probs else 0,
        "accuracy": len(correct) / len(has_actual) if has_actual else None,
        "latest_prediction": items[0] if items else None
    })


# Lambda Handler

def lambda_handler(event, context):
    logger.info(f"Event: {json.dumps(event)}")

    try:
        path_params   = event.get("pathParameters") or {}
        query_params  = event.get("queryStringParameters") or {}
        resource      = event.get("resource", "")
        http_method   = event.get("httpMethod", "GET")

        if http_method != "GET":
            return error_response(405, "Method not allowed")

        # Route: GET /predictions/latest
        if resource == "/predictions/latest":
            return get_latest_predictions(query_params)

        # Route: GET /predictions/{symbol}/stats
        if resource == "/predictions/{symbol}/stats":
            symbol = path_params.get("symbol", "")
            if not symbol:
                return error_response(400, "Thiếu symbol")
            return get_symbol_stats(symbol)

        # Route: GET /predictions/{symbol}
        if resource == "/predictions/{symbol}":
            symbol = path_params.get("symbol", "")
            if not symbol:
                return error_response(400, "Thiếu symbol")
            return get_symbol_history(symbol, query_params)

        return error_response(404, f"Route không tồn tại: {resource}")

    except Exception as e:
        logger.error(f"Lỗi không xử lý được: {e}", exc_info=True)
        return error_response(500, str(e))
