"""
seed.py - Populate the Mechanic Shop API database with realistic demo data.

WHAT THIS DOES
    Creates customers, vehicles, mechanics, inventory items, and service
    tickets (with mechanic assignments and inventory usage) so the live
    demo has something to show besides an empty database.

SAFETY / IDEMPOTENCY
    On startup, this script counts existing rows in the tables it seeds.
      - If all of them are empty, it seeds directly.
      - If any of them already have data, it prints the current counts
        and requires you to type "reset" at an interactive prompt before
        it wipes those tables and reseeds. Anything else cancels with no
        changes made.
      - With the --reset flag, the prompt is skipped and the tables are
        wiped and reseeded automatically. This exists for the scheduled
        reseed GitHub Action (.github/workflows/reseed.yml), where nobody is
        there to type "reset".
    This script only touches the app's own tables: customers, vehicles,
    mechanics, inventory_items, service_tickets, service_inventory, and
    the service_mechanics association table. It does not touch schema,
    migrations, or any other database.

TARGET DATABASE
    This script builds the app with ProductionConfig, which reads
    DATABASE_URL exactly the way flask_app.py does (see config.py's
    get_database_uri()). If DATABASE_URL is not set, ProductionConfig
    silently falls back to a local sqlite file. To prevent accidentally
    seeding the wrong database, this script REFUSES to run unless
    DATABASE_URL is set and does not look like a sqlite URL.

USAGE
    Put DATABASE_URL="<your Supabase connection string>" in a local .env
    file (gitignored, never committed) and run:
        python seed.py            # asks before wiping existing data
        python seed.py --reset    # wipes and reseeds without asking

    (See README "Demo Data" section for the exact Supabase connection
    string format and where to find it.)

NOTES ON MODEL LIMITATIONS (confirmed against app/models.py before writing
this script, not assumed):
    - Mechanic has no password field in the current model, so mechanics
      are seeded without one, matching how the app itself creates them.
    - ServiceTicket has no status field, so there is no open/completed
      status to vary here. Variation instead comes from service_date
      and service_desc.
    - Vehicle.VIN has no format validation at the schema level (just
      "required"), but this script still generates realistic 17-character
      VINs.
"""

import argparse
import os
import random
import sys
from datetime import date, timedelta

from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
load_dotenv()

from app import create_app
from app.models import (
    db,
    Customer,
    Vehicle,
    Mechanic,
    InventoryItem,
    ServiceTicket,
    ServiceInventory,
    service_mechanics,
)


# ---------------------------------------------------------------------------
# Guard: make sure we are actually targeting Supabase, not local SQLite
# ---------------------------------------------------------------------------
def confirm_target_database():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print(
            "ERROR: DATABASE_URL is not set.\n"
            "ProductionConfig falls back to a local SQLite file "
            "(sqlite:///production.db) when DATABASE_URL is missing, and "
            "this script refuses to seed that fallback by accident.\n\n"
            "Set DATABASE_URL to your Supabase connection string first, e.g.:\n"
            '  export DATABASE_URL="postgresql://postgres:[email protected]:5432/postgres"\n'
        )
        sys.exit(1)

    if database_url.startswith("sqlite"):
        print(
            f"ERROR: DATABASE_URL is set to a SQLite database ({database_url}).\n"
            "This script is meant to seed Supabase. Point DATABASE_URL at your "
            "Supabase Postgres connection string instead."
        )
        sys.exit(1)

    # Mask the password before printing, same convention as config.mask_database_uri
    import re

    masked = re.sub(r"(://[^:/@]+:)[^@]+(@)", r"\1****\2", database_url)
    print(f"Target database: {masked}")


# ---------------------------------------------------------------------------
# Seed data definitions
# ---------------------------------------------------------------------------
SEED_EMAIL_DOMAIN = "seed.mechanicshop.demo"

CUSTOMERS = [
    {"name": "Maria Alvarez", "phone": "555-201-3344"},
    {"name": "James Whitfield", "phone": "555-201-9021"},
    {"name": "Priya Natarajan", "phone": "555-201-5567"},
    {"name": "Devon Brooks", "phone": "555-201-7788"},
    {"name": "Lena Kowalski", "phone": "555-201-4432"},
    {"name": "Marcus Reyes", "phone": "555-201-6690"},
    {"name": "Sofia Castellano", "phone": "555-201-1123"},
]

