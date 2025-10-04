from __future__ import annotations

import logging
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Seaborn is nice to have; fall back to matplotlib if missing.
try:
    import seaborn as sns  # type: ignore
    _HAVE_SEABORN = True
    sns.set(style="whitegrid")
except Exception:  # pragma: no cover
    _HAVE_SEABORN = False

# If using NLTK stopwords
try:
    from nltk.corpus import stopwords
    STOPWORDS = set(stopwords.words("english"))
except Exception:  # pragma: no cover
    STOPWORDS = {
        "the", "of", "and", "in", "a", "an", "to", "on", "by", "for", "as", "at",
        "from", "with", "is", "was", "that", "which", "it", "its", "this", "are",
        "or", "be", "used", "use", "type", "such"
    }

QUALITY_ORDER = ["FA", "FL", "A", "GA", "B", "C", "Start", "Stub", "List"]


@dataclass(frozen=True)
class ReportConfig:
    """Parameters that control report generation."""
    output_dir: Path = Path("wikipedia_report")
    histogram_bins: int = 50
    size_bytes_cap: Optional[int] = 175_000
    word_count_cap: Optional[int] = 10_000
    last_edit_cutoff: Optional[str] = "2024-05-01"  # ISO date string or None
    top_wikiprojects: int = 30

    # Filenames
    summary_stats_csv: str = "summary_stats.csv"
    size_hist_png: str = "article_size_distribution.png"
    size_hist_bins_csv: str = "article_size_distribution_bins.csv"
    word_hist_png: str = "word_count_distribution.png"
    word_hist_bins_csv: str = "word_count_distribution_bins.csv"
    last_edit_hist_png: str = "last_edit_histogram.png"
    last_edit_counts_csv: str = "last_edit_histogram_weekly_counts.csv"
    wikiproject_freq_csv: str = "wikiproject_frequencies.csv"
    wikiproject_top_png: str = "top_wikiprojects.png"
    quality_dist_png: str = "article_quality_distribution.png"
    quality_dist_counts_csv: str = "article_quality_distribution_counts.csv"
    shortdesc_words_csv: str = "shortdesc_word_frequencies.csv"


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_and_prepare_data(csv_path: Path | str) -> pd.DataFrame:
    """Load CSV and coerce date columns."""
    df = pd.read_csv(csv_path)
    if "last_edit" in df.columns:
        df["last_edit"] = pd.to_datetime(df["last_edit"], errors="coerce")
    return df


def save_summary_stats(df: pd.DataFrame, cfg: ReportConfig) -> None:
    stats = df[["size_bytes", "word_count"]].describe()
    agg_rows = ["mean", "std"]
    stats.loc[agg_rows] = stats.loc[agg_rows].round(1)
    stats.loc[~stats.index.isin(agg_rows)] = (
        stats.loc[~stats.index.isin(agg_rows)].round().astype(int)
    )
    stats.to_csv(cfg.output_dir / cfg.summary_stats_csv)
    logging.info("Saved %s", cfg.summary_stats_csv)


def _histogram_and_bins(
    series: pd.Series,
    bins: int,
    title: str,
    xlabel: str,
    outfile_png: Path,
    outfile_bins_csv: Path,
) -> None:
    plt.figure(figsize=(10, 6))
    if _HAVE_SEABORN:
        import seaborn as sns  # type: ignore
        sns.histplot(series, bins=bins, kde=True)
    else:
        plt.hist(series.dropna().to_numpy(), bins=bins)

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(outfile_png)
    plt.close()

    counts, bin_edges = np.histogram(series.dropna().to_numpy(), bins=bins)
    bin_labels = [f"{int(bin_edges[i])}–{int(bin_edges[i+1])}" for i in range(len(bin_edges) - 1)]
    pd.DataFrame({"bin_range": bin_labels, "count": counts}).to_csv(outfile_bins_csv, index=False)
    logging.info("Saved %s and %s", outfile_png.name, outfile_bins_csv.name)


def plot_histogram(
    df: pd.DataFrame,
    column: str,
    title: str,
    xlabel: str,
    filename_png: str,
    filename_bins_csv: str,
    bins: int,
    cap: Optional[int],
    cfg: ReportConfig,
) -> None:
    data = df
    title_suffix = ""
    if cap is not None:
        data = df.loc[df[column] <= cap]
        title_suffix = f" (Capped at {cap})"

    _histogram_and_bins(
        series=data[column],
        bins=bins,
        title=title + title_suffix,
        xlabel=xlabel,
        outfile_png=cfg.output_dir / filename_png,
        outfile_bins_csv=cfg.output_dir / filename_bins_csv,
    )


def count_wikiprojects(df: pd.DataFrame, cfg: ReportConfig) -> Optional[pd.DataFrame]:
    if "wikiprojects" not in df.columns:
        logging.info("No 'wikiprojects' column found; skipping.")
        return None

    wp_series = df["wikiprojects"].dropna().astype(str)
    wp_exploded = wp_series.str.split(",").explode().str.strip()
    wp_exploded = wp_exploded[wp_exploded != ""]

    wp_counts = wp_exploded.value_counts()
    wp_counts_df = wp_counts.reset_index()
    wp_counts_df.columns = ["wikiproject", "count"]
    wp_counts_df.to_csv(cfg.output_dir / cfg.wikiproject_freq_csv, index=False)
    logging.info("Saved %s", cfg.wikiproject_freq_csv)
    return wp_counts_df


