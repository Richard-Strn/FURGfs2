import os
import struct

class FURGfs2:

    # Inicializando o FURGfs2
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
        # FAT inicia com blocos livres (-1)
        self.fat = [-1] * self.qtdTotalBlocos
        # Diretório raiz
        self.root = {} 
        self.iniciarFURGfs2()

    # Inicia o sistema a partir do tamanho selecionado
    def iniciarFURGfs2(self):
        if not os.path.exists(self.nomeSistemaArquivos):
            with open(self.nomeSistemaArquivos, 'wb') as sistemaArquivos:
                sistemaArquivos.write(b'\x00' * self.tamanhoTotal)
            # Escrevendo o cabeçalho no início do FURGfs2
            self.escreverCabecalho()
            # Gravando a FAT no FURGfs2
            self.salvarFat()
        else:
            os.remove(self.nomeSistemaArquivos)
            with open(self.nomeSistemaArquivos, 'wb') as sistemaArquivos:
                sistemaArquivos.write(b'\x00' * self.tamanhoTotal)
            # Escrevendo o cabeçalho no início do FURGfs2
            self.escreverCabecalho()
            # Gravando a FAT no FURGfs2
            self.salvarFat()

    # Escreve o cabeçalho com os metadados necessários
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

    # Grava a FAT no FURGfs2
    def salvarFat(self):
        with open(self.nomeSistemaArquivos, 'r+b') as sistemaArquivos:
            sistemaArquivos.seek(self.inicioFat)
            dadosFat = struct.pack(f"{self.qtdTotalBlocos}i", *self.fat)
            sistemaArquivos.write(dadosFat)

    # Pega a FAT do FURGfs2 e carrega na memória
    def carregarFat(self):
        with open(self.nomeSistemaArquivos, 'rb') as sistemaArquivos:
            sistemaArquivos.seek(self.inicioFat)
            dadosFat = sistemaArquivos.read(self.qtdTotalBlocos * 4)
            self.fat = list(struct.unpack(f"{self.qtdTotalBlocos}i", dadosFat))

    # Grava o ROOT no FURGfs2
    def salvarRoot(self):
        with open(self.nomeSistemaArquivos, 'r+b') as sistemaArquivos:
            sistemaArquivos.seek(self.inicioRoot)
            dadosRoot = str(self.root).encode().ljust(self.tamanhoBloco, b'\x00')
            sistemaArquivos.write(dadosRoot)

    # Pega o ROOT do FURGfs2 e carrega na memória
    def carregarRoot(self):
        with open(self.nomeSistemaArquivos, 'rb') as sistemaArquivos:
            sistemaArquivos.seek(self.inicioRoot)
            dadosRoot = sistemaArquivos.read(self.tamanhoBloco).decode().strip('\x00')
            self.root = eval(dadosRoot) if dadosRoot else {}

    # Retorna os primeiros blocos disponíveis segundo a FAT
    def acharBlocosDisponiveis(self, blocosNecessarios):
        blocosDisponiveis = [i for i, bloco in enumerate(self.fat) if bloco == -1]
        if len(blocosDisponiveis) >= blocosNecessarios:
            return blocosDisponiveis[:blocosNecessarios]
        return None

    # Verifica se há blocos disponíveis a partir de seu tamanho, escreve os dados e atualiza a FAT e o ROOT
    def copiarArquivoDiscoSistema(self, enderecoArquivoDisco):
        nomeArquivoDisco = os.path.basename(enderecoArquivoDisco)
        if len(nomeArquivoDisco) > self.tamanhoMaximoNomeArquivo:
            raise ValueError(f"O nome do arquivo é maior que o tamanho máximo permitido de {self.tamanhoMaximoNomeArquivo}.")

        with open(enderecoArquivoDisco, 'rb') as sistemaArquivos:
            arquivoDisco = sistemaArquivos.read()
        
        print(len(arquivoDisco))

        blocosNecessarios = (len(arquivoDisco) + self.tamanhoBloco - 1) // self.tamanhoBloco
        print(blocosNecessarios)  
        blocosDisponiveis = self.acharBlocosDisponiveis(blocosNecessarios)

        if not blocosDisponiveis:
            raise Exception("Não há espaço disponível.")

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
        print(f"{nomeArquivoDisco}' copiado para o FURGfs2.")

    # Pega os blocos do arquivo no sistema e escreve no endereço de destino no disco
    def copiarArquivoSistemaDisco(self, nomeArquivoSistema, enderecoDestino):
        self.carregarRoot()
        if nomeArquivoSistema not in self.root:
            raise FileNotFoundError(f"Arquivo '{nomeArquivoSistema}' não encontrado no FURGfs2.")

        dadosArquivoSistema = self.root[nomeArquivoSistema]

        if dadosArquivoSistema["protegido"]:
            raise PermissionError(f"{nomeArquivoSistema}' está protegido e não pode ser renomeado.")

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
            raise NotADirectoryError(f"Não é um endereço válido.")

        enderecoArquivoDisco = os.path.join(enderecoDestino, nomeArquivoSistema)
    
        with open(enderecoArquivoDisco, 'wb') as disco:
            disco.write(data[:tamanho])

        print(f"{nomeArquivoSistema}' copiado para '{enderecoArquivoDisco}'.")

    # Carrega o nome do arquivo no ROOT e atualiza o mesmo
    def renomearArquivo(self, nomeAntigo, nomeNovo):
        self.carregarRoot()

        if nomeAntigo not in self.root:
            raise FileNotFoundError(f"{nomeAntigo}' não existe.")

        dadosArquivoSistema = self.root[nomeAntigo]

        if dadosArquivoSistema["protegido"]:
            raise PermissionError(f"{nomeAntigo}' está protegido e não pode ser renomeado.")

        if len(nomeNovo) > self.tamanhoMaximoNomeArquivo:
            raise ValueError(f"O nome do arquivo é maior que o tamanho máximo permitido de {self.tamanhoMaximoNomeArquivo}.")

        self.root[nomeNovo] = self.root.pop(nomeAntigo)
        self.salvarRoot()
        print(f"{nomeAntigo}' renomeado para '{nomeNovo}'.")

    # Carrega os dados do arquivo no ROOT, atualiza os blocos do arquivo na FAT como livres e tira os dados do arquivo do ROOT 
    def deletarArquivo(self, nomeArquivoSistema):
        self.carregarRoot()
        if nomeArquivoSistema not in self.root:
            raise FileNotFoundError(f"{nomeArquivoSistema}' não existe.")
        
        dadosArquivoSistema = self.root[nomeArquivoSistema]

        if dadosArquivoSistema["protegido"]:
            raise PermissionError(f"{nomeArquivoSistema}' está protegido e não pode ser renomeado.")

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
        print(f"{nomeArquivoSistema}' removido do FURGfs2.")

    # Pega todos os arquivos que existem no ROOT e exibe seus nomes
    def informarArquivosSistema(self):
        self.carregarRoot()
        for nomeArquivoSistema, dadosArquivoSistema in self.root.items():
            status = "protegido" if dadosArquivoSistema["protegido"] else "normal"
            print(f"{nomeArquivoSistema} - {dadosArquivoSistema['tamanho']} bytes - {status}")

    # Verifica os blocos livres e converte para MB
    def informarEspacoDisponivel(self):
        blocosDisponiveis = self.fat.count(-1)
        espacoDisponivel = blocosDisponiveis * self.tamanhoBloco
        espacoTotal = self.qtdTotalBlocos * self.tamanhoBloco
        espacoDisponivelMb = espacoDisponivel / (1024 * 1024)
        espacoTotalMb = espacoTotal / (1024 * 1024)
        print(f"{espacoDisponivelMb:.1f} MB livres de {espacoTotalMb:.1f} MB.")

    # Altera o status do arquivo para protegido ou desprotegido
    def protegerArquivo(self, nomeArquivoSistema, protegido=True):
        self.carregarRoot()
        if nomeArquivoSistema not in self.root:
            raise FileNotFoundError(f"{nomeArquivoSistema}' não existe.")

        self.root[nomeArquivoSistema]["protegido"] = protegido
        self.salvarRoot()
        action = "protegido" if protegido else "desprotegido"
        print(f"Arquivo '{nomeArquivoSistema}' {action} com sucesso.")