MECHANICS = [
    {"name": "Tony Marchetti", "phone": "555-301-1010", "salary": 58000.00},
    {"name": "Dana Okafor", "phone": "555-301-2020", "salary": 61500.00},
    {"name": "Rick Sullenberger", "phone": "555-301-3030", "salary": 55000.00},
    {"name": "Yuki Tanaka", "phone": "555-301-4040", "salary": 63000.00},
]

VEHICLE_CHOICES = [
    ("Honda", "Civic"),
    ("Toyota", "Camry"),
    ("Ford", "F-150"),
    ("Chevrolet", "Malibu"),
    ("Subaru", "Outback"),
    ("Honda", "CR-V"),
    ("Nissan", "Altima"),
    ("Jeep", "Grand Cherokee"),
    ("Mazda", "CX-5"),
    ("Kia", "Sportage"),
]

INVENTORY_ITEMS = [
    {"name": "Oil Filter", "price": 12.99},
    {"name": "Synthetic Motor Oil (5qt)", "price": 34.50},
    {"name": "Brake Pads (Front Set)", "price": 54.99},
    {"name": "Brake Pads (Rear Set)", "price": 49.99},
    {"name": "Spark Plug", "price": 8.25},
    {"name": "Air Filter", "price": 18.75},
    {"name": "Cabin Air Filter", "price": 15.50},
    {"name": "Serpentine Belt", "price": 27.00},
    {"name": "Wiper Blade Pair", "price": 22.40},
    {"name": "Car Battery", "price": 129.99},
]

SERVICE_DESCRIPTIONS = [
    "Routine oil change and multi-point inspection",
    "Brake pad replacement, front axle",
    "Brake pad replacement, all four wheels",
    "Spark plug replacement and engine tune-up",
    "Battery replacement and charging system check",
    "Serpentine belt replacement",
    "Air filter and cabin air filter replacement",
    "Wiper blade replacement and fluid top-off",
    "Pre-purchase inspection",
    "Check engine light diagnostic",
    "Annual maintenance service",
    "Tire rotation and brake inspection",
]

SEED_TABLES_IN_DELETE_ORDER = [
    "service_inventory",
    "service_mechanics",
    "service_tickets",
    "inventory_items",
    "vehicles",
    "mechanics",
    "customers",
]


def random_vin(index):
    """Generate a plausible-looking, unique 17-character VIN."""
    chars = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"  # excludes I, O, Q like real VINs
    rng = random.Random(1000 + index)
    return "".join(rng.choice(chars) for _ in range(17))


# ---------------------------------------------------------------------------
# Existing-data check
# ---------------------------------------------------------------------------
def existing_row_counts():
    return {
        "customers": db.session.query(Customer).count(),
        "vehicles": db.session.query(Vehicle).count(),
        "mechanics": db.session.query(Mechanic).count(),
        "inventory_items": db.session.query(InventoryItem).count(),
        "service_tickets": db.session.query(ServiceTicket).count(),
        "service_inventory": db.session.query(ServiceInventory).count(),
    }


def wipe_seeded_tables():
    print("Wiping existing rows from all seeded tables...")
    db.session.execute(ServiceInventory.__table__.delete())
    db.session.execute(service_mechanics.delete())
    db.session.execute(ServiceTicket.__table__.delete())
    db.session.execute(InventoryItem.__table__.delete())
    db.session.execute(Vehicle.__table__.delete())
    db.session.execute(Mechanic.__table__.delete())
    db.session.execute(Customer.__table__.delete())
    db.session.commit()
    print("Existing rows removed.\n")


