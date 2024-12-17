class FURGfs2Utils:
     # Retorna os primeiros blocos disponíveis segundo a FAT
    def acharBlocosDisponiveis(self, blocosNecessarios):
        blocosDisponiveis = [i for i, bloco in enumerate(self.fat) if bloco == -1]
        if len(blocosDisponiveis) >= blocosNecessarios:
            return blocosDisponiveis[:blocosNecessarios]
        return None


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