def main():
    while True:
        tamanhoTotalMb = int(input("Digite o tamanho do FURGfs2 em MB. (entre 10 e 200MB): "))
        if 10 <= tamanhoTotalMb <= 200:
            break
        print("Digite um tamanho válido. (entre 10 e 200MB).")

    tamanhoTotal = tamanhoTotalMb * 1024 * 1024

    sistemaArquivos = FURGfs2(tamanhoTotal)

    while True:
        print("\nOpções: ")
        print("1. Copiar um arquivo do disco para o FURGfs2.")
        print("2. Copiar um arquivo do FURGfs2 para o disco.")
        print("3. Renomear um arquivo no FURGfs2.")
        print("4. Remover um arquivo do FURGfs2.")
        print("5. Listar arquivos presents no FURGfs2.")
        print("6. Listar espaço livre no FURGfs2.")
        print("7. Proteger ou desproteger um arquivo no FURGfs2.")
        print("8. Sair")

        opcao = input("Escolha uma opção: ")

        if opcao == '1':
            enderecoArquivoDisco = input("Digite o endereço do arquivo no disco: ")
            sistemaArquivos.copiarArquivoDiscoSistema(enderecoArquivoDisco)
        elif opcao == '2':
            nomeArquivoDisco = input("Digite o nome do arquivo presente no FURGfs2: ")
            enderecoDestino = input("Digite o endereço de destino no disco: ")
            sistemaArquivos.copiarArquivoSistemaDisco(nomeArquivoDisco, enderecoDestino)
        elif opcao == '3':
            nomeAntigo = input("Digite o nome atual do arquivo presente no FURGfs2 que deseja renomear: ")
            nomeNovo = input("Digite o novo nome do arquivo: ")
            sistemaArquivos.renomearArquivo(nomeAntigo, nomeNovo)
        elif opcao == '4':
            nomeArquivoSistema = input("Digite o nome do arquivo presente no FURGfs2 que deseja excluir: ")
            sistemaArquivos.deletarArquivo(nomeArquivoSistema)
        elif opcao == '5':
            sistemaArquivos.informarArquivosSistema()
        elif opcao == '6':
            sistemaArquivos.informarEspacoDisponivel()
        elif opcao == '7':
            nomeArquivoSistema = input("Digite o nome do arquivo presente no FURGfs2: ")
            protegido = input("Proteger (s/n)? ").lower() == 's'
            sistemaArquivos.protegerArquivo(nomeArquivoSistema, protegido)
        elif opcao == '8':
            break
        else:
            print("Opção inválida.")

if __name__ == "__main__":
    main()