def check_existing_data_and_confirm(auto_reset=False):
    counts = existing_row_counts()
    total = sum(counts.values())
    if total == 0:
        return  # clean database, nothing to confirm

    print("Existing data found in one or more tables this script seeds:")
    for table, count in counts.items():
        print(f"  {table}: {count}")

    if auto_reset:
        print("\n--reset was passed, so skipping the confirmation prompt.")
        wipe_seeded_tables()
        return

    print(
        "\nRunning this script again will not append duplicate demo rows on "
        "top of these. To wipe ONLY the tables listed above and reseed from "
        "scratch, type 'reset' below. Anything else cancels with no changes."
    )
    answer = input("Type 'reset' to wipe and reseed, or anything else to cancel: ").strip()
    if answer.lower() != "reset":
        print("Cancelled. No changes were made.")
        sys.exit(0)
    wipe_seeded_tables()


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------
def seed():
    inserted = {}

    # Customers
    customers = []
    for i, c in enumerate(CUSTOMERS):
        email = f"{c['name'].lower().replace(' ', '.')}@{SEED_EMAIL_DOMAIN}"
        customer = Customer(
            name=c["name"],
            email=email,
            phone=c["phone"],
            password=generate_password_hash("DemoPass123!"),
        )
        db.session.add(customer)
        customers.append(customer)
    db.session.flush()  # assigns IDs without committing yet
    inserted["customers"] = len(customers)

    # Vehicles: 1-2 per customer
    vehicles = []
    vin_counter = 0
    for customer in customers:
        num_vehicles = random.Random(customer.id).choice([1, 1, 2])  # mostly 1, sometimes 2
        for _ in range(num_vehicles):
            make, model = random.choice(VEHICLE_CHOICES)
            year = random.randint(2014, 2024)
            vehicle = Vehicle(
                VIN=random_vin(vin_counter),
                make=make,
                model=model,
                year=year,
                customer_id=customer.id,
            )
            vin_counter += 1
            db.session.add(vehicle)
            vehicles.append(vehicle)
    db.session.flush()
    inserted["vehicles"] = len(vehicles)

    # Mechanics (no password field on this model)
    mechanics = []
    for m in MECHANICS:
        email = f"{m['name'].lower().replace(' ', '.')}@{SEED_EMAIL_DOMAIN}"
        mechanic = Mechanic(
            name=m["name"],
            email=email,
            phone=m["phone"],
            salary=m["salary"],
        )
        db.session.add(mechanic)
        mechanics.append(mechanic)
    db.session.flush()
    inserted["mechanics"] = len(mechanics)

    # Inventory items
    items = []
    for item in INVENTORY_ITEMS:
        inventory_item = InventoryItem(name=item["name"], price=item["price"])
        db.session.add(inventory_item)
        items.append(inventory_item)
    db.session.flush()
    inserted["inventory_items"] = len(items)

    # Service tickets: pick a vehicle (and its owning customer), assign
    # 1-3 mechanics and 1-4 inventory items with quantities, vary dates.
    today = date.today()
    num_tickets = 10
    tickets = []
    ticket_item_rows = 0
    for i in range(num_tickets):
        vehicle = vehicles[i % len(vehicles)]
        desc = SERVICE_DESCRIPTIONS[i % len(SERVICE_DESCRIPTIONS)]
        days_ago = random.randint(1, 240)
        ticket = ServiceTicket(
            vehicle_id=vehicle.id,
            customer_id=vehicle.customer_id,
            service_date=today - timedelta(days=days_ago),
            service_desc=desc,
        )
        db.session.add(ticket)
        db.session.flush()  # need ticket.id for associations below

        # Assign 1-3 mechanics
        rng = random.Random(500 + i)
        assigned_mechanics = rng.sample(mechanics, k=rng.randint(1, 3))
        ticket.mechanics.extend(assigned_mechanics)

        # Assign 1-4 inventory items with quantities
        chosen_items = rng.sample(items, k=rng.randint(1, 4))
        for item in chosen_items:
            entry = ServiceInventory(
                service_id=ticket.id,
                item_id=item.id,
                quantity=rng.randint(1, 3),
            )
            db.session.add(entry)
            ticket_item_rows += 1

        tickets.append(ticket)

    db.session.flush()
    inserted["service_tickets"] = len(tickets)
    inserted["service_inventory"] = ticket_item_rows

    db.session.commit()
    return inserted


def parse_args():
    parser = argparse.ArgumentParser(
        description="Seed the Mechanic Shop API database with demo data."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help=(
            "If the seeded tables already contain data, wipe them and reseed "
            "without asking for confirmation (for scheduled, non-interactive runs)."
        ),
    )
    return parser.parse_args()


def main():
    args = parse_args()
    confirm_target_database()

    app = create_app("ProductionConfig")
    with app.app_context():
        check_existing_data_and_confirm(auto_reset=args.reset)
        inserted = seed()

    print("Seed complete. Rows inserted:")
    for table, count in inserted.items():
        print(f"  {table}: {count}")


if __name__ == "__main__":
    main()
