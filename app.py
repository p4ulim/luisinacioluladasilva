"""Mesa Cheia - plataforma contra a fome. Execute: streamlit run app.py"""
import hashlib, os, random, sqlite3
from datetime import date, timedelta
import pandas as pd
import streamlit as st

DB = os.path.join(os.path.dirname(__file__), "mesa_cheia.db")
PRECO = 120.0  # valor médio de uma cesta básica (R$)
st.set_page_config(page_title="Mesa Cheia", page_icon="🍲", layout="wide")
st.markdown("<style>html{font-size:17px}.stButton>button{border-radius:10px;font-weight:600}"
            "[data-testid=stMetricValue]{color:#c2410c}</style>", unsafe_allow_html=True)


# ---------- Banco de dados ----------
def df(sql, p=()):
    with sqlite3.connect(DB) as c:
        return pd.read_sql_query(sql, c, params=p)

def run(sql, p=()):
    with sqlite3.connect(DB) as c:
        return c.execute(sql, p).lastrowid

def h(pw):  # demo: em produção use bcrypt/argon2
    return hashlib.sha256(("mesa" + pw).encode()).hexdigest()

def today():
    return date.today().isoformat()

def notify(titulo, msg):
    run("INSERT INTO notifications(titulo,msg,data) VALUES(?,?,?)", (titulo, msg, today()))

