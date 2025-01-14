import mysql.connector
import clickhouse_driver
import datetime
import os
from tqdm import tqdm
import time

def format_number(n):
    """Formatiert eine Zahl mit Tausendertrennzeichen"""
    return f"{n:,}".replace(",", ".")

class MigrationProgress:
    def __init__(self, total_rows):
        self.total_rows = total_rows
        self.processed_rows = 0
        self.start_time = time.time()
        self.last_update = self.start_time
        self.update_interval = 5  # Sekunden zwischen Updates

    def update(self, batch_size):
        self.processed_rows += batch_size
        current_time = time.time()

        # Nur alle X Sekunden updaten
        if current_time - self.last_update >= self.update_interval:
            self.print_progress()
            self.last_update = current_time

    def print_progress(self):
        elapsed_time = time.time() - self.start_time
        percentage = (self.processed_rows / self.total_rows) * 100

        # Geschwindigkeit berechnen (Datensätze pro Sekunde)
        speed = self.processed_rows / elapsed_time if elapsed_time > 0 else 0

        # Geschätzte verbleibende Zeit
        remaining_rows = self.total_rows - self.processed_rows
        eta = remaining_rows / speed if speed > 0 else 0

        print(f"\nFortschritt: {format_number(self.processed_rows)}/{format_number(self.total_rows)} "
              f"({percentage:.2f}%)")
        print(f"Geschwindigkeit: {format_number(int(speed))} Datensätze/Sekunde")
        print(f"Verstrichene Zeit: {datetime.timedelta(seconds=int(elapsed_time))}")
        print(f"Geschätzte Restzeit: {datetime.timedelta(seconds=int(eta))}")

def wait_for_clickhouse(client, max_attempts=30, delay=2):
    """Wartet, bis Clickhouse verfügbar ist"""
    attempt = 0
    while attempt < max_attempts:
        try:
            client.execute("SELECT 1")
            print("Clickhouse-Verbindung hergestellt!")
            return True
        except Exception as e:
            attempt += 1
            if attempt < max_attempts:
                print(f"Warte auf Clickhouse (Versuch {attempt}/{max_attempts})...")
                time.sleep(delay)
            else:
                print(f"Konnte keine Verbindung zu Clickhouse herstellen nach {max_attempts} Versuchen")
                return False

def check_table_exists(clickhouse_client):
    """Prüft, ob die Tabelle existiert"""
    try:
        result = clickhouse_client.execute('SHOW TABLES LIKE \'PROFILEPRICE\'')
        return len(result) > 0
    except Exception as e:
        print(f"Fehler beim Prüfen der Tabelle: {e}")
        return False

def check_target_empty(clickhouse_client):
    """Prüft, ob die Zieltabelle leer ist"""
    try:
        result = clickhouse_client.execute('SELECT count(*) FROM PROFILEPRICE')
        return result[0][0] == 0
    except Exception as e:
        print(f"Fehler beim Prüfen der Tabelleneinträge: {e}")
        return True

def check_mariadb_target_empty(cursor):
    """Prüft, ob die Zieltabelle in MariaDB leer ist"""
    try:
        cursor.execute('SELECT COUNT(*) FROM PROFILEPRICE')
        result = cursor.fetchone()
        return result[0] == 0
    except Exception as e:
        print(f"Fehler beim Prüfen der MariaDB-Tabelleneinträge: {e}")
        return True

def convert_value(value, column_name):
    """Konvertiert Werte in den korrekten Datentyp"""
    if value is None:
        return None

    try:
        # Spezielle Behandlung für verschiedene Spalten
        if column_name in ['PRICEID', 'ORIGIN_ID', 'ORIGIN_USERID']:
            return int(value) if value is not None else 0  # NOT NULL Felder
        elif column_name in ['PROFILE_PROFILEID', 'CREATOR_USERID',
                           'PRICEVIEW_PRICEVIEWID', 'METAINFOS_ID',
                           'ORIGIN_METAINFOS_ID']:
            return int(value) if value is not None else None  # Nullable Int64
        elif column_name in ['PRICE', 'VAT', 'EXCHANGERATETOEURO']:
            return float(value) if value is not None else 0.0  # NOT NULL Float64
        elif column_name in ['ATTENDANCEPRICE', 'PRICEWITHOUTATTENDANCE']:
            return float(value) if value is not None else None  # Nullable Float64
        elif column_name in ['CREATED', 'DEACTIVATED', 'MODIFIED']:
            return value  # DateTime-Objekte bleiben unverändert
        elif column_name == 'PRICETYPE':
            return int(value)  # Int32
        elif column_name in ['CURRENCY', 'ORIGIN_TOOL']:
            return str(value) if value is not None else ''  # NOT NULL String
        elif column_name == 'COMPANY_COMPANYID':
            return str(value) if value is not None else None  # Nullable String

        return value
    except Exception as e:
        print(f"Fehler bei der Konvertierung von {value} ({type(value)}) für Spalte {column_name}: {e}")
        raise

