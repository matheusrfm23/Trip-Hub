# RELATÓRIO DE AUDITORIA TÉCNICA (FLET 0.80+)

**Data:** 25/05/2024
**Versão Auditada:** src/ (Recursive)
**Foco:** Multi-usuário (SaaS), Oracle Cloud, Mobile First.

---

## [src/logic/auth_service.py]

🔴 **FALHAS CRÍTICAS:**
*   **Vazamento de Sessão (Multi-usuário):** O método `save_cached_login` grava o ID do último usuário logado em `assets/data/cache.json` no servidor. Se o Usuário A logar, o arquivo é sobrescrito. Se o Usuário B abrir o app depois, ele será logado automaticamente na conta do Usuário A. **ISSO É UMA FALHA DE SEGURANÇA GRAVÍSSIMA.**
*   **Estado Global na RAM:** A variável de classe `_cache_profiles` é compartilhada entre todas as sessões. Se um usuário edita o perfil, a alteração reflete na RAM de todos instantaneamente (o que pode ser desejado, mas perigoso se houver dados sensíveis de sessão misturados).

🟡 **PONTOS DE ATENÇÃO:**
*   A leitura do arquivo `profiles.json` carrega TODOS os perfis para a memória RAM na inicialização. Com centenas de usuários, isso consumirá memória desnecessária.

🟢 **O QUE ESTÁ BOM:**
*   Uso correto de `file_lock` para evitar corrupção de arquivo JSON durante escrita concorrente.

🛠️ **SUGESTÃO DE AÇÃO:**
Remover completamente o uso de `cache.json`. O estado da sessão deve ser mantido EXCLUSIVAMENTE no `page.client_storage` (lado do cliente) e validado via token/session_id no `page.session` (lado do servidor, isolado por conexão).

---

## [src/core/router.py]

🔴 **FALHAS CRÍTICAS:**
*   **Uso de `push_route`:** O código utiliza `self.page.push_route("/dashboard")` (linhas 70, 86, 136). No Flet 0.80+, isso é obsoleto e causa inconsistência na pilha de navegação (`page.views`), quebrando o botão "Voltar" do Android/iOS.
*   **Limpeza Agressiva:** `self.page.views.clear()` é chamado em toda troca de rota. Isso impede a construção de um histórico real de navegação (back stack), tornando o app pouco natural em mobile.

🟢 **O QUE ESTÁ BOM:**
*   A lógica de `on_view_pop` (linha 26) está correta para Flet moderno (`page.go(top_view.route)`).

🛠️ **SUGESTÃO DE AÇÃO:**
Substituir todas as chamadas `push_route` por `page.go()`. Refatorar a lógica de limpeza de views para manter o histórico quando necessário (ex: Dashboard -> Detalhe do Voo).

---

## [src/ui/components/smart_banner.py]

🔴 **FALHAS CRÍTICAS:**
*   **Abertura de Browser no Servidor:** O código usa `webbrowser.open(...)` (linhas 262, 265). Isso abrirá o Google Maps **no servidor Oracle Cloud**, não no celular do usuário. É inútil e consome recursos do servidor.

🛠️ **SUGESTÃO DE AÇÃO:**
Substituir `webbrowser.open` por `page.launch_url(url)`, que comanda o navegador do cliente a abrir o link.

---

## [src/ui/components/leisure/hangman.py] & [src/ui/components/leisure/word_search.py]

🔴 **FALHAS CRÍTICAS:**
*   **Bloqueio de Thread (I/O Síncrono):** Utilizam `open(SCORE_FILE, "r")` e `open(..., "w")` diretamente dentro dos métodos da UI. Como o Flet roda em um loop de eventos (asyncio), essa leitura de disco TRAVA todo o servidor para todos os usuários enquanto o arquivo é lido/escrito.

🛠️ **SUGESTÃO DE AÇÃO:**
Mover a lógica de pontuação para um `Service` na camada `src/logic/` e utilizar `aiofiles` ou executar em um `ThreadPoolExecutor` para não bloquear o loop principal.

---

## [src/logic/place_service.py]

🟡 **PONTOS DE ATENÇÃO:**
*   **I/O Bloqueante em Método Async:** O método `toggle_vote` é `async`, mas chama `_persist` que usa `open(...)` de forma síncrona. Isso anula os benefícios do async e pode causar leves "engasgos" na UI de outros usuários quando alguém vota.

🛠️ **SUGESTÃO DE AÇÃO:**
Converter `_persist` para usar `aiofiles` ou rodar em thread separada (`run_in_executor`).

---

## [src/ui/components/modal_preview.py]

🟡 **PONTOS DE ATENÇÃO:**
*   **Sequestro de Evento de Teclado:** O componente sobrescreve `self.page.on_keyboard_event = self._on_keyboard` ao ser registrado. Se outro componente fizer o mesmo, o Modal para de funcionar (ou quebra o outro).

🛠️ **SUGESTÃO DE AÇÃO:**
Implementar um gerenciador de eventos centralizado ou encadear o handler anterior antes de definir o novo.

---

## [src/logic/notification_service.py] & [src/logic/flight_service.py]

🟡 **PONTOS DE ATENÇÃO:**
*   **Escalabilidade (JSON Único):** Todos as notificações e voos de TODOS os usuários são salvos em arquivos JSON únicos (`notifications.json`, `flights.json`). Com o aumento de usuários, esses arquivos ficarão grandes, lentos para ler/gravar e aumentarão o risco de lock contention.

🟢 **O QUE ESTÁ BOM:**
*   A lógica de isolamento (filtrar por `user_id`) está correta funcionalmente, impedindo que um usuário veja dados de outro, apesar de estarem no mesmo arquivo físico.

🛠️ **SUGESTÃO DE AÇÃO:**
A curto prazo, manter. A médio prazo, migrar estas entidades para o SQLite (`database.py`) assim como já é feito com `FinanceService` e `ChatService`.

---

## [src/data/database.py] & [src/logic/finance_service.py]

🟢 **O QUE ESTÁ BOM:**
*   Configuração do SQLite com `WAL` e `check_same_thread=False` está correta para ambiente web.
*   Uso consistente de `conn.close()` dentro de blocos `finally` evita vazamento de conexões.

🛠️ **SUGESTÃO DE AÇÃO:**
Nenhuma ação crítica imediata. Manter o padrão.

---

## [RESUMO GERAL]

O código está bem estruturado em camadas, mas possui **vícios de desenvolvimento local (desktop)** que são fatais para **nuvem/multi-usuário**.

1.  **Prioridade 0 (Imediata):** Corrigir `AuthService` (cache.json) e `Router` (push_route). Sem isso, o app mistura dados de usuários e quebra a navegação.
2.  **Prioridade 1:** Corrigir `webbrowser.open` e I/O Síncrono em componentes de UI.
3.  **Prioridade 2:** Refatorar persistência de JSON para SQLite nas áreas de Lazer e Notificações.
