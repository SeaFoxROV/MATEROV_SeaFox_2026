import socket

UDP_IP   = "0.0.0.0"  # escucha en todas las interfaces
UDP_PORT = 8889       # el mismo que UDP_SEND_PORT en el ESP32

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"Escuchando en puerto {UDP_PORT}...")

while True:
    data, addr = sock.recvfrom(256)
    print(f"{data.decode()}")