import os
import signal
import re
import struct
import socket
import random
import test_v1
import re
from common.connections import ContrailConnections
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
from serial_scripts.perf.base import PerfBase
from tcutils.commands import *
import threading
import thread
import time
import copy

class PerfBaseDpdk(test_v1.BaseTestCase_v1,VerifySvcMirror):
    @classmethod
    def setUpClass(cls):
        super(PerfBaseDpdk, cls).setUpClass()
        cls.nova_h = cls.connections.nova_h
        cls.orch = cls.connections.orch
        cls.vnc_lib_fixture = cls.connections.vnc_lib_fixture
        cls.encap_type = ["MPLSoUDP"]
        cls.results = 'logs/results_%s'%random.randint(0,100000)
        cls.results_file = open(cls.results,"aw")
        cls.process_list = ['qemu','vhost']
        cls.duration = 100
        cls.timeout = cls.duration + 60
        cls.nova_cpu = ['8-15','24-31']
        cls.nova_cpu0 = ['0-7','16-23']
        cls.family = ''
        cls.host_list = cls.connections.orch.get_hosts() 
        cls.host_cpu_cores_8 = {}
        cls.host_cpu_cores_24 = {}
        cls.host_cpu_cores_0 = {}
        cls.host_cpu_cores_16 = {}
        cls.ixia_linux_host = '10.87.132.179'
        cls.ixia_host = '10.87.132.18'
        cls.set_cpu_cores = 4 
        cls.set_si = 1
        cls.dpdk_svc_scaling = False
        cls.nova_flavor= { '2':'contrail_flavor_2cpu','4':'contrail_flavor_4cpu', '8':'contrail_flavor_8cpu'}
        #cls.nova_flavor= { '2':'contrail_flavor_2cpu'}
        cls.vrouter_mask_list = ['0xf','0x3f','0xff','0xf000f']
        cls.bw ='40g'
        for host in cls.host_list:
            if not cls.set_perf_mode(host):
                self.logger.error("Not able to set perf mode ")
                return False
            if not cls.set_nova_vcpupin(host,cls.nova_cpu[0]):
                self.logger.error("Not able to set vcpu in nova.conf")
                return False

    #end setUpClass

    @classmethod
    def tearDownClass(cls):
        cls.results_file.close() 
        super(PerfBaseDpdk, cls).tearDownClass()

    def launch_dpdk_vms(self,hosts,family,vm_num):
        '''
        Launching VMs on specified hosts based on family 
        '''
        self.vn1_name='vn10001'
        self.vn1_subnets=['30.1.1.0/24']
        self.vm_fixtures = []
        self.vm_num = vm_num 
        self.images = ['dpdk-pktgen-auto','dpdk-l3fwd-auto']

        self.set_nova_flavor_key_delete()
        self.set_nova_flavor_key()
        if family == 'v6':
            self.vn1_fixture= self.useFixture(VNFixture(project_name= self.inputs.project_name, connections= self.connections,vn_name=self.vn1_name, inputs= self.inputs,router_asn=self.inputs.router_asn, rt_number=self.inputs.mx_rt))
        else:
            self.vn1_fixture= self.useFixture(VNFixture(project_name= self.inputs.project_name, connections= self.connections,vn_name=self.vn1_name, inputs= self.inputs, subnets= self.vn1_subnets,router_asn=self.inputs.router_asn, rt_number=self.inputs.mx_rt))

        assert self.vn1_fixture.verify_on_setup()

        image_id = 0

        for host in hosts:
            for i in range(0,self.vm_num):
                vm_name = "vm-test"+str(random.randint(1,100000))
                self.vm_fixtures.append(self.useFixture(VMFixture(project_name= self.inputs.project_name, connections= self.connections, vn_objs = [ self.vn1_fixture.obj ], vm_name= vm_name,flavor='contrail_flavor_2cpu',image_name=self.images[image_id],node_name=host)))
            image_id = 1
        time.sleep(100)


        for i in range(0,len(self.vm_fixtures)):
            assert self.vm_fixtures[i].verify_on_setup()
        for i in range(0,len(self.vm_fixtures)):
            if self.inputs.orchestrator =='vcenter':
                ret = self.orch.wait_till_vm_is_active( self.vm_fixtures[i].vm_obj )
            else:
                ret = self.nova_h.wait_till_vm_is_up( self.vm_fixtures[i].vm_obj )

            if ret == False: return {'result':ret,'msg':"%s failed to come up"%self.vm_fixtures[i].vm_name}


        for i in range(0,len(self.vm_fixtures)):
            if not self.start_v6_server(self.vm_fixtures[i]):
                self.logger.error("Not able start v6 server")
                return False

        return True


    def run_perf_tests(self,test_id,mode,proto,family):

        vm_num = 2 

        for host in self.host_list:
            self.host_cpu_cores_8[host] = ['8','9','10','11','12','13','14','15']
            self.host_cpu_cores_24[host] = ['24','25','26','27','28','29','30','31']
            self.host_cpu_cores_0[host] = ['0','1','2','3','4','5','6','7']
            self.host_cpu_cores_16[host] = ['16','17','18','19','20','21','22','23']

        self.print_results("==================================================================\n")

        if mode == 'different':
            self.print_results("DIFFERENT COMPUTE NODES\n")
            if not self.launch_dpdk_vms([self.host_list[0],self.host_list[1]],family,vm_num):
                self.logger.error("Failed to launch VMs")
        elif mode == 'same':
            self.print_results("SAME COMPUTE NODES\n")
            if not self.launch_dpdk_vms([self.host_list[0],self.host_list[0]],family,vm_num):
                self.logger.error("Failed to launch VMs")


        if self.bw == '10g':
            if test_id == 'THROUGHPUT':
                ret = self.dpdk_throughput_test(mode,proto)

            elif test_id == 'LATENCY':
                ret = self.latency_test(mode,proto)
        else:
            if test_id == 'THROUGHPUT':
                ret = self.dpdk_throughput_test_40g(mode,proto)

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

    def dpdk_throughput_test_40g(self,mode,proto):
        threads = []
        ip_list = []
        thread_id = 0

        for id in range(0,len(self.encap_type)):
            threads = []
            for payload in [64, 200, 512, 1400]:
                for th_id in range(0,self.vm_num):
                    src_id = th_id
                    dst_id = th_id + self.vm_num
                    if proto == 'TCP':
                        if not self.run_dpdk_throughput_test(self.vm_fixtures[src_id],self.vm_fixtures[dst_id],self.duration,payload):
                            self.logger.error("ERROR in TCP throughput test")
                            return False
                    if proto == 'UDP':
                        if not self.run_dpdk_throughput_test(self.vm_fixtures[src_id],self.vm_fixtures[dst_id],self.duration,payload):
                           self.logger.error("ERROR in UDP throughput test")
                           return False

                for th_id in range(0,self.vm_num):
                    src_id = th_id
                    dst_id = th_id + self.vm_num
                    ip_list.append(self.vm_fixtures[src_id].local_ip)             

                cmd = 'cd /root/bin/ ; (nohup ./dpdk_run.py >/dev/null  2>&1 &) ; sleep 5'
                if not self.run_parallel_cmds_on_vms(self.vm_fixtures[0].vm_node_data_ip,ip_list,[cmd],True):
                    self.logger.error("ERROR parallel commands")
                    return False

                time.sleep(self.timeout)
                for th_id in range(0,self.vm_num):
                    src_id = th_id
                    dst_id = th_id + self.vm_num
                    if not self.get_dpdk_results(self.vm_fixtures[src_id]):
                        self.logger.error("ERROR in getting results")
                        return False

        return True



    def run_dpdk_throughput_test(self,src_vm_hdl,dest_vm_hdl,duration,payload):
        result = self.start_dpdk_l3fwd(dest_vm_hdl,duration)
        perf_list = []
        time.sleep(5)
        result = self.start_dpdk_ptkgen(src_vm_hdl,dest_vm_hdl,payload)
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
        cmd = 'sed -i -e s/20.1.1.3/%s/g /root/bin/dpdkgen.lua'%vm_fix_src.vm_ip
        vm_fix_src.run_cmd_on_vm(cmds=[cmd],as_sudo=True, timeout=self.timeout)
        cmd = 'sed -i -e s/20.1.1.4/%s/g /root/bin/dpdkgen.lua'%vm_fix_dst.vm_ip
        vm_fix_src.run_cmd_on_vm(cmds=[cmd],as_sudo=True, timeout=self.timeout)
        cmd = 'sed -i -e s/"size =.*"/"size = %s;"/g /root/bin/dpdkgen.lua'%payload
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
        result = result.replace("\r", "").replace("\t","")
        self.print_results(result)
        return True

    def set_nova_compute_service(self,host,mode):
        username = self.inputs.host_data[self.inputs.openstack_ip]['username']
        password = self.inputs.host_data[self.inputs.openstack_ip]['password']
        with hide('everything'):
            with settings(
                host_string='%s@%s' % (username, self.inputs.openstack_ip),
                    password=password):
                services_info = run(
                    'source /etc/contrail/openstackrc; nova service-%s %s nova-compute'%(mode,host))
            
        return True

    @classmethod
    def set_nova_flavor_key(self):
        username = self.inputs.host_data[self.inputs.openstack_ip]['username']
        password = self.inputs.host_data[self.inputs.openstack_ip]['password']
        with hide('everything'):
            with settings(
                host_string='%s@%s' % (username, self.inputs.openstack_ip),
                    password=password):
                    for cpu in self.nova_flavor.keys():
                        run('source /etc/contrail/openstackrc; nova flavor-create --is-public true %s auto 4096 80 %s --rxtx-factor 1.0'%(self.nova_flavor[cpu],int(cpu)))
                        run('source /etc/contrail/openstackrc; nova flavor-key  %s set hw:mem_page_size=large'%self.nova_flavor[cpu])
        return True

    @classmethod
    def set_nova_flavor_key_delete(self):
        username = self.inputs.host_data[self.inputs.openstack_ip]['username']
        password = self.inputs.host_data[self.inputs.openstack_ip]['password']
        with hide('everything'):
            with settings(
                host_string='%s@%s' % (username, self.inputs.openstack_ip),
                    password=password):
                    for cpu in self.nova_flavor.keys():
                        run('source /etc/contrail/openstackrc; nova flavor-delete %s'%self.nova_flavor[cpu])
        return True

    def print_results(self,result):
        self.results_file.write(result)

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
        self.vm_num = 4 
        self.cpu_id_0=['16','17','18','19','20','21','22','23']
        self.cpu_id_10=['8','9','10','11','12','13','14','15']
        self.cpu_id_11=['24','25','26','27','28','29','30','31']
        self.images = ['dpdk-pktgen-auto','dpdk-l3fwd-auto']
        self.set_nova_flavor_key_delete()
        self.set_nova_flavor_key()

        for i in range(0,self.vm_num):
            val = random.randint(1,100000)
            self.vmlist.append("vm-test"+str(val))

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
                          right_vn=self.vn2_fq_name,svc_mode='in-network',svc_img_name=image_name,flavor=self.nova_flavor[str(self.set_cpu_cores)],
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
            if not self.update_process_cpu_dpdk(host,'qemu'):
                self.logger.error("Not able to pin cpu :%s "%proc)

        return True 

    def run_ixia_perf_tests(self,test_id,mode,proto,family,cores,si):
        self.host_list = self.connections.orch.get_hosts()
        self.disable_hosts = copy.deepcopy(self.host_list) 
        self.set_cpu_cores = cores
        self.set_si = si
        self.encap_type = ["MPLSoGRE"]
        host_vm = self.disable_hosts.pop(-1)
        self.set_nova_flavor_key_delete()
        self.set_nova_flavor_key()

        for host in self.disable_hosts:
            if not self.set_nova_compute_service(host,'disable'):
                self.logger.error("Error in disabling nova compute")
                return False

        for vrouter_mask in self.vrouter_mask_list:
            self.print_results("==================================================================\n")
            test_log  = 'vrouter mask : %s , VM cpu cores : %s , mode : %s , protocol : %s ' % \
                             (vrouter_mask,cores,mode,proto) 
            self.print_results(test_log) 
            self.set_vrouter_vcpupin(host_vm,vrouter_mask)
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

            cmd = 'cat /root/AggregateResults.csv; sleep 5 ; rm /root/AggregateResults.csv'
            res = self.inputs.run_cmd_on_server(self.inputs.cfgm_ip,cmd)
            self.logger.info(res)
            self.print_results(res) 
            self.print_results("==================================================================\n")

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
            cmd='cat results | grep ResultPath'
            result = self.inputs.run_cmd_on_server(self.ixia_linux_host, cmd,username='root',password='contrail123')
            self.update_results(result)
            return True 

    def update_results(self,result):
        result = result.replace("\r","")
        result = result.split("\n")
        res = str(result).strip('[]').strip('\'')
        res=res.replace('\\','/').replace('ResultPath:  /root/C://Users//Administrator//Desktop','%s'%self.ixia_host)+'/AggregateResults.csv'
        self.logger.info("Result : %s "%res)
        cmd = 'wget %s'%res
        res = self.inputs.run_cmd_on_server(self.inputs.cfgm_ip,cmd)
        return True
 
    def cleanup_vms(self):
        self.delete_si_st(self.perf_si_fixtures, self.perf_st_fixture)
        self.detach_policy(self.vn1_policy_fix)
        self.detach_policy(self.vn2_policy_fix)
        self.unconfig_policy(self.svc_policy_fixture)
        return True

    def remove_from_cleanups(self, fix):
        for cleanup in self._cleanups:
            if fix.cleanUp in cleanup:
                self._cleanups.remove(cleanup)
                break
                
    def update_process_cpu_dpdk(self,host,name):
        cmd = 'ps ax | pgrep %s'%name
        res = self.inputs.run_cmd_on_server(host, cmd)
        res = res.replace("\r","")
        res = res.split("\n")
        for id in res:
            self.logger.info("Process Id : %s "%id)
            cmd = 'taskset -pc %s'%id
            task_out = self.inputs.run_cmd_on_server(host, cmd)
            task_out=task_out.split(" ")
            self.logger.info("cpu mask :%s "%task_out[5])

            if re.findall("8-15",task_out[5]):
               if not self.set_task_pin_dpdk(host,self.cpu_id_10,id):
                    self.logger.error("Error in pinnng cpu :%s "%cmd)
            elif re.findall("24-31",task_out[5]):
                if not self.set_task_pin_dpdk(host,self.cpu_id_11,id):
                    self.logger.error("Error in pinnng cpu :%s "%cmd)
                    return False 
            elif re.findall("0-7",task_out[5]):
                if not self.set_task_pin_dpdk(host,self.cpu_id_00,id):
                    self.logger.error("Error in pinnng cpu :%s "%cmd)
                    return False 
            elif re.findall("16-23",task_out[5]):
                if not self.set_task_pin_dpdk(host,self.cpu_id_0,id):
                    self.logger.error("Error in pinnng cpu :%s "%cmd)
                    return False 

        return True

    def get_cpu_core_dpdk(self,cpu_id):
        if len(cpu_id):
            return cpu_id.pop(0) 
        else:
            return False

    def set_task_pin_dpdk(self,host,cpu_id,pid):
        cpu_core = self.get_cpu_core_dpdk(cpu_id)
        if not cpu_core:
            self.logger.error("Not able to get cpu core")
            return False
        for i in range(1,(self.set_cpu_cores)) :
            cpu_core1 = self.get_cpu_core_dpdk(cpu_id)
        cmd = 'taskset -a -pc %s-%s %s'%(cpu_core,str(cpu_core1),pid)
        task_out = self.inputs.run_cmd_on_server(host, cmd)
        cmd = 'taskset -pc %s'%pid
        task_out = self.inputs.run_cmd_on_server(host, cmd)
        task_out=task_out.split(" ")
        self.logger.info("cpu mask :%s "%task_out[5])
        return True 

    @classmethod
    def set_perf_mode(self,host):
        cmd='for f in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor ; do echo performance > $f; cat $f; done'
        out = self.inputs.run_cmd_on_server(host, cmd)
        cmd='service  irqbalance stop'
        out = self.inputs.run_cmd_on_server(host, cmd)
        cmd = 'cat /etc/*-release'
        out = self.inputs.run_cmd_on_server(host, cmd)
        if re.findall('Ubuntu',out):
            cmd='mac=$(maclist=$(ifconfig vhost0 | awk {\'print $5\'}) ; echo $maclist | sed s/MTU.*$//g) ; \
                intfs=$(ifconfig | grep $mac | awk {\'print $1\'} | sed s/vhost0//g | sed s/bond0//g ); \
                for intf in $intfs ; do for i in $(grep $intf /proc/interrupts | awk {\'print $1\'} | sed s/://g); \
                do echo "8000" > /proc/irq/"$i"/smp_affinity ; done ; done '
        else:
             cmd='intfs=$(cat /proc/net/bonding/bond0 | grep Interface | awk {\'print $3\'} ); \
                for intf in $intfs ; do for i in $(grep $intf /proc/interrupts | awk {\'print $1\'} | sed s/://g); \
                do echo "8000" > /proc/irq/"$i"/smp_affinity ; done ; done '
        out = self.inputs.run_cmd_on_server(host, cmd)
        return True

    @classmethod
    def set_nova_vcpupin(self,host,cpu):
        cmd='openstack-config --set /etc/nova/nova.conf DEFAULT vcpu_pin_set %s'%cpu
        out = self.inputs.run_cmd_on_server(host, cmd)
        cmd='service nova-compute restart'
        out = self.inputs.run_cmd_on_server(host, cmd)
        return True

    def set_vrouter_vcpupin(self,host,mask):
        cmd='sed -i -e s/0x.[A-Za-z0-9]*/%s/  /etc/contrail/supervisord_vrouter_files/contrail-vrouter-dpdk.ini ;sleep 4'%mask
        out = self.inputs.run_cmd_on_server(host, cmd)
        cmd='service supervisor-vrouter restart'
        out = self.inputs.run_cmd_on_server(host, cmd)
        time.sleep(30)
        return True


    def run_parallel_cmds_on_vms(self,host,ip_list, cmds=[],as_sudo=False, timeout=30, as_daemon=False):
        '''run cmd on VMs in parallel
        '''
        self.return_output_cmd_dict = {}
        self.return_output_values_list = []
        cmdList = cmds
        vm_username='root'
        vm_password='c0ntrail123'
        output = ''
        try:
            self.orch.put_key_file_to_host(self.inputs.host_data[host]['host_ip'])
            fab_connections.clear()
            with hide('everything'):
                with settings(
                    host_string='%s@%s' % (self.inputs.host_data[host]['username'], self.inputs.host_data[host]['host_ip']),
                    password=self.inputs.host_data[host]['password'],
                        warn_only=True, abort_on_prompts=False):
                    for cmd in cmdList:
                        self.logger.debug('Running Cmd on %s %s' % (ip_list , cmd))
                        output = run_parallel_on_node( ip_list, username=vm_username, password=vm_password, cmds=cmd)
                        self.logger.debug(output)
                        self.return_output_values_list.append(output)
                    self.return_output_cmd_dict = dict(
                        zip(cmdList, self.return_output_values_list))
            return self.return_output_cmd_dict
        except Exception, e:
            self.logger.exception(
                'Exception occured while trying ping from VM')
            return self.return_output_cmd_dict
