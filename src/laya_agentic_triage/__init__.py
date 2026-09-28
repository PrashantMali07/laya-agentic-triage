import uvicorn
def main() -> None:
    uvicorn.run("laya_agentic_triage.main:app", host="0.0.0.0", port=8000, reload=True)