def plot_top_wikiprojects(wp_counts_df: pd.DataFrame, cfg: ReportConfig) -> None:
    top = wp_counts_df.head(cfg.top_wikiprojects)
    plt.figure(figsize=(10, 6))
    if _HAVE_SEABORN:
        import seaborn as sns  # type: ignore
        sns.barplot(y="wikiproject", x="count", data=top)
    else:
        plt.barh(top["wikiproject"], top["count"])
        plt.gca().invert_yaxis()

    plt.title(f"Top {cfg.top_wikiprojects} WikiProjects by Article Count")
    plt.xlabel("Number of Articles")
    plt.ylabel("WikiProject")
    plt.tight_layout()
    plt.savefig(cfg.output_dir / cfg.wikiproject_top_png)
    plt.close()
    logging.info("Saved %s", cfg.wikiproject_top_png)


def plot_quality_distribution(df: pd.DataFrame, cfg: ReportConfig) -> None:
    if "quality" not in df.columns:
        logging.info("No 'quality' column found; skipping.")
        return

    quality_counts = df["quality"].value_counts()
    ordered_counts = pd.Series({q: int(quality_counts.get(q, 0)) for q in QUALITY_ORDER if q in quality_counts})

    plt.figure(figsize=(8, 5))
    if _HAVE_SEABORN:
        import seaborn as sns  # type: ignore
        sns.barplot(x=ordered_counts.index, y=ordered_counts.values)
    else:
        plt.bar(ordered_counts.index, ordered_counts.values)

    plt.title("Distribution of Article Quality Ratings")
    plt.xlabel("Quality Class")
    plt.ylabel("Number of Articles")
    plt.tight_layout()
    plt.savefig(cfg.output_dir / cfg.quality_dist_png)
    plt.close()
    logging.info("Saved %s", cfg.quality_dist_png)

    counts_df = ordered_counts.reset_index()
    counts_df.columns = ["quality_class", "count"]
    counts_df.to_csv(cfg.output_dir / cfg.quality_dist_counts_csv, index=False)
    # ordered_counts.reset_index(names=["quality_class"]).rename(columns={0: "count"}).to_csv(
    #     cfg.output_dir / cfg.quality_dist_counts_csv, index=False
    # )
    logging.info("Saved %s", cfg.quality_dist_counts_csv)


def count_common_shortdesc_words(df: pd.DataFrame, cfg: ReportConfig, top_n: int = 300) -> Optional[pd.DataFrame]:
    if "shortdesc" not in df.columns:
        logging.info("No 'shortdesc' column found; skipping.")
        return None

    descs = df["shortdesc"].dropna().astype(str).tolist()
    all_words: list[str] = []
    for line in descs:
        words = re.findall(r"\b[a-zA-Z]{3,}\b", line.lower())  # 3+ letters
        all_words.extend([w for w in words if w not in STOPWORDS])

    word_counts = Counter(all_words)
    most_common = word_counts.most_common(top_n)
    word_df = pd.DataFrame(most_common, columns=["word", "count"])
    word_df.to_csv(cfg.output_dir / cfg.shortdesc_words_csv, index=False)
    logging.info("Saved %s", cfg.shortdesc_words_csv)
    return word_df


def plot_last_edit_histogram(df: pd.DataFrame, cfg: ReportConfig, title: str) -> None:
    if "last_edit" not in df.columns:
        logging.info("No 'last_edit' column found; skipping.")
        return

    data = df.copy()
    if cfg.last_edit_cutoff is not None:
        cutoff = pd.to_datetime(cfg.last_edit_cutoff)
        data = data[data["last_edit"] >= cutoff]
        title = f"{title} (From {cutoff.date()})"

    data["edit_week"] = data["last_edit"].dt.to_period("W").dt.start_time
    weekly_df = (
        data["edit_week"].value_counts().sort_index().rename_axis("week_start").reset_index(name="count")
    )

    plt.figure(figsize=(12, 6))
    if _HAVE_SEABORN:
        import seaborn as sns  # type: ignore
        sns.barplot(data=weekly_df, x="week_start", y="count", color="skyblue")
    else:
        plt.bar(weekly_df["week_start"].astype(str), weekly_df["count"])

    plt.title(title)
    plt.xlabel("Week of Last Edit")
    plt.ylabel("Number of Articles")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(cfg.output_dir / cfg.last_edit_hist_png)
    plt.close()
    logging.info("Saved %s", cfg.last_edit_hist_png)

    weekly_df.to_csv(cfg.output_dir / cfg.last_edit_counts_csv, index=False)
    logging.info("Saved %s", cfg.last_edit_counts_csv)


def generate_report(df: pd.DataFrame, cfg: ReportConfig) -> None:
    """Run the full report with the provided configuration."""
    ensure_output_dir(cfg.output_dir)
    save_summary_stats(df, cfg)

    plot_histogram(
        df=df,
        column="size_bytes",
        title="Distribution of Article Sizes (Bytes)",
        xlabel="Size (bytes)",
        filename_png=cfg.size_hist_png,
        filename_bins_csv=cfg.size_hist_bins_csv,
        bins=cfg.histogram_bins,
        cap=cfg.size_bytes_cap,
        cfg=cfg,
    )

    plot_histogram(
        df=df,
        column="word_count",
        title="Distribution of Word Counts",
        xlabel="Word Count",
        filename_png=cfg.word_hist_png,
        filename_bins_csv=cfg.word_hist_bins_csv,
        bins=cfg.histogram_bins,
        cap=cfg.word_count_cap,
        cfg=cfg,
    )

    plot_last_edit_histogram(df, cfg, title="Histogram of Article Last Edit Dates")

    wp_counts = count_wikiprojects(df, cfg)
    if wp_counts is not None and not wp_counts.empty:
        plot_top_wikiprojects(wp_counts, cfg)

    plot_quality_distribution(df, cfg)
    count_common_shortdesc_words(df, cfg)
