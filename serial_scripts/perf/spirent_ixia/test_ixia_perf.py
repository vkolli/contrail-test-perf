from base import PerfBaseIxia
import time
from tcutils.wrappers import preposttest_wrapper
import test

class PerfIxiaTest(PerfBaseIxia):

    @classmethod
    def setUpClass(cls):
        super(PerfIxiaTest, cls).setUpClass()

    @preposttest_wrapper
    def test_ixia_pps_tcp_v4_2_3si(self):
        return self.run_ixia_perf_tests_pps('THROUGHPUT','TCP','v4',2,3)

    @preposttest_wrapper
    def test_ixia_pps_tcp_v4_2_2si(self):
        return self.run_ixia_perf_tests_pps('THROUGHPUT','TCP','v4',2,2)

    @preposttest_wrapper
    def test_ixia_pps_tcp_v4_2_4si(self):
        return self.run_ixia_perf_tests_pps('THROUGHPUT','TCP','v4',2,4)

    @preposttest_wrapper
    def test_ixia_pps_tcp_v4_2_1si(self):
        return self.run_ixia_perf_tests_pps('THROUGHPUT','TCP','v4',2,1)

    @preposttest_wrapper
    def test_ixia_pps_tcp_v4_4_1si(self):
        return self.run_ixia_perf_tests_pps('THROUGHPUT','TCP','v4',4,1)

    @preposttest_wrapper
    def test_ixia_perf_tcp_vm_to_vm_compute_8_1si(self):
        return self.run_ixia_perf_tests_pps('THROUGHPUT','TCP','v4',8,1)

    @preposttest_wrapper
    def test_ixia_perf_tcp_vm_to_vm_compute_4_2si(self):
        return self.run_ixia_perf_tests_pps('THROUGHPUT','TCP','v4',4,2)

#end PerfIxiaTest





