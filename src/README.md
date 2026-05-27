# API de Atividades da Mergington High School

Uma aplicação FastAPI super simples que permite aos alunos visualizar e se inscrever em atividades extracurriculares.

## Funcionalidades

- Visualizar todas as atividades extracurriculares disponíveis
- Inscrever-se em atividades
- Exibir anúncios dinâmicos carregados do MongoDB
- Permitir que professores autenticados gerenciem anúncios

## Como começar

1. Instale as dependências:

   ```
   pip install -r requirements.txt
   ```

2. Execute a aplicação:

   ```
   python app.py
   ```

3. Abra seu navegador e acesse:
   - Documentação da API: http://localhost:8000/docs
   - Documentação alternativa: http://localhost:8000/redoc

## Endpoints da API

| Método | Endpoint                                                          | Descrição                                                            |
| ------ | ----------------------------------------------------------------- | -------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Obtém todas as atividades com detalhes e número atual de participantes |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Inscreve-se em uma atividade                                         |
| GET    | `/announcements`                                                  | Retorna os anúncios ativos exibidos no cabeçalho                     |
| GET    | `/announcements/manage?teacher_username=principal`                | Retorna todos os anúncios para a tela de gerenciamento               |
| POST   | `/announcements?teacher_username=principal`                       | Cria um anúncio com `title`, `message`, `expiration_date` e `start_date` opcional |
| PUT    | `/announcements/{announcement_id}?teacher_username=principal`     | Atualiza um anúncio existente                                        |
| DELETE | `/announcements/{announcement_id}?teacher_username=principal`     | Exclui um anúncio existente                                          |

## Modelo de Dados

A aplicação usa um modelo de dados simples com identificadores significativos:

1. **Atividades** - Usa o nome da atividade como identificador:
   - Descrição
   - Horário
   - Número máximo de participantes permitidos
   - Lista de e-mails dos alunos inscritos

2. **Alunos** - Usa o e-mail como identificador:
   - Nome
   - Série

Os dados são persistidos no MongoDB local configurado em [src/backend/database.py](c:/Workspace/skills-copilot-code-review/src/backend/database.py).
