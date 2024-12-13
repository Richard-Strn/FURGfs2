import os

class Cabecalho:
    def __init__(self, tamanho_total: int, espaco_livre: int, tamanho_bloco: int, 
                 inicio_cabecalho: int, inicio_raiz: int, inicio_fat: int, inicio_dados: int):
        self.tamanho_total = tamanho_total
        self.espaco_livre = espaco_livre
        self.tamanho_bloco = tamanho_bloco
        self.inicio_cabecalho = inicio_cabecalho
        self.inicio_raiz = inicio_raiz
        self.inicio_fat = inicio_fat
        self.inicio_dados = inicio_dados

    def __repr__(self):
        return (f"Cabecalho(tamanho_total={self.tamanho_total}, espaco_livre={self.espaco_livre}, "
                f"tamanho_bloco={self.tamanho_bloco}, inicio_cabecalho={self.inicio_cabecalho}, "
                f"inicio_raiz={self.inicio_raiz}, inicio_fat={self.inicio_fat}, inicio_dados={self.inicio_dados})")


class EntradaArquivo:
    def __init__(self, nome: str, caminho: str, primeiro_bloco: int, protegido: bool, e_diretorio: bool):
        self.nome = nome
        self.caminho = caminho
        self.primeiro_bloco = primeiro_bloco
        self.protegido = protegido
        self.e_diretorio = e_diretorio

    def __repr__(self):
        tipo_entrada = "Diretorio" if self.e_diretorio else "Arquivo"
        return (f"{tipo_entrada}(nome='{self.nome}', caminho='{self.caminho}', primeiro_bloco={self.primeiro_bloco}, "
                f"protegido={self.protegido})")


class EntradaFat:
    def __init__(self, id_bloco: int, id_proximo_bloco: int, usado: bool):
        self.id_bloco = id_bloco
        self.id_proximo_bloco = id_proximo_bloco
        self.usado = usado

    def __repr__(self):
        return (f"EntradaFat(id_bloco={self.id_bloco}, id_proximo_bloco={self.id_proximo_bloco}, "
                f"usado={self.usado})")


