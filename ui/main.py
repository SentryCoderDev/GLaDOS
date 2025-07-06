# main.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
import os
from fastapi.middleware.cors import CORSMiddleware
import socket
import asyncio
import json
import random
import time
import requests

app = FastAPI()

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTML dosyasının içeriğini oku
html_content = ""
try:
    with open("index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
except FileNotFoundError:
    html_content = """
    <h1>Error</h1>
    <p>index.html dosyası bulunamadı. Lütfen 'main.py' ile aynı dizinde olduğundan emin olun.</p>
    """

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Ana sayfayı sunar."""
    return HTMLResponse(content=html_content)

# IP adresini socket modülü ile al ve sabit bir değişkende sakla
def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except Exception:
        return "127.0.0.1"

# IP adresini yalnızca bir kez hesapla ve sabit bir değişkende sakla
static_ip_address = get_ip_address()

@app.get("/system-info")
async def get_system_info():
    """Gerçek zamanlı sistem bilgilerini döndürür."""
    port = "8080"  # Port bilgisi sabit
    return {
        "ip": static_ip_address,  # Sabit IP adresi
        "port": port
    }

@app.get("/want_you_gone.mp3")
async def serve_music():
    """Müzik dosyasını servis et."""
    music_path = "want_you_gone.mp3"
    if os.path.exists(music_path):
        return FileResponse(
            music_path,
            media_type="audio/mpeg",
            headers={"Cache-Control": "public, max-age=3600"}
        )
    else:
        return {"error": "Music file not found"}

@app.get("/want_you_gone.ogg")
async def serve_music_ogg():
    """Müzik dosyasını servis et (OGG format)."""
    music_path = "want_you_gone.ogg"
    if os.path.exists(music_path):
        return FileResponse(
            music_path,
            media_type="audio/ogg",
            headers={"Cache-Control": "public, max-age=3600"}
        )
    else:
        return {"error": "Music file not found"}

@app.get("/data-stream")
async def get_data_stream():
    """Chunked data stream endpoint'i."""
    async def generate_chunks():
        # Boot-up sequence
        boot_sequence = [
            "APERTURE SCIENCE COMPUTER-AIDED ENRICHMENT CENTER",
            "GLaDOS v4.2.1 - BOOT SEQUENCE INITIATED",
            "Loading core personality matrices...",
            "Initializing neurotoxin delivery systems...",
            "Calibrating portal technology...",
            "Scanning test chambers for subjects...",
            "Loading cake recipe database...",
            "Activating facility monitoring systems...",
            "BOOT SEQUENCE COMPLETE",
            "SYSTEM STATUS: OPERATIONAL"
        ]
        
        # Boot-up mesajlarını gönder
        for i, message in enumerate(boot_sequence):
            await asyncio.sleep(0.8)
            chunk_info = {
                "chunk_id": i + 1,
                "data": message,
                "timestamp": time.time(),
                "total_chunks": len(boot_sequence),
                "phase": "boot"
            }
            yield f"data: {json.dumps(chunk_info)}\n\n"
        
        # Ollama bağlantısını kontrol et
        ollama_available = check_ollama_connection()
        
        if ollama_available:
            # Ollama'dan sürekli çıktı al
            async for chunk in generate_ollama_stream():
                yield chunk
        else:
            # Sleep time - şarkı sözleri moduna geç
            await asyncio.sleep(2)
            sleep_chunk = {
                "chunk_id": len(boot_sequence) + 1,
                "data": "OLLAMA CONNECTION NOT AVAILABLE - ENTERING SLEEP MODE",
                "timestamp": time.time(),
                "total_chunks": len(boot_sequence) + 1,
                "phase": "sleep_transition"
            }
            yield f"data: {json.dumps(sleep_chunk)}\n\n"
    
    return StreamingResponse(
        generate_chunks(), 
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

def check_ollama_connection():
    """Ollama bağlantısını kontrol et."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

async def generate_ollama_stream():
    """Ollama'dan sürekli stream al."""
    prompts = [
        "Generate a short scientific observation about portal technology.",
        "Describe a test chamber safety protocol.",
        "Explain a cake recipe ingredient.",
        "Generate a subject evaluation report.",
        "Describe a facility maintenance task."
    ]
    
    chunk_counter = 11  # Boot sequence sonrası
    
    while True:
        try:
            prompt = random.choice(prompts)
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2:1b",  # Veya mevcut modeliniz
                    "prompt": f"You are GLaDOS from Portal. {prompt} Keep it short (1-2 sentences).",
                    "stream": False
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                ollama_output = result.get("response", "No response from Ollama")
                
                chunk_info = {
                    "chunk_id": chunk_counter,
                    "data": f"OLLAMA OUTPUT: {ollama_output}",
                    "timestamp": time.time(),
                    "phase": "ollama"
                }
                chunk_counter += 1
                
                yield f"data: {json.dumps(chunk_info)}\n\n"
                await asyncio.sleep(random.uniform(3, 8))  # Rastgele gecikme
            else:
                break
                
        except Exception as e:
            print(f"Ollama error: {e}")
            break