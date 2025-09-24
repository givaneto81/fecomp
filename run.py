import os
from fecomp import create_app

# Carrega a variável de ambiente para determinar o modo de execução
# O padrão é 'production' para maior segurança
FLASK_ENV = os.environ.get('FLASK_ENV', 'production')

app = create_app()

if __name__ == '__main__':
    # O modo de depuração só será ativado se FLASK_ENV for 'development'
    is_debug_mode = (FLASK_ENV == 'development')
    app.run(host='0.0.0.0', port=5000, debug=is_debug_mode)