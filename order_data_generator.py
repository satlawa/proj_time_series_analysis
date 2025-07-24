import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, time
from typing import List

from geopy.distance import geodesic
import numpy as np


@dataclass
class GeoCoordinate:
    latitude: float
    longitude: float


@dataclass
class LoadingHours:
    day_of_week: int  # 1=Monday ... 7=Sunday
    from_time: time
    to_time: time


@dataclass
class RequestedTimeOfArrival:
    from_datetime: datetime
    to_datetime: datetime


@dataclass
class Milestone:
    location: GeoCoordinate
    loading_hours: LoadingHours
    rta: RequestedTimeOfArrival


@dataclass
class Order:
    trailer_type: str
    milestones: List[Milestone] = field(default_factory=list)


# List of major European city coordinates with simple weights (population approx)
CITY_COORDS = [
    ((52.5200, 13.4050), 10),  # Berlin
    ((48.8566, 2.3522), 10),   # Paris
    ((51.5074, -0.1278), 9),   # London
    ((50.1109, 8.6821), 7),    # Frankfurt
    ((45.4642, 9.1900), 6),    # Milan
    ((52.3676, 4.9041), 6),    # Amsterdam
    ((41.9028, 12.4964), 6),   # Rome
    ((40.4168, -3.7038), 6),   # Madrid
    ((52.2297, 21.0122), 5),   # Warsaw
    ((59.3293, 18.0686), 5),   # Stockholm
    ((55.7558, 37.6173), 5),   # Moscow
    ((50.0755, 14.4378), 4),   # Prague
    ((47.4979, 19.0402), 4),   # Budapest
    ((53.3498, -6.2603), 3),   # Dublin
    ((60.1699, 24.9384), 2),   # Helsinki
]

CITY_WEIGHTS = [w for _, w in CITY_COORDS]
CITY_POINTS = [pt for pt, _ in CITY_COORDS]



def choose_city_coordinate() -> GeoCoordinate:
    index = random.choices(range(len(CITY_POINTS)), weights=CITY_WEIGHTS, k=1)[0]
    lat, lon = CITY_POINTS[index]
    # add small jitter to avoid identical coordinates
    lat += random.uniform(-0.2, 0.2)
    lon += random.uniform(-0.2, 0.2)
    return GeoCoordinate(latitude=lat, longitude=lon)


# Europe bounding box used for more random locations
LAT_MIN, LAT_MAX = 35.0, 70.0
LON_MIN, LON_MAX = -10.0, 40.0


def random_coordinate_europe() -> GeoCoordinate:
    lat = random.uniform(LAT_MIN, LAT_MAX)
    lon = random.uniform(LON_MIN, LON_MAX)
    return GeoCoordinate(latitude=lat, longitude=lon)


def generate_location() -> GeoCoordinate:
    # 80% probability to be near major city (densely populated)
    if random.random() < 0.8:
        return choose_city_coordinate()
    return random_coordinate_europe()


# Loading hours generation

def generate_loading_hours() -> LoadingHours:
    # Day of week selection
    day_prob = random.random()
    if day_prob < 0.995:
        day_of_week = random.randint(1, 5)  # Monday-Friday
    elif day_prob < 0.9995:
        day_of_week = 6  # Saturday
    else:
        day_of_week = 7  # Sunday

    hour_prob = random.random()
    if hour_prob < 0.5:
        from_hour, to_hour = 8, 16
    elif hour_prob < 0.6:
        from_hour, to_hour = 0, 24
    else:
        from_hour = random.randint(5, 9)
        to_hour = int(np.clip(random.gauss(18, 2), 13, 22))
        if to_hour <= from_hour:
            to_hour = from_hour + 1
    return LoadingHours(
        day_of_week=day_of_week,
        from_time=time(hour=from_hour),
        to_time=time(hour=to_hour if to_hour < 24 else 23, minute=59 if to_hour >= 24 else 0),
    )


