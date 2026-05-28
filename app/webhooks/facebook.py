import json
import hmac
import hashlib
from fastapi import APIRouter, Query, Request, Header, HTTPException, Response
from app.core.config import settings
from app.db.redis import redis_manager
from loguru import logger

router = APIRouter()

@router.get("/facebook")
async def verify_facebook_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """Xác thực Webhook với Facebook (Verification)."""
    if hub_mode == "subscribe" and hub_verify_token == settings.social.fb_verify_token:
        logger.bind(context="FB-Webhook").info("Facebook webhook verified successfully")
        return Response(content=hub_challenge)
    
    logger.bind(context="FB-Webhook").warning("Facebook webhook verification failed")
    return Response(content="Verification failed", status_code=403)

@router.post("/facebook")
async def handle_facebook_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None)
):
    """Nhận và xử lý sự kiện Webhook từ Facebook (Events)."""
    # 1. Xác thực chữ ký (Security)
    if not x_hub_signature_256:
        raise HTTPException(status_code=401, detail="X-Hub-Signature-256 missing")

    body = await request.body()
    expected_signature = "sha256=" + hmac.new(
        settings.social.fb_app_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(x_hub_signature_256, expected_signature):
        logger.bind(context="FB-Webhook").warning("Signature mismatch")
        raise HTTPException(status_code=403, detail="Signature mismatch")

    # 2. Xử lý payload
    try:
        data = json.loads(body.decode())
        logger.bind(context="FB-Webhook").info(f"Received FB Webhook: {data}")
        
        # 3. Đẩy vào Redis Stream
        # Stream Name: FACEBOOK_MESSAGE_STREAM
        # Format: { "message": JSON_STRING({ "type": "FACEBOOK_MESSAGE", "data": messaging }) }
        if data.get("object") == "page":
            stream_name = "FACEBOOK_MESSAGE_STREAM"
            for entry in data.get("entry", []):
                for messaging in entry.get("messaging", []):
                    event_data = {
                        "message": json.dumps({
                            "type": "FACEBOOK_MESSAGE",
                            "data": messaging
                        })
                    }
                    await redis_manager.client.xadd(stream_name, event_data)
                    logger.bind(context="FB-Webhook").debug("Added FB event to Redis Stream")
        
        return {"status": "ok"}
    except Exception as e:
        logger.bind(context="FB-Webhook").error(f"Error processing FB Webhook: {e}")
        return {"status": "error", "message": str(e)}
