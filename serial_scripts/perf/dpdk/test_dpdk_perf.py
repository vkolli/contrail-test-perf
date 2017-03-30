from base import PerfBaseDpdk 
import time
from tcutils.wrappers import preposttest_wrapper
import test

class PerfDpdkTest(PerfBaseDpdk):

    @classmethod
    def setUpClass(cls):
        super(PerfDpdkTest, cls).setUpClass()

#    @preposttest_wrapper
#    def test_perfdpdk_tcp_vm_to_vm_differ_compute(self):
#        return self.run_perf_tests('THROUGHPUT','different','TCP','v4')

#    @preposttest_wrapper
#    def test_perfdpdk_tcp_vm_to_vm_same_compute(self):
#        return self.run_perf_tests('THROUGHPUT','same','TCP','v4')

#    @preposttest_wrapper
#    def test_ixia_perfdpdk_tcp_vm_to_vm_compute_2_1si(self):
#        return self.run_ixia_perf_tests('THROUGHPUT','different','TCP','v4',2,1)

    @preposttest_wrapper
    def test_ixia_perfdpdk_tcp_vm_to_vm_compute_4_1si(self):
        return self.run_ixia_perf_tests('THROUGHPUT','different','TCP','v4',4,1)

    @preposttest_wrapper
    def test_ixia_perfdpdk_tcp_vm_to_vm_compute_8_1si(self):
        return self.run_ixia_perf_tests('THROUGHPUT','different','TCP','v4',8,1)

#    @preposttest_wrapper
#    def test_ixia_perfdpdk_tcp_vm_to_vm_compute_2_2si(self):
#        return self.run_ixia_perf_tests('THROUGHPUT','different','TCP','v4',2,2)

    @preposttest_wrapper
    def test_ixia_perfdpdk_tcp_vm_to_vm_compute_4_2si(self):
        return self.run_ixia_perf_tests('THROUGHPUT','different','TCP','v4',4,2)

#    @preposttest_wrapper
#    def test_ixia_perfdpdk_tcp_vm_to_vm_compute_2_4si(self):
#        return self.run_ixia_perf_tests('THROUGHPUT','different','TCP','v4',2,4)

"""
    @preposttest_wrapper
    def test_perfdpdk_udp_vm_to_vm_differ_compute(self):
        return self.run_perf_tests('THROUGHPUT','different','UDP','v4')

    @preposttest_wrapper
    def test_perfdpdk_udp_vm_to_vm_same_compute(self):
        return self.run_perf_tests('THROUGHPUT','same','UDP','v4')


    @preposttest_wrapper
    def test_latdpdk_tcp_vm_to_vm_differ_compute(self):
        return self.run_perf_tests('LATENCY','different','TCP','v4')

    @preposttest_wrapper
    def test_latdpdk_udp_vm_to_vm_differ_compute(self):
        return self.run_perf_tests('LATENCY','different','UDP','v4')

    @preposttest_wrapper
    def test_latdpdk_tcp_vm_to_vm_same_compute(self):
        return self.run_perf_tests('LATENCY','same','TCP','v4')

    @preposttest_wrapper
    def test_latdpdk_udp_vm_to_vm_same_compute(self):
        return self.run_perf_tests('LATENCY','same','UDP','v4')

    @preposttest_wrapper
    def test_perf6dpdk_tcp_vm_to_vm_differ_compute(self):
        return self.run_perf_tests('THROUGHPUT','different','TCP','v6')

    @preposttest_wrapper
    def test_perf6dpdk_udp_vm_to_vm_differ_compute(self):
        return self.run_perf_tests('THROUGHPUT','different','UDP','v6')

    @preposttest_wrapper
    def test_perf6dpdk_tcp_vm_to_vm_same_compute(self):
        return self.run_perf_tests('THROUGHPUT','same','TCP','v6')

    @preposttest_wrapper
    def test_perf6dpdk_udp_vm_to_vm_same_compute(self):
        return self.run_perf_tests('THROUGHPUT','same','UDP','v6')

    @preposttest_wrapper
    def test_lat6dpdk_tcp_vm_to_vm_differ_compute(self):
        return self.run_perf_tests('LATENCY','different','TCP','v6')

    @preposttest_wrapper
    def test_lat6dpdk_udp_vm_to_vm_differ_compute(self):
        return self.run_perf_tests('LATENCY','different','UDP','v6')

    @preposttest_wrapper
    def test_lat6dpdk_tcp_vm_to_vm_same_compute(self):
        return self.run_perf_tests('LATENCY','same','TCP','v6')

    @preposttest_wrapper
    def test_lat6dpdk_udp_vm_to_vm_same_compute(self):
        return self.run_perf_tests('LATENCY','same','UDP','v6')
"""

#end PerfDpdkTest





