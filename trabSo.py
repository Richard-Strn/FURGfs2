import os
import struct

class SimpleFATFileSystem:
    BLOCK_SIZE = 4096
    MAX_FILE_NAME_LENGTH = 255 

    def __init__(self, file_name, total_size):
        self.file_name = file_name
        self.total_size = total_size
        self.total_blocks = total_size // self.BLOCK_SIZE
        self.header_size = 512
        self.fat_start = self.header_size
        self.fat_size = self.total_blocks * 4 
        self.root_dir_start = self.fat_start + self.fat_size
        self.data_start = self.root_dir_start + self.BLOCK_SIZE 
        self.fat = [-1] * self.total_blocks
        self.root_dir = {} 
        self.init_file()

    def init_file(self):
        if not os.path.exists(self.file_name):
            with open(self.file_name, 'wb') as f:
                f.write(b'\x00' * self.total_size)
            self.write_header()
            self.save_fat()

    def write_header(self):
        with open(self.file_name, 'r+b') as f:
            header_data = struct.pack(
                'I I I I I I',
                self.header_size,   
                self.BLOCK_SIZE,   
                self.total_size,   
                self.fat_start,
                self.root_dir_start, 
                self.data_start   
            )
            f.write(header_data.ljust(self.header_size, b'\x00'))

    def save_fat(self):
        with open(self.file_name, 'r+b') as f:
            f.seek(self.fat_start)
            fat_data = struct.pack(f"{self.total_blocks}i", *self.fat)
            f.write(fat_data)

    def load_fat(self):
        with open(self.file_name, 'rb') as f:
            f.seek(self.fat_start)
            fat_data = f.read(self.total_blocks * 4)
            self.fat = list(struct.unpack(f"{self.total_blocks}i", fat_data))

    def save_root_dir(self):
        with open(self.file_name, 'r+b') as f:
            f.seek(self.root_dir_start)
            root_data = str(self.root_dir).encode().ljust(self.BLOCK_SIZE, b'\x00')
            f.write(root_data)

    def load_root_dir(self):
        with open(self.file_name, 'rb') as f:
            f.seek(self.root_dir_start)
            root_data = f.read(self.BLOCK_SIZE).decode().strip('\x00')
            self.root_dir = eval(root_data) if root_data else {}

    def find_free_blocks(self, num_blocks):
        """
        Encontra e retorna uma lista de blocos livres no sistema de arquivos.

        :param num_blocks: Número de blocos necessários.
        :return: Lista de blocos livres ou None se não houver blocos suficientes.
        """
        free_blocks = [i for i, block in enumerate(self.fat) if block == -1]
        if len(free_blocks) >= num_blocks:
            return free_blocks[:num_blocks]
        return None

    def copy_to_fs(self, source_path):
        """
        Copia um arquivo do disco para o sistema de arquivos.
        
        :param source_path: Caminho do arquivo no disco.
        """
        file_name = os.path.basename(source_path)
        if len(file_name) > self.MAX_FILE_NAME_LENGTH:
            raise ValueError(f"O nome do arquivo excede o tamanho máximo de {self.MAX_FILE_NAME_LENGTH} caracteres.")

        with open(source_path, 'rb') as f:
            data = f.read()
        
        print(len(data))

        num_blocks = (len(data) + self.BLOCK_SIZE - 1) // self.BLOCK_SIZE
        print(num_blocks)  
        free_blocks = self.find_free_blocks(num_blocks)

        if not free_blocks:
            raise Exception(f"Espaço insuficiente no sistema de arquivos para armazenar o arquivo '{file_name}'.")

        self.load_fat()
        self.load_root_dir()

        start_block = free_blocks[0]
        self.root_dir[file_name] = {
            "start_block": start_block,
            "size": len(data),
            "protected": False
        }

        with open(self.file_name, 'r+b') as f:
            for i, block in enumerate(free_blocks):
                start = i * self.BLOCK_SIZE
                end = start + self.BLOCK_SIZE
                f.seek(self.data_start + self.BLOCK_SIZE * block)
                f.write(data[start:end].ljust(self.BLOCK_SIZE, b'\x00'))

                self.fat[block] = free_blocks[i + 1] if i + 1 < len(free_blocks) else -2

        self.save_fat()
        self.save_root_dir()
        print(f"Arquivo '{file_name}' copiado para o sistema de arquivos.")

    def copy_from_fs(self, file_name, dest_path):
        self.load_root_dir()
        if file_name not in self.root_dir:
            raise FileNotFoundError(f"Arquivo '{file_name}' não encontrado no sistema de arquivos.")

        file_info = self.root_dir[file_name]
        start_block = file_info["start_block"]
        size = file_info["size"]

        data = b''

        self.load_fat()
        with open(self.file_name, 'rb') as f:
            block = start_block
            while block != -2:
                f.seek(self.data_start + self.BLOCK_SIZE * block)
                data += f.read(self.BLOCK_SIZE)
                block = self.fat[block]  

        if not os.path.isdir(dest_path):
            raise NotADirectoryError(f"O caminho '{dest_path}' não é um diretório válido.")

        dest_file_path = os.path.join(dest_path, file_name)
    
        with open(dest_file_path, 'wb') as f:
            f.write(data[:size])

        print(f"Arquivo '{file_name}' copiado para '{dest_file_path}'.")


    def rename_file(self, old_name, new_name):
        self.load_root_dir()
        if old_name not in self.root_dir:
            raise FileNotFoundError(f"Arquivo '{old_name}' não encontrado no sistema de arquivos.")

        if len(new_name) > self.MAX_FILE_NAME_LENGTH:
            raise ValueError(f"O nome do arquivo excede o tamanho máximo de {self.MAX_FILE_NAME_LENGTH} caracteres.")

        self.root_dir[new_name] = self.root_dir.pop(old_name)
        self.save_root_dir()
        print(f"Arquivo '{old_name}' renomeado para '{new_name}'.")

    def remove_file(self, file_name):
        self.load_root_dir()
        if file_name not in self.root_dir:
            raise FileNotFoundError(f"Arquivo '{file_name}' não encontrado no sistema de arquivos.")

        file_info = self.root_dir[file_name]
        start_block = file_info["start_block"]

        self.load_fat()
        block = start_block
        while block != -2:
            next_block = self.fat[block]
            self.fat[block] = -1
            block = next_block

        del self.root_dir[file_name]
        self.save_fat()
        self.save_root_dir()
        print(f"Arquivo '{file_name}' removido do sistema de arquivos.")

    def list_files(self):
        self.load_root_dir()
        for file_name, file_info in self.root_dir.items():
            status = "protegido" if file_info["protected"] else "normal"
            print(f"{file_name} - {file_info['size']} bytes - {status}")

    def get_free_spacee(self):
        free_blocks = self.fat.count(-1)
        free_space = free_blocks * self.BLOCK_SIZE
        total_space = self.total_blocks * self.BLOCK_SIZE
        free_space_mb = free_space / (1024 * 1024)
        total_space_mb = total_space / (1024 * 1024)
        print(f"{free_space_mb:.1f} MB livres de {total_space_mb:.1f} MB.")


    def protect_file(self, file_name, protect=True):
        self.load_root_dir()
        if file_name not in self.root_dir:
            raise FileNotFoundError(f"Arquivo '{file_name}' não encontrado no sistema de arquivos.")

        self.root_dir[file_name]["protected"] = protect
        self.save_root_dir()
        action = "protegido" if protect else "desprotegido"
        print(f"Arquivo '{file_name}' {action} com sucesso.")

