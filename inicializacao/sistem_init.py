import os
import struct

class FURGfs2Init:
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