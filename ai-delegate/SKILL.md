---
name: ai-delegate
description: Delega tarefas de código delimitadas para IAs gratuitas (Ollama local com qwen3.5/qwen2.5-coder, Groq com gpt-oss-120b/qwen3.6-27b, Gemini Flash) para economizar tokens do Claude. Use quando a tarefa for volume braçal bem especificado - boilerplate, testes unitários de função existente, docstrings, strings i18n, commit messages, resumo de arquivo/log, primeira versão de função a partir de spec curta - ou quando o usuário pedir "usa a IA local", "delega pra IA barata", "economiza tokens". NÃO use para arquitetura, refactor multi-arquivo, debugging profundo ou decisões - isso é trabalho do Claude.
---

Você (Claude) é o orquestrador: escreve a spec, delega a geração bruta a um worker
gratuito, revisa a saída e aplica a edição você mesmo. O worker NUNCA edita arquivo.

## A frota

| Worker | Modelo | Força | Limites |
|---|---|---|---|
| `groq` | gpt-oss-120b (Groq) | Melhor qualidade geral, ~470 tok/s, resposta em ~1s | 1.000 req/dia, **8K tokens/min** - prompt+resposta ≤6K tokens |
| `groq-code` | qwen3.6-27b (Groq) | Código puro, ótimo custo/qualidade | mesmo free tier do Groq |
| `groq-fast` | llama-3.1-8b-instant | Triagem/classificação em massa | idem |
| `local` | qwen3.5:9b (Ollama) | Generalista local, ctx até 32K | ~17-22 tok/s; privado e ilimitado |
| `coder` | qwen2.5-coder:14b (Ollama) | Código puro local, ctx ≤16K | ~9-13 tok/s; o mais pesado que cabe nos 16 GB |
| `fast` | qwen3.5:4b (Ollama) | Commit msgs, resumos, trivial | ~35-50 tok/s |
| `gemini` | gemini-flash-latest | Contexto gigante (1M) | **TREINA nos dados** - nunca código sensível |

## Como chamar

```bash
bash ~/.claude/skills/ai-delegate/scripts/ai.sh <worker> "prompt"
# contexto extra via stdin (vira bloco CONTEXTO no fim do prompt):
bash ~/.claude/skills/ai-delegate/scripts/ai.sh coder "Escreva testes pytest para esta função. Só código." < src/billing.py
```

A resposta sai crua no stdout; erros de API saem como `GROQ_ERROR:`/`OLLAMA_ERROR:`/`GEMINI_ERROR:`.
Para lote de tarefas independentes, dispare várias chamadas em paralelo (Groq aguenta 30 req/min;
no Ollama local rode UMA por vez - só há RAM para um modelo carregado).

## Regras de ouro

1. **Worker gera texto; VOCÊ aplica com Edit/Write.** Modelos ≤14B quebram diffs e falham em
   tool-calling - nunca deixe um worker mexer em arquivo, e nunca aplique a saída sem ler.
2. **Spec curta e completa:** assinatura/contrato, 1 exemplo do estilo do repo, critérios de
   aceite, "só código, sem explicação". Não cole arquivos inteiros sem necessidade.
3. **Roteamento:** trivial → `fast` · código delimitado com pressa/qualidade → `groq`/`groq-code` ·
   volume alto ou offline → `local`/`coder` · contexto gigante e código público → `gemini`.
4. **Código sensível (segredos, billing, auth de produção, dados de usuário): SÓ workers locais.**
   Groq não treina (contratual), mas é externo; Gemini treina e tem revisão humana.
5. **Se a saída vier errada 2 vezes, pare de insistir e faça você mesmo** - retrabalho de review
   custa mais token do que gerar direto.
6. Groq: fatie qualquer coisa acima de ~6K tokens (TPM de 8K). Local: prefill é lento no M4 -
   prompts de até ~4-8K tokens rendem melhor.

## Saúde e manutenção

- Ollama fora do ar? `curl -s localhost:11434/api/tags` → se falhar, `brew services start ollama`.
  O serviço do brew já roda com `OLLAMA_FLASH_ATTENTION=1` e `OLLAMA_KV_CACHE_TYPE=q8_0` e
  sobe sozinho no login. Modelo descarrega da RAM após ~5 min ocioso (normal).
- Keys em `~/.config/ai-workers/{groq,gemini}.key` (chmod 600). **NUNCA commitar keys neste repo.**
- `GEMINI_ERROR ... 429 prepayment credits`: o projeto do AI Studio está em modo pré-pago sem
  créditos - o operador precisa ativar o free tier/trocar o projeto em https://ai.studio/projects.
- Nesta máquina (Mac mini M4 16 GB): não rode `coder` com apps pesados abertos.
- Noutra máquina sincada sem Ollama/keys: use só os workers remotos, ou replique o setup
  (brew install ollama; ollama pull qwen3.5:4b qwen3.5:9b qwen2.5-coder:14b; criar as keys).
