import os
import signal
import re
import struct
import socket
import random
from fabric.state import connections as fab_connections
import test
import traffic_tests
from common.contrail_test_init import *
from common import isolated_creds
from vn_test import *
from vm_test import *
from floating_ip import *
from common.servicechain.config import ConfigSvcChain
from common.servicechain.verify import VerifySvcChain
from common.servicechain.mirror.verify import VerifySvcMirror
from common.servicechain.mirror.config import ConfigSvcMirror
from serial_scripts.perf.base import *
from tcutils.commands import *
import threading
import thread
import time
import copy

class PerfBaseDpdk(test.BaseTestCase,VerifySvcMirror,PerfBase):

    @classmethod
    def setUpClass(cls):
        super(PerfBaseDpdk, cls).setUpClass()
        cls.isolated_creds = isolated_creds.IsolatedCreds(cls.__name__, \
				cls.inputs, ini_file = cls.ini_file, \
				logger = cls.logger)
        cls.isolated_creds.setUp()
        cls.project = cls.isolated_creds.create_tenant() 
        cls.isolated_creds.create_and_attach_user_to_tenant()
        cls.inputs = cls.isolated_creds.get_inputs()
        cls.connections = cls.isolated_creds.get_conections() 
        cls.nova_h = cls.connections.nova_h
        cls.orch = cls.connections.orch
        cls.vnc_lib_fixture = cls.connections.vnc_lib_fixture
#        cls.encap_type = ["MPLSoUDP","MPLSoGRE","VXLAN"]
        cls.encap_type = ["MPLSoUDP"]
        cls.family = ''
        cls.ixia_linux_host = '10.87.132.179'
        cls.set_cpu_cores = 4 
        cls.set_si = 1
        cls.dpdk_svc_scaling = False
