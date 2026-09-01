# Evidências — Exercício 1.3 (Cold start)

Function: `func-qc-ro6i2l` (Flex Consumption, FC1, `eastus`), endpoint
`/api/produtos?categoria=vestuario`, medido com `curl -w` (latência de rede
real embutida, não é só tempo de execução da Function).

## Chamada 1 (fria, ~12 min sem tráfego HTTP antes) — 02:15:03 UTC

```
$ { time curl -s -o /dev/null -w "http_code=%{http_code} time_total=%{time_total}s\n" \
    "$HOSTNAME/api/produtos?categoria=vestuario" ; } 2>&1
http_code=200 time_total=2.822712s
0.03s user 0.01s system 1% cpu 2.832 total
```

## Chamada 2 (quente, +5 s) — 02:15:18 UTC

```
$ sleep 5
$ { time curl -s -o /dev/null -w "http_code=%{http_code} time_total=%{time_total}s\n" \
    "$HOSTNAME/api/produtos?categoria=vestuario" ; } 2>&1
http_code=200 time_total=2.745923s
0.03s user 0.01s system 1% cpu 2.756 total
```

## Verificação intermediária — /health (não toca Storage) + /produtos de novo

```
$ { time curl -s -o /dev/null -w "http_code=%{http_code} time_total=%{time_total}s\n" \
    "$HOSTNAME/api/health" ; } 2>&1
http_code=200 time_total=2.776689s

$ { time curl -s -o /dev/null -w "http_code=%{http_code} time_total=%{time_total}s\n" \
    "$HOSTNAME/api/produtos?categoria=vestuario" ; } 2>&1
http_code=200 time_total=3.030764s
```

## Chamada 3 (fria de novo, idle real de ~20 min sem tráfego) — 12:13:20 UTC

```
$ { time curl -s -o /dev/null -w "http_code=%{http_code} time_total=%{time_total}s\n" \
    "$HOSTNAME/api/produtos?categoria=vestuario" ; } 2>&1
http_code=200 time_total=3.006176s
0.03s user 0.01s system 1% cpu 3.018 total
```

## Isolando TLS handshake de TTFB (achado real)

```
$ curl -s -o /dev/null \
    -w "dns=%{time_namelookup}s connect=%{time_connect}s tls=%{time_appconnect}s ttfb=%{time_starttransfer}s total=%{time_total}s\n" \
    "$HOSTNAME/api/health"
dns=0.002414s connect=0.122583s tls=0.397395s ttfb=2.381940s total=2.382241s

$ curl -s -o /dev/null \
    -w "dns=%{time_namelookup}s connect=%{time_connect}s tls=%{time_appconnect}s ttfb=%{time_starttransfer}s total=%{time_total}s\n" \
    "$HOSTNAME/api/health"
dns=0.003895s connect=0.128679s tls=0.397597s ttfb=2.441246s total=2.441532s
```

TLS handshake (`time_appconnect`) fica estável em ~0.40 s nas duas chamadas.
TTFB (`time_starttransfer` − `time_appconnect`) fica em ~1.98–2.04 s mesmo em
`/health`, que não toca o Blob Storage — confirma que o gargalo não é I/O de
dados, é dispatch/inicialização do host por trás do endpoint.

## Resumo (os três números citados no relatório)

| Chamada | Horário (UTC) | `time_total` bruto |
|---|---|---|
| 1 | 02:15:03 | 2.822712s → **2.823 s** |
| 2 | 02:15:18 | 2.745923s → **2.746 s** |
| 3 | 12:13:20 | 3.006176s → **3.006 s** |

Valores no relatório principal (`entrega-grupo-aula03.md`, Exercício 1.3) são
o `time_total` bruto acima arredondado para 3 casas decimais — reproduzível
a partir deste arquivo.
