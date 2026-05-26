# HTTP Hosts Benchmarking

This repository contains tools and scripts for benchmarking HTTP hosts performance.

## Prerequisites

Before running the benchmarks, you need to create a path list (`path_list_500k.txt`). You have two options:

1. Generate from real-world server logs using `nginx_to_path_list.py`
2. Generate randomly (Note: real-world usage patterns are typically non-random, e.g., ocean tiles are rarely accessed)

## Important Notes

- Run the benchmarks on `localhost`, and not over the internet! Otherwise you'd be just testing your internet speed.
- The benchmark uses [wrk](https://github.com/wg/wrk) HTTP benchmarking tool

## Usage

Basic command:

```bash
wrk -c10 -t4 -d10s -s /data/ofm/benchmark/wrk_custom_list.lua http://localhost
```

### Parameters Explained

- `-c10`: Number of connections to keep open
- `-t4`: Number of threads to use
- `-d10s`: Duration of the test (10 seconds)
- `-s`: Script file to use

### Thread Count Considerations

- `-t1`: More accurate results as the URL list is loaded exactly in sequence
- `-t4`: Better reflects real-world usage patterns

## Results

Benchmark results can be found in [results.md](results.md)

## Contributing

Feel free to submit your results including which hosts were used.
