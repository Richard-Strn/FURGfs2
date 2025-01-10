import os

class FURGfs2FileOperations:
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
            raise FileNotFoundError(f"{nomeArquivoSistema} não existe.")

        dadosArquivoSistema = self.root[nomeArquivoSistema]

        # Verifica se o arquivo está protegido
        if dadosArquivoSistema["protegido"]:
            print(f"Arquivo '{nomeArquivoSistema}' está protegido e **não pode ser removido**.")
            return

        inicioBloco = dadosArquivoSistema["inicioBloco"]

        self.carregarFat()
        bloco = inicioBloco
        while bloco != -2:
            proximoBloco = self.fat[bloco]
            self.fat[bloco] = -1  # Marca o bloco como livre
            bloco = proximoBloco

        # Remove o arquivo do Root
        del self.root[nomeArquivoSistema]
        self.salvarFat()
        self.salvarRoot()
        print(f"Arquivo '{nomeArquivoSistema}' foi removido do FURGfs2.")
    
    # Pega todos os arquivos que existem no ROOT e exibe seus nomes
    def informarArquivosSistema(self):
        self.carregarRoot()
        for nomeArquivoSistema, dadosArquivoSistema in self.root.items():
            status = "protegido" if dadosArquivoSistema["protegido"] else "normal"
            print(f"{nomeArquivoSistema} - {dadosArquivoSistema['tamanho']} bytes - {status}")