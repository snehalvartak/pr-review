import csv
import io


def to_csv(rows):
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0]) if rows else [])
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()
