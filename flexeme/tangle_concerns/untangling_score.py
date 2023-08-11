#!/usr/bin/env python3

"""
Calculate line-based Rand Index score for the parsed Flexeme clustering of the synthetic benchmark. The ground truth is considered
the original atomic commit that a line belongs to before the commit was tangled.
- First, the script parses the graph into a readable CSV file: each line will have a group assigned by Flexeme (tool_group) and a group assigned by 
    the synthetic benchmark (truth_group)
- Then, calculate RandIndex score for all the synthetic commits and output them to a CSV file

Command Line Args: Find all validated Flexeme PDF graphs (.dot files) in /data/corpora_clean/merged_output_wl_1.dot
    - flexeme_untangling_graph_dir: Directory containing subfolders where merged PDG are stored as .dot files
Returns:
    A CSV file of line-based RandIndex scores for all the synthetic commits {commit_path, score}
    {file, score}
"""

import os
import sys
import pandas as pd
from parse_flexeme_results import translate_PDG_to_CSV
from sklearn.metrics import rand_score
from io import StringIO


def main():
    args = sys.argv[1:]

    if len(args) != 2:
        print("usage: untangling_score.py <path/to/flexeme/graphs>")
        sys.exit(1)

    directory = args[0]
    output_scores_filename = args[1]
    graphname = "merged_output_wl_1.dot"
    synthetic_benchmark_scores = os.path.join(
        directory, output_scores_filename
    )
    synthetic_benchmark_scores_str = ""

    # Grab all result file by walking the data/corpora_clean directory
    for root, _, files in os.walk(directory):
        # Find all files that has the name /merged_output_wl_1.dot
        for file in files:
            if file == graphname:
                # Translates a PDG into CSV to also export a column with the true label (the 'community' attribute of the node)
                PDG_path = os.path.join(root, file)
                CSV_path = os.path.join(root, "flexeme.csv")
                if os.path.exists(CSV_path):
                    continue
                translate_PDG_to_CSV(PDG_path, CSV_path)
                # Calculate the Rand Index score
                df = pd.read_csv(CSV_path)
                RI_score = rand_score(df["truth_group"], df["tool_group"])
                print(PDG_path)
                synthetic_benchmark_scores_str += f"{PDG_path},{RI_score}\n"

    df = pd.read_csv(
        StringIO(synthetic_benchmark_scores_str),
        names=["file", "score"],
        na_values="None",
    )
    df = df.convert_dtypes()  # Forces pandas to use floats as scores.
    df = df.drop_duplicates()
    df.to_csv(synthetic_benchmark_scores, index=False)


if __name__ == "__main__":
    main()
