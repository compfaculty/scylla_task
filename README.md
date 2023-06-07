# Analysis and runner program

The Analysis program will run concurrently N stress commands while each one of them will run in a separate thread.
The analysis program should parse the results summary of each of the stress threads and print the aggregated summary of all threads.

## Requirements:

* Number of concurrent stress commands to run will be received as a command line argument.

* Each stress command runtime duration may be different.

* The program should print an aggregated summary with the details below.

* Number of stress processes that ran.

* Calculated aggregation of "Op rate" (sum).

* Calculated average of "Latency mean" (average).

* Calculated average of "Latency 99th percentile" (average).

* Standard deviation calculation of all "Latency max" results.

## How to run

* Create env and install poetry dependencies 

* python main.py  --threads_number 5 --duration 10 10 10 20 5 --node_ip=172.17.0.2


## Usefull 

Get container IP:

`docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' test-scylla`