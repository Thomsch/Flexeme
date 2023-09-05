#!/usr/bin/env python3

"""
Translates Flexeme grouping results ((dot files) in decomposition/flexeme for each D4J bug file
to the line level.

Each line is labelled by collecting all of its nodes' groups (it is possible for one line
to have multiple groups).

Command Line Args:
    - result_dir: Directory to flexeme.dot results in decomposition/flexeme
    - output_path: Directory to store returned CSV file in evaluation/flexeme.csv
Returns:
    A flexeme.csv file in the respective /evaluation/<D4J bug> subfolder.
    CSV header: {file, source, target, tool_group=0,1,2,etc., truth_group=0,1,2,etc.}
        - file: The relative file path from the project root for a change
        - source: The line number of the change if the change is a deletion
        - target: The line number of the change if the change is an addition
        - tool_group: The group number of the change for the synthetic commit determined by Flexeme.
        - truth_group: The true group number of the changed for the synthetic commit determined before being tangled.
"""

import logging
import sys
from io import StringIO
import os
import networkx as nx
import pandas as pd


UPDATE_ADD = "add"
UPDATE_REMOVE = "remove"


def translate_PDG_to_CSV(PDG_path):
    """
    Implement the logic of the script. See the module docstring.
    """
    try:
        graph = nx.nx_pydot.read_dot(PDG_path)
    except FileNotFoundError:
        # Flexeme doesn't generate a PDG if it doesn't detect multiple groups.
        # In this case, we do not create a CSV file. The untangling score will be
        # calculated as if Flexeme grouped all changes in one group in `untangling_score.py`.
        print("PDG not found, skipping creation of CSV file", file=sys.stderr)
        sys.exit(1)
    root = os.path.dirname(PDG_path)
    CSV_path = os.path.join(root, "flexeme.csv")
    result = ""
    if not os.path.exists(CSV_path):
        for node, data in graph.nodes(data=True):
            # Changed nodes are the only nodes with a color attribute.
            if "color" not in data.keys():
                continue

            if data["color"] not in ["green", "red"]:
                logging.error(f"Color {data['color']} not supported")
                continue

            if "label" not in data.keys():
                logging.error(f"Attribute 'label' not found in node {node}")
                continue
            if "community" not in data.keys():
                continue
            truth = int(data["community"])
            group = get_node_label(data)
            span_start, span_end = get_span(data)
            update_type = get_update_type(data)

            file = (
                data["filepath"].replace('"', "")
                if "filepath" in data.keys()
                # then do nothing
                else data["cluster"].replace('"', "")
            )
            for line in range(span_start, span_end + 1):
                if update_type == UPDATE_REMOVE:
                    result += f"'{file}','{line}',,'{group}','{truth}'\n"  # We separate the fileds by semicolon as the filepath may contain commas
                elif update_type == UPDATE_ADD:
                    result += f"'{file}',,'{line}','{group}','{truth}'\n"
                else:
                    logging.error(f"Update {update_type} unsupported")
                    continue
        export_csv(CSV_path, result)


def export_tool_decomposition_as_csv(df, output_path):
    """
    Export the dataframe to a CSV file. Print an error message if the dataframe is empty.

    Args:
        df: The dataframe to be exported. The dataframe represents the decomposition results for a tool.
        output_path: The path to the CSV file to be created.
    """
    if len(df) == 0:
        print(
            f"No results generated for {output_path}. Verify decomposition results and paths.",
            file=sys.stderr,
        )
    df.to_csv(output_path, index=False)


def export_csv(output_path, result):
    """
    Export the results to a CSV file.

    Args:
        output_path: The path to the CSV file to be created.
        result: The string containing the results to be written to the CSV file.
    """
    df = pd.read_csv(
        StringIO(result),
        names=["file", "source", "target", "tool_group", "truth_group"],
        delimiter=",",
        na_values="None",
        quotechar="'",
    )
    df = df.convert_dtypes()  # Forces pandas to use ints in source and target columns.
    df = df.drop_duplicates()
    export_tool_decomposition_as_csv(df, output_path)


def get_update_type(data):
    """
    Get the update type for this node.

    Args:
        data: The data attribute of the node.

    Returns:
        The update type of the node as a string. Can be either UPDATE_ADD or UPDATE_REMOVE.
    """
    color_attribute = data["color"]
    if color_attribute == "green":
        update = UPDATE_ADD
    elif color_attribute == "red":
        update = UPDATE_REMOVE
    else:
        raise ValueError(f"Color {color_attribute} not supported")
    return update


def get_span(data):
    """
    Get the line span for this node.

    Args:
        data: The data attribute of the node.

    Returns:
        The line span of the node as a tuple (span_end, span_start).
    """
    span_attribute = data["span"].replace('"', "").split("-")
    span_start = int(span_attribute[0])
    span_end = int(span_attribute[1])
    return span_start, span_end


def get_node_label(data):
    """
    Get the label for this node. Flexeme prepends "%d:" to the label of the node.

    Args:
        data: The data attribute of the node.

    Returns:
        The group label of the node.
    """
    label_attribute = data["label"]
    group = label_attribute.split(":")[0].replace('"', "")
    return group


if __name__ == "__main__":
    args = sys.argv[1:]

    if len(args) != 1:
        print("usage: parse_flexeme_results.py <path/to/root/results>")
        sys.exit(1)

    translate_PDG_to_CSV(args[0])
