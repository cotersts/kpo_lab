import asyncio
import os
import random
import statistics as st
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import httpx


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
DURATION = float(os.getenv("DURATION", "10"))          # seconds
CONCURRENCY = int(os.getenv("CONCURRENCY", "10"))      # workers
TIMEOUT = float(os.getenv("TIMEOUT", "10"))            # seconds
SEED = int(os.getenv("SEED", "42"))

API_PREFIX = "/api"
PRODUCTS = f"{API_PREFIX}/products"
CUSTOMERS = f"{API_PREFIX}/customers"
SALES = f"{API_PREFIX}/sales"


@dataclass
class Stats:
    lat_ms: List[float] = field(default_factory=list)
    ok: int = 0
    fail: int = 0
    codes: Dict[int, int] = field(default_factory=dict)

    def add(self, ms: float, status_code: Optional[int], ok: bool):
        self.lat_ms.append(ms)
        if ok:
            self.ok += 1
        else:
            self.fail += 1
        if status_code is not None:
            self.codes[status_code] = self.codes.get(status_code, 0) + 1

    @property
    def total(self) -> int:
        return self.ok + self.fail


def pct(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


def fmt_ms(x: float) -> str:
    return f"{x:8.1f}"


def safe_median(values: List[float]) -> float:
    return st.median(values) if values else 0.0


def safe_mean(values: List[float]) -> float:
    return st.mean(values) if values else 0.0


def safe_min(values: List[float]) -> float:
    return min(values) if values else 0.0


def safe_max(values: List[float]) -> float:
    return max(values) if values else 0.0


def status_ok(code: int) -> bool:
    return 200 <= code < 400


async def seed_entities(client: httpx.AsyncClient) -> Tuple[Optional[int], Optional[int]]:
    """
    Создаём 1 товар и 1 клиента для продажи.
    .
    """
    product_id = None
    customer_id = None

    sku = f"LOAD-{int(time.time())}-{random.randint(100,999)}"
    prod_payload = {"sku": sku, "name": "Load Product", "category": "Other", "price": 10000.0}

    try:
        r = await client.post(PRODUCTS, json=prod_payload)
        if status_ok(r.status_code):
            product_id = r.json().get("id")
    except Exception:
        pass

    cust_payload = {"name": "Load Customer", "email": f"load_{random.randint(1,999999)}@example.com", "phone": "+70000000000"}
    try:
        r = await client.post(CUSTOMERS, json=cust_payload)
        if status_ok(r.status_code):
            customer_id = r.json().get("id")
    except Exception:
        pass

    return product_id, customer_id


async def op_get_products(client: httpx.AsyncClient) -> httpx.Response:
    q = random.choice(["", "TV", "Load", "Samsung", "Washer"])
    url = PRODUCTS if q == "" else f"{PRODUCTS}?q={httpx.QueryParams({'q': q})['q']}"
    return await client.get(url)


async def op_create_product(client: httpx.AsyncClient) -> httpx.Response:
    sku = f"LOAD-{random.randint(100000,999999)}"
    payload = {"sku": sku, "name": f"Load Gen {sku}", "category": "Other", "price": float(random.randint(1000, 99999))}
    return await client.post(PRODUCTS, json=payload)


async def op_get_sales(client: httpx.AsyncClient) -> httpx.Response:
    return await client.get(SALES)


async def op_create_sale(client: httpx.AsyncClient, product_id: Optional[int], customer_id: Optional[int]) -> httpx.Response:
    # если seed не сработал — попробуем без customer и с product_id=None (скорее всего упадёт, но будет видно в отчёте)
    pid = product_id or 0
    qty = random.randint(1, 3)
    payload = {
        "customer_id": customer_id,
        "items": [{"product_id": pid, "quantity": qty, "unit_price": 10000.0}],
    }
    return await client.post(SALES, json=payload)


async def one_call(
    client: httpx.AsyncClient,
    label: str,
    coro,
    stats_map: Dict[str, Stats],
):
    t0 = time.perf_counter()
    status_code = None
    ok = False
    try:
        r: httpx.Response = await coro
        status_code = r.status_code
        ok = status_ok(r.status_code)
    except Exception:
        ok = False
    dt_ms = (time.perf_counter() - t0) * 1000.0
    stats_map[label].add(dt_ms, status_code, ok)


async def worker(
    wid: int,
    stop_at: float,
    stats_map: Dict[str, Stats],
    product_id: Optional[int],
    customer_id: Optional[int],
):
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
        rnd = random.Random(SEED + wid)

        # веса 
        ops = [
            ("GET /products", lambda: op_get_products(client), 45),
            ("POST /products", lambda: op_create_product(client), 15),
            ("GET /sales", lambda: op_get_sales(client), 25),
            ("POST /sales", lambda: op_create_sale(client, product_id, customer_id), 15),
        ]
        labels = [o[0] for o in ops]
        weights = [o[2] for o in ops]

        while time.perf_counter() < stop_at:
            label = rnd.choices(labels, weights=weights, k=1)[0]
            fn = None
            for (lab, f, _) in ops:
                if lab == label:
                    fn = f
                    break
            await one_call(client, label, fn(), stats_map)


def print_summary(stats_map: Dict[str, Stats], duration_s: float):
    # собираем “итого”
    all_lat = []
    total_ok = total_fail = 0
    total_codes: Dict[int, int] = {}

    for s in stats_map.values():
        all_lat += s.lat_ms
        total_ok += s.ok
        total_fail += s.fail
        for code, cnt in s.codes.items():
            total_codes[code] = total_codes.get(code, 0) + cnt

    total = total_ok + total_fail
    rps = total / duration_s if duration_s > 0 else 0.0

    print("\n==================== SUMMARY ====================")
    print(f"Base URL     : {BASE_URL}")
    print(f"Duration     : {duration_s:.1f}s")
    print(f"Concurrency  : {CONCURRENCY}")
    print(f"Total req    : {total}")
    print(f"OK / FAIL    : {total_ok} / {total_fail}")
    print(f"RPS          : {rps:.2f}")
    if total_codes:
        codes_str = ", ".join(f"{k}:{v}" for k, v in sorted(total_codes.items()))
        print(f"Status codes : {codes_str}")

    print("\nLatency (ms):")
    print(f"  min   : {fmt_ms(safe_min(all_lat))}")
    print(f"  avg   : {fmt_ms(safe_mean(all_lat))}")
    print(f"  med   : {fmt_ms(safe_median(all_lat))}")
    print(f"  p90   : {fmt_ms(pct(all_lat, 90))}")
    print(f"  p95   : {fmt_ms(pct(all_lat, 95))}")
    print(f"  p99   : {fmt_ms(pct(all_lat, 99))}")
    print(f"  max   : {fmt_ms(safe_max(all_lat))}")

    print("\n==================== FUNCTION (per endpoint) ====================")
    header = f"{'function':<18} {'req':>6} {'ok':>6} {'fail':>6} {'rps':>8} {'avg(ms)':>10} {'p95(ms)':>10}"
    print(header)
    print("-" * len(header))
    for label, s in stats_map.items():
        rps_i = s.total / duration_s if duration_s > 0 else 0.0
        print(
            f"{label:<18} {s.total:>6} {s.ok:>6} {s.fail:>6} "
            f"{rps_i:>8.2f} {safe_mean(s.lat_ms):>10.1f} {pct(s.lat_ms,95):>10.1f}"
        )

    print("\n==================== FUNCTION DETAILS ====================")
    for label, s in stats_map.items():
        print(f"\n--- {label} ---")
        if s.total == 0:
            print("no data")
            continue
        print(f"req: {s.total} | ok: {s.ok} | fail: {s.fail}")
        if s.codes:
            codes_str = ", ".join(f"{k}:{v}" for k, v in sorted(s.codes.items()))
            print(f"codes: {codes_str}")
        print("latency ms:")
        print(f"  min : {fmt_ms(safe_min(s.lat_ms))}")
        print(f"  avg : {fmt_ms(safe_mean(s.lat_ms))}")
        print(f"  med : {fmt_ms(safe_median(s.lat_ms))}")
        print(f"  p90 : {fmt_ms(pct(s.lat_ms, 90))}")
        print(f"  p95 : {fmt_ms(pct(s.lat_ms, 95))}")
        print(f"  p99 : {fmt_ms(pct(s.lat_ms, 99))}")
        print(f"  max : {fmt_ms(safe_max(s.lat_ms))}")


async def main():
    random.seed(SEED)

    labels = ["GET /products", "POST /products", "GET /sales", "POST /sales"]
    stats_map: Dict[str, Stats] = {k: Stats() for k in labels}

    # seed делаем отдельным клиентом
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
        product_id, customer_id = await seed_entities(client)

    t0 = time.perf_counter()
    stop_at = t0 + DURATION

    tasks = [
        asyncio.create_task(worker(i, stop_at, stats_map, product_id, customer_id))
        for i in range(CONCURRENCY)
    ]
    await asyncio.gather(*tasks)

    duration_s = time.perf_counter() - t0
    print_summary(stats_map, duration_s)


if __name__ == "__main__":
    asyncio.run(main())
