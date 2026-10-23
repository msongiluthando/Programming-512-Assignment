def to_minutes(time_text):
    hours, minutes = time_text.split(":")
    return int(hours) * 60 + int(minutes)


def to_text(total_minutes):
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


class CampusPolicy:

    def __init__(self, campus_name, max_duration, opening_time, closing_time):
        self.campus_name = campus_name
        self.max_duration = max_duration
        self.opening_time = opening_time
        self.closing_time = closing_time

        self._rules = [self._check_duration, self._check_hours]

    @property
    def opening_minutes(self):
        return to_minutes(self.opening_time)

    @property
    def closing_minutes(self):
        return to_minutes(self.closing_time)

    def describe(self):
        return (
            f"{self.campus_name}: maximum {self.max_duration} minutes "
            f"per booking; bookings only between "
            f"{self.opening_time} and {self.closing_time}."
        )

    def validate(self, start_minutes, duration_minutes):
        for rule in self._rules:
            problem = rule(start_minutes, duration_minutes)
            if problem:
                return problem
        return None


    def _check_duration(self, start_minutes, duration_minutes):
        if duration_minutes > self.max_duration:
            return (
                f"This campus allows bookings up to "
                f"{self.max_duration} minutes."
            )
        return None

    def _check_hours(self, start_minutes, duration_minutes):
        end_minutes = start_minutes + duration_minutes
        if (
            start_minutes < self.opening_minutes
            or end_minutes > self.closing_minutes
        ):
            return (
                f"Bookings must fall within campus hours: "
                f"{self.opening_time}–{self.closing_time}."
            )
        return None
