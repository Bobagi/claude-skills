# MCP servers

Inventario dos MCP servers usados nesta conta e como cada um e provisionado numa
maquina nova. **Nenhum** precisa de `claude mcp add` manual.

| MCP server | Tipo | Como aparece numa maquina nova |
|------------|------|--------------------------------|
| `claude.ai Gmail` | Remoto (HTTP, OAuth) — `https://gmailmcp.googleapis.com/mcp/v1` | Vem com a **conta claude.ai**. Basta fazer login no Claude Code com a mesma conta; reconecta sozinho. Nao ha config local pra versionar. |
| `claude.ai Google Drive` | Remoto (HTTP, OAuth) — `https://drivemcp.googleapis.com/mcp/v1` | Idem: ligado a conta claude.ai, reconecta apos login. |
| `chrome-devtools` | Local (stdio, `npx chrome-devtools-mcp@<versao>`) | **Vem do plugin `chrome-devtools-mcp`** (ver `plugins.txt`). Instalar o plugin ja registra o MCP. |

## Observacoes

- Nao ha MCP servers definidos localmente em `~/.claude.json` (`mcpServers` esta vazio).
  Tudo que aparece em `claude mcp list` vem ou da conta claude.ai (Gmail/Drive) ou de um plugin
  (chrome-devtools). Por isso o `sync.sh` nao precisa rodar `claude mcp add`.
- Para o `chrome-devtools` **conectar de fato** (alem de instalado) a maquina precisa de
  **Node/npx** e de um **Chrome/Chromium**. Sem isso o plugin instala mas o MCP fica "failed to connect"
  ate ter o browser — o que e esperado em servidores sem GUI.
- Se um dia adicionar um MCP local proprio (`claude mcp add ...`), documente-o aqui e, se quiser
  versiona-lo, adicione o comando correspondente ao `sync.sh`.
