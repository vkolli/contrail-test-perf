from base import PerfBaseIxia
import time
from tcutils.wrappers import preposttest_wrapper
import test

class PerfIxiaTest(PerfBaseIxia):

    @classmethod
    def setUpClass(cls):
        super(PerfIxiaTest, cls).setUpClass()

    @test.attr(type=['perf_DPDK','demo'])
    @preposttest_wrapper
    def test_ixia_0PPS_latency_DPDK_4core(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_latency_binary_64_dpdk_4ports.ixncfg','TCP','v4',3,2,3)

    @test.attr(type=['perf_DPDK'])
    @preposttest_wrapper
    def test_ixia_0PPS_jitter_DPDK_4core_v6(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_jitter_binary_64_dpdk_4ports_ipv6.ixncfg','TCP','dual',3,2,3)

    @test.attr(type=['perf_DPDK'])
    @preposttest_wrapper
    def test_ixia_0PPS_latency_DPDK_4core_v6(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_latency_binary_64_dpdk_4ports_ipv6.ixncfg','TCP','dual',3,2,3)
    @test.attr(type=['perf_DPDK'])
    @preposttest_wrapper
    def test_ixia_1460_PPS_jitter_DPDK_4core_v6(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_jitter_binary_1460_dpdk_4ports_ipv6.ixncfg','TCP','dual',3,2,3,encap='MPLSoUDP')

    @test.attr(type=['perf_DPDK'])
    @preposttest_wrapper
    def test_ixia_1460_PPS_latency_DPDK_4core_v6(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_latency_binary_1460_dpdk_4ports_ipv6.ixncfg','TCP','dual',3,2,3,encap='MPLSoUDP')

    @test.attr(type=['perf_DPDK'])
    @preposttest_wrapper
    def test_ixia_0PPS_jitter_DPDK_4core(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_jitter_binary_64_dpdk_4ports.ixncfg','TCP','v4',3,2,3)

    @test.attr(type=['perf_DPDK'])
    @preposttest_wrapper
    def test_ixia_PPS_1460latency_DPDK_4core(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_latency_binary_1460_dpdk_4ports.ixncfg','TCP','v4',3,2,3,encap='MPLSoUDP')

    @test.attr(type=['perf_DPDK'])
    @preposttest_wrapper
    def test_ixia_PPS_1460jitter_DPDK_4core(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_jitter_binary_1460_dpdk_4ports.ixncfg','TCP','v4',3,2,3,encap='MPLSoUDP')

    @test.attr(type=['perf_KVM'])
    @preposttest_wrapper
    def test_ixia_PPS_latency_KVM(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_latency_binary_64_kvm_4ports.ixncfg','TCP','v4',2,3,1)

    @test.attr(type=['perf_KVM'])
    @preposttest_wrapper
    def test_ixia_PPS_latency_KVM_mplsoudp(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_latency_binary_64_kvm_4ports.ixncfg','TCP','v4',2,3,1,encap='MPLSoUDP')

    @test.attr(type=['perf_KVM'])
    @preposttest_wrapper
    def test_ixia_PPS_jitter_KVM(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_jitter_binary_64_kvm_4ports.ixncfg','TCP','v4',2,3,1)

#    @test.attr(type=['perf_KVM'])
#    @preposttest_wrapper
#    def test_ixia_PPS_jitter_KVM_v6(self):
#        return self.run_ixia_perf_tests_pps('pps_1_vms_jitter_binary_64_kvm_4ports_ipv6.ixncfg','TCP','v4',2,3,8)

#    @test.attr(type=['perf_KVM'])
#    @preposttest_wrapper
#    def test_ixia_PPS_latency_KVM_v6(self):
#        return self.run_ixia_perf_tests_pps('pps_1_vms_latency_binary_64_kvm_4ports_ipv6.ixncfg','TCP','v4',2,3,8)

    @test.attr(type=['perf_KVM','perf_MQ'])
    @preposttest_wrapper
    def test_ixia_PPS_latency_KVM_MQ2(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_latency_binary_64_kvm_4ports.ixncfg','TCP','v4',2,1,2)

    @test.attr(type=['perf_KVM','perf_MQ'])
    @preposttest_wrapper
    def test_ixia_PPS_jitter_KVM_MQ2(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_jitter_binary_64_kvm_4ports.ixncfg','TCP','v4',2,1,2)

    @test.attr(type=['perf_KVM','perf_MQ'])
    @preposttest_wrapper
    def test_ixia_PPS_latency_KVM_MQ4(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_latency_binary_64_kvm_4ports.ixncfg','TCP','v4',4,1,4)

    @test.attr(type=['perf_KVM','perf_MQ'])
    @preposttest_wrapper
    def test_ixia_PPS_jitter_KVM_MQ4(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_jitter_binary_64_kvm_4ports.ixncfg','TCP','v4',4,1,4)


#    @test.attr(type=['perf_KVM'])
#    @preposttest_wrapper
#    def test_ixia_PPS_latency_KVM_udp(self):
#        return self.run_ixia_perf_tests_pps('pps_3_vms_latency_binary_64_200_IMIX_udp.ixncfg','TCP','v4',3,3,1)

    @test.attr(type=['perf_netronome'])
    @preposttest_wrapper
    def test_ixia_PPS_jitter_Netronome_4core(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_jitter_binary_64_dpdk_4ports.ixncfg','TCP','v4',4,1,5)

    @test.attr(type=['perf_netronome'])
    @preposttest_wrapper
    def test_ixia_PPS_latency_Netronome_4core(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_latency_binary_64_dpdk_4ports.ixncfg','TCP','v4',4,1,5)

    @test.attr(type=['perf_netronome'])
    @preposttest_wrapper
    def test_ixia_PPS_jitter_Netronome_4core_mplsoudp(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_jitter_binary_64_dpdk_4ports.ixncfg','TCP','v4',4,1,5,encap='MPLSoUDP')

    @test.attr(type=['perf_netronome'])
    @preposttest_wrapper
    def test_ixia_PPS_latency_Netronome_4core_mplsoudp(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_latency_binary_64_dpdk_4ports.ixncfg','TCP','v4',4,1,5,encap='MPLSoUDP')

#    @test.attr(type=['perf_netronome','netronome_v6'])
#    @preposttest_wrapper
#    def test_ixia_PPS_jitter_Netronome_4core_v6(self):
#        return self.run_ixia_perf_tests_pps('pps_1_vms_jitter_binary_64_dpdk_4ports_ipv6.ixncfg','TCP','dual',4,1,5)

#    @test.attr(type=['perf_netronome','netronome_v6'])
#    @preposttest_wrapper
#    def test_ixia_PPS_latency_Netronome_4core_v6(self):
#        return self.run_ixia_perf_tests_pps('pps_1_vms_latency_binary_64_dpdk_4ports_ipv6.ixncfg','TCP','dual',4,1,5)

#    @test.attr(type=['perf_netronome','netronome_v6'])
#    @preposttest_wrapper
#    def test_ixia_PPS_jitter_Netronome_4core_v6_mplsoudp(self):
#        return self.run_ixia_perf_tests_pps('pps_1_vms_jitter_binary_64_dpdk_4ports_ipv6.ixncfg','TCP','dual',4,1,5,encap='MPLSoUDP')

#    @test.attr(type=['perf_netronome','netronome_v6'])
#    @preposttest_wrapper
#    def test_ixia_PPS_latency_Netronome_4core_v6_mplsoudp(self):
#        return self.run_ixia_perf_tests_pps('pps_1_vms_latency_binary_64_dpdk_4ports_ipv6.ixncfg','TCP','dual',4,1,5,encap='MPLSoUDP')

    @test.attr(type=['perf_KVM'])
    @preposttest_wrapper
    def test_ixia_PPS_1460latency_KVM_4core(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_latency_binary_1460_kvm_4ports.ixncfg','TCP','v4',2,3,1)

    @test.attr(type=['perf_KVM'])
    @preposttest_wrapper
    def test_ixia_PPS_1460jitter_KVM_4core(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_jitter_binary_1460_kvm_4ports.ixncfg','TCP','v4',2,3,1)

    @test.attr(type=['perf_DPDK','perf_MQ'])
    @preposttest_wrapper
    def test_ixia_PPS_jitter_DPDK_4coremq(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_jitter_binary_64_dpdk_4ports.ixncfg','TCP','v4',4,1,7)

#    @test.attr(type=['perf_DPDK','perf_MQ'])
#    @preposttest_wrapper
#    def test_ixia_PPS_latency_DPDK_4coremq(self):
#        return self.run_ixia_perf_tests_pps('pps_1_vms_latency_binary_64_dpdk_4ports.ixncfg','TCP','v4',4,1,7)


'''
    @test.attr(type=['perf_DPDK'])
    @preposttest_wrapper
    def test_ixia_PPS_latency_DPDK_4core_miltique(self):
        return self.run_ixia_perf_tests_pps('pps_3_vms_latency_binary_64_200_IMIX_kvm_4ports.ixncfg','TCP','v4',4,1,4)

    @test.attr(type=['perf_DPDK'])
    @preposttest_wrapper
    def test_ixia_PPS_latency_DPDK_2core_miltique(self):
        return self.run_ixia_perf_tests_pps('pps_3_vms_latency_binary_64_200_IMIX_kvm_4ports.ixncfg','TCP','v4',2,3,2)
'''
"""
    @test.attr(type=['perf_DPDK'])
    @preposttest_wrapper
    def test_ixia_IMIX_PPS_jitter_DPDK_4core_v6(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_jitter_binary_IMIX_dpdk_4ports_ipv6.ixncfg','TCP','dual',3,2,3)

    @test.attr(type=['perf_DPDK'])
    @preposttest_wrapper
    def test_ixia_IMIX_PPS_latency_DPDK_4core_v6(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_latency_binary_IMIX_dpdk_4ports_ipv6.ixncfg','TCP','dual',3,2,3)
"""
"""
    @test.attr(type=['perf_KVM'])
    @preposttest_wrapper
    def test_ixia_IMIX_PPS_latency_KVM_4core(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_latency_binary_IMIX_KVM_4ports.ixncfg','TCP','v4',3,3,1)

    @test.attr(type=['perf_KVM'])
    @preposttest_wrapper
    def test_ixia_IMIX_PPS_jitter_KVM_4core(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_jitter_binary_IMIX_KVM_4ports.ixncfg','TCP','v4',3,3,1)
"""
"""
    @test.attr(type=['perf_DPDK'])
    @preposttest_wrapper
    def test_ixia_IMIX_PPS_latency_DPDK_4core(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_latency_binary_IMIX_dpdk_4ports.ixncfg','TCP','v4',3,2,3)

    @test.attr(type=['perf_DPDK'])
    @preposttest_wrapper
    def test_ixia_IMIX_PPS_jitter_DPDK_4core(self):
        return self.run_ixia_perf_tests_pps('pps_1_vms_jitter_binary_IMIX_dpdk_4ports.ixncfg','TCP','v4',3,2,3)
"""

#end PerfIxiaTest




