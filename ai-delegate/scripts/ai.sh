#!/usr/bin/env bash
# ai.sh - chama um worker de IA (local via Ollama ou free tier remoto) e imprime a resposta crua.
# Uso: ai.sh <worker> "prompt"  [contexto extra via stdin]
# Workers: groq | groq-code | groq-fast | local | coder | fast | gemini
set -euo pipefail

worker="${1:?uso: ai.sh <groq|groq-code|groq-fast|cerebras|local|coder|fast|gemini> \"prompt\"}"
prompt="${2:?falta o prompt}"

if [ ! -t 0 ]; then
  ctx="$(cat)"
  [ -n "$ctx" ] && prompt="$prompt

--- CONTEXTO ---
$ctx"
fi

groq_call() {
  local payload
  payload=$(jq -n --arg m "$1" --arg p "$prompt" \
    '{model:$m, messages:[{role:"user",content:$p}], temperature:0.2, max_tokens:4096}')
  curl -sS --max-time 120 https://api.groq.com/openai/v1/chat/completions \
    -H "Authorization: Bearer $(cat "$HOME/.config/ai-workers/groq.key")" \
    -H "Content-Type: application/json" -d "$payload" \
    | jq -r 'if .error then "GROQ_ERROR: " + .error.message else .choices[0].message.content end'
}

ollama_call() {
  # $2 = "nothink" desliga o thinking (qwen3.5 vem com thinking LIGADO por default e
  # pode gastar todos os tokens pensando e devolver content vazio; qwen2.5 não aceita o campo)
  local model="$1" payload
  if [ "${2:-}" = "nothink" ]; then
    payload=$(jq -n --arg m "$model" --arg p "$prompt" \
      '{model:$m, messages:[{role:"user",content:$p}], stream:false, think:false, options:{temperature:0.2}}')
  else
    payload=$(jq -n --arg m "$model" --arg p "$prompt" \
      '{model:$m, messages:[{role:"user",content:$p}], stream:false, options:{temperature:0.2}}')
  fi
  curl -sS --max-time 600 localhost:11434/api/chat -d "$payload" \
    | jq -r '.message.content // ("OLLAMA_ERROR: " + (.error | tostring))'
}

case "$worker" in
  groq)      groq_call "openai/gpt-oss-120b" ;;
  cerebras)
    payload=$(jq -n --arg p "$prompt" \
      '{model:"gpt-oss-120b", messages:[{role:"user",content:$p}], temperature:0.2, max_tokens:4096}')
    curl -sS --max-time 120 https://api.cerebras.ai/v1/chat/completions \
      -H "Authorization: Bearer $(cat "$HOME/.config/ai-workers/cerebras.key")" \
      -H "Content-Type: application/json" -d "$payload" \
      | jq -r 'if .error then "CEREBRAS_ERROR: " + (.error.message // (.error|tostring)) else .choices[0].message.content end'
    ;;
  groq-code) groq_call "qwen/qwen3.6-27b" ;;
  groq-fast) groq_call "llama-3.1-8b-instant" ;;
  local)     ollama_call "qwen3.5:9b" nothink ;;
  coder)     ollama_call "qwen2.5-coder:14b" ;;
  fast)      ollama_call "qwen3.5:4b" nothink ;;
  gemini)
    payload=$(jq -n --arg p "$prompt" '{contents:[{parts:[{text:$p}]}]}')
    curl -sS --max-time 120 \
      "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent" \
      -H 'Content-Type: application/json' \
      -H "X-goog-api-key: $(cat "$HOME/.config/ai-workers/gemini.key")" \
      -X POST -d "$payload" \
      | jq -r 'if .error then "GEMINI_ERROR: " + .error.message else .candidates[0].content.parts[0].text end'
    ;;
  *) echo "worker desconhecido: $worker (use groq|groq-code|groq-fast|local|coder|fast|gemini)" >&2; exit 1 ;;
esac
