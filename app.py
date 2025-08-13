
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
import os
import httpx

APP_NAME = os.getenv("APP_NAME", "Virtual Terminal Frontend")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000").rstrip("/")

app = FastAPI(title=APP_NAME)

# CORS for Android terminals if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

PROTOCOLS = [
    "POS Terminal -101.1 (4-digit approval)",
    "POS Terminal -101.4 (6-digit approval)",
    "POS Terminal -101.6 (Pre-authorization)",
    "POS Terminal -101.7 (4-digit approval)",
    "POS Terminal -101.8 (PIN-LESS transaction)",
    "POS Terminal -201.1 (6-digit approval)",
    "POS Terminal -201.3 (6-digit approval)",
    "POS Terminal -201.5 (6-digit approval)"
]

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "protocols": PROTOCOLS,
        "backend": BACKEND_BASE_URL
    })

@app.post("/process", response_class=HTMLResponse)
async def process(request: Request,
                  card_number: str = Form(...),
                  protocol: str = Form(...),
                  auth_code: str = Form(...),
                  amount: float = Form(...),
                  payout_type: str = Form(...),
                  payout_network: str = Form(None),
                  payout_target: str = Form(...)):
    payload = {
        "card_number": card_number,
        "protocol": protocol,
        "auth_code": auth_code,
        "amount": amount,
        "payout_type": payout_type,
        "payout_network": payout_network if payout_type == "CRYPTO" else None,
        "payout_target": payout_target
    }
    async with httpx.AsyncClient(timeout=25) as client:
        try:
            r = await client.post(f"{BACKEND_BASE_URL}/api/v1/transactions/process", json=payload)
            r.raise_for_status()
            data = r.json()
        except httpx.HTTPStatusError as e:
            detail = e.response.json().get("detail", str(e))
            return templates.TemplateResponse("result.html", {
                "request": request,
                "ok": False,
                "error": detail,
                "backend": BACKEND_BASE_URL
            }, status_code=e.response.status_code)
        except Exception as ex:
            return templates.TemplateResponse("result.html", {
                "request": request,
                "ok": False,
                "error": str(ex),
                "backend": BACKEND_BASE_URL
            }, status_code=500)
    return templates.TemplateResponse("result.html", {
        "request": request,
        "ok": True,
        "result": data,
        "backend": BACKEND_BASE_URL
    })

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    # simply embed backend dashboard in an iframe for convenience
    backend_dash = f"{BACKEND_BASE_URL}/dashboard"
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "backend_dashboard": backend_dash
    })

@app.get("/health")
def health():
    return {"ok": True, "frontend": APP_NAME, "backend": BACKEND_BASE_URL}
