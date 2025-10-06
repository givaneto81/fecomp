# Educa AI - Repositório Académico Inteligente

Educa AI é uma aplicação web desenvolvida em Flask que funciona como um repositório académico pessoal, permitindo que os estudantes organizem os seus materiais e conversem com uma IA.

## Como Executar o Projeto Localmente

Siga estes passos para ter a aplicação a funcionar na sua máquina.

### Pré-requisitos
- Python 3.8 ou superior instalado.
- Git (para clonar o repositório).

---

### Guia de Instalação

**1. Clone o Repositório**
   - Abra um terminal e execute o seguinte comando:
     ```bash
     git clone <URL_DO_SEU_REPOSITORIO>
     cd fecompzera
     ```

**2. Crie e Ative o Ambiente Virtual**
   - Este passo cria um ambiente Python isolado para o projeto.
     ```bash
     # 1. Criar o ambiente
     python -m venv .venv

     # 2. Ativar o ambiente (no Windows PowerShell)
     .\.venv\Scripts\Activate
     ```
   - *(Se tiver um erro de permissão no PowerShell, consulte a secção "Solução de Problemas" no final deste guia).*

**3. Configure o Banco de Dados**
   - Você tem duas opções. Para uma simples demonstração, a Opção A é a mais fácil.

   <details>
     <summary><strong>Opção A (Fácil): Usar SQLite - Não precisa de instalar nada</strong></summary>
     
     <br>
     O projeto está pré-configurado para usar um banco de dados SQLite, que é apenas um ficheiro (`site.db`) criado automaticamente. Para usar esta opção:
     
     1. Certifique-se de que no seu ficheiro `.env` (que você criará no Passo 5), a linha `SQLALCHEMY_DATABASE_URI` está **apagada ou comentada** com um `#` no início.
     
     E é só isso! A aplicação irá criar e usar o ficheiro `site.db` sozinha.
   </details>

   <details>
     <summary><strong>Opção B (Avançado): Usar PostgreSQL - Para desenvolvimento completo</strong></summary>
     
     <br>
     Se quiser usar o mesmo ambiente de desenvolvimento que o autor, siga estes passos:
     
     1. **Instale o PostgreSQL:** Baixe e instale o PostgreSQL a partir do [site oficial](https://www.postgresql.org/download/). Durante a instalação, defina uma senha para o utilizador `postgres`. **Anote essa senha!**

     2. **Crie a Base de Dados:**
        - Abra o terminal `psql` (que é instalado com o PostgreSQL).
        - Execute o seguinte comando SQL para criar a base de dados (o nome `educa_ai_db` é o que está no ficheiro `.env`):
          ```sql
          CREATE DATABASE educa_ai_db;
          ```
        - Pode fechar o `psql` digitando `\q`.

     3. **Configure a Conexão:**
        - No Passo 5, quando criar o seu ficheiro `.env`, certifique-se de que a linha `SQLALCHEMY_DATABASE_URI` está presente e correta, substituindo `SUA_SENHA` pela senha que você definiu na instalação do PostgreSQL:
          ```
          SQLALCHEMY_DATABASE_URI="postgresql+pg8000://postgres:SUA_SENHA@localhost/educa_ai_db"
          ```
   </details>

**4. Instale as Dependências**
   - Com o ambiente virtual ativo (o seu terminal deve mostrar `(.venv)`), instale todas as bibliotecas necessárias:
     ```bash
     pip install -r requirements.txt
     ```

**5. Configure as Variáveis de Ambiente**
   - Crie uma cópia do ficheiro `.env.example` e renomeie-a para `.env`.
   - Abra o ficheiro `.env` e preencha as variáveis, principalmente a `GEMINI_API_KEY` se quiser que o chatbot funcione.
   - Ajuste a linha `SQLALCHEMY_DATABASE_URI` de acordo com a sua escolha no Passo 3.

**6. Execute a Aplicação!**
   - Certifique-se de que o ambiente virtual ainda está ativo.
   - Execute o comando:
     ```bash
     python run.py
     ```
   - Abra `http://127.0.0.1:5000` no seu navegador.

---

### Solução de Problemas

**Erro de "Execução de Scripts Desabilitada" no PowerShell:**
Se ao tentar ativar o `.venv` vir um erro de segurança, siga estes passos:
1. Abra o PowerShell **como Administrador**.
2. Execute o comando: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`
3. Confirme com `S` se for pedido.
4. Feche o PowerShell de administrador e tente ativar o ambiente virtual novamente no seu terminal normal.