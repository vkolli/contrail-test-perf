from base import PerfBase 
import time
from tcutils.wrappers import preposttest_wrapper
import test

class PerfTest(PerfBase):

    @classmethod
    def setUpClass(cls):
        super(PerfTest, cls).setUpClass()

    @preposttest_wrapper
    def test_perf_tcp_vm_to_vm_differ_compute(self):
        return self.run_perf_tests('THROUGHPUT','different','TCP','v4','40g')

    @preposttest_wrapper
    def test_perf_tcp_vm_to_vm_differ_compute(self):
        return self.run_perf_tests('THROUGHPUT','different','TCP','v4','40g')

    @preposttest_wrapper
    def test_perf_udp_vm_to_vm_differ_compute(self):
        return self.run_perf_tests('THROUGHPUT','different','UDP','v4','40g')

    @preposttest_wrapper
    def test_perf_tcp_vm_to_vm_same_compute(self):
        return self.run_perf_tests('THROUGHPUT','same','TCP','v4','40g')

    @preposttest_wrapper
    def test_perf_udp_vm_to_vm_same_compute(self):
        return self.run_perf_tests('THROUGHPUT','same','UDP','v4','40g')

    @preposttest_wrapper
    def test_lat_tcp_vm_to_vm_differ_compute(self):
        return self.run_perf_tests('LATENCY','different','TCP','v4','10g')

    @preposttest_wrapper
    def test_lat_udp_vm_to_vm_differ_compute(self):
        return self.run_perf_tests('LATENCY','different','UDP','v4','10g')

    @preposttest_wrapper
    def test_lat_tcp_vm_to_vm_same_compute(self):
        return self.run_perf_tests('LATENCY','same','TCP','v4','10g')

    @preposttest_wrapper
    def test_lat_udp_vm_to_vm_same_compute(self):
        return self.run_perf_tests('LATENCY','same','UDP','v4','10g')

    @preposttest_wrapper
    def test_perf6_tcp_vm_to_vm_differ_compute(self):
        return self.run_perf_tests('THROUGHPUT','different','TCP','v6','40g')

    @preposttest_wrapper
    def test_perf6_udp_vm_to_vm_differ_compute(self):
        return self.run_perf_tests('THROUGHPUT','different','UDP','v6','40g')

    @preposttest_wrapper
    def test_perf6_tcp_vm_to_vm_same_compute(self):
        return self.run_perf_tests('THROUGHPUT','same','TCP','v6','40g')

    @preposttest_wrapper
    def test_perf6_udp_vm_to_vm_same_compute(self):
        return self.run_perf_tests('THROUGHPUT','same','UDP','v6','40g')

    @preposttest_wrapper
    def test_lat6_tcp_vm_to_vm_differ_compute(self):
        return self.run_perf_tests('LATENCY','different','TCP','v6','10g')

    @preposttest_wrapper
    def test_lat6_udp_vm_to_vm_differ_compute(self):
        return self.run_perf_tests('LATENCY','different','UDP','v6','10g')

    @preposttest_wrapper
    def test_lat6_tcp_vm_to_vm_same_compute(self):
        return self.run_perf_tests('LATENCY','same','TCP','v6','10g')

    @preposttest_wrapper
    def test_lat6_udp_vm_to_vm_same_compute(self):
        return self.run_perf_tests('LATENCY','same','UDP','v6','10g')

#end PerfTest





