### wrk localhost

clean cache after nginx restart

```
service nginx restart
wrk -c10 -t4 -d60s -s /data/ofm/benchmark/wrk_custom_list.lua http://localhost
Running 1m test @ http://localhost
  4 threads and 10 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     2.02ms    7.04ms  50.43ms   93.23%
    Req/Sec     8.42k     2.01k   18.52k    69.79%
  2871265 requests in 1.00m, 230.65GB read
Requests/sec:  47811.00
Transfer/sec:      3.84GB
```

Super much overkill, we'd only need 125 MB/s for Gigabit connection and this is 3840 MB/s.
Also max request time is super nice + no errors.



### wrk over network

```
wrk -c10 -t4 -d60s -s /data/ofm/benchmark/wrk_custom_list.lua http://x.x.x.x
Running 1m test @ http://144.76.168.195
  4 threads and 10 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     7.57ms    6.61ms  45.34ms   84.32%
    Req/Sec   293.85    141.33     1.18k    73.07%
  71628 requests in 1.00m, 6.05GB read
Requests/sec:   1191.88
Transfer/sec:    103.01MB
```

Realistically this is the max over Gigabit connection.
