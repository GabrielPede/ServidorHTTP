import socket
import os
import threading
import urllib.parse


# Função para criar uma resposta HTTP com base nos parâmetros fornecidos
def criar_resposta_http(codigo_status, tipo_conteudo, conteudo):
    tamanho_conteudo = len(conteudo)
    
    resposta = "HTTP/1.1 {}\r\n".format(codigo_status)
    resposta += "Content-Type: {}\r\n".format(tipo_conteudo)
    resposta += "Content-Length: {}\r\n".format(tamanho_conteudo)
    resposta += "Connection: close\r\n"
    resposta += "\r\n"
    resposta = resposta.encode("utf-8") + conteudo
    return resposta

# Função para lidar com uma requisição HTTP recebida
def lidar_com_requisicao(socket_cliente, diretorio):
    # Recebe a requisição
    requisicao = socket_cliente.recv(1024).decode("utf-8").strip()
    partes_requisicao = requisicao.split(" ")
    metodo = partes_requisicao[0]
    caminho_arquivo = os.path.join(diretorio, urllib.parse.unquote(partes_requisicao[1][1:]))
    
    if metodo == "GET":
        if partes_requisicao[1] == "/HEADER":
            # Se a requisição for "/HEADER", retorna a própria requisição
            resposta = criar_resposta_http("200 OK", "text/plain", requisicao.encode("utf-8"))
        elif os.path.isfile(caminho_arquivo):
            # Se o caminho especificado for um arquivo válido, lê o arquivo e envia seu conteúdo em partes
            with open(caminho_arquivo, "rb") as arquivo:
                buffer_size = 1024
                conteudo = arquivo.read(buffer_size)
                while conteudo:
                    resposta = criar_resposta_http("200 OK", "application/octet-stream", conteudo)
                    socket_cliente.sendall(resposta)
                    conteudo = arquivo.read(buffer_size)
            return
        elif os.path.isdir(caminho_arquivo):
            # Se o caminho especificado for um diretório, lista os arquivos e cria links HTML para cada um deles
            lista_arquivos = os.listdir(caminho_arquivo)
            
            conteudo = ""
            for nome_arquivo in lista_arquivos:
                link_arquivo = '<a href="{}">{}</a><br>'.format(os.path.join(partes_requisicao[1], nome_arquivo), nome_arquivo)
                conteudo += link_arquivo
            resposta = criar_resposta_http("200 OK", "text/html", conteudo.encode("utf-8"))
        else:
            # Se o arquivo não for encontrado, retorna uma resposta 404
            resposta = criar_resposta_http("404 Not Found", "text/plain", "Arquivo não encontrado".encode("utf-8"))
    else:
        # Se o método da requisição não for suportado, retorna uma resposta 405
        resposta = criar_resposta_http("405 Method Not Allowed", "text/plain", "Método não permitido".encode("utf-8"))
    
    # Envia a resposta ao cliente
    socket_cliente.sendall(resposta)
    socket_cliente.close()

# Função para obter o endereço IP local da máquina
def obter_ip_local():
    return socket.gethostbyname(socket.gethostname())

# Função para executar o servidor
def executar_servidor(porta, diretorio):
    socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socket_servidor.bind((obter_ip_local(), porta))
    socket_servidor.listen()

    print("Servidor rodando em", obter_ip_local() + ":" + str(porta))

    while True:
        socket_cliente, endereco = socket_servidor.accept()
        print("Cliente conectado:", endereco)

        # Cria uma nova thread para lidar com a requisição do cliente
        thread = threading.Thread(target=lidar_com_requisicao, args=(socket_cliente, diretorio))
        thread.start()

if __name__ == "__main__":
    porta = 8000
    diretorio = "/Users/Gabriel/Desktop/teste1"  # Coloque o diretório desejado aqui
    executar_servidor(porta, diretorio)
