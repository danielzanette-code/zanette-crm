from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "crm.db"

STATUS_CLIENTE = ["Prospect", "Mapeado", "Em desenvolvimento", "Ativo", "Pausado", "Inativo"]
PRIORIDADES = ["Baixa", "Media", "Alta", "Critica"]
TIPOS_INTERACAO = ["Visita tecnica", "Ligacao", "Reuniao", "WhatsApp", "Atualizacao cadastral", "Follow-up"]
TIPOLOGIAS = ["Porcelanato", "Via seca", "Gres", "Monoporosa", "Colorificio", "Outro"]


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_schema() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tecnicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                email TEXT,
                telefone TEXT,
                ativo INTEGER NOT NULL DEFAULT 1,
                criado_em TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS empresas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                segmento TEXT,
                tipologia TEXT,
                produtos_pesquisados INTEGER,
                capacidade_m2 REAL,
                producao_m2 REAL,
                capacidade_polido_m2 REAL,
                producao_polido_m2 REAL,
                regiao TEXT,
                cidade TEXT,
                estado TEXT,
                status TEXT NOT NULL DEFAULT 'Prospect',
                prioridade TEXT NOT NULL DEFAULT 'Media',
                tecnico_id INTEGER,
                contato_principal TEXT,
                telefone TEXT,
                email TEXT,
                observacoes TEXT,
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL,
                FOREIGN KEY (tecnico_id) REFERENCES tecnicos(id)
            )
            """
        )
        empresa_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(empresas)").fetchall()
        }
        empresa_extra_columns = {
            "tipologia": "TEXT",
            "produtos_pesquisados": "INTEGER",
            "capacidade_m2": "REAL",
            "producao_m2": "REAL",
            "capacidade_polido_m2": "REAL",
            "producao_polido_m2": "REAL",
        }
        for column, sql_type in empresa_extra_columns.items():
            if column not in empresa_columns:
                conn.execute(f"ALTER TABLE empresas ADD COLUMN {column} {sql_type}")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS interacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa_id INTEGER NOT NULL,
                tecnico_id INTEGER,
                data TEXT NOT NULL,
                tipo TEXT NOT NULL,
                titulo TEXT NOT NULL,
                descricao TEXT,
                proxima_acao TEXT,
                data_proxima_acao TEXT,
                capacidade_m2 REAL,
                producao_m2 REAL,
                consumo_kg REAL,
                criado_em TEXT NOT NULL,
                FOREIGN KEY (empresa_id) REFERENCES empresas(id),
                FOREIGN KEY (tecnico_id) REFERENCES tecnicos(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS produtos_cliente (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa_id INTEGER NOT NULL,
                produto TEXT NOT NULL,
                seguimento TEXT,
                tipologia TEXT,
                consumo_kg REAL,
                produtos_pesquisados INTEGER,
                preco_medio REAL,
                faturamento REAL,
                capacidade_m2 REAL,
                producao_m2 REAL,
                producao_polido_m2 REAL,
                fornecedor_atual TEXT,
                observacoes TEXT,
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL,
                FOREIGN KEY (empresa_id) REFERENCES empresas(id)
            )
            """
        )
        produto_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(produtos_cliente)").fetchall()
        }
        if "seguimento" not in produto_columns:
            conn.execute("ALTER TABLE produtos_cliente ADD COLUMN seguimento TEXT")
        if "produtos_pesquisados" not in produto_columns:
            conn.execute("ALTER TABLE produtos_cliente ADD COLUMN produtos_pesquisados INTEGER")
        conn.execute(
            """
            UPDATE produtos_cliente
            SET
                preco_medio = faturamento,
                faturamento = COALESCE(consumo_kg, 0) * COALESCE(faturamento, 0)
            WHERE COALESCE(preco_medio, 0) = 0
              AND COALESCE(faturamento, 0) > 0
            """
        )


def metrics() -> dict[str, int]:
    with connect() as conn:
        empresas = conn.execute("SELECT COUNT(*) FROM empresas").fetchone()[0]
        tecnicos = conn.execute("SELECT COUNT(*) FROM tecnicos WHERE ativo = 1").fetchone()[0]
        interacoes = conn.execute("SELECT COUNT(*) FROM interacoes").fetchone()[0]
        produtos = conn.execute("SELECT COUNT(*) FROM produtos_cliente").fetchone()[0]
        acoes = conn.execute(
            "SELECT COUNT(*) FROM interacoes WHERE data_proxima_acao IS NOT NULL AND TRIM(data_proxima_acao) <> ''"
        ).fetchone()[0]
    return {"empresas": empresas, "tecnicos": tecnicos, "interacoes": interacoes, "produtos": produtos, "acoes": acoes}


def list_tecnicos() -> pd.DataFrame:
    with connect() as conn:
        return pd.read_sql_query("SELECT id, nome, email, telefone, ativo FROM tecnicos ORDER BY nome", conn)


