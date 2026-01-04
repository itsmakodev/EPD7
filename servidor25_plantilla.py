import socket
import argparse
import os
import shutil

USERS_FILE = "usuarios.txt"

# ======================
# UTILIDADES
# ======================


def obtener_usuarios():
    usuarios = []
    if not os.path.exists(USERS_FILE):
        return usuarios

    with open(USERS_FILE, "r") as f:
        for linea in f:
            if linea.strip():
                u, p = linea.strip().split(",")
                usuarios.append({"usuario": u, "contrasenia": p})
    return usuarios


def guardar_usuario(usuario, contrasenia):
    with open(USERS_FILE, "a") as f:
        f.write(f"{usuario},{contrasenia}\n")

# ======================
# COMANDOS
# ======================


def listar_ficheros(ruta):
    return "\n".join(os.listdir(ruta))


def borrar_fichero(ruta, nombre):
    try:
        os.remove(os.path.join(ruta, nombre))
        return "DELETED"
    except Exception:
        return "ERROR"


def descargar_fichero(conn, ruta, nombre):
    path = os.path.join(ruta, nombre)
    if not os.path.exists(path):
        conn.sendall(b"ERROR")
        return

    size = os.path.getsize(path)
    conn.sendall(str(size).encode("ascii"))

    if conn.recv(1024).decode("ascii") != "ACK":
        return

    with open(path, "rb") as f:
        conn.sendall(f.read())


def subir_fichero(conn, ruta, nombre):
    conn.sendall(b"UPLOAD_ACK")

    size = int(conn.recv(1024).decode("ascii"))
    conn.sendall(b"UPLOAD_ACK")

    data = b''
    while len(data) < size:
        data += conn.recv(4096)

    path = os.path.join(ruta, nombre)
    base = path
    i = 1
    while os.path.exists(path):
        path = f"{base}_copia{i}"
        i += 1

    with open(path, "wb") as f:
        f.write(data)

    conn.sendall(b"SUCCESS")


def renombrar_fichero(ruta, orig, nuevo):
    o = os.path.join(ruta, orig)
    n = os.path.join(ruta, nuevo)
    if not os.path.exists(o) or os.path.exists(n):
        return "RENAME_ERROR"
    os.rename(o, n)
    return "RENAMED"


def iniciar_sesion(usuario, contrasenia):
    for u in obtener_usuarios():
        if u["usuario"] == usuario and u["contrasenia"] == contrasenia:
            ruta = f"./{usuario}"
            os.makedirs(ruta, exist_ok=True)
            return True, ruta
    return False, ""


def registrar_usuario(usuario, contrasenia, confirmacion):
    if contrasenia != confirmacion:
        return "ERROR"
    for u in obtener_usuarios():
        if u["usuario"] == usuario:
            return "ERROR"
    guardar_usuario(usuario, contrasenia)
    os.makedirs(usuario, exist_ok=True)
    return "SUCCESS"


def compartir_fichero(ruta, fichero, usuario):
    destino = f"./{usuario}/{fichero}"
    origen = os.path.join(ruta, fichero)

    if not os.path.exists(origen):
        return "ERROR"
    if not os.path.exists(f"./{usuario}"):
        return "ERROR"

    shutil.copy(origen, destino)
    return "SUCCESS"

# ======================
# SERVIDOR
# ======================


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="0.0.0.0")
    parser.add_argument("--puerto", type=int, default=5005)
    args = parser.parse_args()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((args.ip, args.puerto))
    s.listen(1)

    print("Servidor esperando conexiones...")
    shutdown = False

    while not shutdown:
        conn, addr = s.accept()
        print("Cliente conectado:", addr)

        ruta_usuario = ""
        sesion = False

        try:
            while True:
                data = conn.recv(4096)
                if not data:
                    break

                partes = data.decode("ascii").split()
                orden = partes[0].upper()

                # ---------- SIN SESIÓN ----------
                if not sesion and orden not in ("LOGIN", "SING_IN", "SHUTDOWN"):
                    conn.sendall(b"ERROR: LOGIN_REQUIRED")
                    continue

                if orden == "LOGIN":
                    ok, ruta = iniciar_sesion(partes[1], partes[2])
                    if ok:
                        sesion = True
                        ruta_usuario = ruta
                        conn.sendall(b"SUCCESS")
                    else:
                        conn.sendall(b"ERROR")

                elif orden == "SING_IN":
                    resp = registrar_usuario(partes[1], partes[2], partes[3])
                    conn.sendall(resp.encode("ascii"))

                elif orden == "LIST_FILES":
                    conn.sendall(listar_ficheros(ruta_usuario).encode("ascii"))

                elif orden == "DOWNLOAD_FILE":
                    descargar_fichero(conn, ruta_usuario, partes[1])

                elif orden == "UPLOAD_FILE":
                    subir_fichero(conn, ruta_usuario, partes[1])

                elif orden == "DELETE_FILE":
                    resp = borrar_fichero(ruta_usuario, partes[1])
                    conn.sendall(resp.encode("ascii"))

                elif orden == "RENAME_FILE":
                    resp = renombrar_fichero(ruta_usuario, partes[1], partes[2])
                    conn.sendall(resp.encode("ascii"))

                elif orden == "SHARE":
                    resp = compartir_fichero(ruta_usuario, partes[1], partes[2])
                    conn.sendall(resp.encode("ascii"))

                elif orden == "SHUTDOWN":
                    shutdown = True
                    conn.sendall(b"Servidor apagado")
                    break

                else:
                    conn.sendall(b"UNKNOWN_COMMAND")

        except ConnectionResetError:
            print("Cliente desconectado")

        conn.close()

    s.close()
    print("Servidor cerrado")
