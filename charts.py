import io

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt


def create_lead_pipeline_chart(lead_stats):

    statuses = [
        "New",
        "Contacted",
        "Interested",
        "Converted",
        "Lost"
    ]

    values = [lead_stats.get(status.lower(), 0) for status in statuses]

    # Create chart
    fig, ax = plt.subplots(figsize=(7, 3.2))

    bars = ax.bar(
        statuses,
        values,
        color="#7c3aed"
    )

    # Dashboard background
    fig.patch.set_facecolor("#18181d")
    ax.set_facecolor("#18181d")

    # Remove unnecessary borders
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.spines["bottom"].set_color("#2a2a32")
    ax.spines["left"].set_color("#2a2a32")

    # Axis styling
    ax.tick_params(
        colors="#a1a1aa"
    )

    ax.set_ylabel(
        "Number of Leads",
        color="#a1a1aa"
    )

    ax.set_title(
        "Lead Pipeline",
        color="#f5f5f5",
        fontsize=15,
        fontweight="bold",
        pad=15
    )

    # Grid
    ax.grid(
        axis="y",
        linestyle="--",
        alpha=0.2
    )

    # Put numbers above bars
    for bar in bars:

        height = bar.get_height()

        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + 0.1,
            str(int(height)),
            ha="center",
            color="#f5f5f5",
            fontsize=10
        )

    plt.tight_layout()

    # Store image in memory
    image = io.BytesIO()

    plt.savefig(
        image,
        format="png",
        dpi=120,
        bbox_inches="tight",
        facecolor=fig.get_facecolor()
    )

    plt.close(fig)

    image.seek(0)

    return image