# HMDB-Row-Merger

### Script requirements
The script uses [pipenv](https://pipenv.pypa.io/en/latest/) for package management. Make sure that any package related manipulations use `pipenv` command, instead of `pip`

- Activate env

  ```shell
  pipenv shell
  ```

- Install requirements

  ```shell
  pipenv install
  ```

### Run script

- Run the script. See the required arguments by running:

  ```shell
  python main.py --help
  ```

- Here you can see example:

  ```shell
  python main.py --min-syn-length 3 ./dataset/hmdb_synonyma_test.csv
  ```