# Helper to pick a datetime within 14 days for a given weekday

def random_date_for_weekday(weekday: int) -> datetime:
    now = datetime.utcnow()
    for _ in range(100):
        dt = now + timedelta(days=random.randint(0, 14))
        if dt.isoweekday() == weekday:
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    # fallback if not found within 14 days
    dt = now + timedelta(days=random.randint(0, 14))
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


# RTA generation respecting loading hours

def generate_rta(loading: LoadingHours) -> RequestedTimeOfArrival:
    scenario = random.random()
    base_date = random_date_for_weekday(loading.day_of_week)
    if scenario < 0.5:
        # full loading hours on same day
        start_dt = datetime.combine(base_date.date(), loading.from_time)
        end_dt = datetime.combine(base_date.date(), loading.to_time)
    elif scenario < 0.7:
        # from == to at some time within loading hours
        start_hour = random.randint(loading.from_time.hour, loading.to_time.hour - 1)
        start_dt = datetime.combine(base_date.date(), time(start_hour))
        end_dt = start_dt
    elif scenario < 0.95:
        # same day shorter than full hours
        start_hour = random.randint(loading.from_time.hour, loading.to_time.hour - 1)
        end_hour = random.randint(start_hour + 1, loading.to_time.hour)
        start_dt = datetime.combine(base_date.date(), time(start_hour))
        end_dt = datetime.combine(base_date.date(), time(end_hour if end_hour < 24 else 23, 59 if end_hour >= 24 else 0))
    else:
        # spanning multiple days up to 4 days
        start_hour = random.randint(loading.from_time.hour, loading.to_time.hour - 1)
        start_dt = datetime.combine(base_date.date(), time(start_hour))
        days_span = random.randint(1, 4)
        end_dt = start_dt + timedelta(days=days_span)
        end_dt = end_dt.replace(hour=loading.to_time.hour, minute=loading.to_time.minute)
    return RequestedTimeOfArrival(from_datetime=start_dt, to_datetime=end_dt)


# Compute the earliest datetime within loading hours that is >= given dt

def next_within_loading_hours(dt: datetime, loading: LoadingHours) -> datetime:
    current = dt
    while True:
        if current.isoweekday() == loading.day_of_week:
            start = datetime.combine(current.date(), loading.from_time)
            end = datetime.combine(current.date(), loading.to_time)
            if current <= start:
                return start
            if start <= current <= end:
                return current
        current += timedelta(days=1)


def generate_order() -> Order:
    trailer_type = "standard" if random.random() < 0.85 else "mega"
    # Milestone count distribution
    m_rand = random.random()
    if m_rand < 0.95:
        count = 2
    elif m_rand < 0.995:
        count = 3
    elif m_rand < 0.999:
        count = 4
    else:
        count = 5

    milestones = []
    prev_location = None
    prev_end = None
    for _ in range(count):
        location = generate_location()
        loading = generate_loading_hours()
        rta = generate_rta(loading)
        if prev_location is not None:
            # ensure reachability
            dist_km = geodesic((prev_location.latitude, prev_location.longitude), (location.latitude, location.longitude)).km
            travel_hours = dist_km / 70.0  # assume 70km/h average
            earliest_start = prev_end + timedelta(hours=travel_hours)
            start_candidate = next_within_loading_hours(earliest_start, loading)
            # adjust rta times accordingly
            span = rta.to_datetime - rta.from_datetime
            rta.from_datetime = start_candidate
            rta.to_datetime = start_candidate + span
        prev_location = location
        prev_end = rta.to_datetime
        milestones.append(Milestone(location=location, loading_hours=loading, rta=rta))
    return Order(trailer_type=trailer_type, milestones=milestones)


__all__ = [
    "GeoCoordinate",
    "LoadingHours",
    "RequestedTimeOfArrival",
    "Milestone",
    "Order",
    "generate_order",
]
