# wrk benchmarks

Real world usage, 500k requests replayed from server log. 



### Hetnzer dedicated server with NVME ssd

#### localhost

clean cache after nginx restart. 

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

#### over network

```
wrk -c10 -t4 -d60s -s /data/ofm/benchmark/wrk_custom_list.lua http://x.x.x.x
Running 1m te st @ http://144.76.168.195
  4 threads and 10 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     7.57ms    6.61ms  45.34ms   84.32%
    Req/Sec   293.85    141.33     1.18k    73.07%
  71628 requests in 1.00m, 6.05GB read
Requests/sec:   1191.88
Transfer/sec:    103.01MB
```

Realistically this is the max over Gigabit connection.

---



### BuyVM KVM machine with 1 TB BuyVM Block Storage Slab

Advertisement: 40Gbit+ InfiniBand RDMA Storage Fabric giving near local storage performance.

Reality:

```
wrk -c10 -t4 -d60s -s /data/ofm/benchmark/wrk_custom_list.lua http://localhost
Running 1m test @ http://localhost
  4 threads and 10 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency   226.10ms  343.52ms   1.99s    87.75%
    Req/Sec    29.77     38.06   272.00     89.72%
  3655 requests in 1.00m, 232.76MB read
  Socket errors: connect 0, read 0, write 0, timeout 8
Requests/sec:     60.87
Transfer/sec:      3.88MB
```

Wow, this is 60 request per second compared to Hetzner's 47000, just wow! Repeated tests with hot cache resulted in a bit better performance, but still not Gigabit.

```
Requests/sec:    266.99
Transfer/sec:     23.07MB
```

Abandoned the idea of using BuyVM, even though their unlimited bandwidth is quite unique in this price range in USA.





