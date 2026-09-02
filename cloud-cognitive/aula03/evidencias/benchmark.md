# Evidências — Exercício 3.2 (Benchmark de carga)

`hey -n 1000 -c 50`, executado de verdade contra os dois endpoints vivos na
mesma sessão, back-to-back (ACI primeiro, Function em seguida).

## ACI (`aci-qc-ro6i2l`, 0.5 vCPU / 1 GB)

```
$ hey -n 1000 -c 50 "http://qc-api-ro6i2l.eastus.azurecontainer.io:8080/produtos?categoria=moveis"

Summary:
  Total:        6.3440 secs
  Slowest:      1.3405 secs
  Fastest:      0.1297 secs
  Average:      0.2876 secs
  Requests/sec: 157.6282

Latency distribution:
  10%% in 0.1612 secs   50%% in 0.2433 secs   95%% in 0.6512 secs   99%% in 0.7750 secs

Status code distribution:
  [200] 1000 responses
```

## Function (`func-qc-ro6i2l`, Flex Consumption FC1)

```
$ hey -n 1000 -c 50 "https://func-qc-ro6i2l.azurewebsites.net/api/produtos?categoria=moveis"

Summary:
  Total:        7.7423 secs
  Slowest:      4.8960 secs
  Fastest:      0.1340 secs
  Average:      0.3187 secs
  Requests/sec: 129.1603

Latency distribution:
  10%% in 0.1375 secs   50%% in 0.1444 secs   95%% in 2.9488 secs   99%% in 3.8749 secs

Response time histogram (recorte):
  0.134 [1]    |
  0.610 [946]  |■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  ...
  3.467 [32]   |■
  3.944 [8]    |
  4.420 [1]    |
  4.896 [7]    |

Status code distribution:
  [200] 1000 responses
```

946 das 1000 respostas da Function ficaram abaixo de 0,61s; uma cauda de
~48 respostas entre 3s e 4,9s — coerente com instâncias novas subindo sob a
rajada de 50 concorrentes (mesmo fenômeno do cold start do Exercício 1.3,
desta vez sob carga).
