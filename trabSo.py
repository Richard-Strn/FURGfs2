from inicializacao.sistem_init import FURGfs2Init
from fat.fat import FURGfs2Fat
from root.root import FURGfs2Root
from operations.operations import FURGfs2FileOperations
from utils.utils import FURGfs2Utils

class FURGfs2(FURGfs2Init, FURGfs2Fat, FURGfs2Root, FURGfs2FileOperations, FURGfs2Utils):
    pass

def main():
    # Lógica do menu interativo para o sistema de arquivos
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
