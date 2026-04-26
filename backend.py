#!/usr/bin/env python3
"""
Backend Flask — Fórum de EPIs
Arquivo de dados: dados.json (mesma pasta)
Endpoints:
  GET    /api/epis                        -> lista todos
  POST   /api/epis                        -> adiciona EPI
  DELETE /api/epis/<id>                   -> exclui EPI
  POST   /api/epis/<id>/comentarios       -> adiciona comentário
  DELETE /api/epis/<id>/comentarios/<cid> -> exclui comentário
"""

from flask import Flask, jsonify, request, send_from_directory, abort
import json, os, threading
from datetime import date

APP_DIR  = os.path.dirname(os.path.abspath(__file__))
DADOS    = os.path.join(APP_DIR, "dados.json")
LOCK     = threading.Lock()

app = Flask(__name__, static_folder=APP_DIR)

# ── helpers ──────────────────────────────────────────────────────────────────
def carregar():
    with open(DADOS, encoding="utf-8") as f:
        return json.load(f)

def salvar(data):
    with open(DADOS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def proximo_id(lista):
    return max((i["id"] for i in lista), default=0) + 1

# ── static (serve o forum_epis.html) ─────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(APP_DIR, "forum_epis.html")

# ── EPIs ──────────────────────────────────────────────────────────────────────
@app.route("/api/epis", methods=["GET"])
def listar_epis():
    return jsonify(carregar()["epis"])

@app.route("/api/epis", methods=["POST"])
def adicionar_epi():
    body = request.get_json(force=True)
    for campo in ("codigo", "nome", "ca"):
        if not body.get(campo, "").strip():
            abort(400, f"Campo obrigatório ausente: {campo}")
    with LOCK:
        dados = carregar()
        novo = {
            "id":           proximo_id(dados["epis"]),
            "codigo":       body.get("codigo","").strip(),
            "nome":         body.get("nome","").strip(),
            "ca":           body.get("ca","").strip(),
            "fabricante":   body.get("fabricante",""),
            "validade":     body.get("validade",""),
            "tamanho":      body.get("tamanho",""),
            "risco":        body.get("risco",""),
            "lote":         body.get("lote",""),
            "revisao":      body.get("revisao"),
            "diasvalidade": body.get("diasvalidade"),
            "obs":          body.get("obs",""),
            "comentarios":  []
        }
        dados["epis"].insert(0, novo)
        salvar(dados)
    return jsonify(novo), 201

@app.route("/api/epis/<int:epi_id>", methods=["DELETE"])
def excluir_epi(epi_id):
    with LOCK:
        dados = carregar()
        antes = len(dados["epis"])
        dados["epis"] = [e for e in dados["epis"] if e["id"] != epi_id]
        if len(dados["epis"]) == antes:
            abort(404, "EPI não encontrado")
        salvar(dados)
    return jsonify({"ok": True})

# ── Comentários ───────────────────────────────────────────────────────────────
@app.route("/api/epis/<int:epi_id>/comentarios", methods=["POST"])
def adicionar_comentario(epi_id):
    body = request.get_json(force=True)
    texto = body.get("texto","").strip()
    if not texto:
        abort(400, "Texto do comentário obrigatório")
    with LOCK:
        dados = carregar()
        epi = next((e for e in dados["epis"] if e["id"] == epi_id), None)
        if not epi:
            abort(404, "EPI não encontrado")
        novo_c = {
            "id":    proximo_id(epi["comentarios"]),
            "texto": texto,
            "data":  str(date.today())
        }
        epi["comentarios"].append(novo_c)
        salvar(dados)
    return jsonify(novo_c), 201

@app.route("/api/epis/<int:epi_id>/comentarios/<int:cid>", methods=["DELETE"])
def excluir_comentario(epi_id, cid):
    with LOCK:
        dados = carregar()
        epi = next((e for e in dados["epis"] if e["id"] == epi_id), None)
        if not epi:
            abort(404, "EPI não encontrado")
        antes = len(epi["comentarios"])
        epi["comentarios"] = [c for c in epi["comentarios"] if c["id"] != cid]
        if len(epi["comentarios"]) == antes:
            abort(404, "Comentário não encontrado")
        salvar(dados)
    return jsonify({"ok": True})

# ── CORS simples (facilita dev local) ────────────────────────────────────────
@app.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"]  = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,DELETE,OPTIONS"
    return resp

@app.route("/api/epis", methods=["OPTIONS"])
@app.route("/api/epis/<path:p>", methods=["OPTIONS"])
def options(p=""):
    return "", 204

if __name__ == "__main__":
    print("✅  Servidor rodando em http://localhost:5000")
    print(f"📁  Dados em: {DADOS}")
    app.run(debug=True, port=5000)
