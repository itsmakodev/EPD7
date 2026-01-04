import socket
import argparse


def leer_fichero(nombre):
    try:
        with open(nombre, "rb") as f:
            return True, f.read()
    except Exception:
        return False, b""


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1")
    parser.add_argument("--puerto", type=int, default=5005)
    parser.add_argument("comando", nargs="+")
    args = parser.parse_args()

    comando = " ".join(args.comando)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((args.ip, args.puerto))

    s.sendall(comando.encode("ascii"))

    orden = args.comando[0].upper()

    if orden == "DOWNLOAD_FILE":
        resp = s.recv(1024).decode("ascii")
        if resp == "ERROR":
            print("Error descargando")
        else:
            size = int(resp)
            s.sendall(b"ACK")
            data = b''
            while len(data) < size:
                data += s.recv(4096)
            with open(args.comando[1], "wb") as f:
                f.write(data)
            print("Descarga correcta")

    elif orden == "UPLOAD_FILE":
        if s.recv(1024).decode("ascii") != "UPLOAD_ACK":
            print("Error")
        else:
            ok, contenido = leer_fichero(args.comando[1])
            if not ok:
                print("No existe el fichero")
            else:
                s.sendall(str(len(contenido)).encode("ascii"))
                s.recv(1024)
                s.sendall(contenido)
                print(s.recv(1024).decode("ascii"))

    else:
        print(s.recv(4096).decode("ascii"))

    s.close()