def migrate_data():
    source_mysql_cursor = None
    source_mysql_conn = None
    target_mariadb_cursor = None
    target_mariadb_conn = None

    try:
        # ClickHouse Verbindung
        clickhouse_client = clickhouse_driver.Client(
            host=os.environ['CLICKHOUSE_HOST'],
            user=os.environ['CLICKHOUSE_USER'],
            password=os.environ['CLICKHOUSE_PASSWORD'],
            database=os.environ['CLICKHOUSE_DATABASE']
        )

        # MariaDB Zielverbindung
        target_mariadb_conn = mysql.connector.connect(
            host=os.environ['MARIADB_TARGET_HOST'],
            user=os.environ['MARIADB_TARGET_USER'],
            password=os.environ['MARIADB_TARGET_PASSWORD'],
            database=os.environ['MARIADB_TARGET_DATABASE']
        )
        target_mariadb_cursor = target_mariadb_conn.cursor()

        # Quell-MariaDB Verbindung
        source_mysql_conn = mysql.connector.connect(
            host=os.environ['MYSQL_HOST'],
            user=os.environ['MYSQL_USER'],
            password=os.environ['MYSQL_PASSWORD'],
            database=os.environ['MYSQL_DATABASE']
        )
        source_mysql_cursor = source_mysql_conn.cursor()


        # Warte auf Clickhouse
        if not wait_for_clickhouse(clickhouse_client):
            raise Exception("Clickhouse ist nicht verfügbar")

        # Prüfe ob Tabelle existiert
        if not check_table_exists(clickhouse_client):
            raise Exception("Tabelle PROFILEPRICE existiert nicht in Clickhouse")

        if not check_target_empty(clickhouse_client):
            print("Clickhouse-Tabelle enthält bereits Daten. Migration wird übersprungen.")
            return

        if not check_mariadb_target_empty(target_mariadb_cursor):
            print("MariaDB-Tabelle enthält bereits Daten. Migration wird übersprungen.")
            return

        print("Zieltabellen sind leer. Starte Migration...")


        # Spaltennamen definieren
        columns = [
            'PRICEID', 'PRICE', 'CREATED', 'PRICETYPE', 'VAT',
            'DEACTIVATED', 'EXCHANGERATETOEURO', 'CURRENCY',
            'PROFILE_PROFILEID', 'CREATOR_USERID', 'COMPANY_COMPANYID',
            'PRICEVIEW_PRICEVIEWID', 'METAINFOS_ID', 'ATTENDANCEPRICE',
            'PRICEWITHOUTATTENDANCE', 'ORIGIN_ID', 'ORIGIN_TOOL',
            'ORIGIN_USERID', 'ORIGIN_METAINFOS_ID', 'MODIFIED'
        ]

        # Batch-Größe
        BATCH_SIZE = 10000

        # Gesamtanzahl der Datensätze ermitteln
        source_mysql_cursor.execute("""
            SELECT COUNT(*)
            FROM PROFILEPRICE
            WHERE CREATED >= '2024-01-01 00:00:00'
            AND CREATED < '2024-02-01 00:00:00'
        """)
        total_rows = source_mysql_cursor.fetchone()[0]

        progress = MigrationProgress(total_rows)

        print(f"Starte Migration von {format_number(total_rows)} Datensätzen...")

        # Daten in Batches verarbeiten
        for offset in tqdm(range(0, total_rows, BATCH_SIZE)):
            query = f"""
                SELECT {', '.join(columns)}
                FROM PROFILEPRICE
                WHERE CREATED >= '2024-01-01 00:00:00'
                AND CREATED < '2024-02-01 00:00:00'
                LIMIT {BATCH_SIZE} OFFSET {offset}
            """
            source_mysql_cursor.execute(query)
            rows = source_mysql_cursor.fetchall()
            progress.update(len(rows))
            progress.print_progress()

            # Daten für ClickHouse aufbereiten
            prepared_data = []
            for row_index, row in enumerate(rows):
                try:
                    processed_row = [
                        convert_value(value, column_name)
                        for value, column_name in zip(row, columns)
                    ]
                    prepared_data.append(processed_row)
                except Exception as e:
                    print(f"Fehler bei Datensatz {offset + row_index}: {e}")
                    print(f"Problematischer Datensatz: {row}")
                    continue

            # In MariaDB einfügen
            if prepared_data:
                placeholders = ', '.join(['(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'] * len(prepared_data))
                flat_values = [item for sublist in prepared_data for item in sublist]

                insert_query = f"""
                    INSERT INTO PROFILEPRICE (
                        {', '.join(columns)}
                    ) VALUES {placeholders}
                """
                target_mariadb_cursor.execute(insert_query, flat_values)
                target_mariadb_conn.commit()

            # In Clickhouse einfügen (bisheriger Code)
            if prepared_data:
                clickhouse_client.execute(
                    f"""
                    INSERT INTO PROFILEPRICE (
                        {', '.join(columns)}
                    ) VALUES
                    """,
                    prepared_data,
                    types_check=True
                )


    except Exception as e:
        print(f"Fehler bei der Migration: {e}")
        raise

    finally:
        if source_mysql_cursor:
            source_mysql_cursor.close()
        if source_mysql_conn:
            source_mysql_conn.close()
        if target_mariadb_cursor:
            target_mariadb_cursor.close()
        if target_mariadb_conn:
            target_mariadb_conn.close()

if __name__ == "__main__":
    # Zeitmessung
    start_time = datetime.datetime.now()
    print(f"Migration gestartet: {start_time}")

    migrate_data()

    end_time = datetime.datetime.now()
    print(f"Migration beendet: {end_time}")
    print(f"Dauer: {end_time - start_time}")
