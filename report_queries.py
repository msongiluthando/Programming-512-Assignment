WEEKDAYS = [
    "Sunday", "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday"
]


def fetch_all_bookings(connection, campus_id=None):
    where = "WHERE b.campus_id = ?" if campus_id is not None else ""
    params = (campus_id,) if campus_id is not None else ()

    return connection.execute(f"""
        SELECT b.booking_id, c.campus_name, u.full_name,
               r.resource_name, b.booking_date, b.start_time,
               b.duration_minutes, b.status
        FROM bookings b
        JOIN campuses c ON c.campus_id = b.campus_id
        JOIN users u ON u.user_id = b.lecturer_id
        JOIN resources r ON r.resource_id = b.resource_id
        {where}
        ORDER BY b.booking_date DESC, b.start_time DESC
    """, params).fetchall()


def fetch_monthly_trends(connection, campus_id=None):
    where = "WHERE c.campus_id = ?" if campus_id is not None else ""
    params = (campus_id,) if campus_id is not None else ()

    return connection.execute(f"""
        SELECT c.campus_name,
               substr(b.booking_date, 1, 7) AS month,
               SUM(CASE WHEN b.status = 'active' THEN 1 ELSE 0 END),
               SUM(CASE WHEN b.status = 'cancelled' THEN 1 ELSE 0 END),
               AVG(CASE WHEN b.status = 'active'
                        THEN b.duration_minutes END),
               AVG(CASE WHEN b.status = 'active'
                        THEN b.duration_minutes * 100.0 / c.max_duration
                   END)
        FROM campuses c
        JOIN bookings b ON b.campus_id = c.campus_id
        {where}
        GROUP BY c.campus_id, c.campus_name, month
        ORDER BY c.campus_name, month
    """, params).fetchall()


def fetch_weekday_usage(connection, campus_id=None):

    where = "AND c.campus_id = ?" if campus_id is not None else ""
    params = (campus_id,) if campus_id is not None else ()

    rows = connection.execute(f"""
        SELECT c.campus_name,
               CAST(strftime('%w', b.booking_date) AS INTEGER),
               COUNT(*) AS total
        FROM campuses c
        JOIN bookings b ON b.campus_id = c.campus_id
        WHERE b.status = 'active'
          {where}
        GROUP BY c.campus_id, c.campus_name,
                 strftime('%w', b.booking_date)
        ORDER BY c.campus_name, total DESC
    """, params).fetchall()

    return [(campus, WEEKDAYS[day], total) for campus, day, total in rows]
