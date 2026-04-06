import json
import time

from celery import shared_task
from django.conf import settings

from apps.common.models import Country, Region


@shared_task
def test_task():
    time.sleep(3)
    print("Task finished")
    return True


@shared_task
def import_countries_and_regions():
    """Import countries and regions from JSON files into the database."""
    # 1. Load countries
    with open(settings.BASE_DIR / "seeds" / "countries.json") as f:
        countries_data = json.load(f)

    country_map = {}  # json_id -> db_object
    for item in countries_data:
        country, created = Country.objects.get_or_create(
            name=item["name"],
        )
        country_map[item["id"]] = country

    countries_count = len(countries_data)

    # 2. Load regions
    with open(settings.BASE_DIR / "seeds" / "regions.json") as f:
        regions_data = json.load(f)

    regions_count = 0
    for item in regions_data:
        country = country_map.get(item["country_id"])
        if country:
            Region.objects.get_or_create(
                name=item["name"],
                country=country,
            )
            regions_count += 1

    return f"Imported {countries_count} countries and {regions_count} regions"
