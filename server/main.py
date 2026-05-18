import hmac
import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from server.config import get_settings
from server.dedup import DuplicateAlertStore
from server.logging_setup import configure_logging
from server.models import TradingViewAlert
from server.okx import OKXClient


settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("webhook.api")

dedup_store = DuplicateAlertStore(settings.sqlite_path, settings.duplicate_window_seconds)
okx_client = OKXClient(settings)

app = FastAPI(title="TradingView OKX Webhook Server", version="1.0.0")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    response = JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "invalid request body",
            "errors": exc.errors(),
        },
    )
    logger.warning("Validation error response=%s", response.body.decode("utf-8"))
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    content = {
        "status": "error",
        "message": exc.detail,
    }
    logger.warning("HTTP error response=%s", content)
    return JSONResponse(status_code=exc.status_code, content=content)


@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(alert: TradingViewAlert, request: Request) -> dict:
    logger.info(
        "Incoming webhook ip=%s action=%s symbol=%s price=%s timeframe=%s strategy=%s market_type=%s leverage=%s",
        request.client.host if request.client else "unknown",
        alert.action,
        alert.symbol,
        alert.price,
        alert.timeframe,
        alert.strategy_name,
        alert.market_type,
        alert.leverage,
    )

    if settings.webhook_secret:
        provided_secret = request.headers.get("x-webhook-secret", "")
        if not hmac.compare_digest(provided_secret, settings.webhook_secret):
            logger.warning("Rejected webhook with invalid secret")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid webhook secret",
            )

    payload = alert.model_dump(mode="json")
    payload["_duplicate_window_seconds"] = settings.duplicate_window_seconds
    is_duplicate, dedupe_key = dedup_store.is_duplicate(payload)
    if is_duplicate:
        logger.warning("Duplicate webhook rejected dedupe_key=%s symbol=%s", dedupe_key, alert.symbol)
        response_payload = {
            "status": "duplicate_rejected",
            "message": "duplicate alert rejected within time window",
            "dedupe_key": dedupe_key,
        }
        logger.info("Webhook response dedupe_key=%s body=%s", dedupe_key, response_payload)
        return response_payload

    try:
        okx_response = await okx_client.execute_alert(alert)
        response_payload = {
            "status": "success",
            "message": "alert accepted and processed",
            "dedupe_key": dedupe_key,
            "okx": okx_response,
        }
        logger.info("Webhook response dedupe_key=%s body=%s", dedupe_key, response_payload)
        return response_payload
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected webhook processing failure")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="unexpected server error",
        )
