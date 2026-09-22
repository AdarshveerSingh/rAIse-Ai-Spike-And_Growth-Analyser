from datetime import datetime
from dateutil.relativedelta import relativedelta


def calculate_research_window(
    spike_date,
    months_before=6,
    months_after=3
):
    """
    Creates the research window around a growth event.

    Default:
        6 months before
        3 months after
    """

    if isinstance(spike_date, str):
        spike_date = datetime.fromisoformat(
            spike_date.replace("Z", "+00:00")
        )

    start_date = spike_date - relativedelta(
        months=months_before
    )

    end_date = spike_date + relativedelta(
        months=months_after
    )

    return {
        "start": start_date.isoformat(),
        "spike": spike_date.isoformat(),
        "end": end_date.isoformat(),
        "months_before": months_before,
        "months_after": months_after
    }