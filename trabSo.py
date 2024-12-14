import os
import struct

class FURGfs2:

    def __init__(self, tamanhoTotal):
        self.nomeSistemaArquivos = "FURGSfs2.fs"
        self.tamanhoBloco = 4096
        self.tamanhoMaximoNomeArquivo = 255
        self.tamanhoTotal = tamanhoTotal
        self.qtdTotalBlocos = tamanhoTotal // self.tamanhoBloco
        self.tamanhoHeader = 512
        self.inicioFat = self.tamanhoHeader
        self.tamanhoFat = self.qtdTotalBlocos * 4 
        self.inicioRoot = self.inicioFat + self.tamanhoFat
        self.inicioData = self.inicioRoot + self.tamanhoBloco 
        self.fat = [-1] * self.qtdTotalBlocos
        self.root = {} 
        self.iniciarFURGfs2()

    def iniciarFURGfs2(self):
        if not os.path.exists(self.nomeSistemaArquivos):
            with open(self.nomeSistemaArquivos, 'wb') as sistemaArquivos:
                sistemaArquivos.write(b'\x00' * self.tamanhoTotal)
            self.escreverCabecalho()
            self.salvarFat()

    def escreverCabecalho(self):
        with open(self.nomeSistemaArquivos, 'r+b') as sistemaArquivos:
            dadosCabecalho = struct.pack(
                'I I I I I I',
                self.tamanhoHeader,   
                self.tamanhoBloco,   
                self.tamanhoTotal,   
                self.inicioFat,
                self.inicioRoot, 
                self.inicioData   
            )
            sistemaArquivos.write(dadosCabecalho.ljust(self.tamanhoHeader, b'\x00'))

    def salvarFat(self):
        with open(self.nomeSistemaArquivos, 'r+b') as sistemaArquivos:
            sistemaArquivos.seek(self.inicioFat)
            dadosFat = struct.pack(f"{self.qtdTotalBlocos}i", *self.fat)
            sistemaArquivos.write(dadosFat)

    def carregarFat(self):
        with open(self.nomeSistemaArquivos, 'rb') as sistemaArquivos:
            sistemaArquivos.seek(self.inicioFat)
            dadosFat = sistemaArquivos.read(self.qtdTotalBlocos * 4)
            self.fat = list(struct.unpack(f"{self.qtdTotalBlocos}i", dadosFat))

    def salvarRoot(self):
        with open(self.nomeSistemaArquivos, 'r+b') as sistemaArquivos:
            sistemaArquivos.seek(self.inicioRoot)
            dadosRoot = str(self.root).encode().ljust(self.tamanhoBloco, b'\x00')
            sistemaArquivos.write(dadosRoot)

    def carregarRoot(self):
        with open(self.nomeSistemaArquivos, 'rb') as sistemaArquivos:
            sistemaArquivos.seek(self.inicioRoot)
            dadosRoot = sistemaArquivos.read(self.tamanhoBloco).decode().strip('\x00')
            self.root = eval(dadosRoot) if dadosRoot else {}

    def acharBlocosDisponiveis(self, blocosNecessarios):
        """
        Encontra e retorna uma lista de blocos livres no sistema de arquivos.

        :param blocosNecessarios: Número de blocos necessários.
        :return: Lista de blocos livres ou None se não houver blocos suficientes.
        """
        blocosDisponiveis = [i for i, bloco in enumerate(self.fat) if bloco == -1]
        if len(blocosDisponiveis) >= blocosNecessarios:
            return blocosDisponiveis[:blocosNecessarios]
        return None

    def copiarArquivoDiscoSistema(self, enderecoArquivoDisco):
        """
        Copia um arquivo do disco para o sistema de arquivos.
        
        :param source_path: Caminho do arquivo no disco.
        """
        nomeArquivoDisco = os.path.basename(enderecoArquivoDisco)
        if len(nomeArquivoDisco) > self.tamanhoMaximoNomeArquivo:
            raise ValueError(f"O nome do arquivo excede o tamanho máximo de {self.tamanhoMaximoNomeArquivo} caracteres.")

        with open(enderecoArquivoDisco, 'rb') as sistemaArquivos:
            arquivoDisco = sistemaArquivos.read()
        
        print(len(arquivoDisco))

        blocosNecessarios = (len(arquivoDisco) + self.tamanhoBloco - 1) // self.tamanhoBloco
        print(blocosNecessarios)  
        blocosDisponiveis = self.acharBlocosDisponiveis(blocosNecessarios)

        if not blocosDisponiveis:
            raise Exception(f"Espaço insuficiente no sistema de arquivos para armazenar o arquivo '{nomeArquivoDisco}'.")

        self.carregarFat()
        self.carregarRoot()

        inicioBloco = blocosDisponiveis[0]
        self.root[nomeArquivoDisco] = {
            "inicioBloco": inicioBloco,
            "tamanho": len(arquivoDisco),
            "protegido": False
        }

        with open(self.nomeSistemaArquivos, 'r+b') as sistemaArquivos:
            for i, bloco in enumerate(blocosDisponiveis):
                start = i * self.tamanhoBloco
                end = start + self.tamanhoBloco
                sistemaArquivos.seek(self.inicioData + self.tamanhoBloco * bloco)
                sistemaArquivos.write(arquivoDisco[start:end].ljust(self.tamanhoBloco, b'\x00'))

                self.fat[bloco] = blocosDisponiveis[i + 1] if i + 1 < len(blocosDisponiveis) else -2

        self.salvarFat()
        self.salvarRoot()
        print(f"Arquivo '{nomeArquivoDisco}' copiado para o sistema de arquivos.")

    def copiarArquivoSistemaDisco(self, nomeArquivoSistema, enderecoDestino):
        self.carregarRoot()
        if nomeArquivoSistema not in self.root:
            raise FileNotFoundError(f"Arquivo '{nomeArquivoSistema}' não encontrado no sistema de arquivos.")

        dadosArquivoSistema = self.root[nomeArquivoSistema]
        inicioBloco = dadosArquivoSistema["inicioBloco"]
        tamanho = dadosArquivoSistema["tamanho"]

        data = b''

        self.carregarFat()
        with open(self.nomeSistemaArquivos, 'rb') as sistemaArquivos:
            bloco = inicioBloco
            while bloco != -2:
                sistemaArquivos.seek(self.inicioData + self.tamanhoBloco * bloco)
                data += sistemaArquivos.read(self.tamanhoBloco)
                bloco = self.fat[bloco]  

        if not os.path.isdir(enderecoDestino):
            raise NotADirectoryError(f"O caminho '{enderecoDestino}' não é um diretório válido.")

        enderecoArquivoDisco = os.path.join(enderecoDestino, nomeArquivoSistema)
    
        with open(enderecoArquivoDisco, 'wb') as sistemaArquivos:
            sistemaArquivos.write(data[:tamanho])

        print(f"Arquivo '{nomeArquivoSistema}' copiado para '{enderecoArquivoDisco}'.")


    def renomearArquivo(self, nomeAntigo, nomeNovo):
        self.carregarRoot()
        if nomeAntigo not in self.root:
            raise FileNotFoundError(f"Arquivo '{nomeAntigo}' não encontrado no sistema de arquivos.")

        if len(nomeNovo) > self.tamanhoMaximoNomeArquivo:
            raise ValueError(f"O nome do arquivo excede o tamanho máximo de {self.tamanhoMaximoNomeArquivo} caracteres.")

        self.root[nomeNovo] = self.root.pop(nomeAntigo)
        self.salvarRoot()
        print(f"Arquivo '{nomeAntigo}' renomeado para '{nomeNovo}'.")

    def deletarArquivo(self, nomeArquivoSistema):
        self.carregarRoot()
        if nomeArquivoSistema not in self.root:
            raise FileNotFoundError(f"Arquivo '{nomeArquivoSistema}' não encontrado no sistema de arquivos.")

        dadosArquivoSistema = self.root[nomeArquivoSistema]
        inicioBloco = dadosArquivoSistema["inicioBloco"]

        self.carregarFat()
        bloco = inicioBloco
        while bloco != -2:
            proximoBloco = self.fat[bloco]
            self.fat[bloco] = -1
            bloco = proximoBloco

        del self.root[nomeArquivoSistema]
        self.salvarFat()
        self.salvarRoot()
        print(f"Arquivo '{nomeArquivoSistema}' removido do sistema de arquivos.")

    def informarArquivosSistema(self):
        self.carregarRoot()
        for nomeArquivoSistema, dadosArquivoSistema in self.root.items():
            status = "protegido" if dadosArquivoSistema["protegido"] else "normal"
            print(f"{nomeArquivoSistema} - {dadosArquivoSistema['tamanho']} bytes - {status}")

    def informarEspacoDisponivel(self):
        blocosDisponiveis = self.fat.count(-1)
        espacoDisponivel = blocosDisponiveis * self.tamanhoBloco
        espacoTotal = self.qtdTotalBlocos * self.tamanhoBloco
        espacoDisponivelMb = espacoDisponivel / (1024 * 1024)
        espacoTotalMb = espacoTotal / (1024 * 1024)
        print(f"{espacoDisponivelMb:.1f} MB livres de {espacoTotalMb:.1f} MB.")


    def protegerArquivo(self, nomeArquivoSistema, protegido=True):
        self.carregarRoot()
        if nomeArquivoSistema not in self.root:
            raise FileNotFoundError(f"Arquivo '{nomeArquivoSistema}' não encontrado no sistema de arquivos.")

        self.root[nomeArquivoSistema]["protegido"] = protegido
        self.salvarRoot()
        action = "protegido" if protegido else "desprotegido"
        print(f"Arquivo '{nomeArquivoSistema}' {action} com sucesso.")

