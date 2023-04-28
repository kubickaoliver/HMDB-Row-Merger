import os
import typer
import pandas as pd
import warnings
import rich
from rich.progress import Progress
from rich.console import Console


def concat_synonyms_to_str(synonyms: list, min_syn_length: int) -> str:
    unique_values = set()
    for sublist in synonyms:
        for val in sublist:
            if isinstance(val, (str)):
                unique_values.add(val)
    return '#'.join(str(item) for item in list(unique_values) if len(str(item)) >= min_syn_length and str(item) != 'nan') + '\n'


def main(
    hmdb_file_path: str = typer.Argument('', help="The file path to HMDB file (csv format). This file should not include headers, and the columns must be delimited by the '#' symbol."),
    output_dir: str = typer.Argument('./', help='To save the merged HMDB files, you should specify an output directory.'),
    min_syn_length: int = typer.Option(3, help='Synonyms below this length are not considered relevant and will be deleted (rows will not be joined based on them)'),
    match_threshold: float = typer.Option(0.1, help="Percentage value. Let's compare the two lines, find out what percentage they match and if they match <= 10%, the synonyms in which they match will be excluded from further evaluation and deleted and will be deleted but saved in file excluded_synonyms.csv."),
):
    console = Console()
    progress = Progress(console=console)

    rich.print(':arrow_down_small: 1/4 Loading HMDB dataset')
    warnings.filterwarnings("ignore")
    df = pd.read_csv(hmdb_file_path, delimiter='#', header=None)

    with progress:
        # Creating a dictionary that maps chemical synonyms to the list of rows 
        # in which they are located within the HMDB datasets
        chemicals_rows = {}
        task_1 = progress.add_task(":wrench: 2/4 Creating chemical synonyms dict", total=len(df))
        for index, row in df.iterrows():
            for column in df.columns:
                if isinstance(row[column], str) and len(row[column]) >= min_syn_length:
                    if chemicals_rows.get(row[column]):
                        if index not in chemicals_rows[row[column]]:
                            chemicals_rows[row[column]].append(index)
                    else:
                        chemicals_rows[row[column]] = [index]
            progress.update(task_1, advance=1)

        # Determining which row needs to be joined with, based on same chemical synonyms
        task_2 = progress.add_task(":wrench: 3/4 Determining which HMDB rows to join", total=len(chemicals_rows))
        rows_to_concat = {}
        for _, row_list in chemicals_rows.items():
            main_row = row_list[0]
            parent = None
            for index, row in enumerate(row_list):
                if rows_to_concat.get(row) and isinstance(rows_to_concat[row], int):
                    parent = rows_to_concat[row]
                    break
            
            if parent:
                rows_to_concat[parent] = list(set(rows_to_concat[parent]).union(set(row_list)))
            else:
                if not rows_to_concat.get(main_row) and len(row_list) > 1:
                    rows_to_concat[main_row] = row_list

            # Define which key point to which key
            for index, row in enumerate(row_list):
                if not rows_to_concat.get(row):
                    if parent:
                        rows_to_concat[row] = parent
                    elif row != main_row:
                        rows_to_concat[row] = main_row
            progress.update(task_2, advance=1)

        # Merging HMDB dataset rows which contain same chemical synonyms
        task_3 = progress.add_task(":fire: 4/4 Joining HMDB rows", total=df.shape[0])
        output_path = os.path.join(output_dir, 'merged_hmdb.csv')

        with open(output_path, 'a') as f:
            for index in range(0, df.shape[0]):
                if rows_to_concat.get(index):
                    if isinstance(rows_to_concat[index], list):
                        # Concat rows from df
                        data = df.iloc[rows_to_concat[index]].values.tolist()
                        file_output = concat_synonyms_to_str(data, min_syn_length)
                        if file_output:
                            f.write(file_output)
                else:
                    data = df.iloc[index].values.tolist()
                    file_output = concat_synonyms_to_str([data], min_syn_length)
                    if file_output:
                        f.write(file_output)
                progress.update(task_3, advance=1)


if __name__ == '__main__':
    typer.run(main)