#        cls.logger= cls.inputs.logger
    #end setUpClass

    @classmethod
    def tearDownClass(cls):
        cls.results_file.close() 
        super(PerfBaseDpdk, cls).tearDownClass()
    #end tearDownClass 

    def launch_dpdk_vms(self,hosts,family,vm_num):
        '''
        Launching VMs on specified hosts based on family 
        '''
        self.vn1_name='vn10001'
        self.vn1_subnets=['20.1.1.0/24']
        self.vm_fixtures = []
        self.vm_num = vm_num 
        self.images = ['dpdk-pktgen-auto','dpdk-l3fwd-auto']

        if family == 'v6':
            self.vn1_fixture= self.useFixture(VNFixture(project_name= self.inputs.project_name, connections= self.connections,vn_name=self.vn1_name, inputs= self.inputs,router_asn=self.inputs.router_asn, rt_number=self.inputs.mx_rt))
        else:
            self.vn1_fixture= self.useFixture(VNFixture(project_name= self.inputs.project_name, connections= self.connections,vn_name=self.vn1_name, inputs= self.inputs, subnets= self.vn1_subnets,router_asn=self.inputs.router_asn, rt_number=self.inputs.mx_rt))

        assert self.vn1_fixture.verify_on_setup()

        image_id = 0

        for host in hosts:
            for i in range(0,self.vm_num):
                vm_name = "vm-test"+str(random.randint(1,100000))
                self.vm_fixtures.append(self.useFixture(VMFixture(project_name= self.inputs.project_name, connections= self.connections, vn_objs = [ self.vn1_fixture.obj ], vm_name= vm_name,flavor='contrail_flavor_small',image_name=self.images[image_id],node_name=host)))
            image_id = 1

        for i in range(0,len(self.vm_fixtures)):
            assert self.vm_fixtures[i].verify_on_setup()

        for i in range(0,len(self.vm_fixtures)):
            if self.inputs.orchestrator =='vcenter':
                ret = self.orch.wait_till_vm_is_active( self.vm_fixtures[i].vm_obj )
            else:
                ret = self.nova_h.wait_till_vm_is_up( self.vm_fixtures[i].vm_obj )

            if ret == False: return {'result':ret,'msg':"%s failed to come up"%self.vm_fixtures[i].vm_name}

        for host in list(set(hosts)):
            for proc in self.process_list:
                if not self.update_process_cpu(host,proc):
                    self.logger.error("Not able to pin cpu :%s "%proc)

        for i in range(0,len(self.vm_fixtures)):
            if not self.start_v6_server(self.vm_fixtures[i]):
                self.logger.error("Not able start v6 server")
                return False

        return True


    def run_perf_tests(self,test_id,mode,proto,family):

        vm_num = 1

        for host in self.host_list:
            self.host_cpu_cores_8[host] = ['8','9','10','11','12','13','14','15']
            self.host_cpu_cores_24[host] = ['24','25','26','27','28','29','30','31']
            self.host_cpu_cores_0[host] = ['0','1','2','3','4','5','6','7']
            self.host_cpu_cores_16[host] = ['16','17','18','19','20','21','22','23']
            if not self.update_vrouter_sysctl(host,self.host_cpu_cores_8[host]):
                self.logger.error("Error in updating sysctl")
                return False

        self.inputs.set_af(family)

        import pdb;pdb.set_trace()
        self.print_results("==================================================================\n")

        if mode == 'different':
            self.print_results("DIFFERENT COMPUTE NODES\n")
            if not self.launch_dpdk_vms([self.host_list[0],self.host_list[1]],family,vm_num):
                self.logger.error("Failed to launch VMs")
        elif mode == 'same':
            self.print_results("SAME COMPUTE NODES\n")
            if not self.launch_dpdk_vms([self.host_list[0],self.host_list[0]],family,vm_num):
                self.logger.error("Failed to launch VMs")

        if test_id == 'THROUGHPUT':
            ret = self.dpdk_throughput_test(mode,proto)

        self.print_results("==================================================================\n")

        return ret

    def dpdk_throughput_test(self,mode,proto):
        for id in range(0,len(self.encap_type)):
            self.update_encap_mode(self.inputs.host_data[self.inputs.cfgm_ip]['host_ip'],self.encap_type[id])
            if proto == 'TCP':
                if not self.run_dpdk_throughput_test(self.vm_fixtures[0],self.vm_fixtures[1],self.duration):
                    self.logger.error("ERROR in TCP throughput test")
                    return False
            if proto == 'UDP':
                if not self.run_dpdk_throughput_test(self.vm_fixtures[0],self.vm_fixtures[1],self.duration):
                    self.logger.error("ERROR in UDP throughput test")
                    return False
        return True

    def run_dpdk_throughput_test(self,src_vm_hdl,dest_vm_hdl,duration):
        result = self.start_dpdk_l3fwd(dest_vm_hdl,duration)
        #import pdb ; pdb.set_trace()
        #for payload in  [ 64, 128, 512, 1400 ]:
        for payload in  [64]:
            perf_list = []
            time.sleep(5)
            result = self.start_dpdk_ptkgen(src_vm_hdl,dest_vm_hdl,payload)
            time.sleep(200)
            result = "PAYLOAD : %s TCP %s THROUGHPUT :  : \n"%(payload ,self.inputs.get_af())
            self.logger.info("Result : %s "%result)
            self.print_results(result)
            self.get_dpdk_results(src_vm_hdl)
            #import pdb ; pdb.set_trace()
        time.sleep(10)
        return True

    def start_dpdk_l2fwd(self,vm_fix,delay):
        time.sleep(5)
        vm_fix.vm_username = 'root'
        vm_fix.vm_password = 'c0ntrail123'
        cmd = '(nohup ./start_l2fwd_app.sh >/dev/null 2>&1 &) ; sleep 5'
        vm_fix.run_cmd_on_vm(cmds=[cmd],as_sudo=True, timeout=self.timeout)
        return True

    def start_dpdk_l3fwd(self,vm_fix,delay):
        time.sleep(5)
        vm_fix.vm_username = 'root'
        vm_fix.vm_password = 'c0ntrail123'
        cmd = 'cd /root/vrouter-pktgen-tests/ ; (nohup ./dpdk_l3fwd.sh >/dev/null 2>&1 &) ; sleep 5'
        vm_fix.run_cmd_on_vm(cmds=[cmd],as_sudo=True, timeout=self.timeout)
        return True


    def start_dpdk_ptkgen(self,vm_fix_src,vm_fix_dst,payload):
        host = vm_fix_src.node_name
        vm_fix_src.vm_username = 'root'
        vm_fix_src.vm_password = 'c0ntrail123'
        cmd = 'rm /root/pktgen2vrouter*.log'
        vm_fix_src.run_cmd_on_vm(cmds=[cmd],as_sudo=True, timeout=self.timeout)
        cmd = 'sed -i -e s/12.1.1.4/%s/g /root/bin/dpdkgen.lua'%vm_fix_src.vm_ip
        vm_fix_src.run_cmd_on_vm(cmds=[cmd],as_sudo=True, timeout=self.timeout)
        cmd = 'sed -i -e s/12.1.1.3/%s/g /root/bin/dpdkgen.lua'%vm_fix_dst.vm_ip
        vm_fix_src.run_cmd_on_vm(cmds=[cmd],as_sudo=True, timeout=self.timeout)
        cmd = 'sed -i -e s/"size =.*"/"size = %s;"/g /root/bin/dpdkgen.lua'%payload
        vm_fix_src.run_cmd_on_vm(cmds=[cmd],as_sudo=True, timeout=self.timeout)
        #import pdb;pdb.set_trace()
        cmd = 'cd /root/bin/ ; (nohup ./dpdk_run.py >/dev/null  2>&1 &) ; sleep 5'
        vm_fix_src.run_cmd_on_vm(cmds=[cmd],as_sudo=True, timeout=self.timeout)
        return True

    def get_dpdk_results(self,vm_fix_src):
        host = vm_fix_src.node_name
        vm_fix_src.vm_username = 'root'
        vm_fix_src.vm_password = 'c0ntrail123'
        cmd = 'cat /root/pktgen2vrouter*.log'
        result = vm_fix_src.run_cmd_on_vm(cmds=[cmd],as_sudo=True, timeout=self.timeout)
        result = vm_fix_src.return_output_cmd_dict[cmd]
        self.logger.info("Result : %s "%result)
        #import pdb;pdb.set_trace()
        result = result.replace("\r", "").replace("\t","")
        self.print_results(result)
        return True

    def launch_svc_vms(self,hosts,family,image_name='dpdk-l2-no-delay'):
        # Create two virtual networks
        self.vn1_name='vn20000'
        self.vn1_subnets=['12.1.1.0/24']
        self.vn1_fq_name = "default-domain:" + self.inputs.project_name + ":" + self.vn1_name
        self.vn2_name = 'vn30000'
        self.vn2_subnets = ['13.1.1.0/24'] 
        self.vn2_fq_name = "default-domain:" + self.inputs.project_name + ":" + self.vn2_name
        self.left_rt = '2000'
        self.right_rt = '3000'
        self.vmlist = []
        self.vm_fixture = []
        self.vm_num = 1 
        self.cpu_id_0=['16','17','18','19','20','21','22','23']
        self.cpu_id_10=['8','9','10','11','12','13','14','15']
        self.cpu_id_11=['24','25','26','27','28','29','30','31']
        self.images = ['dpdk-pktgen-auto','dpdk-l3fwd-auto']

        for i in range(0,self.vm_num):
            val = random.randint(1,100000)
            self.vmlist.append("vm-test"+str(val))

        for i in range(0,len(hosts)):
            if not self.set_perf_mode(hosts[i]):
                self.logger.error("Not able to set perf mode ")
            if not self.set_nova_vcpupin(hosts[i]):
                self.logger.error("Not able to set vcpu in nova.conf")
        
        self.inputs.set_af(family)

        if family == 'v6':
            self.vn1_fixture= self.useFixture(VNFixture(project_name= self.inputs.project_name, connections= self.connections,vn_name=self.vn1_name, inputs= self.inputs,router_asn=self.inputs.router_asn, rt_number=self.inputs.mx_rt))
        else:
            self.vn1_fixture= self.useFixture(VNFixture(project_name= self.inputs.project_name, connections= self.connections,vn_name=self.vn1_name, inputs= self.inputs, subnets= self.vn1_subnets,router_asn=self.inputs.router_asn, rt_number=self.left_rt))
            self.vn2_fixture= self.useFixture(VNFixture(project_name= self.inputs.project_name, connections= self.connections,vn_name=self.vn2_name, inputs= self.inputs, subnets= self.vn2_subnets,router_asn=self.inputs.router_asn, rt_number=self.right_rt))

        assert self.vn1_fixture.verify_on_setup()
        assert self.vn2_fixture.verify_on_setup()
        # Create service instance 
        self.svc_tmp_name = 'perf_svc_template'
        self.svc_int_prefix = 'perf_vm_'
        self.svc_policy_name = 'perf_svc_policy'

        if self.set_si > 1:
            self.dpdk_svc_scaling = True

        self.perf_st_fixture , self.perf_si_fixtures = self.config_st_si(self.svc_tmp_name,
                          self.svc_int_prefix,self.vm_num,left_vn=self.vn1_fq_name ,svc_scaling=self.dpdk_svc_scaling,max_inst=self.set_si, 
                          right_vn=self.vn2_fq_name,svc_mode='in-network',svc_img_name=image_name,flavor='contrail_flavor_4cpu',
                          project=self.inputs.project_name)
        action_list = self.chain_si(self.vm_num,self.svc_int_prefix,self.inputs.project_name)

        self.project.set_sec_group_for_allow_all()
        # Create a policy 
        self.rules = [{'direction': '<>',
                 'protocol': 'any',
                 'source_network': self.vn1_name,
                 'src_ports': [0, -1],
                 'dest_network': self.vn2_name,
                 'dst_ports': [0, -1],
                 'simple_action': None,
                 'action_list': {'apply_service': action_list}
                 }]

        self.svc_policy_fixture = self.config_policy(self.svc_policy_name, self.rules)

        self.vn1_policy_fix = self.attach_policy_to_vn(
            self.svc_policy_fixture, self.vn1_fixture)
        self.vn2_policy_fix = self.attach_policy_to_vn(
            self.svc_policy_fixture, self.vn2_fixture)
        time.sleep(180)

        for host in hosts:
            if not self.update_process_cpu(host,'qemu'):
                self.logger.error("Not able to pin cpu :%s "%proc)

        # Create service instance 
        # Create a policy 
        # Attach policy to VNs
        # attach policy to service instance
        return True 

    def run_ixia_perf_tests(self,test_id,mode,proto,family,cores,si):
        self.host_list = self.connections.orch.get_hosts()
        #self.disable_hosts = self.connections.orch.get_hosts()
        self.disable_hosts = copy.deepcopy(self.host_list) 
        self.set_cpu_cores = cores
        self.set_si = si
        #self.disable_hosts = self.host_list
        host_vm = self.disable_hosts.pop(-1)

        for host in self.disable_hosts:
            if not self.set_nova_compute_service(host,'disable'):
                self.logger.error("Error in disabling nova compute")
                return False

        if mode == 'different':
            if not self.launch_svc_vms([host_vm],family):
                for host in self.host_list:
                    self.set_nova_compute_service(host,'enable')
                self.logger.error("Failed to launch VMs")
                return False
        elif mode == 'same':
            if not self.launch_svc_vms([host_vm],family):
                for host in self.host_list:
                    self.set_nova_compute_service(host,'enable')
                self.logger.error("Failed to launch VMs")
                return False
        if not self.run_ixia_throughput_tests(proto):
            for host in self.host_list:
                self.set_nova_compute_service(host,'enable')
            self.logger.error("Failed to run ixia tests")
            return False

        if not self.cleanup_vms():
            for host in self.host_list:
                self.set_nova_compute_service(host,'enable')
            self.logger.error("ERROR: In deleting service instance VM and template")
            return False

        for host in self.host_list:
                self.set_nova_compute_service(host,'enable')

        return True

    def run_ixia_throughput_tests(self,proto):
        for id in range(0,len(self.encap_type)):
            self.update_encap_mode(self.inputs.host_data[self.inputs.cfgm_ip]['host_ip'],self.encap_type[id])
            if proto == 'TCP':
                if not self.start_ixia_rfc_tests():
                    self.logger.error("ERROR in TCP throughput test")
                    return False
            if proto == 'UDP':
                if not self.start_ixia_rfc_tests():
                    self.logger.error("ERROR in TCP throughput test")
                    return False
        return True 
 
    def start_ixia_rfc_tests(self):
        cmd='(nohup python /root/scripts/qt.py > results 2>&1 &); sleep 5'
        result = self.inputs.run_cmd_on_server(self.ixia_linux_host, cmd,username='root',password='contrail123')
        self.logger.info("RFC Test Running: %s "%result)
        while True:
            if self.verify_ixia_test():
               self.logger.info("RFC Test FINISHED")
               break 
            time.sleep(60)
            self.logger.info("RFC Test Running")
        return True

    def verify_ixia_test(self):
        cmd='cat results'
        result = self.inputs.run_cmd_on_server(self.ixia_linux_host, cmd,username='root',password='contrail123')
        if not re.findall('FINISHED',result):
            return False
        elif re.findall('ERROR',result): 
            self.logger.info("RFC Test ERROR%s"%result)
            return True 
        else:
            self.logger.info("RFC Test FINISHED%s"%result)
            return True 

    def cleanup_vms(self):
        #import pdb;pdb.set_trace()
        self.delete_si_st(self.perf_si_fixtures, self.perf_st_fixture)
        self.detach_policy(self.vn1_policy_fix)
        self.detach_policy(self.vn2_policy_fix)
        self.unconfig_policy(self.svc_policy_fixture)
#        self.delete_vn(self.vn1_fixture)
#        self.delete_vn(self.vn2_fixture)
        return True

    def remove_from_cleanups(self, fix):
        for cleanup in self._cleanups:
            if fix.cleanUp in cleanup:
                self._cleanups.remove(cleanup)
                break
                

