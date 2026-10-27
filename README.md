# WordPress Public Posts Export

Cliente Python original, somente leitura, para catalogar publicações públicas de um WordPress com REST API habilitada. Usa a biblioteca padrão, paginação limitada, timeout e validação do contrato. Não instala plugins, autentica usuários, cria rascunhos ou publica conteúdo.

```console
python examples/wordpress_export/export_posts.py https://SEU-SITE.example catalogo.json --max-pages 5 --per-page 20
python -m unittest discover -s examples/wordpress_export -p "test_*.py" -v
```

Substitua o endereço pelo site público desejado. Algumas instalações não usam a rota `/wp-json/`, restringem a API ou possuem filtros próprios; este cliente cobre o contrato padrão e informa falhas, sem contornar restrições. Respeite a capacidade do site. O catálogo é JSON, não CSV para execução em planilhas. Títulos são convertidos de HTML para texto. Sem credenciais ou dados privados.

O campo `truncated` informa quando o limite de páginas impediu completar a consulta. Uma publicação inserida durante a paginação pode mudar o conjunto retornado: a API não oferece uma transação de snapshot. IDs repetidos causam erro para evitar um catálogo silenciosamente inconsistente. O conteúdo é acumulado em memória, limitado a 20 páginas de até 100 itens e 2 MB por resposta.

Validação local: testes com respostas fictícias e servidor HTTP local verificam paginação, título, limites, contrato e falha de transporte. Não equivalem a teste num WordPress real; uma verificação pública adicional, quando realizada, será documentada separadamente.

Em 27/10/2026, o comando também foi executado contra `https://wordpress.org/news`, limitado a uma página e duas publicações. A consulta pública GET retornou dois registros e marcou `truncated=true`, como esperado. A saída está em `verificacao-publica.json`. Essa consulta comprova o caminho de leitura naquele endpoint e instante; não garante compatibilidade com todos os sites WordPress. Sete testes automatizados locais passaram.

Referências: [WordPress REST API — Posts](https://developer.wordpress.org/rest-api/reference/posts/) e [Pagination](https://developer.wordpress.org/rest-api/using-the-rest-api/pagination/). Implementação original, sem copiar código do blog. Licença MIT em `LICENSE` nesta pasta.