def add_tecnico(nome: str, email: str, telefone: str) -> None:
    nome = nome.strip()
    if not nome:
        raise ValueError("Informe o nome do tecnico.")
    with connect() as conn:
        conn.execute(
            "INSERT INTO tecnicos (nome, email, telefone, ativo, criado_em) VALUES (?, ?, ?, 1, ?)",
            (nome, email.strip() or None, telefone.strip() or None, now_text()),
        )


def tecnico_options() -> tuple[list[str], dict[str, int]]:
    tecnicos = list_tecnicos()
    mapping = {row["nome"]: int(row["id"]) for _, row in tecnicos.iterrows()}
    return list(mapping.keys()), mapping


def list_empresas(search: str = "", status: str = "Todos", tecnico_id: int | None = None) -> pd.DataFrame:
    query = """
        SELECT e.id, e.nome, e.segmento, e.tipologia, e.produtos_pesquisados,
               e.capacidade_m2, e.producao_m2, e.capacidade_polido_m2, e.producao_polido_m2,
               e.regiao, e.cidade, e.estado, e.status, e.prioridade,
               t.nome AS tecnico, e.contato_principal, e.telefone, e.email, e.atualizado_em
        FROM empresas e
        LEFT JOIN tecnicos t ON t.id = e.tecnico_id
        WHERE 1 = 1
    """
    params: list[object] = []
    if search.strip():
        query += " AND e.nome LIKE ?"
        params.append(f"%{search.strip()}%")
    if status != "Todos":
        query += " AND e.status = ?"
        params.append(status)
    if tecnico_id:
        query += " AND e.tecnico_id = ?"
        params.append(tecnico_id)
    query += " ORDER BY e.nome"
    with connect() as conn:
        return pd.read_sql_query(query, conn, params=params)


def get_empresa(empresa_id: int) -> sqlite3.Row | None:
    with connect() as conn:
        return conn.execute("SELECT * FROM empresas WHERE id = ?", (empresa_id,)).fetchone()


def delete_empresa(empresa_id: int) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM produtos_cliente WHERE empresa_id = ?", (empresa_id,))
        conn.execute("DELETE FROM interacoes WHERE empresa_id = ?", (empresa_id,))
        conn.execute("DELETE FROM empresas WHERE id = ?", (empresa_id,))


