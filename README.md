## Setup

1. Kopiere .env.example nach .env und passe die Werte an
2. Ändere in main.py ggfls die zeitliche Einschränkung der Queries:
```sql
WHERE CREATED >= '2024-01-01 00:00:00'
AND CREATED < '2024-02-01 00:00:00'
```
3. Führe `docker-compose up --build` aus

## Testing
- Verbindung zur MariaDB via Port 3306
- Verbindung zur ClickhouseDB via Port 8123, 9000 oder in der Play-Console: http://localhost:8123/play
