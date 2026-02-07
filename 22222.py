import asyncio
import websockets
import os
import http.server
import threading

# --- CONFIG ---
PORT = int(os.environ.get("PORT", 8080))

# Простейший HTTP сервер для "обмана" Render (Health Check)
class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Nexus Tunnel is Running")

def run_health_check():
    server = http.server.HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
    server.serve_forever()

# --- WEBSOCKET LOGIC ---
async def tunnel_logic(websocket, path):
    # Тот же код, что я давал раньше
    if path == "/control":
        print("[+] Деревня подключена")
        try:
            async for message in websocket:
                # Обработка трафика ратки
                pass
        except: pass
    else:
        await websocket.close()

async def main():
    # Запускаем WebSocket на том же порту (некоторые хостинги не дают два порта)
    # Если Render не пускает, придется использовать библиотеку 'aiohttp'
    async with websockets.serve(tunnel_logic, "0.0.0.0", PORT + 1): 
        print(f"WS Tunnel started on {PORT + 1}")
        await asyncio.Future()

if __name__ == "__main__":
    # Запускаем проверку здоровья в отдельном потоке
    threading.Thread(target=run_health_check, daemon=True).start()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
