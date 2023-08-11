#!/usr/bin/env python3

"""
Calculate line-based Rand Index score for the parsed Flexeme clustering of the synthetic benchmark. The ground truth is considered
the original atomic commit that a line belongs to before the commit was tangled.
- First, the script takes in readable CSV file which is the parsed PDG results: each line will have a group assigned by Flexeme (tool_group) and a group assigned by 
    the synthetic benchmark (truth_group)
- Then, calculate RandIndex score for the synthetic commit and output them to a CSV file

Command Line Args: Find all validated Flexeme PDF graphs (.dot files) in /data/corpora_clean/merged_output_wl_1.dot
    - flexeme.csv: a readable CSV file: each line will have a group assigned by Flexeme (tool_group) and a group assigned by 
                   the synthetic benchmark (truth_group)
Returns:
    A scores.csv file of line-based RandIndex scores for one synthetic commit {commit_filepath, score}
"""

import os
import sys
import pandas as pd
from parse_flexeme_results import translate_PDG_to_CSV
from sklearn.metrics import rand_score
from io import StringIO


def main():
    """
    Calculate the line-based Rand Index scores for one synthetic commit parsed Flexeme results.
    """
    args = sys.argv[1:]

    if len(args) != 1:
        print("usage: untangling_score.py <path/to/flexeme/parsed/CSV/file>")
        sys.exit(1)
    # Refactor job so that you can parallelize
    # Take in the flexeme graph, take its dirname, and write to
    translated_CSV_file = args[0]
    root = os.path.dirname(translated_CSV_file)
    synthetic_benchmark_scores_file = os.path.join(root, "scores.csv")
    synthetic_benchmark_scores_str = ""
    try:
        df = pd.read_csv(translated_CSV_file)
    except FileNotFoundError:
        "The results does not exist or not have been parsed"
        print(
            "Parsed Flexeme PDG not found, skipping calculation of Rand Index score file",
            file=sys.stderr,
        )
        sys.exit(1)

    RI_score = rand_score(df["truth_group"], df["tool_group"])
    synthetic_benchmark_scores_str += f"{root},{RI_score}\n"

    RI_df = pd.read_csv(
        StringIO(synthetic_benchmark_scores_str),
        names=["file", "score"],
        na_values="None",
    )
    RI_df.to_csv(synthetic_benchmark_scores_file, index=False)


if __name__ == "__main__":
    main()