class SistemaArquivos:
    def __init__(self, tamanho_total: int, tamanho_bloco: int):
        self.cabecalho = Cabecalho(
            tamanho_total=tamanho_total,
            espaco_livre=tamanho_total,
            tamanho_bloco=tamanho_bloco,
            inicio_cabecalho=0,
            inicio_raiz=1,
            inicio_fat=2,
            inicio_dados=3
        )
        self.entradas_fat = [EntradaFat(id_bloco=i, id_proximo_bloco=None, usado=False) for i in range(tamanho_total // tamanho_bloco)]
        self.entradas_arquivo = []

    def adicionar_arquivo(self, nome: str, caminho: str, tamanho: int, protegido: bool, e_diretorio: bool):
        num_blocos = -(-tamanho // self.cabecalho.tamanho_bloco)  # Divisao para cima
        blocos_alocados = []

        for _ in range(num_blocos):
            bloco_livre = self._encontrar_bloco_livre()
            if bloco_livre is None:
                raise ValueError("Espaco insuficiente para adicionar o arquivo.")

            self.entradas_fat[bloco_livre].usado = True
            if blocos_alocados:
                self.entradas_fat[blocos_alocados[-1]].id_proximo_bloco = bloco_livre
            blocos_alocados.append(bloco_livre)

        self.cabecalho.espaco_livre -= num_blocos * self.cabecalho.tamanho_bloco

        self.entradas_arquivo.append(
            EntradaArquivo(nome=nome, caminho=caminho, primeiro_bloco=blocos_alocados[0], protegido=protegido, e_diretorio=e_diretorio)
        )

    def copiar_para_sistema(self, caminho_origem: str, caminho_destino: str):
        if not os.path.exists(caminho_origem):
            raise FileNotFoundError("O arquivo de origem nao existe.")

        tamanho = os.path.getsize(caminho_origem)
        nome = os.path.basename(caminho_destino)
        protegido = False
        e_diretorio = False

        with open(caminho_origem, "rb") as f:
            conteudo = f.read()

        self.adicionar_arquivo(nome, caminho_destino, tamanho, protegido, e_diretorio)

    def copiar_para_disco(self, nome_arquivo: str, caminho_destino: str):
        entrada = next((e for e in self.entradas_arquivo if e.nome == nome_arquivo), None)
        if entrada is None:
            raise FileNotFoundError("Arquivo não encontrado no sistema de arquivos.")
        
        # Aqui você pode obter o conteúdo real do arquivo
        conteudo = "Conteúdo com caracteres não ASCII"


        with open(caminho_destino, "wb") as f:
            f.write(conteudo)

    def renomear_arquivo(self, nome_atual: str, novo_nome: str):
        entrada = next((e for e in self.entradas_arquivo if e.nome == nome_atual), None)
        if entrada is None:
            raise FileNotFoundError("Arquivo nao encontrado.")
        entrada.nome = novo_nome

    def remover_arquivo(self, nome_arquivo: str):
        entrada = next((e for e in self.entradas_arquivo if e.nome == nome_arquivo), None)
        if entrada is None:
            raise FileNotFoundError("Arquivo nao encontrado.")

        self.entradas_arquivo.remove(entrada)
        bloco = entrada.primeiro_bloco
        while bloco is not None:
            self.entradas_fat[bloco].usado = False
            bloco = self.entradas_fat[bloco].id_proximo_bloco

    def listar_espaco_livre(self):
        print(f"Espaco livre: {self.cabecalho.espaco_livre} bytes")

    def proteger_arquivo(self, nome_arquivo: str, proteger: bool):
        entrada = next((e for e in self.entradas_arquivo if e.nome == nome_arquivo), None)
        if entrada is None:
            raise FileNotFoundError("Arquivo nao encontrado.")
        entrada.protegido = proteger

    def _encontrar_bloco_livre(self):
        for i, entrada in enumerate(self.entradas_fat):
            if not entrada.usado:
                return i
        return None

    def listar_arquivos(self):
        if not self.entradas_arquivo:
            print("Nenhum arquivo ou diretorio encontrado.")
        else:
            for arquivo in self.entradas_arquivo:
                print(arquivo)

    def __repr__(self):
        return (f"SistemaArquivos(Cabecalho={self.cabecalho}, "
                f"EntradasFat={self.entradas_fat}, EntradasArquivo={self.entradas_arquivo})")


def converter_para_bytes(tamanho: int, unidade: str) -> int:
    unidades = {"b": 1, "kb": 1024, "mb": 1024**2, "gb": 1024**3}
    unidade = unidade.lower()
    if unidade not in unidades:
        raise ValueError("Unidade invalida. Use 'B', 'KB', 'MB' ou 'GB'.")
    return tamanho * unidades[unidade]


def principal():
    sistema = None

    while True:
        print("\n=== Menu do Sistema de Arquivos ===")
        print("1. Criar Sistema de Arquivos")
        print("2. Adicionar Arquivo/Diretorio")
        print("3. Listar Arquivos")
        print("4. Mostrar Informacoes do Sistema de Arquivos")
        print("5. Copiar Arquivo do Disco para o Sistema de Arquivos")
        print("6. Copiar Arquivo do Sistema de Arquivos para o Disco")
        print("7. Renomear Arquivo")
        print("8. Remover Arquivo")
        print("9. Listar Espaco Livre")
        print("10. Proteger/Desproteger Arquivo")
        print("0. Sair")
        
        escolha = input("Digite sua escolha: ")

        if escolha == "1":
            tamanho_total = int(input("Digite o tamanho total do sistema de arquivos: "))
            unidade_total = input("Digite a unidade (B, KB, MB, GB): ")
            tamanho_bloco = int(input("Digite o tamanho do bloco: "))
            unidade_bloco = input("Digite a unidade (B, KB, MB, GB): ")

            tamanho_total_bytes = converter_para_bytes(tamanho_total, unidade_total)
            tamanho_bloco_bytes = converter_para_bytes(tamanho_bloco, unidade_bloco)

            sistema = SistemaArquivos(tamanho_total=tamanho_total_bytes, tamanho_bloco=tamanho_bloco_bytes)
            print("Sistema de arquivos criado com sucesso.")

        elif escolha == "2":
            if sistema is None:
                print("Crie um sistema de arquivos primeiro.")
                continue

            nome = input("Digite o nome do arquivo/diretorio: ")
            caminho = input("Digite o caminho: ")
            tamanho = int(input("Digite o tamanho: "))
            unidade_tamanho = input("Digite a unidade (B, KB, MB, GB): ")
            tamanho_bytes = converter_para_bytes(tamanho, unidade_tamanho)

            protegido = input("O arquivo e protegido? (sim/nao): ").lower() == "sim"
            e_diretorio = input("E um diretorio? (sim/nao): ").lower() == "sim"

            try:
                sistema.adicionar_arquivo(nome, caminho, tamanho_bytes, protegido, e_diretorio)
                print("Arquivo/Diretorio adicionado com sucesso.")
            except ValueError as e:
                print(f"Erro: {e}")

        elif escolha == "3":
            if sistema is None:
                print("Crie um sistema de arquivos primeiro.")
                continue

            print("\nArquivos/Diretorios:")
            sistema.listar_arquivos()

        elif escolha == "4":
            if sistema is None:
                print("Crie um sistema de arquivos primeiro.")
                continue

            print("\nInformacoes do Sistema de Arquivos:")
            print(sistema)

        elif escolha == "5":
            if sistema is None:
                print("Crie um sistema de arquivos primeiro.")
                continue

            caminho_origem = input("Digite o caminho do arquivo no disco: ")
            caminho_destino = input("Digite o caminho no sistema de arquivos: ")

            try:
                sistema.copiar_para_sistema(caminho_origem, caminho_destino)
                print("Arquivo copiado para o sistema de arquivos com sucesso.")
            except Exception as e:
                print(f"Erro: {e}")

        elif escolha == "6":
            if sistema is None:
                print("Crie um sistema de arquivos primeiro.")
                continue

            nome_arquivo = input("Digite o nome do arquivo no sistema de arquivos: ")
            caminho_destino = input("Digite o caminho no disco: ")

            try:
                sistema.copiar_para_disco(nome_arquivo, caminho_destino)
                print("Arquivo copiado para o disco com sucesso.")
            except Exception as e:
                print(f"Erro: {e}")

        elif escolha == "7":
            if sistema is None:
                print("Crie um sistema de arquivos primeiro.")
                continue

            nome_atual = input("Digite o nome atual do arquivo: ")
            novo_nome = input("Digite o novo nome do arquivo: ")

            try:
                sistema.renomear_arquivo(nome_atual, novo_nome)
                print("Arquivo renomeado com sucesso.")
            except Exception as e:
                print(f"Erro: {e}")

        elif escolha == "8":
            if sistema is None:
                print("Crie um sistema de arquivos primeiro.")
                continue

            nome_arquivo = input("Digite o nome do arquivo a ser removido: ")

            try:
                sistema.remover_arquivo(nome_arquivo)
                print("Arquivo removido com sucesso.")
            except Exception as e:
                print(f"Erro: {e}")

        elif escolha == "9":
            if sistema is None:
                print("Crie um sistema de arquivos primeiro.")
                continue

            sistema.listar_espaco_livre()

        elif escolha == "10":
            if sistema is None:
                print("Crie um sistema de arquivos primeiro.")
                continue

            nome_arquivo = input("Digite o nome do arquivo: ")
            proteger = input("Deseja proteger o arquivo? (sim/nao): ").lower() == "sim"

            try:
                sistema.proteger_arquivo(nome_arquivo, proteger)
                print("Arquivo atualizado com sucesso.")
            except Exception as e:
                print(f"Erro: {e}")

        elif escolha == "0":
            print("Saindo...")
            break

        else:
            print("Escolha invalida. Tente novamente.")


if __name__ == "__main__":
    principal()
