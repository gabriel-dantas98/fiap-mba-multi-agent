# Contribuindo

## Adicionando um projeto novo

1. Fork e clone o repo.
2. Rode o scaffold:

   ```bash
   uv run scripts/new_project.py \
     --group grupo-alpha \
     --slug meu-bot \
     --kind backend \
     --description "Descrição curta" \
     --members "Seu Nome" "Outro"
   ```

3. Implemente o app dentro de `apps/<grupo>/<slug>/`.
4. Rode localmente:

   ```bash
   uv sync
   uv run uvicorn homepage.main:app --reload
   # Acesse http://localhost:8000/<grupo>/<slug>/
   ```

5. Abra um PR. CI vai rodar lint + validação de manifest. Se você habilitou
   `checks.pytest: true` ou `checks.mypy: true` no `project.yaml`, esses checks
   também rodam só na sua app.

## Convenções

- Pastas em `apps/` usam `underscore_case` (são módulos Python).
- `slug` e `group` em YAML usam `hyphen-case`.
- `mount_path` deve ser exatamente `/<group>/<slug>`.

## Licença

Ao contribuir, você concorda em licenciar sua contribuição sob Apache 2.0.
