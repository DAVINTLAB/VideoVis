import json
import os
from pysentimiento import create_analyzer
from tqdm import tqdm

analyzer = create_analyzer(task="sentiment", lang="pt")

ARQUIVO = os.path.join("input", "oscar_comments.json")

# Carregar comentários
with open(ARQUIVO, "r", encoding="utf-8") as f:
    comentarios = json.load(f)

# Classificar sentimentos
for comentario in tqdm(comentarios, desc="Classificando sentimentos"):
    mensagem = comentario.get("message", "")
    
    if not mensagem.strip():
        comentario["sentiment"] = "NEU"  # padrão se estiver vazio
        continue
    
    resultado = analyzer.predict(mensagem)
    comentario["sentiment"] = resultado.output  # 'POS', 'NEU', 'NEG'

with open(ARQUIVO, "w", encoding="utf-8") as f:
    json.dump(comentarios, f, ensure_ascii=False, indent=2)

print(f"\nClassificação concluída. Total de comentários processados: {len(comentarios)}")
print(f"Modificacoes salvas em: {ARQUIVO}")