def init():
    with sqlite3.connect(DB) as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, nome, email UNIQUE, senha, perfil, telefone, cidade, criado);
        CREATE TABLE IF NOT EXISTS institutions(id INTEGER PRIMARY KEY, nome, tipo, endereco, cidade, lat REAL, lon REAL, horario);
        CREATE TABLE IF NOT EXISTS campaigns(id INTEGER PRIMARY KEY, titulo, descricao, meta INTEGER, criador_id INTEGER, fim);
        CREATE TABLE IF NOT EXISTS donations(id INTEGER PRIMARY KEY, doador_id INTEGER, tipo, quantidade INTEGER, valor REAL,
            instituicao_id INTEGER, campanha_id INTEGER, data);
        CREATE TABLE IF NOT EXISTS requests(id INTEGER PRIMARY KEY, user_id INTEGER, pessoas INTEGER, criancas INTEGER, idosos INTEGER,
            renda REAL, motivo, prioridade INTEGER, status, data);
        CREATE TABLE IF NOT EXISTS deliveries(id INTEGER PRIMARY KEY, request_id INTEGER, instituicao_id INTEGER, status, data);
        CREATE TABLE IF NOT EXISTS notifications(id INTEGER PRIMARY KEY, titulo, msg, data);
        """)
    if df("SELECT COUNT(*) n FROM users").n[0] == 0:
        seed()

def prioridade(pessoas, criancas, idosos, renda):
    base = 40 if renda <= 0 else max(0, 40 - (renda / max(pessoas, 1)) / 20)
    return round(criancas * 8 + idosos * 6 + pessoas * 2 + base)

def nivel(score):
    return "🔴 Crítica" if score >= 70 else "🟠 Alta" if score >= 45 else "🟡 Média"

def seed():
    random.seed(7)
    users = [("Administrador", "admin@demo.com", "admin123", "admin", "Campinas"),
             ("Marcos Doador", "doador@demo.com", "demo123", "doador", "São Paulo"),
             ("Supermercado Bom Preço", "super@demo.com", "demo123", "doador", "Botucatu"),
             ("Restaurante Sabor Caseiro", "rest@demo.com", "demo123", "doador", "São Manuel"),
             ("Maria Aparecida", "familia@demo.com", "demo123", "familia", "São Manuel"),
             ("José Santos", "jose@demo.com", "demo123", "familia", "Botucatu"),
             ("Ana Lima", "ana@demo.com", "demo123", "familia", "Botucatu"),
             ("Carla Nunes", "carla@demo.com", "demo123", "familia", "São Manuel")]
    for n, e, s, p, c in users:
        run("INSERT INTO users(nome,email,senha,perfil,telefone,cidade,criado) VALUES(?,?,?,?,?,?,?)",
            (n, e, h(s), p, "(14) 90000-0000", c, today()))
    inst = [("Banco de Alimentos Esperança", "ONG", "Rua das Flores, 120", "São Manuel", -22.7317, -48.5719, "Seg-Sex 8h-17h"),
            ("Igreja Nossa Senhora Aparecida", "Instituição religiosa", "Praça Central, 10", "São Manuel", -22.7355, -48.5702, "Sáb 9h-12h"),
            ("Cozinha Solidária Vida Nova", "ONG", "Av. Brasil, 455", "Botucatu", -22.8858, -48.4451, "Seg-Sáb 10h-16h"),
            ("Associação Mãos Dadas", "Associação", "Rua XV, 88", "Botucatu", -22.8800, -48.4500, "Ter e Qui 9h-15h"),
            ("Ponto de Coleta Mercado Bom Preço", "Supermercado", "Av. Paulista, 900", "São Paulo", -23.5614, -46.6559, "Todos os dias 8h-22h")]
    for i in inst:
        run("INSERT INTO institutions(nome,tipo,endereco,cidade,lat,lon,horario) VALUES(?,?,?,?,?,?,?)", i)
    run("INSERT INTO campaigns(titulo,descricao,meta,criador_id,fim) VALUES(?,?,?,?,?)",
        ("Natal Sem Fome", "Meta de 100 cestas para as festas de fim de ano.", 100, 1, (date.today() + timedelta(60)).isoformat()))
    run("INSERT INTO campaigns(titulo,descricao,meta,criador_id,fim) VALUES(?,?,?,?,?)",
        ("Volta às Aulas Alimentada", "Cestas para famílias com crianças em idade escolar.", 50, 3, (date.today() + timedelta(30)).isoformat()))
    for _ in range(24):
        d = (date.today() - timedelta(random.randint(0, 29))).isoformat()
        if random.random() < .6:
            run("INSERT INTO donations(doador_id,tipo,quantidade,valor,instituicao_id,campanha_id,data) VALUES(?,?,?,?,?,?,?)",
                (random.choice([2, 3, 4]), "Cesta", random.randint(1, 8), 0, random.randint(1, 5), random.choice([None, 1, 2]), d))
        else:
            run("INSERT INTO donations(doador_id,tipo,quantidade,valor,instituicao_id,campanha_id,data) VALUES(?,?,?,?,?,?,?)",
                (random.choice([2, 3, 4]), "Valor", 0, random.choice([50, 120, 240, 500]), random.randint(1, 5), random.choice([None, 1, 2]), d))
    reqs = [(5, 5, 3, 0, 0, "Desemprego recente"), (6, 4, 2, 1, 600, "Renda insuficiente"),
            (7, 6, 4, 0, 400, "Família numerosa"), (8, 3, 1, 0, 1200, "Despesas médicas"),
            (5, 5, 3, 0, 0, "Segunda solicitação")]
    for i, (u, p, c, idz, r, m) in enumerate(reqs):
        run("INSERT INTO requests(user_id,pessoas,criancas,idosos,renda,motivo,prioridade,status,data) VALUES(?,?,?,?,?,?,?,?,?)",
            (u, p, c, idz, r, m, prioridade(p, c, idz, r), "Atendida" if i < 2 else "Pendente",
             (date.today() - timedelta(10 - i * 2)).isoformat()))
    run("INSERT INTO deliveries(request_id,instituicao_id,status,data) VALUES(1,1,'Entregue',?)", (today(),))
    run("INSERT INTO deliveries(request_id,instituicao_id,status,data) VALUES(2,3,'Agendada',?)", (today(),))
    notify("🎄 Nova campanha: Natal Sem Fome", "Ajude-nos a chegar a 100 cestas!")
    notify("📦 Nova doação", "O Supermercado Bom Preço doou 5 cestas básicas.")

def stats():
    d = df("SELECT tipo,quantidade,valor FROM donations")
    arrec = int(d[d.tipo == "Cesta"].quantidade.sum() + d[d.tipo == "Valor"].valor.sum() // PRECO)
    ent = int(df("SELECT COUNT(*) n FROM deliveries WHERE status='Entregue'").n[0])
    res = int(df("SELECT COUNT(*) n FROM deliveries").n[0])
    return arrec, ent, arrec - res

def metrics():
    a, e, d = stats()
    pend = int(df("SELECT COUNT(*) n FROM requests WHERE status='Pendente'").n[0])
    c = st.columns(4)
    c[0].metric("Cestas arrecadadas", a); c[1].metric("Entregues", e)
    c[2].metric("Disponíveis", d); c[3].metric("Pedidos pendentes", pend)


# ---------- Páginas ----------
def home():
    st.title("🍲 Mesa Cheia")
    st.subheader("Ninguém deveria dormir com fome. Vamos conectar quem pode ajudar a quem precisa.")
    st.write("Plataforma que une **famílias, doadores, supermercados, restaurantes, ONGs e instituições** "
             "para arrecadar e distribuir cestas básicas com organização e transparência.")
    metrics()
    c = st.columns(3)
    c[0].info("**1. Cadastre-se**\n\nFamílias, doadores e instituições criam seu perfil.")
    c[1].info("**2. Doe ou solicite**\n\nDoe cestas ou valores. Famílias pedem auxílio e são priorizadas por vulnerabilidade.")
    c[2].info("**3. Acompanhe**\n\nVeja doações, entregas e campanhas em tempo real.")
    st.caption("Contas demo — admin@demo.com / admin123 · doador@demo.com / demo123 · familia@demo.com / demo123")

def auth():
    st.title("🔐 Entrar / Cadastrar")
    t1, t2 = st.tabs(["Entrar", "Criar conta"])
    with t1:
        e = st.text_input("E-mail", key="le"); s = st.text_input("Senha", type="password", key="ls")
        if st.button("Entrar"):
            u = df("SELECT * FROM users WHERE email=? AND senha=?", (e.strip().lower(), h(s)))
            if u.empty: st.error("E-mail ou senha incorretos.")
            else:
                st.session_state.user = u.iloc[0].to_dict(); st.rerun()
    with t2:
        n = st.text_input("Nome completo"); em = st.text_input("E-mail", key="re")
        pw = st.text_input("Senha (mín. 6 caracteres)", type="password", key="rs")
        tel = st.text_input("Telefone"); cid = st.text_input("Cidade")
        per = st.selectbox("Sou...", ["familia", "doador", "instituicao"],
                           format_func=lambda x: {"familia": "Pessoa/família que precisa de auxílio",
                                                  "doador": "Doador (pessoa, supermercado, restaurante)",
                                                  "instituicao": "ONG / instituição parceira"}[x])
        if st.button("Criar conta"):
            if not (n and em and len(pw) >= 6): st.error("Preencha nome, e-mail e senha válida.")
            else:
                try:
                    run("INSERT INTO users(nome,email,senha,perfil,telefone,cidade,criado) VALUES(?,?,?,?,?,?,?)",
                        (n, em.strip().lower(), h(pw), per, tel, cid, today()))
                    st.success("Conta criada! Faça login na aba “Entrar”.")
                except sqlite3.IntegrityError:
                    st.error("Este e-mail já está cadastrado.")

def panel(u):
    st.title(f"👋 Olá, {u['nome']}")
    metrics()
    if u["perfil"] == "familia":
        r = df("""SELECT r.id Pedido, r.data Data, r.prioridade Prioridade, r.status Status,
                  COALESCE(d.status,'—') Entrega, COALESCE(i.nome,'—') Local
                  FROM requests r LEFT JOIN deliveries d ON d.request_id=r.id
                  LEFT JOIN institutions i ON i.id=d.instituicao_id WHERE r.user_id=?""", (u["id"],))
        st.subheader("Meus pedidos"); st.dataframe(r, hide_index=True, use_container_width=True)
    else:
        d = df("SELECT data Data, tipo Tipo, quantidade Cestas, valor Valor FROM donations WHERE doador_id=? ORDER BY id DESC", (u["id"],))
        st.subheader("Minhas doações"); st.dataframe(d, hide_index=True, use_container_width=True)

def donate(u):
    st.title("🎁 Fazer uma doação")
    inst = df("SELECT id,nome,cidade FROM institutions"); camp = df("SELECT id,titulo FROM campaigns")
    tipo = st.radio("O que deseja doar?", ["Cesta", "Valor"], horizontal=True,
                    format_func=lambda x: "Cestas básicas" if x == "Cesta" else "Valor em dinheiro")
    q = v = 0
    if tipo == "Cesta": q = st.number_input("Quantidade de cestas", 1, 500, 1)
    else:
        v = st.number_input("Valor (R$)", 10.0, 100000.0, 120.0, 10.0)
        st.caption(f"Equivale a {v / PRECO:.1f} cesta(s) (cesta ≈ R$ {PRECO:.0f}).")
    i = st.selectbox("Instituição / ponto de entrega", inst.id, format_func=lambda x: inst.set_index("id").loc[x, "nome"] + " — " + inst.set_index("id").loc[x, "cidade"])
    c = st.selectbox("Campanha (opcional)", [None] + camp.id.tolist(),
                     format_func=lambda x: "Sem campanha" if x is None else camp.set_index("id").loc[x, "titulo"])
    if st.button("Confirmar doação", type="primary"):
        run("INSERT INTO donations(doador_id,tipo,quantidade,valor,instituicao_id,campanha_id,data) VALUES(?,?,?,?,?,?,?)",
            (u["id"], tipo, int(q), float(v), int(i), None if c is None else int(c), today()))
        notify("📦 Nova doação", f"{u['nome']} doou " + (f"{q} cesta(s)." if tipo == "Cesta" else f"R$ {v:.2f}."))
        st.success("Obrigado! Sua doação foi registrada. 💛"); st.balloons()

def request_aid(u):
    st.title("🧺 Solicitar cesta básica")
    p = st.number_input("Pessoas na família", 1, 20, 3); c = st.number_input("Crianças (até 12 anos)", 0, 15, 0)
    i = st.number_input("Idosos (60+)", 0, 10, 0); r = st.number_input("Renda familiar mensal (R$)", 0.0, 20000.0, 0.0, 50.0)
    m = st.text_area("Situação / motivo")
    if st.button("Enviar solicitação", type="primary"):
        pr = prioridade(p, c, i, r)
        run("INSERT INTO requests(user_id,pessoas,criancas,idosos,renda,motivo,prioridade,status,data) VALUES(?,?,?,?,?,?,?,?,?)",
            (u["id"], p, c, i, r, m, pr, "Pendente", today()))
        notify("🧺 Novo pedido", f"Nova solicitação com prioridade {nivel(pr)}.")
        st.success(f"Solicitação enviada! Prioridade: {nivel(pr)} ({pr} pontos).")

def locations():
    st.title("📍 Pontos de coleta e instituições")
    i = df("SELECT * FROM institutions")
    cid = st.selectbox("Filtrar por cidade", ["Todas"] + sorted(i.cidade.unique()))
    if cid != "Todas": i = i[i.cidade == cid]
    st.map(i.rename(columns={"lon": "longitude", "lat": "latitude"}), size=200)
    st.dataframe(i[["nome", "tipo", "endereco", "cidade", "horario"]], hide_index=True, use_container_width=True)

def campaigns(u):
    st.title("📣 Campanhas contra a fome")
    for _, c in df("SELECT * FROM campaigns ORDER BY id DESC").iterrows():
        d = df("SELECT tipo,quantidade,valor FROM donations WHERE campanha_id=?", (c.id,))
        got = int(d[d.tipo == "Cesta"].quantidade.sum() + d[d.tipo == "Valor"].valor.sum() // PRECO)
        with st.container(border=True):
            st.subheader(c.titulo); st.write(c.descricao)
            st.progress(min(got / c.meta, 1.0), text=f"{got} de {c.meta} cestas · termina em {c.fim}")
    if u and u["perfil"] != "familia":
        with st.expander("➕ Criar nova campanha"):
            t = st.text_input("Título"); ds = st.text_area("Descrição")
            mt = st.number_input("Meta (cestas)", 1, 10000, 50); fim = st.date_input("Encerramento", date.today() + timedelta(30))
            if st.button("Publicar campanha") and t:
                run("INSERT INTO campaigns(titulo,descricao,meta,criador_id,fim) VALUES(?,?,?,?,?)", (t, ds, int(mt), u["id"], fim.isoformat()))
                notify(f"📣 Nova campanha: {t}", ds); st.rerun()

def history(u):
    st.title("🕑 Histórico")
    adm = u["perfil"] == "admin"
    w = "" if adm else "WHERE d.doador_id=%d" % u["id"]
    st.subheader("Doações")
    st.dataframe(df(f"""SELECT d.data Data, us.nome Doador, d.tipo Tipo, d.quantidade Cestas, d.valor Valor, i.nome Instituição
        FROM donations d JOIN users us ON us.id=d.doador_id JOIN institutions i ON i.id=d.instituicao_id {w} ORDER BY d.id DESC"""),
        hide_index=True, use_container_width=True)
    if adm or u["perfil"] == "familia":
        w2 = "" if adm else "WHERE r.user_id=%d" % u["id"]
        st.subheader("Entregas")
        st.dataframe(df(f"""SELECT d.data Data, us.nome Família, d.status Status, i.nome Local FROM deliveries d
            JOIN requests r ON r.id=d.request_id JOIN users us ON us.id=r.user_id JOIN institutions i ON i.id=d.instituicao_id {w2}
            ORDER BY d.id DESC"""), hide_index=True, use_container_width=True)

def notifications():
    st.title("🔔 Notificações")
    for _, n in df("SELECT * FROM notifications ORDER BY id DESC LIMIT 30").iterrows():
        st.info(f"**{n.titulo}** — {n.msg}  \n_{n.data}_")

def admin():
    st.title("🛠️ Painel administrativo")
    metrics()
    t1, t2, t3, t4 = st.tabs(["Pedidos por prioridade", "Entregas", "Instituições", "Usuários e doações"])
    with t1:
        p = df("""SELECT r.id, us.nome Família, r.pessoas Pessoas, r.criancas Crianças, r.idosos Idosos, r.renda Renda,
                  r.prioridade Pontos, r.data Data FROM requests r JOIN users us ON us.id=r.user_id
                  WHERE r.status='Pendente' ORDER BY r.prioridade DESC, r.data ASC""")
        p["Nível"] = p["Pontos"].map(nivel)
        st.dataframe(p, hide_index=True, use_container_width=True)
        disp = stats()[2]; st.write(f"Cestas disponíveis para alocar: **{disp}**")
        if st.button("⚡ Atender pedidos por ordem de prioridade", disabled=disp <= 0 or p.empty):
            inst = df("SELECT id FROM institutions").id.tolist()
            for _, r in p.head(disp).iterrows():
                run("UPDATE requests SET status='Aprovada' WHERE id=?", (int(r.id),))
                run("INSERT INTO deliveries(request_id,instituicao_id,status,data) VALUES(?,?,?,?)",
                    (int(r.id), random.choice(inst), "Agendada", today()))
            notify("✅ Pedidos aprovados", "Novas entregas foram agendadas."); st.rerun()
    with t2:
        d = df("""SELECT d.id, us.nome Família, i.nome Local, d.status Status, d.data Data FROM deliveries d
                  JOIN requests r ON r.id=d.request_id JOIN users us ON us.id=r.user_id
                  JOIN institutions i ON i.id=d.instituicao_id ORDER BY d.id DESC""")
        st.dataframe(d, hide_index=True, use_container_width=True)
        ag = d[d.Status == "Agendada"]
        if not ag.empty:
            sel = st.selectbox("Marcar entrega como concluída", ag.id, format_func=lambda x: f"#{x} · {ag.set_index('id').loc[x, 'Família']}")
            if st.button("Confirmar entrega"):
                run("UPDATE deliveries SET status='Entregue' WHERE id=?", (int(sel),))
                run("UPDATE requests SET status='Atendida' WHERE id=(SELECT request_id FROM deliveries WHERE id=?)", (int(sel),)); st.rerun()
    with t3:
        st.dataframe(df("SELECT nome,tipo,endereco,cidade,horario FROM institutions"), hide_index=True, use_container_width=True)
        with st.expander("➕ Cadastrar instituição"):
            n = st.text_input("Nome"); tp = st.selectbox("Tipo", ["ONG", "Instituição religiosa", "Associação", "Supermercado", "Restaurante"])
            e = st.text_input("Endereço"); c = st.text_input("Cidade")
            la = st.number_input("Latitude", value=-22.73, format="%.4f"); lo = st.number_input("Longitude", value=-48.57, format="%.4f")
            hr = st.text_input("Horário")
            if st.button("Salvar instituição") and n:
                run("INSERT INTO institutions(nome,tipo,endereco,cidade,lat,lon,horario) VALUES(?,?,?,?,?,?,?)", (n, tp, e, c, la, lo, hr)); st.rerun()
    with t4:
        st.dataframe(df("SELECT nome,email,perfil,cidade,criado FROM users"), hide_index=True, use_container_width=True)
        s = df("SELECT data, SUM(CASE WHEN tipo='Cesta' THEN quantidade ELSE valor/%s END) cestas FROM donations GROUP BY data ORDER BY data" % PRECO)
        st.subheader("Arrecadação por dia (em cestas)"); st.bar_chart(s.set_index("data"))


# ---------- Navegação ----------
init()
u = st.session_state.get("user")
menu = {"🏠 Início": home, "📍 Pontos de coleta": locations, "📣 Campanhas": lambda: campaigns(u), "🔔 Notificações": notifications}
if not u:
    menu["🔐 Entrar / Cadastrar"] = auth
else:
    menu["👤 Meu painel"] = lambda: panel(u)
    if u["perfil"] != "familia": menu["🎁 Doar"] = lambda: donate(u)
    if u["perfil"] == "familia": menu["🧺 Solicitar cesta"] = lambda: request_aid(u)
    menu["🕑 Histórico"] = lambda: history(u)
    if u["perfil"] == "admin": menu["🛠️ Administração"] = admin
st.sidebar.title("🍲 Mesa Cheia")
page = st.sidebar.radio("Menu", list(menu), label_visibility="collapsed")
if u:
    st.sidebar.caption(f"Conectado: {u['nome']} ({u['perfil']})")
    if st.sidebar.button("Sair"):
        st.session_state.pop("user"); st.rerun()
menu[page]()
