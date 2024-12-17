class FURGfs2Root:
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
