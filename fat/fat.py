import struct

class FURGfs2Fat:
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