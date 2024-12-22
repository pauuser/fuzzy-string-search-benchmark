# Fuzzy string search benchmark

## **Overview**

This benchmark compares two popular fuzzy string search extensions in PostgreSQL: `fuzzystrmatch` and `pg_trgm`. The goal is to test how each module performs with different query complexities.

## **Prerequisites**

To run the benchmark, make sure you have the following installed:

- Python 3.13
- Docker 27.4.0

## **Run**

1. Navigate to the [src](./src) directory:

```sh
cd src
```

2. Run PostgreSQL using Docker:

```sh
docker-compose up -d
```

3. Set up Python environment and install dependencies

```sh
python3.13 -m venv venv
source ./venv/bin/activate
python3.13 -m pip install requirements.txt
```

4. Populate the database with fake data

```sh
python3.13 generate_data.py
```

5. Run the benchmark

```sh
python3.13 run_benchmark.py
```

## **Measurements**

Here are the results from running the benchmark on **10 million records**:

| **N of filters** |       **Method**       | **Explain (ms)** | **Bench (avg ms)** |
|:----------------:|:----------------------:|:----------------:|:------------------:|
|                1 | levenshtein            | 35.101           | 0.5603333333       |
|                1 | levenshtein_less_equal | 3.594            | 0.3331333333       |
|                1 | pg_trgm_no_index       | 11507.211        | 11524.4438         |
|                1 | pg_trgm_with_index     | 272.524          | 223.0975333        |
|                2 | levenshtein            | 169.678          | 48.22906667        |
|                2 | levenshtein_less_equal | 49.391           | 47.918             |
|                2 | pg_trgm_no_index       | 2890.741         | 2771.548533        |
|                2 | pg_trgm_with_index     | 1068.766         | 1042.972133        |
|                3 | levenshtein            | 24975.06         | 24109.7406         |
|                3 | levenshtein_less_equal | 23805.783        | 23651.13687        |
|                3 | pg_trgm_no_index       | 2801.801         | 2815.5706          |
|                3 | pg_trgm_with_index     | 1074.334         | 1043.978267        |

### **Key Takeaways**

- For simple queries with just one filter, `levenshtein_less_equal` is the fastest, taking less than 1 ms on average.

- As queries become more complex, especially with two or more filters, `pg_trgm` with a GIN index is the clear winner, staying under 1,100 ms even for queries with three filters.

- Without indexes, `pg_trgm` is very slow, highlighting the importance of using GIN indexes for better performance.

## **Conclusion**

- If you’re doing quick, simple fuzzy searches, `levenshtein_less_equal` is the way to go.

- For more complex searches with multiple filters, using `pg_trgm` with GIN indexes is your best bet.