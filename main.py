import os
import typer
import pandas as pd
import warnings
from rich import print
from rich.progress import Progress
from rich.console import Console


def main(
    hmdb_file_path: str = typer.Argument('', help="The file path to HMDB file (csv format). This file should not include headers, and the columns must be delimited by the '#' symbol."),
    output_dir: str = typer.Argument('./', help='To save the merged HMDB files, you should specify an output directory.')
):
    console = Console()
    progress = Progress(console=console)

    print(':arrow_down_small: 1/4 Loading HMDB dataset')
    warnings.filterwarnings("ignore")
    df = pd.read_csv(hmdb_file_path, delimiter='#', header=None)

    with progress:
        # Creating a dictionary that maps chemical synonyms to the list of rows 
        # in which they are located within the HMDB datasets
        chemicals_rows = {}
        task_1 = progress.add_task(":wrench: 2/4 Creating chemical synonyms dict", total=len(df))
        for index, row in df.iterrows():
            for column in df.columns:
                if isinstance(row[column], str):
                    if chemicals_rows.get(row[column]):
                        if index not in chemicals_rows[row[column]]:
                            chemicals_rows[row[column]].append(index)
                    else:
                        chemicals_rows[row[column]] = [index]
            progress.update(task_1, advance=1)

        # Determining which row needs to be joined with which based on same chemical synonyms
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
                        # concat rows from df
                        data = df.iloc[rows_to_concat[index]].values.tolist()
                        unique_values = set()
                        for sublist in data:
                            for val in sublist:
                                if isinstance(val, (str)):
                                    unique_values.add(val)
                        f.write('#'.join(str(item) for item in list(unique_values)) + '\n')
                else:
                    data = df.iloc[index].values.tolist()
                    f.write('#'.join(str(item) for item in data) + '\n')
                progress.update(task_3, advance=1)


if __name__ == '__main__':
    typer.run(main)