def main():
    file_name = "FURGSfs2.fs"

    while True:
        total_size_mb = int(input("Digite o tamanho do sistema de arquivos em MB (entre 10 e 200): "))
        if 10 <= total_size_mb <= 200:
            break
        print("Por favor, insira um valor válido entre 10 e 200 MB.")

    total_size = total_size_mb * 1024 * 1024  # Converter MB para bytes

    fs = SimpleFATFileSystem(file_name, total_size)

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

        choice = input("Escolha uma opção: ")

        if choice == '1':
            source_path = input("Digite o caminho do arquivo no disco: ")
            fs.copy_to_fs(source_path)
        elif choice == '2':
            file_name = input("Digite o nome do arquivo no sistema de arquivos: ")
            dest_path = input("Digite o caminho de destino no disco: ")
            fs.copy_from_fs(file_name, dest_path)
        elif choice == '3':
            old_name = input("Digite o nome atual do arquivo: ")
            new_name = input("Digite o novo nome do arquivo: ")
            fs.rename_file(old_name, new_name)
        elif choice == '4':
            file_name = input("Digite o nome do arquivo a ser removido: ")
            fs.remove_file(file_name)
        elif choice == '5':
            fs.list_files()
        elif choice == '6':
            fs.get_free_space()
        elif choice == '7':
            file_name = input("Digite o nome do arquivo: ")
            protect = input("Proteger (s/n)? ").lower() == 's'
            fs.protect_file(file_name, protect)
        elif choice == '8':
            break
        else:
            print("Opção inválida.")

if __name__ == "__main__":
    main()
