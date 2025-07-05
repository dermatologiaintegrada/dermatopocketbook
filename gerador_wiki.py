import os
import re


def slugify(text):
    """Converte o texto em um slug amigável para nomes de arquivo."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)  # Remove caracteres especiais
    text = re.sub(r'\s+', '-', text)  # Substitui espaços por hífens
    text = text.strip('-')  # Remove hífens no início/fim
    return text


def parse_markdown_and_create_files(input_filepath):
    """
    Analisa um arquivo Markdown e cria arquivos separados para cada seção,
    incluindo índices para subtítulos.
    """
    output_dir = os.path.dirname(input_filepath)  # Diretório onde dermato.md está
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(input_filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Estrutura para armazenar as seções e seus conteúdos
    # { 'level1_title': { 'content': [], 'subsections': {} } }
    # Cada subsection tem a mesma estrutura
    parsed_sections = {'content': [], 'subsections': {}}
    current_path = [parsed_sections]  # Caminho atual na hierarquia

    all_level1_titles = []  # Para o index.md principal

    for line in lines:
        match = re.match(r'^(#+)\s*(.*)', line)
        if match:
            level = len(match.group(1))  # Nível do título (1, 2, 3 ou 4)
            title = match.group(2).strip()

            # Se o nível for 4, ele será parte do conteúdo do nível 3 (ou superior)
            if level > 3:
                current_path[-1]['content'].append(line)
                continue

            # Ajusta o caminho na hierarquia
            while len(current_path) > level:
                current_path.pop()

            # Cria a nova seção
            new_section = {'content': [], 'subsections': {}, 'title': title, 'level': level}
            current_path[-1]['subsections'][title] = new_section
            current_path.append(new_section)

            if level == 1:
                all_level1_titles.append((title, slugify(title) + '.md'))
        else:
            # Adiciona a linha ao conteúdo da seção atual
            current_path[-1]['content'].append(line)

    # Agora, escreve os arquivos recursivamente
    def write_sections_recursively(sections, parent_filepath=None):
        for title, section_data in sections['subsections'].items():
            level = section_data['level']
            slug_title = slugify(title)

            # Decide o nome do arquivo. Para níveis 2 e 3, pode ser interessante
            # prefixar com o slug do pai para evitar colisões e organizar melhor.
            if level == 1:
                filename = f"{slug_title}.md"
            elif level == 2:
                # Ex: "doencas-de-pele/acne.md"
                parent_slug = slugify(
                    parent_filepath.split(os.sep)[-1].replace('.md', '')) if parent_filepath else "untitled"
                filename = f"{slug_title}.md"
            elif level == 3:
                # Ex: "doencas-de-pele/acne/tipos-de-acne.md"
                # Aqui simplificamos para manter no mesmo nível do pai se o pai for nivel 2
                filename = f"{slug_title}.md"
            else:  # Nível 4 não cria arquivo próprio, é conteúdo
                continue

            # Ajustar o caminho completo para o arquivo de saída
            # Para manter a estrutura plana como pedido (todos os arquivos no mesmo nível do input)
            output_filepath = os.path.join(output_dir, filename)

            with open(output_filepath, 'w', encoding='utf-8') as outfile:
                # Escreve o título da seção no arquivo
                outfile.write(f"{'#' * level} {title}\n\n")

                # Adiciona índice se houver subtítulos diretos (nível + 1)
                if section_data['subsections']:
                    outfile.write("## Índice\n\n")
                    for sub_title, sub_data in section_data['subsections'].items():
                        # Para níveis 1 e 2, linkamos para o próprio arquivo do subtitulo
                        if sub_data['level'] == level + 1 and sub_data['level'] <= 3:
                            outfile.write(f"- [{sub_title}]({slugify(sub_title)}.md)\n")
                        # Para nível 3, o subtítulo de nível 4 fica no mesmo arquivo
                        elif sub_data['level'] == level + 1 and sub_data['level'] == 4:
                            outfile.write(f"- [{sub_title}](#{slugify(sub_title)})\n")  # Link interno na página
                    outfile.write("\n---\n\n")

                # Escreve o conteúdo da seção
                for content_line in section_data['content']:
                    # Reajusta o nível dos títulos internos para manter a hierarquia
                    # Ex: um H4 dentro de um arquivo de H3, continua sendo H4
                    outfile.write(content_line)

                # Recursivamente escreve as subseções, passando o nome do arquivo pai para formar nomes mais específicos
                write_sections_recursively(section_data, output_filepath)

    write_sections_recursively(parsed_sections)

    # Cria o index.md principal
    index_md_content = "# Sumário da Wiki Dermatológica\n\n"
    index_md_content += "Bem-vindo à nossa Wiki de Dermatologia. Navegue pelos tópicos principais abaixo:\n\n---\n\n"
    for title, filename in all_level1_titles:
        index_md_content += f"- [{title}]({filename})\n"

    with open(os.path.join(output_dir, 'index.md'), 'w', encoding='utf-8') as f:
        f.write(index_md_content)


# --- Configurações ---
# Garanta que o caminho para 'dermato.md' esteja correto no seu projeto
# Se 'dermato.md' estiver na raiz do seu projeto (e:\projects\pocketbook)
# então o caminho relativo é 'dermato.md'
# Caso contrário, ajuste conforme necessário. Ex: os.path.join('docs', 'dermato.md')
DERMATO_MD_PATH = r'e:\projects\pocketbook\dermato.md'  # Ou 'dermato.md' se estiver na raiz

if __name__ == "__main__":
    if os.path.exists(DERMATO_MD_PATH):
        print(f"Processando o arquivo: {DERMATO_MD_PATH}")
        parse_markdown_and_create_files(DERMATO_MD_PATH)
        print("Processamento concluído! Os arquivos foram criados no mesmo diretório.")
    else:
        print(f"Erro: O arquivo '{DERMATO_MD_PATH}' não foi encontrado.")
        print("Por favor, verifique o caminho e o nome do arquivo.")