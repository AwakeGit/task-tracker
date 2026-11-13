import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Task


def tasks_dataframe(db: Session) -> pd.DataFrame:
    tasks = db.scalars(select(Task)).all()
    return pd.DataFrame(
        [
            {
                "id": t.id,
                "title": t.title,
                "theme": t.theme,
                "status": t.status,
                "owner_id": t.owner_id,
                "executor_id": t.executor_id,
            }
            for t in tasks
        ]
    )


def summary(db: Session) -> dict:
    df = tasks_dataframe(db)
    if df.empty:
        return {"total": 0, "by_status": {}, "by_theme": {}, "by_executor": {}}
    return {
        "total": int(len(df)),
        "by_status": df.groupby("status").size().to_dict(),
        "by_theme": df.groupby("theme").size().to_dict(),
        "by_executor": {
            str(k): int(v)
            for k, v in df.fillna({"executor_id": 0}).groupby("executor_id").size().items()
        },
    }


def status_chart_png(db: Session) -> bytes:
    df = tasks_dataframe(db)
    fig, ax = plt.subplots(figsize=(6, 4))
    if df.empty:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.set_axis_off()
    else:
        counts = df.groupby("status").size().sort_index()
        counts.plot.bar(ax=ax, color="steelblue")
        ax.set_title("Tasks by status")
        ax.set_xlabel("Status")
        ax.set_ylabel("Count")
        fig.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=120)
    plt.close(fig)
    return buffer.getvalue()