def save_empresa(payload: dict[str, object], empresa_id: int | None = None) -> int:
    timestamp = now_text()
    values = (
        payload.get("nome"),
        payload.get("segmento"),
        payload.get("tipologia"),
        payload.get("produtos_pesquisados"),
        payload.get("capacidade_m2"),
        payload.get("producao_m2"),
        payload.get("capacidade_polido_m2"),
        payload.get("producao_polido_m2"),
        payload.get("regiao"),
        payload.get("cidade"),
        payload.get("estado"),
        payload.get("status"),
        payload.get("prioridade"),
        payload.get("tecnico_id"),
        payload.get("contato_principal"),
        payload.get("telefone"),
        payload.get("email"),
        payload.get("observacoes"),
    )
    if not str(payload.get("nome") or "").strip():
        raise ValueError("Informe o nome da empresa.")

    with connect() as conn:
        if empresa_id:
            conn.execute(
                """
                UPDATE empresas
                SET nome = ?, segmento = ?, tipologia = ?, produtos_pesquisados = ?,
                    capacidade_m2 = ?, producao_m2 = ?, capacidade_polido_m2 = ?, producao_polido_m2 = ?,
                    regiao = ?, cidade = ?, estado = ?, status = ?, prioridade = ?,
                    tecnico_id = ?, contato_principal = ?, telefone = ?, email = ?, observacoes = ?,
                    atualizado_em = ?
                WHERE id = ?
                """,
                values + (timestamp, empresa_id),
            )
            return empresa_id
        else:
            cursor = conn.execute(
                """
                INSERT INTO empresas (
                    nome, segmento, tipologia, produtos_pesquisados, capacidade_m2, producao_m2,
                    capacidade_polido_m2, producao_polido_m2, regiao, cidade, estado, status, prioridade, tecnico_id,
                    contato_principal, telefone, email, observacoes, criado_em, atualizado_em
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values + (timestamp, timestamp),
            )
            return int(cursor.lastrowid)


def add_interacao(payload: dict[str, object]) -> None:
    if not str(payload.get("titulo") or "").strip():
        raise ValueError("Informe um titulo para a interacao.")
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO interacoes (
                empresa_id, tecnico_id, data, tipo, titulo, descricao, proxima_acao, data_proxima_acao,
                capacidade_m2, producao_m2, consumo_kg, criado_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.get("empresa_id"),
                payload.get("tecnico_id"),
                payload.get("data"),
                payload.get("tipo"),
                payload.get("titulo"),
                payload.get("descricao"),
                payload.get("proxima_acao"),
                payload.get("data_proxima_acao"),
                payload.get("capacidade_m2"),
                payload.get("producao_m2"),
                payload.get("consumo_kg"),
                now_text(),
            ),
        )
        conn.execute("UPDATE empresas SET atualizado_em = ? WHERE id = ?", (now_text(), payload.get("empresa_id")))


def list_interacoes(empresa_id: int | None = None, limit: int = 100) -> pd.DataFrame:
    query = """
        SELECT i.id, i.data, e.nome AS empresa, t.nome AS tecnico, i.tipo, i.titulo, i.proxima_acao,
               i.data_proxima_acao, i.capacidade_m2, i.producao_m2, i.consumo_kg, i.descricao
        FROM interacoes i
        LEFT JOIN empresas e ON e.id = i.empresa_id
        LEFT JOIN tecnicos t ON t.id = i.tecnico_id
        WHERE 1 = 1
    """
    params: list[object] = []
    if empresa_id:
        query += " AND i.empresa_id = ?"
        params.append(empresa_id)
    query += " ORDER BY i.data DESC, i.id DESC LIMIT ?"
    params.append(limit)
    with connect() as conn:
        return pd.read_sql_query(query, conn, params=params)


def add_produto_cliente(payload: dict[str, object]) -> None:
    produto = str(payload.get("produto") or "").strip()
    if not produto:
        raise ValueError("Informe o produto.")

    timestamp = now_text()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO produtos_cliente (
                empresa_id,
                produto,
                seguimento,
                tipologia,
                consumo_kg,
                produtos_pesquisados,
                preco_medio,
                faturamento,
                capacidade_m2,
                producao_m2,
                producao_polido_m2,
                fornecedor_atual,
                observacoes,
                criado_em,
                atualizado_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.get("empresa_id"),
                produto,
                payload.get("seguimento"),
                payload.get("tipologia"),
                payload.get("consumo_kg"),
                payload.get("produtos_pesquisados"),
                payload.get("preco_medio"),
                payload.get("faturamento"),
                payload.get("capacidade_m2"),
                payload.get("producao_m2"),
                payload.get("producao_polido_m2"),
                payload.get("fornecedor_atual"),
                payload.get("observacoes"),
                timestamp,
                timestamp,
            ),
        )
        conn.execute("UPDATE empresas SET atualizado_em = ? WHERE id = ?", (timestamp, payload.get("empresa_id")))


def update_produto_cliente(produto_id: int, payload: dict[str, object]) -> None:
    produto = str(payload.get("produto") or "").strip()
    if not produto:
        raise ValueError("Informe o produto.")

    timestamp = now_text()
    with connect() as conn:
        row = conn.execute(
            "SELECT empresa_id FROM produtos_cliente WHERE id = ?",
            (produto_id,),
        ).fetchone()
        if row is None:
            raise ValueError("Produto não encontrado.")

        conn.execute(
            """
            UPDATE produtos_cliente
            SET
                produto = ?,
                consumo_kg = ?,
                preco_medio = ?,
                faturamento = ?,
                fornecedor_atual = ?,
                observacoes = ?,
                atualizado_em = ?
            WHERE id = ?
            """,
            (
                produto,
                payload.get("consumo_kg"),
                payload.get("preco_medio"),
                payload.get("faturamento"),
                payload.get("fornecedor_atual"),
                payload.get("observacoes"),
                timestamp,
                produto_id,
            ),
        )
        conn.execute("UPDATE empresas SET atualizado_em = ? WHERE id = ?", (timestamp, row["empresa_id"]))


def delete_produto_cliente(produto_id: int) -> None:
    timestamp = now_text()
    with connect() as conn:
        row = conn.execute(
            "SELECT empresa_id FROM produtos_cliente WHERE id = ?",
            (produto_id,),
        ).fetchone()
        if row is None:
            return

        conn.execute("DELETE FROM produtos_cliente WHERE id = ?", (produto_id,))
        conn.execute("UPDATE empresas SET atualizado_em = ? WHERE id = ?", (timestamp, row["empresa_id"]))


def list_produtos_cliente(empresa_id: int | None = None, limit: int = 500) -> pd.DataFrame:
    query = """
        SELECT
            p.id,
            e.nome AS cliente,
            p.produto,
            p.seguimento,
            p.tipologia,
            p.produtos_pesquisados,
            p.capacidade_m2,
            p.producao_m2,
            p.consumo_kg,
            p.producao_polido_m2,
            p.preco_medio,
            p.faturamento,
            p.fornecedor_atual,
            p.observacoes,
            p.atualizado_em
        FROM produtos_cliente p
        LEFT JOIN empresas e ON e.id = p.empresa_id
        WHERE 1 = 1
    """
    params: list[object] = []
    if empresa_id:
        query += " AND p.empresa_id = ?"
        params.append(empresa_id)
    query += " ORDER BY e.nome, p.produto LIMIT ?"
    params.append(limit)
    with connect() as conn:
        return pd.read_sql_query(query, conn, params=params)
