# Bug Report

Security and data-quality issues found while reviewing the Mechanic Shop API before opening it to the public.

All steps to reproduce run against a **local copy** of the app (`python run.py`, which serves at `http://127.0.0.1:5000`). Never run them against the live Render URL.

A bug marked "Fixed in branch harden-rate-limits" stays that way until the branch is merged into `main`.

---

## 1. No rate limit on login

**Where:** `app/blueprints/customers/routes.py`, `POST /customers/login`

**Steps to reproduce:**
1. Start the app locally with `python run.py`.
2. Register a customer with `POST /customers/`.
3. Send `POST /customers/login` with that email and a wrong password 20 times in a row.

**Expected:** After a few failed attempts, further requests are rejected with `429 Too Many Requests`.

**Actual:** Every attempt is processed and returns `401`, so passwords can be guessed without limit.

**Severity:** High

**Status:** Fixed in branch harden-rate-limits (5 per minute, 30 per hour).

---

## 2. No rate limit on registration

**Where:** `app/blueprints/customers/routes.py`, `POST /customers/`

**Steps to reproduce:**
1. Start the app locally with `python run.py`.
2. Send `POST /customers/` 20 times, each with a different email.

**Expected:** After a small number of registrations, further requests are rejected with `429`.

**Actual:** All 20 accounts are created, so a script can fill the database with fake accounts.

**Severity:** Medium

**Status:** Fixed in branch harden-rate-limits (5 per hour, 20 per day).

---

## 3. Vehicle create, update and delete need no login

**Where:** `app/blueprints/vehicles/routes.py`, `POST /vehicles/`, `PUT /vehicles/<id>`, `DELETE /vehicles/<id>`

**Steps to reproduce:**
1. Start the app locally with `python run.py`.
2. Register a customer and add a vehicle for them.
3. Without sending an `Authorization` header, send `PUT /vehicles/<id>` with a different `customer_id`, then `DELETE /vehicles/<id>`.

**Expected:** Requests without a token return `401`. A customer can only add, change or delete their own vehicles (otherwise `403`).

**Actual:** Anyone can create vehicles for any customer, reassign vehicles between customers, and delete any vehicle.

**Severity:** High

**Status:** Fixed in branch harden-rate-limits (token required, ownership checked, rate limited).

---

## 4. Service ticket create, edit and delete need no login

**Where:** `app/blueprints/service_tickets/routes.py`, `POST /service_tickets/`, `PUT /service_tickets/<id>/edit`, `DELETE /service_tickets/<id>`

**Steps to reproduce:**
1. Start the app locally with `python run.py`.
2. Create a customer, a vehicle and a service ticket.
3. Without sending an `Authorization` header, send `PUT /service_tickets/<id>/edit` to add a mechanic, then `DELETE /service_tickets/<id>`.

**Expected:** Changing or deleting a ticket requires a login token.

**Actual:** Anyone can create, edit or delete any service ticket. The harden-rate-limits branch adds rate limits to these routes, which slows abuse but does not require a login.

**Severity:** High

**Status:** Open

---

## 5. Inventory update and delete need no login

**Where:** `app/blueprints/inventory/routes.py`, `PUT /inventory/<id>`, `DELETE /inventory/<id>`

**Steps to reproduce:**
1. Start the app locally with `python run.py`.
2. Create an inventory item with `POST /inventory/`.
3. Without sending an `Authorization` header, send `PUT /inventory/<id>` with a new price, then `DELETE /inventory/<id>`.

**Expected:** Changing or deleting inventory requires a login token.

**Actual:** Both requests succeed for anyone. They are rate limited, but not protected.

**Severity:** Medium

**Status:** Open

---

## 6. Customer responses include the password hash

**Where:** `app/blueprints/customers/schemas.py`, the `password` field; visible through `GET /customers/` and `POST /customers/`

**Steps to reproduce:**
1. Start the app locally with `python run.py`.
2. Register a customer with `POST /customers/`.
3. Send `GET /customers/`.

**Expected:** Responses never contain the `password` field.

**Actual:** Each customer in the response includes their password hash, which can be attacked offline.

**Severity:** High

**Status:** Fixed in branch harden-rate-limits (`password` is now `load_only`).

---

## 7. A ticket can pair a customer with another customer's vehicle

**Where:** `app/blueprints/service_tickets/routes.py`, `create_service_ticket` (`POST /service_tickets/`)

**Steps to reproduce:**
1. Start the app locally with `python run.py`.
2. Register customer A and customer B, and add a vehicle for customer B.
3. Send `POST /service_tickets/` with customer A's `customer_id` and customer B's `vehicle_id`.

**Expected:** `400` or `403`, because the vehicle does not belong to that customer.

**Actual:** `201`. The route only checks that the customer and the vehicle each exist, not that they belong together.

**Severity:** Medium

**Status:** Open

---

## 8. Invalid values are accepted

**Where:** The schemas in `app/blueprints/*/schemas.py`. Only email and phone formats are validated today.

**Steps to reproduce:**
1. Start the app locally with `python run.py`.
2. Send any of these:
   1. `POST /inventory/` with `"price": -50`.
   2. `POST /mechanics/` with `"salary": -1000`.
   3. A vehicle create with `"year": -5` and `"VIN": "X"`.
   4. `PUT /service_tickets/<id>/edit` adding an item with `"quantity": -3`.
   5. `POST /customers/` with `"name": ""` and `"password": ""`.
   6. `POST /service_tickets/` with `"service_desc": ""`.

**Expected:** Each request returns `400` with a validation message.

**Actual:** The records are saved with the invalid values.

**Severity:** Medium

**Status:** Open

---

## 9. README claimed Redis caching that is not implemented

**Where:** `README.md`, tech stack table, Performance Features and Project Phases

**Steps to reproduce:**
1. Read the README tech stack table, which listed "Flask-Caching, Redis 6.2.0".
2. Search the app code for `@cache`.

**Expected:** The README describes only what the app does.

**Actual:** No route uses caching. The only `@cache` decorator was commented out, and the configured cache is in-memory (`SimpleCache`), not Redis.

**Severity:** Low

**Status:** Fixed by the README commit in branch harden-rate-limits, once merged.

---

## 10. Mechanic create, update and delete need no login

**Where:** `app/blueprints/mechanics/routes.py`, `POST /mechanics/`, `PUT /mechanics/<id>`, `DELETE /mechanics/<id>`

**Steps to reproduce:**
1. Start the app locally with `python run.py`.
2. Without sending an `Authorization` header, send `POST /mechanics/` to create a mechanic.
3. Send `PUT /mechanics/<id>` to change their salary, then `DELETE /mechanics/<id>`.

**Expected:** Managing mechanics requires a staff or admin login.

**Actual:** Anyone can create, change or delete mechanics. The routes are rate limited, but there is no staff or admin role in the app to protect them with, so a fix needs that role added first.

**Severity:** Medium

**Status:** Open (found during review)
