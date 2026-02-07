import os
from aiohttp import web, WSMsgType
import asyncio

# Хранилище активных соединений
village_ws = None
web_conns = {}

async def handle_control(request):
    """Управляющее соединение (для твоего bridge.py)"""
    global village_client
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    village_client = ws
    print("[+] Мост из деревни подключен")
    
    try:
        async for msg in ws:
            if msg.type == WSMsgType.BINARY:
                data = msg.data
                if data.startswith(b"DATA:"):
                    parts = data.split(b":", 2)
                    conn_id = parts[1].decode()
                    if conn_id in web_conns:
                        await web_conns[conn_id].send_bytes(parts[2])
    finally:
        village_client = None
        print("[-] Мост отключен")
    return ws

async def handle_public(request):
    """Входящие соединения (для твоей ратки)"""
    global village_client
    if not village_client:
        return web.Response(status=503, text="Tunnel Offline")

    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    import uuid
    conn_id = str(uuid.uuid4())[:8]
    web_conns[conn_id] = ws
    
    print(f"[*] Новое соединение [{conn_id}]")
    await village_client.send_str(f"OPEN:{conn_id}")

    try:
        async for msg in ws:
            if msg.type in (WSMsgType.BINARY, WSMsgType.TEXT):
                payload = msg.data if isinstance(msg.data, bytes) else msg.data.encode()
                packet = f"DATA:{conn_id}:".encode() + payload
                await village_client.send_bytes(packet)
    finally:
        if village_client:
            await village_client.send_str(f"CLOSE:{conn_id}")
        web_conns.pop(conn_id, None)
    return ws

async def health_check(request):
    return web.Response(text="Nexus Tunnel is Live")

app = web.Application()
app.add_routes([
    web.get('/control', handle_control), # Сюда вешаем bridge.py
    web.get('/', health_check),          # Это для Render (Health Check)
    web.get('/{tail:.*}', handle_public) # Всё остальное — трафик для ратки
])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host='0.0.0.0', port=port)
