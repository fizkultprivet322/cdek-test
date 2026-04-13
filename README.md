- app.py - FastAPI-сервис с эндпоинтами:
  - GET / - OK
  - GET /metrics - Prometheus-compatible text/plain с http_requests_total и http_errors_total
- Dockerfile - сборка и запуск приложения на порту 8000, запуск от непривилегированного пользователя.
- docker-compose.yml - запуск сервиса с пробросом 8000:8000, restart: always и healthcheck.
- .github/workflows/ci.yml - CI для main: build, run, проверки curl, остановка контейнера.
- autoheal.sh - фоновая проверка доступности каждые 30 секунд, рестарт через docker compose restart и логирование в autoheal.log.

# Результаты локальной проверки
- Поднятие сервиса:
```bash
docker compose up -d --build
```
- Проверка корневого эндпоинта:
```bash
curl http://127.0.0.1:8000/
```
```text
OK
```
- Проверка метрик:
```bash
curl http://127.0.0.1:8000/metrics
```
```text
# HELP http_requests_total Total requests
# TYPE http_requests_total counter
http_requests_total 2
# HELP http_errors_total Total errors
# TYPE http_errors_total counter
http_errors_total 0
```
- Имитация падения контейнера:
```bash
docker kill sre-trainee-web
sleep 40
curl http://127.0.0.1:8000/
```
```text
OK
```
- Проверка лога autoheal:
```bash
cat autoheal.log
```
```text
2026-04-13T20:09:41Z service unavailable; running docker compose restart
```

## Ответы на вопросы

### 1) Какие метрики добавить в production (кроме http_requests_total и http_errors_total)?

1. http_request_duration_seconds - latency p50/p95/p99.
2. http_requests_in_flight - число активных запросов.
3. process_resident_memory_bytes - потребление RAM.
4. process_cpu_seconds_total - CPU-время процесса.
5. container_restarts_total - перезапуски контейнера (индикатор нестабильности).

### 2) Как проверял автоматическое восстановление при падении контейнера?

Использовал принудительное завершение контейнера:

```bash
docker kill sre-trainee-web
```

После этого:

- docker compose ps показал, что контейнер был перезапущен политикой restart: always.
- при работе ./autoheal.sh в autoheal.log появляется запись с timestamp о срабатывании docker compose restart.
- curl http://localhost:8000/ снова возвращает OK.

Пример строки лога:

```
2026-04-13T18:25:31Z service unavailable; running docker compose restart
```

### 4) SLI / SLO

SLI: доступность сервиса (доля успешных ответов GET / за период).

SLO: 99.9% месячной доступности.

Расчёт допустимого простоя в 30-дневном месяце:

- всего минут: 30 × 24 × 60 = 43200
- бюджет ошибки: 0.1% = 0.001
- допустимый простой: 43200 × 0.001 = 43.2 минуты

Итого: при SLO 99.9% можно допустить примерно 43 минуты 12 секунд недоступности в месяц.

### 5) Постмортем: «Сервис не отвечал 15 минут из-за утечки памяти»

Во время штатной нагрузки сервис перестал отвечать из-за роста потребления памяти и последующего OOM-kill контейнера. Инцидент был обнаружен по алерту на недоступность эндпоинта / и по всплеску рестартов контейнера. Дежурный инженер подтвердил причину через логи контейнера и метрики памяти процесса. Для восстановления сервис перезапустили, а проблемный участок кода с накоплением объектов в памяти был исправлен и задеплоен. Дополнительно добавили лимиты памяти контейнера и алерты на рост RSS, чтобы ловить деградацию до падения. Чтобы исключить повторение, внедрили нагрузочный тест в CI и регулярный профилинг памяти перед релизом.

## CI

Workflow запускается при каждом push в main и выполняет:

1. docker build
2. docker run
3. curl http://localhost:8000/ (ожидается OK)
4. curl http://localhost:8000/metrics (проверка наличия обеих метрик)
5. остановка контейнера

```text
https://github.com/fizkultprivet322/cdek-test/actions/runs/24365281210/job/71155272994
```