def main():
    while True:
        tamanhoTotalMb = int(input("Digite o tamanho do sistema de arquivos em MB (entre 10 e 200): "))
        if 10 <= tamanhoTotalMb <= 200:
            break
        print("Por favor, insira um valor válido entre 10 e 200 MB.")

    tamanhoTotal = tamanhoTotalMb * 1024 * 1024  # Converter MB para bytes

    sistemaArquivos = FURGfs2(tamanhoTotal)

    while True:
        print("\nOpções:")
        print("1. Copiar um arquivo do disco para o sistema de arquivos")
        print("2. Copiar um arquivo do sistema de arquivos para o disco")
        print("3. Renomear um arquivo no sistema de arquivos")
        print("4. Remover um arquivo do sistema de arquivos")
        print("5. Listar arquivos no sistema de arquivos")
        print("6. Listar espaço livre no sistema de arquivos")
        print("7. Proteger ou desproteger um arquivo")
        print("8. Sair")

        opcao = input("Escolha uma opção: ")

        if opcao == '1':
            enderecoArquivoDisco = input("Digite o caminho do arquivo no disco: ")
            sistemaArquivos.copiarArquivoDiscoSistema(enderecoArquivoDisco)
        elif opcao == '2':
            nomeArquivoDisco = input("Digite o nome do arquivo no sistema de arquivos: ")
            enderecoDestino = input("Digite o caminho de destino no disco: ")
            sistemaArquivos.copiarArquivoSistemaDisco(nomeArquivoDisco, enderecoDestino)
        elif opcao == '3':
            nomeAntigo = input("Digite o nome atual do arquivo: ")
            nomeNovo = input("Digite o novo nome do arquivo: ")
            sistemaArquivos.renomearArquivo(nomeAntigo, nomeNovo)
        elif opcao == '4':
            nomeArquivoSistema = input("Digite o nome do arquivo a ser removido: ")
            sistemaArquivos.deletarArquivo(nomeArquivoSistema)
        elif opcao == '5':
            sistemaArquivos.informarArquivosSistema()
        elif opcao == '6':
            sistemaArquivos.informarEspacoDisponivel()
        elif opcao == '7':
            nomeArquivoSistema = input("Digite o nome do arquivo: ")
            protegido = input("Proteger (s/n)? ").lower() == 's'
            sistemaArquivos.protegerArquivo(nomeArquivoSistema, protegido)
        elif opcao == '8':
            break
        else:
            print("Opção inválida.")

if __name__ == "__main__":
    main()
