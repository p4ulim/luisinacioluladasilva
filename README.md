# 🍞 Rede Fome Zero

Plataforma em Python + Streamlit + SQLite que conecta famílias em insegurança alimentar, doadores, mercados,
restaurantes, ONGs e instituições sociais para organizar a doação e a entrega de cestas básicas.

## Como executar localmente
1. Instale o Python 3.9+.
2. (Opcional) crie um ambiente virtual:
   `python -m venv venv` e ative com `source venv/bin/activate` (Linux/Mac) ou `venv\Scripts\activate` (Windows).
3. Instale as dependências: `pip install -r requirements.txt`
4. Rode: `streamlit run app.py`
5. Abra http://localhost:8501

Na primeira execução o banco `fome_zero.db` é criado com dados fictícios. Para recomeçar, apague esse arquivo.

## Contas de demonstração
| Perfil | E-mail | Senha |
|---|---|---|
| Administrador | admin@fome.zero | admin123 |
| Doador | doador@demo.com | demo123 |
| Família | familia@demo.com | demo123 |

## Funcionalidades
- Cadastro/login (senhas com PBKDF2 + salt) para famílias, doadores e instituições
- Doação de cestas ou valores (R$ 150 = 1 cesta, ajustável em `CESTA_VALOR`)
- Solicitação de cestas com **pontuação de prioridade** (tamanho da família, crianças, idosos, gestantes, desemprego, renda per capita)
- Painel com cestas arrecadadas, entregues e disponíveis
- Mapa e lista de pontos de coleta
- Campanhas com barra de progresso, notificações e histórico de doações/entregas
- Painel administrativo: fila por prioridade, agendamento/conclusão de entregas, confirmação de doações, campanhas, instituições e avisos

## Estrutura do banco (SQLite)
`usuarios`, `instituicoes`, `campanhas`, `doacoes`, `solicitacoes`, `entregas`, `notificacoes`.

## Próximos passos sugeridos
Integração de pagamento (Pix), e-mail/WhatsApp para notificações, verificação documental das famílias e deploy no Streamlit Community Cloud.
