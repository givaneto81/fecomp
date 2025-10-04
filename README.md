# Educa AI - Repositório Académico Inteligente

Educa AI é uma aplicação web desenvolvida em Flask que funciona como um repositório académico pessoal, permitindo que os estudantes organizem os seus materiais e conversem com uma IA.

## Como Executar o Projeto Localmente (Para Testes)

Siga estes passos para ter a aplicação a funcionar na sua máquina.

### Pré-requisitos
- Python 3.8 ou superior instalado.

### Guia de Instalação

**1. Descarregue o Código**
   - Clone ou descarregue este repositório como um ficheiro ZIP e extraia-o.

**2. Configure o Ambiente Virtual (Passo Crucial!)**
   - Abra um terminal (PowerShell ou CMD) na pasta do projeto (`fecompzera/`).
   - Execute o comando abaixo para criar um ambiente isolado para o projeto:
     ```bash
     python -m venv .venv
     ```
   - Agora, ative o ambiente que acabou de criar:
     ```bash
     # No Windows (PowerShell)
     .\.venv\Scripts\Activate
     ```
     *(Se tiver um erro de permissão, consulte a secção "Solução de Problemas" abaixo)*

**3. Instale as Dependências**
   - Com o ambiente virtual ativo (o seu terminal deve mostrar `(.venv)` no início), execute o seguinte comando para instalar todas as bibliotecas necessárias de uma só vez:
     ```bash
     pip install -r requirements.txt
     ```

**4. Configure as Variáveis de Ambiente**
   - Na pasta do projeto, vai encontrar um ficheiro chamado `.env.example`.
   - Faça uma cópia deste ficheiro e renomeie a cópia para `.env`.
   - **(Opcional, mas recomendado)** Se quiser testar o chatbot, abra o ficheiro `.env` e cole a sua chave da API do Google Gemini no campo `GEMINI_API_KEY`. Se não o fizer, o resto da aplicação funcionará, mas o chat não.

**5. Execute a Aplicação!**
   - Certifique-se de que o ambiente virtual ainda está ativo.
   - Execute o comando:
     ```bash
     python run.py
     ```
   - O terminal irá mostrar uns links. Abra `http://127.0.0.1:5000` no seu navegador.

A aplicação irá criar automaticamente um ficheiro de base de dados chamado `site.db` na primeira vez que for executada.

### Solução de Problemas

**Erro de "Execução de Scripts Desabilitada" no PowerShell:**
Se ao tentar ativar o `.venv` vir um erro de segurança, siga estes passos:
1. Abra o PowerShell **como Administrador**.
2. Execute o comando: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`
3. Confirme com `S` se for pedido.
4. Feche o PowerShell de administrador e tente ativar o ambiente virtual novamente no seu terminal normal.

---