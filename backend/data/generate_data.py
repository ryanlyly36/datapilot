import pandas as pd
import numpy as np
from datetime import date, timedelta
import os

np.random.seed(42)

DEVICE_TYPES = ["mobile", "desktop", "tablet"]
TRAFFIC_SOURCES = ["organic", "paid_social", "paid_search", "email", "direct"]
REGIONS = ["west", "east", "midwest", "south"]
PRODUCT_CATEGORIES = ["electronics", "apparel", "home", "sports"]

def generate_data(start_date: date, num_days: int = 30) -> pd.DataFrame:
    rows = []

    for i in range(num_days):
        current_date = start_date + timedelta(days=i)

        # Simulate a conversion drop in the last 7 days
        is_recent_week = i >= 23

        for device in DEVICE_TYPES:
            for source in TRAFFIC_SOURCES:
                for region in REGIONS:
                    for category in PRODUCT_CATEGORIES:

                        sessions = int(np.random.normal(500, 80))
                        sessions = max(sessions, 50)

                        # Base conversion rate varies by device
                        if device == "mobile":
                            base_cvr = 0.032
                        elif device == "desktop":
                            base_cvr = 0.055
                        else:
                            base_cvr = 0.041

                        # Simulate mobile + paid social drop in recent week
                        if is_recent_week and device == "mobile":
                            base_cvr *= 0.70  # 30% drop on mobile
                        if is_recent_week and source == "paid_social":
                            base_cvr *= 0.75  # 25% drop on paid social

                        orders = int(sessions * base_cvr * np.random.normal(1.0, 0.05))
                        orders = max(orders, 0)

                        add_to_cart = int(sessions * base_cvr * 2.8 * np.random.normal(1.0, 0.05))
                        checkout_start = int(add_to_cart * 0.6 * np.random.normal(1.0, 0.05))
                        revenue = round(orders * np.random.normal(85, 15), 2)
                        bounce_rate = round(np.random.normal(0.42, 0.05), 3)

                        rows.append({
                            "date": current_date,
                            "device_type": device,
                            "traffic_source": source,
                            "region": region,
                            "product_category": category,
                            "sessions": sessions,
                            "orders": orders,
                            "add_to_cart": add_to_cart,
                            "checkout_start": checkout_start,
                            "revenue": revenue,
                            "bounce_rate": bounce_rate
                        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    start = date(2026, 3, 9)
    df = generate_data(start_date=start, num_days=30)

    output_path = os.path.join(os.path.dirname(__file__), "analytics_data.csv")
    df.to_csv(output_path, index=False)

    print(f"Generated {len(df)} rows")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Saved to: {output_path}")
    print(df.head())