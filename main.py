import socket
import threading
import sys

def get_local_ip():
    """
    Tries to determine the local IP address of the machine.
    This is the IP the other user needs to connect to if you are hosting.
    """
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        if s:
            s.close()
    return ip


def receive_messages(sock):
    """
    This function runs in a separate thread and continuously listens for
    incoming messages from the peer.
    """
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                print("\n[+] Peer has disconnected. Press ENTER to exit.")
                break
            
            print(f"\rPeer: {data.decode('utf-8')}\nYou: ", end="")

        except ConnectionResetError:
            print("\n[!] Connection was forcibly closed by the peer. Press ENTER to exit.")
            break
        except Exception as e:
            print(f"\n[!] An error occurred in receiving: {e}. Press ENTER to exit.")
            break
    
    sock.close()
    sys.exit()


def send_messages(sock):
    while True:
        try:
            message = input("You: ")
            
            if message.lower() == 'exit':
                print("[+] You have chosen to disconnect.")
                break

            sock.sendall(message.encode('utf-8'))

        except (EOFError, KeyboardInterrupt):
            print("\n[+] Disconnecting...")
            break
        except Exception as e:
            print(f"\n[!] An error occurred in sending: {e}")
            break

    sock.close()


def main():
    """
    Main function to set up the P2P connection.
    """
    PORT = 65432  # Port to listen on (non-privileged ports are > 1023)

    while True:
        choice = input("Do you want to (1) Host a chat or (2) Connect to a chat? [1/2]: ")
        if choice in ['1', '2']:
            break
        print("Invalid choice. Please enter 1 or 2.")

    # --- Host Logic ---
    if choice == '1':
        host_ip = get_local_ip()
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # This allows reusing the address, helpful for quick restarts
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        server_socket.bind((host_ip, PORT))
        server_socket.listen()
        
        print(f"[+] Hosting on IP: {host_ip}")
        print(f"[+] Listening on port: {PORT}")
        print("[+] Waiting for a connection...")
        
        try:
            # accept() blocks and waits for an incoming connection.
            # When a client connects, it returns a new socket object representing
            # the connection and a tuple holding the address of the client.
            peer_socket, addr = server_socket.accept()
            print(f"[+] Connected by {addr}")
        except KeyboardInterrupt:
            print("\n[+] Host setup cancelled. Exiting.")
            server_socket.close()
            sys.exit()
        finally:
            # The server socket is no longer needed after a connection is made
            server_socket.close()

    # --- Client Logic ---
    else: # choice == '2'
        target_ip = input("Enter the host's IP address: ")
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        print(f"[+] Connecting to {target_ip}:{PORT}...")
        try:
            peer_socket.connect((target_ip, PORT))
            print("[+] Connection successful!")
        except ConnectionRefusedError:
            print("[!] Connection refused. Is the host running and did you enter the correct IP?")
            sys.exit()
        except socket.gaierror:
            print("[!] Hostname could not be resolved. Invalid IP address.")
            sys.exit()
        except Exception as e:
            print(f"[!] An error occurred: {e}")
            sys.exit()

    print("\n--- Chat Started ---")
    print("Type 'exit' or press Ctrl+C to disconnect.\n")
    
    receiver = threading.Thread(target=receive_messages, args=(peer_socket,), daemon=True)
    receiver.start()

    
    send_messages(peer_socket)
    
    print("[+] Chat session ended.")


if __name__ == "__main__":
    main()
