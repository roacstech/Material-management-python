from typing import Any, Dict, List, Optional, Tuple
from datetime import date, datetime, timedelta

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

DEFAULT_LOOKBACK_DAYS = 30
DEFAULT_SAFETY_DAYS = 2
DEFAULT_LEAD_TIME_DAYS = 1
PERIODS = {
    "daily": 1,
    "weekly": 7,
    "monthly": 30,
}


def pos(value: Any) -> float:
    return max(0.0, float(value or 0))


def fix(value: Any, digits: int = 3) -> float:
    return round(float(value or 0), digits)


def safe_divide(numerator: float, denominator: float) -> float:
    if denominator is None or denominator <= 0:
        return 0.0
    return float(numerator) / float(denominator)


urgency_order = {
    "Out of Stock": 0,
    "Critical": 1,
    "Order Now": 2,
    "Low": 3,
    "OK": 4,
}


class ForecastService:
    @staticmethod
    def _load_forecast_data(
        db: Session,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        category_filter = ""
        params: Dict[str, Any] = {}

        if category and category.lower() != "all":
            category_filter = "AND m.category = :category"
            params["category"] = category

        query = text(
            f"""
            SELECT
                m.material_id,
                m.material_code,
                m.material_name,
                m.category,
                m.unit_of_measure,
                m.current_quantity,
                m.minimum_stock_level,
                sfs.safety_stock_days,
                sfs.lead_time_days,
                sfs.manual_avg_daily_usage,
                sfs.lookback_days
            FROM materials AS m
            LEFT JOIN stock_forecast_settings AS sfs
                ON m.material_id = sfs.material_id
            WHERE m.status = 1
            {category_filter}
            ORDER BY m.material_name ASC
            """
        )

        materials = [
            dict(row)
            for row in db.execute(query, params).mappings().all()
        ]

        if not materials:
            return {
                "materials": [],
                "movement_map": {},
                "sales_map": {},
            }

        material_ids = [mat["material_id"] for mat in materials]

        ids_query = text(
            "SELECT smi.material_id, SUM(smi.quantity) AS total_consumed "
            "FROM stock_movement_items AS smi "
            "JOIN stock_movements AS sm ON smi.movement_id = sm.movement_id "
            "WHERE smi.material_id IN :material_ids "
            "AND sm.movement_type IN ('Issue', 'Wastage') "
            "AND sm.movement_date >= DATE_SUB(CURDATE(), INTERVAL :lookback DAY) "
            "GROUP BY smi.material_id"
        ).bindparams(bindparam("material_ids", expanding=True))

        movement_rows = db.execute(
            ids_query,
            {
                "material_ids": material_ids,
                "lookback": DEFAULT_LOOKBACK_DAYS,
            },
        ).mappings().all()

        movement_map = {
            int(row["material_id"]): float(row["total_consumed"] or 0)
            for row in movement_rows
        }

        sales_query = text(
            "SELECT mi.material_id, "
            "SUM(dsi.quantity_sold * mi.quantity) AS total_sales_consumed "
            "FROM daily_sales_items AS dsi "
            "JOIN menu_ingredients AS mi "
            "ON dsi.item_id = mi.item_id AND dsi.item_type = 'food' "
            "WHERE mi.material_id IN :material_ids "
            "AND dsi.created_at >= DATE_SUB(CURDATE(), INTERVAL :lookback DAY) "
            "GROUP BY mi.material_id"
        ).bindparams(bindparam("material_ids", expanding=True))

        sales_map: Dict[int, float] = {}

        try:
            sales_rows = db.execute(
                sales_query,
                {
                    "material_ids": material_ids,
                    "lookback": DEFAULT_LOOKBACK_DAYS,
                },
            ).mappings().all()

            sales_map = {
                int(row["material_id"]): float(row["total_sales_consumed"] or 0)
                for row in sales_rows
            }
        except Exception:
            sales_map = {}

        return {
            "materials": materials,
            "movement_map": movement_map,
            "sales_map": sales_map,
        }

    @staticmethod
    def _aggregate_consumption(
        db: Session,
        material_ids: List[int],
        start_date: date,
        end_date: date,
        period: str = "day",
    ) -> Dict[int, List[Tuple[str, float]]]:
        """
        Return mapping: material_id -> list of (period_key, total_consumed)
        period: 'day' -> YYYY-MM-DD, 'week' -> YYYY-WW, 'month' -> YYYY-MM
        """
        if not material_ids:
            return {}

        if period == "day":
            grp = "DATE(sm.movement_date)"
            key_expr = "DATE(sm.movement_date)"
        elif period == "week":
            # use DATE_FORMAT for ISO-style year-week and group by alias to satisfy ONLY_FULL_GROUP_BY
            key_expr = "DATE_FORMAT(sm.movement_date, '%Y-%u')"
        else:
            grp = "DATE_FORMAT(sm.movement_date, '%Y-%m')"
            key_expr = "DATE_FORMAT(sm.movement_date, '%Y-%m')"

        q = text(
            "SELECT smi.material_id, "
            f"{key_expr} as period_key, SUM(smi.quantity) as total_consumed "
            "FROM stock_movement_items AS smi "
            "JOIN stock_movements AS sm ON smi.movement_id = sm.movement_id "
            "WHERE smi.material_id IN :material_ids "
            "AND sm.movement_type IN ('Issue','Wastage') "
            "AND sm.movement_date BETWEEN :start_date AND :end_date "
            "GROUP BY smi.material_id, period_key "
            "ORDER BY smi.material_id, period_key DESC"
        ).bindparams(bindparam("material_ids", expanding=True))

        rows = db.execute(
            q,
            {"material_ids": material_ids, "start_date": start_date, "end_date": end_date},
        ).mappings().all()

        out: Dict[int, List[Tuple[str, float]]] = {}
        for r in rows:
            mid = int(r["material_id"])
            out.setdefault(mid, []).append((str(r["period_key"]), float(r["total_consumed"] or 0)))

        # also include sales consumption
        try:
            sales_q = text(
                "SELECT mi.material_id, "
                f"{key_expr} as period_key, SUM(dsi.quantity_sold * mi.quantity) as total_sales_consumed "
                "FROM daily_sales_items AS dsi "
                "JOIN menu_ingredients AS mi ON dsi.item_id = mi.item_id AND dsi.item_type = 'food' "
                "WHERE mi.material_id IN :material_ids "
                "AND dsi.created_at BETWEEN :start_date AND :end_date "
                "GROUP BY mi.material_id, period_key "
                "ORDER BY mi.material_id, period_key DESC"
            ).bindparams(bindparam("material_ids", expanding=True))

            sales_rows = db.execute(
                sales_q,
                {"material_ids": material_ids, "start_date": start_date, "end_date": end_date},
            ).mappings().all()

            for r in sales_rows:
                mid = int(r["material_id"])
                out.setdefault(mid, []).append((str(r["period_key"]), float(r["total_sales_consumed"] or 0)))
        except Exception:
            pass

        # merge values with same period_key by material
        merged: Dict[int, Dict[str, float]] = {}
        for mid, items in out.items():
            m: Dict[str, float] = {}
            for key, val in items:
                m[key] = m.get(key, 0.0) + val
            merged[mid] = [(k, m[k]) for k in sorted(m.keys(), reverse=True)]

        return merged

    @staticmethod
    def calculate_metrics(
        current_stock: float,
        min_level: float,
        avg_daily_usage: float,
        lead_time_days: float,
        safety_days: float,
        horizon: float,
    ) -> Dict[str, Any]:
        forecast_consumption = avg_daily_usage * horizon
        safety_stock = avg_daily_usage * safety_days
        projected_stock = current_stock - forecast_consumption
        reorder_point = min_level + avg_daily_usage * lead_time_days
        target_stock = forecast_consumption + safety_stock + min_level

        topup_qty = pos(target_stock - current_stock)
        shortage_qty = pos(min_level - current_stock)

        days_remaining = (
            int(current_stock / avg_daily_usage)
            if avg_daily_usage > 0
            else None
        )

        urgency = "OK"

        if current_stock <= 0:
            urgency = "Out of Stock"
        elif current_stock < min_level:
            urgency = "Critical"
        elif (
            days_remaining is not None
            and days_remaining <= (lead_time_days + safety_days)
        ):
            urgency = "Order Now"
        elif days_remaining is not None and days_remaining <= horizon:
            urgency = "Low"

        return {
            "projected_stock": fix(projected_stock),
            "shortage_qty": fix(shortage_qty),
            "topup_qty": fix(topup_qty),
            "reorder_point": fix(reorder_point),
            "target_stock": fix(target_stock),
            "days_remaining": days_remaining,
            "urgency": urgency,
        }

    @staticmethod
    def get_forecast(
        db: Session,
        forecast_type: str = "weekly",
        months: int = 1,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        # horizon in days used by calculate_metrics
        if forecast_type == "daily":
            horizon = PERIODS["daily"]
        elif forecast_type == "weekly":
            horizon = PERIODS["weekly"]
        else:
            horizon = max(1, months) * 30

        data = ForecastService._load_forecast_data(db=db, category=category)

        materials = data["materials"]
        movement_map = data["movement_map"]
        sales_map = data["sales_map"]

        forecast: List[Dict[str, Any]] = []

        # prepare ids for time-series queries
        material_ids = [int(m["material_id"]) for m in materials]

        today = date.today()

        for mat in materials:
            safety_days = pos(
                mat.get("safety_stock_days") or DEFAULT_SAFETY_DAYS
            )
            lead_time_days = pos(
                mat.get("lead_time_days") or DEFAULT_LEAD_TIME_DAYS
            )
            lookback_days = int(
                mat.get("lookback_days") or DEFAULT_LOOKBACK_DAYS
            )
            current_stock = pos(mat.get("current_quantity"))
            min_level = pos(mat.get("minimum_stock_level"))
            # manual override
            if mat.get("manual_avg_daily_usage") is not None:
                avg_daily_usage = pos(mat["manual_avg_daily_usage"])
            else:
                # compute based on requested forecast_type
                mid = int(mat["material_id"])

                if forecast_type == "daily":
                    # use last 7 days
                    lb = 7
                    sd = today - timedelta(days=lb - 1)
                    ed = today
                    agg = ForecastService._aggregate_consumption(db, [mid], sd, ed, period="day")
                    total = sum(v for _, v in agg.get(mid, []))
                    avg_daily_usage = safe_divide(total, lb)

                elif forecast_type == "weekly":
                    # use last 4 weeks, average weekly then /7
                    weeks = 4
                    sd = today - timedelta(days=weeks * 7 - 1)
                    ed = today
                    agg = ForecastService._aggregate_consumption(db, [mid], sd, ed, period="week")
                    weekly_sums = [v for _, v in agg.get(mid, [])][:weeks]
                    if not weekly_sums:
                        # fallback to movement_map
                        movement_consumption = movement_map.get(mid, 0.0)
                        avg_daily_usage = safe_divide(movement_consumption, lookback_days)
                    else:
                        weekly_avg = sum(weekly_sums) / len(weekly_sums)
                        avg_daily_usage = weekly_avg / 7.0

                elif forecast_type == "monthly":
                    # determine lookback months based on requested horizon
                    if months <= 1:
                        lookback_months = 3
                    elif months == 2:
                        lookback_months = 4
                    elif months == 3:
                        lookback_months = 6
                    else:
                        lookback_months = 12

                    sd = today - timedelta(days=lookback_months * 31)
                    ed = today
                    agg = ForecastService._aggregate_consumption(db, [mid], sd, ed, period="month")
                    month_vals = [v for _, v in agg.get(mid, [])][:lookback_months]
                    if not month_vals:
                        movement_consumption = movement_map.get(mid, 0.0)
                        avg_daily_usage = safe_divide(movement_consumption, lookback_days)
                    else:
                        k = len(month_vals)
                        # exponential decay weights (most recent heavier)
                        decay = 0.6
                        raw = [decay ** i for i in range(k)]
                        raw.reverse()  # make most recent first
                        total_w = sum(raw)
                        weights = [r / total_w for r in raw]
                        weighted_month_total = sum(val * w for val, w in zip(month_vals, weights))
                        # convert to daily usage (approx)
                        avg_daily_usage = weighted_month_total / 30.0

                elif forecast_type == "custom":
                    if not start_date or not end_date:
                        # fallback
                        movement_consumption = movement_map.get(mid, 0.0)
                        avg_daily_usage = safe_divide(movement_consumption, lookback_days)
                    else:
                        sd = start_date
                        ed = end_date
                        if isinstance(sd, datetime):
                            sd = sd.date()
                        if isinstance(ed, datetime):
                            ed = ed.date()
                        days = (ed - sd).days + 1
                        agg = ForecastService._aggregate_consumption(db, [mid], sd, ed, period="day")
                        total = sum(v for _, v in agg.get(mid, []))
                        avg_daily_usage = safe_divide(total, days)

                else:
                    # default fallback
                    movement_consumption = movement_map.get(mid, 0.0)
                    sales_consumption = sales_map.get(mid, 0.0)
                    avg_daily_usage = safe_divide(movement_consumption * 0.7 + sales_consumption * 0.3, lookback_days)

            metrics = ForecastService.calculate_metrics(
                current_stock=current_stock,
                min_level=min_level,
                avg_daily_usage=avg_daily_usage,
                lead_time_days=lead_time_days,
                safety_days=safety_days,
                horizon=horizon,
            )

            forecast.append(
                {
                    "material_id": mat.get("material_id"),
                    "material_code": mat.get("material_code"),
                    "material_name": mat.get("material_name"),
                    "category": mat.get("category"),
                    "unit": mat.get("unit_of_measure"),
                    "current_stock": fix(current_stock),
                    "min_stock_level": fix(min_level),
                    "avg_daily_usage": fix(avg_daily_usage),
                    "lead_time_days": lead_time_days,
                    "safety_stock_days": safety_days,
                    **metrics,
                }
            )

        forecast.sort(key=lambda item: urgency_order[item["urgency"]])

        return {
            "status": True,
            "message": "Stock forecast generated successfully",
            "data": {
                "forecast": forecast,
                "summary": {
                    "total_materials": len(forecast),
                    "out_of_stock": len(
                        [f for f in forecast if f["urgency"] == "Out of Stock"]
                    ),
                    "critical": len(
                        [f for f in forecast if f["urgency"] == "Critical"]
                    ),
                    "order_now": len(
                        [f for f in forecast if f["urgency"] == "Order Now"]
                    ),
                    "low": len(
                        [f for f in forecast if f["urgency"] == "Low"]
                    ),
                    "needs_topup": len(
                        [f for f in forecast if f["topup_qty"] > 0]
                    ),
                },
            },
        }
