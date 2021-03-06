from base import PerfBaseIxia
import time
from tcutils.wrappers import preposttest_wrapper
import test

class PerfIxiaTest(PerfBaseIxia):

    @classmethod
    def setUpClass(cls):
        super(PerfIxiaTest, cls).setUpClass()

#    @test.attr(type=['perf_KVM'])
#    @preposttest_wrapper
#    def test_spirent_flow_KVM_tiny(self):
#        return self.run_spirent_perf_test('Contrail_Perf2-Flow_KVM','TCP','v4',1,1,6)

    @test.attr(type=['perf_KVM','demo'])
    @preposttest_wrapper
    def test_spirent_flow_KVM(self):
        return self.run_spirent_perf_test('Contrail_Perf2-Flow_KVM','TCP','v4',2,1,1)

    @test.attr(type=['perf_KVM'])
    @preposttest_wrapper
    def test_spirent_flow_scale_KVM(self):
        return self.run_spirent_perf_test('Contrail_Perf2-Flow_Scale_KVM','TCP','v4',2,1,1)

    @test.attr(type=['perf_KVM','perf_THPT'])
    @preposttest_wrapper
    def test_spirent_Throughput_KVM(self):
        return self.run_spirent_perf_test('Contrail_Perf2-Throughput_KVM','TCP','v4',2,3,1,encap='MPLSoUDP')

    @test.attr(type=['perf_KVM','perf_THPT'])
    @preposttest_wrapper
    def test_spirent_Throughput_KVM_Jumbo(self):
        for host in self.host_list:
             if not self.update_mtu(host,'8600'):
                 self.logger.error("Not able to update mtu")
                 return False

        ret = self.run_spirent_perf_test('Contrail_Perf2-Throughput_KVM_Jumbo','TCP','v4',2,3,1,encap='MPLSoUDP')
        for host in self.host_list:
             if not self.update_mtu(host,'1500'):
                 self.logger.error("Not able to update mtu")
                 return False

        return ret

    @test.attr(type=['perf_KVM','perf_THPT'])
    @preposttest_wrapper
    def test_spirent_Throughput_KVM_SC(self):
        for host in self.host_list:
             if not self.update_mtu(host,'1500'):
                 self.logger.error("Not able to update mtu")
                 return False
        return self.run_spirent_perf_test('Contrail_Perf2-Throughput_KVM_SC','TCP','v4',2,3,1,encap='MPLSoUDP')

    @test.attr(type=['perf_KVM','perf_THPT'])
    @preposttest_wrapper
    def test_spirent_Throughput_KVM_multique(self):
        return self.run_spirent_perf_test('Contrail_Perf2-Throughput_KVM_multique','TCP','v4',2,1,2,encap='MPLSoUDP')

    @test.attr(type=['perf_KVM','perf_THPT'])
    @preposttest_wrapper
    def test_spirent_Throughput_KVM_multique_4(self):
        return self.run_spirent_perf_test('Contrail_Perf2-Throughput_KVM_multique4','TCP','v4',4,1,4,encap='MPLSoUDP')

    @test.attr(type=['perf_DPDK'])
    @preposttest_wrapper
    def test_spirent_flow_DPDK(self):
        return self.run_spirent_perf_test('Contrail_Perf2-Flow_DPDK','TCP','v4',4,1,3)

    @test.attr(type=['perf_DPDK'])
    @preposttest_wrapper
    def test_spirent_flow_scale_DPDK(self):
        return self.run_spirent_perf_test('Contrail_Perf2-Flow_Scale_DPDK','TCP','v4',4,1,3)

    @test.attr(type=['perf_DPDK','perf_THPT'])
    @preposttest_wrapper
    def test_spirent_Throughput_DPDK_SC(self):
        return self.run_spirent_perf_test('Contrail_Perf2-Throughput_DPDK_SC','TCP','v4',4,1,3,encap='MPLSoUDP')


    @test.attr(type=['perf_netronome'])
    @preposttest_wrapper
    def test_spirent_flow_netronome(self):
        return self.run_spirent_perf_test('Contrail_Perf2-Flow_KVM','TCP','v4',2,1,5)

#    @test.attr(type=['perf_netronome'])
#    @preposttest_wrapper
#    def test_spirent_Throughput_Netronome(self):
#        return self.run_spirent_perf_test('Contrail_Perf2-Throughput_KVM','TCP','v4',2,3,5)

#    @test.attr(type=['perf_netronome'])
#    @preposttest_wrapper
#    def test_spirent_Throughput_Netronome_SC(self):
#        return self.run_spirent_perf_test('Contrail_Perf2-Throughput_KVM_SC','TCP','v4',2,3,5)
#end PerfIxiaTest




