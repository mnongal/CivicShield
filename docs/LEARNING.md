# Learn Python through CivicShield

## 1. A model describes valid input

Open `app/schemas.py`. `Situation` is a class with typed fields. `household_size: int` describes an integer. `Field(ge=1)` rejects zero. `bool | None` represents three possibilities: yes, no and unknown. FastAPI validates submitted JSON with this model.

Try it: send household size zero through `/docs`. Read the 422 validation response. Then run `python -m pytest tests/test_api.py -q`.

## 2. A function turns inputs into a result

Open `evaluate()` in `app/rules.py`. It receives a situation, a program and an optional date. `if` statements choose a result, and `return` ends the function. It has no network calls or database writes. Identical inputs and evaluation date produce identical results.

Try it: read the income boundary test. Why does `23475` match but `23475.01` fail? Money uses `Decimal` to avoid binary floating-point rounding inside the rule.

## 3. A dataclass groups related values

`Decision` holds `status`, `reasons` and `missing`. `@dataclass` generates the constructor. `frozen=True` stops accidental field reassignment. Tuples keep the reason collections immutable too. The explanation function receives this result rather than deciding eligibility again.

Try it: run `python -m pytest tests/test_rules.py -k explanation -q`. The test proves that an attempted status change raises an error.

## 4. Lists and dictionaries build API responses

In `main.py`, a list comprehension evaluates every program. Each explanation is a dictionary with keys such as `source_url` and `next_step`. FastAPI converts these into JSON. `sort(key=...)` arranges resources and possible matches before review results.

Try it: compare the response in `/docs` with the cards in the browser. Find which dictionary fields each card uses in `static/app.js`.

## 5. A database session has a lifetime

In `database.py`, `with Session(engine) as session:` opens a session and closes it when the block ends. `session.merge()` inserts or updates seed rows, and `commit()` saves the changes. Only public program records are stored.

Try it: restart the app twice and call `/api/health`. Why does the count remain seven? Read the test for idempotent seeding.

## 6. A decorator connects a URL to a function

`@app.post('/api/screen')` tells FastAPI which function handles that route. The typed argument tells it how to validate the JSON body. A plain returned dictionary becomes the HTTP response.

Your next small exercise: add a clearly labeled `screening_scope` field to an explanation and display it in the expanded card. Keep the rule decision unchanged, then run the tests. This is a safe first change across Python and the frontend.
