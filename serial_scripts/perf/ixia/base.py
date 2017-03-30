import sys
import os
import subprocess
import signal
import re
import struct
import socket
import random
import inspect
#from fabric.state import connections as fab_connections
import test_v1
import re
from common.connections import ContrailConnections
from common.device_connection import NetconfConnection
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

class PerfBaseIxia(PerfBase,VerifySvcMirror):

    @classmethod
    def setUpClass(cls):
        super(PerfBaseIxia, cls).setUpClass()
        cls.nova_h = cls.connections.nova_h
        cls.orch = cls.connections.orch
        cls.vnc_lib_fixture = cls.connections.vnc_lib_fixture
        cls.encap_type = ["MPLSoUDP","MPLSoGRE"]
        cls.spirent_linux_user = 'root'
        cls.spirent_linux_passwd = 'n1keenA'
        cls.family = ''
        cls.ixia_linux_host = '10.87.132.179'
        cls.ixia_host = '10.87.132.18'
        cls.spirent_linux_host = '10.87.132.185'
        cls.set_cpu_cores = 4 
        cls.set_si = 1
        cls.dpdk_svc_scaling = False
        cls.nova_flavor= { '2':'perf_flavor_2','3':'perf_flavor_3','4':'perf_flavor_4', '8':'perf_flavor_8'}
        #cls.image_flavor= { '1':'perf-ubuntu-1404', '2':'ubuntu-perf-multique-2', '3':'dpdk-l2-no-delay','4':'ubuntu-perf-multique-4','5':'perf-ubuntu-netronome'}
        cls.image_flavor= { '1':'perf-ubuntu-1404', '2':'ubuntu-perf-multique-2', '3':'dpdk_l2fwd_sleep3','4':'ubuntu-perf-multique-4','5':'dpdk-l2-no-delay-new','6':'tiny_in-net','7':'dpdk-l3fwd-mq-2','8':'perf-ubuntu-1404-v6-2','8':'perf-ubuntu-netronome','9':'DPDK-l2fwd-virtio-new'}
        cls.vrouter_mask_list = ['0xf','0x3f','0xff','0xf000f']
        cls.mx1_ip = '10.87.64.246'
        cls.mx2_ip = '10.87.140.181'
        cls.mx_user = 'root'
        cls.mx_password = 'Embe1mpls'
        cls.mx1_handle = NetconfConnection(host = cls.mx1_ip,username=cls.mx_user,password=cls.mx_password)
        cls.mx1_handle.connect()
        cls.mx2_handle = NetconfConnection(host = cls.mx2_ip,username=cls.mx_user,password=cls.mx_password)
        cls.mx2_handle.connect()
        #cls.create_availability_zone()
 

    @classmethod
    def tearDownClass(cls):
        cls.results_file.close() 
        super(PerfBaseIxia, cls).tearDownClass()
        if not cls.set_nova_flavor_key_delete():
            self.logger.error("ERROR: In deleting flavor keys")
            return False

    def run_perf_tests(self,test_id,mode,proto,family):
        vm_num = 1
#        for host in self.host_list:
#            self.host_cpu_cores_8[host] = ['8','9','10','11','12','13']
#            if not self.update_vrouter_sysctl(host,self.host_cpu_cores_8[host]):
#                self.logger.error("Error in updating sysctl")
#                return False

        self.inputs.set_af(family)

        self.print_results("\n==================================================================\n")

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

        self.print_results("\n==================================================================\n")

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
        for payload in  [ 64, 128, 512, 1400 ]:
            perf_list = []
            time.sleep(5)
            result = self.start_dpdk_ptkgen(src_vm_hdl,dest_vm_hdl,payload)
            time.sleep(200)
            result = "PAYLOAD : %s TCP %s THROUGHPUT :  : \n"%(payload ,self.inputs.get_af())
            self.logger.info("Result : %s "%result)
            self.print_results(result)
            self.get_dpdk_results(src_vm_hdl)
        time.sleep(10)
        return True

    def start_dpdk_l2fwd(self,vm_fix,delay):
        time.sleep(5)
        vm_fix.vm_username = 'root'
        vm_fix.vm_password = 'c0ntrail123'
        #cmd = '(nohup ./start_l2fwd_app.sh >/dev/null 2>&1 &) ; sleep 5'
        cmd = '(nohup /root/l2fwd_tests/l2fwd_start.sh >/dev/null 2>&1 &) ; sleep 5'
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
                        run('source /etc/contrail/openstackrc; nova flavor-key  %s set hw:mem_page_size=large'%self.nova_flavor[cpu])
        return True

    @classmethod
    def set_nova_flavor_key_delete_bak(self):
        username = self.inputs.host_data[self.inputs.openstack_ip]['username']
        password = self.inputs.host_data[self.inputs.openstack_ip]['password']
        with hide('everything'):
            with settings(
                host_string='%s@%s' % (username, self.inputs.openstack_ip),
                    password=password):
                    for cpu in self.nova_flavor.keys():
                        run('source /etc/contrail/openstackrc; nova flavor-delete %s'%self.nova_flavor[cpu])
 
        return True

    @classmethod
    def set_nova_flavor_key_delete(self):
        username = self.inputs.host_data[self.inputs.openstack_ip]['username']
        password = self.inputs.host_data[self.inputs.openstack_ip]['password']
        cmd = 'source /etc/contrail/openstackrc; nova flavor-list | grep perf_flavor | awk {\'print $4\'}'
        res = self.inputs.run_cmd_on_server(self.inputs.openstack_ip, cmd)
        res = res.replace("\r","")
        res = res.split("\n")
        for flavor in res:
            cmd = 'source /etc/contrail/openstackrc; nova flavor-delete %s'%flavor
            res = self.inputs.run_cmd_on_server(self.inputs.openstack_ip, cmd)
        return True

    def launch_svc_vms(self,hosts,family,image_name='dpdk-l2-no-delay',zone_name='nova', left_rt='2000',right_rt='3000'):
        # Create two virtual networks
        self.vn1_name='vn100-left'
        self.vn1_subnets=['12.0.0.0/8','2005::/64']
        self.vn1_fq_name = "default-domain:" + self.inputs.project_name + ":" + self.vn1_name
        self.vn2_name = 'vn100-right'
        self.vn2_subnets = ['13.0.0.0/8','2006::/64'] 
        self.vn2_fq_name = "default-domain:" + self.inputs.project_name + ":" + self.vn2_name
        self.left_rt = left_rt 
        self.right_rt = right_rt 
        self.vmlist = []
        self.vm_fixture = []
        self.vm_num = 1 
        self.version = '2'
        self.zone = zone_name
        self.cpu_id_0=['0','1','2','3','4','5','8','9','10','11','12','13']
        self.cpu_id_00=['3','4','5','6','7','8','9','10','11']
        self.cpu_id_10=['8','9','10','11','12','13','14','15']
        #self.cpu_id_10=['14','15','16','17','18','19','20','21','22','23','24','25','26','27']
        self.cpu_id_11=['24','25','26','27','28','29','30','31']
        self.userdata = '/tmp/metadata_script.txt'

        for i in range(0,self.vm_num):
            val = random.randint(1,100000)
            self.vmlist.append("vm-test"+str(val))
        
        self.inputs.set_af(family)

        self.create_startup_script_queues('2')

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
   

        if self.version == '2':
            self.perf_st_fixture , self.perf_si_fixtures = self.config_st_si(self.svc_tmp_name,
                          self.svc_int_prefix,self.vm_num,left_vn=self.vn1_fq_name ,svc_scaling=self.dpdk_svc_scaling,max_inst=self.set_si, 
                          right_vn=self.vn2_fq_name,svc_mode='in-network',svc_img_name=image_name,flavor=self.nova_flavor[str(self.set_cpu_cores)],
			  project=self.inputs.project_name,st_version=2,zone=self.zone)

        else : 
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

        for host in self.host_list:
            if not self.update_process_cpu_virt(host,'qemu'):
                self.logger.error("Not able to pin cpu :%s "%'qemu')

        if image_name != 'dpdk-l2-no-delay-new' or image_name != 'dpdk_l2fwd_sleep3':
            for host in self.host_list:
                if not self.update_process_cpu_virt(host,'vhost'):
                    self.logger.error("Not able to pin cpu :%s "%'vhost')
                if not self.update_txquelen(host):
                    self.logger.error("Not able to update tap")
        return True 

    def create_availability_zone(self):
        host_list = self.connections.orch.get_hosts() 
        #kvm = self.inputs.get_node_name(self.inputs.compute_names[1])
        #cmd = 'source /etc/contrail/openstackrc; nova aggregate-create kvm kvm-az ; nova aggregate-add-host kvm %s' %(kvm)
        #res = self.inputs.run_cmd_on_server(self.inputs.cfgm_ip,cmd)
        if self.inputs.dpdk_data != [{}]:
            dpdk_ip = re.findall( r'[0-9]+(?:\.[0-9]+){3}',str(self.inputs.dpdk_data))
            dpdk = self.inputs.get_node_name(dpdk_ip[0])
            cmd = 'source /etc/contrail/openstackrc; nova aggregate-create dpdk dpdk-az ; nova aggregate-add-host dpdk %s' %(dpdk)
            res = self.inputs.run_cmd_on_server(self.inputs.cfgm_ip,cmd)
        netronome = '5b4s25'
        cmd = 'source /etc/contrail/openstackrc; nova aggregate-create netronome netronome-az ; nova aggregate-add-host netronome %s' %(netronome)
        res = self.inputs.run_cmd_on_server(self.inputs.cfgm_ip,cmd)
        return True 

    def run_ixia_perf_tests_pps(self,test_id,proto,family,cores,si,image_id,encap='MPLSoGRE'):
        self.host_list = self.connections.orch.get_hosts()
        self.disable_hosts = copy.deepcopy(self.host_list) 
        self.set_cpu_cores = cores
        self.set_si = si
        self.encap_type = ["MPLSoGRE"]
        # DEBUG MX
        self.set_nova_flavor_key_delete()
        self.configure_mx(encap,self.mx1_handle) 
        #self.configure_mx(encap,self.mx2_handle) 
        self.restart_control()
        self.add_image(image_id)
        zone = 'nova'
        host_vm = self.inputs.get_node_name(self.inputs.compute_names[0])
        if image_id == 3 or  image_id == 7:
            zone = 'dpdk-az'
            host_ip = re.findall( r'[0-9]+(?:\.[0-9]+){3}',str(self.inputs.dpdk_data))
            host_vm = self.inputs.get_node_name(host_ip[0])
        if image_id == 5 or image_id == 9:
            zone = 'netronome-az' 

        self.create_availability_zone()
	if not self.launch_svc_vms([host_vm],family,self.image_flavor[str(image_id)],zone, '2000','3000'):
             self.logger.error("Failed to launch VMs")
             return False
        for host in self.host_list:
            self.set_perf_mode_jumbo(host)

        if image_id == 2 or image_id == 4 :
            for host in self.host_list:
                self.set_perf_mode_disable(host)
        if image_id == 7 :
            self.start_dpdk_mq_app()
        
        time.sleep(300)
        if not self.run_ixia_throughput_tests(proto,test_id):
            self.logger.error("Failed to run ixia tests")
            return False
        cmd = 'cat /root/AggregateResults.csv; sleep 5 ; rm /root/AggregateResults.csv'
        res = self.inputs.run_cmd_on_server(self.inputs.cfgm_ip,cmd)
        self.logger.info(res)
        out = '\ntest: %s \nencap : %s   cores : %s  family: %s  instances : %s \n'%(inspect.stack()[1][3],encap,cores,family,si)
        self.print_results("test_profile: %s"%test_id) 
        self.print_results(out) 
        self.print_results(res) 
        self.print_results("\n==================================================================\n")
        
        return True

    def add_image(self,image_id):
        self.connections.nova_h.get_image(self.image_flavor[str(image_id)])
        for cpu in self.nova_flavor.keys():
            self.connections.nova_h.get_flavor(self.nova_flavor[cpu])
        if image_id == 2 or image_id == 4 or image_id == 7 :
            cmd='source /etc/contrail/openstackrc; nova image-meta %s set hw_vif_multiqueue_enabled=\"true\"' %(self.image_flavor[str(image_id)])
            print cmd
            ret = self.inputs.run_cmd_on_server(self.inputs.cfgm_ip, cmd)
            print ret 

        #DPDK and Netronome
        if image_id == 3 or image_id == 5 or image_id == 7 or image_id == 9: 
            self.set_nova_flavor_key()

    def run_spirent_perf_test(self,test_id,proto,family,cores,si,image_id,encap='MPLSoGRE'):
        self.host_list = self.connections.orch.get_hosts()
        self.disable_hosts = copy.deepcopy(self.host_list)
        self.set_cpu_cores = cores
        self.set_si = si
        self.encap_type = ["MPLSoGRE"]
        self.set_nova_flavor_key_delete()
        self.configure_mx(encap,self.mx1_handle) 
        #self.configure_mx(encap,self.mx2_handle) 
        self.restart_control()
        host_vm = self.disable_hosts.pop(-1)
        self.add_image(image_id)
        freemem=0
        freemem1=0
        zone = 'nova'
        host_vm = self.inputs.get_node_name(self.inputs.compute_names[0])
        if image_id == 3:
            zone = 'dpdk-az'
            host_ip = re.findall( r'[0-9]+(?:\.[0-9]+){3}',str(self.inputs.dpdk_data))
            host_vm = self.inputs.get_node_name(host_ip[0])
        if image_id == 5 or image_id == 9:
            zone = 'netronome-az' 
        self.create_availability_zone()

        self.add_image(image_id)
        if not self.launch_svc_vms([host_vm],family,self.image_flavor[str(image_id)],zone,'1','2'):
            for host in self.host_list:
                self.set_nova_compute_service(host,'enable')
            self.logger.error("Failed to launch VMs")
            return False

        for host in self.host_list:
            self.set_perf_mode_jumbo(host)
            cmd="cat /proc/meminfo | grep MemFree | awk \{'print $2'\}" 
            freemem = self.inputs.run_cmd_on_server(host, cmd)
            print freemem            
        time.sleep(300)
        self.update_url_list(self.spirent_linux_passwd, self.spirent_linux_user, self.spirent_linux_host, test_id)
        if not self.start_spirent_traffic(self.spirent_linux_passwd, self.spirent_linux_user, self.spirent_linux_host, test_id):
            self.logger.error("Failed to run Spirent tests")
            return False

        if not self.get_spirent_result(self.spirent_linux_passwd, self.spirent_linux_user, self.spirent_linux_host, test_id):
            self.logger.error("Failed to collect test results")
            return False
        for host in self.host_list:
            cmd="cat /proc/meminfo | grep MemFree | awk \{'print $2'\}" 
            freemem1 = self.inputs.run_cmd_on_server(host, cmd)
            print freemem1          
        self.logger.info("Initial Memory: %s"%freemem) 
        self.logger.info("Final Memory: %s"%freemem1) 

        return True

    def start_spirent_traffic (self, web_server_password, web_server_username, web_server, script_name):
        cmd = "service contrail-control restart; sleep 5" 
        print cmd
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            print line,
        retval = p.wait()
        cmd = "rm -rf /root/spirent/tests/%s/results; source /root/.bash_profile ;(nohup tclsh /root/spirent/tests/%s/test.tcl > results 2>&1 &); sleep 5" %(script_name, script_name)
        result = self.inputs.run_cmd_on_server(self.spirent_linux_host, cmd, web_server_username, web_server_password)
        self.logger.info("Spirent Test Running: %s "%result)
        while True:
            if self.verify_spirent_test(web_server_username, web_server_password):
               self.logger.info("Finished running")
               break
            time.sleep(60)
            self.logger.info("Spirent Test Running")
        return True


    def get_spirent_result (self, web_server_password, web_server_username, web_server, script_name):
        cmd = "mkdir /var/www/html/tests/results/%s/; id=$(uuidgen); mkdir /var/www/html/tests/results/%s/$id ; cp -r /root/spirent/tests/%s/results/ /var/www/html/tests/results/%s/$id/; sleep 1" %(script_name, script_name, script_name, script_name)
        result = self.inputs.run_cmd_on_server(self.spirent_linux_host, cmd, web_server_username, web_server_password)
        cmd = "mkdir %s ; rm -rf %s/*; sshpass -p %s scp -o StrictHostKeyChecking=no -r %s@%s:/root/spirent/tests/%s/results %s" %(script_name, script_name, web_server_password, web_server_username, web_server, script_name, script_name)
        print cmd
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            print line,
        retval = p.wait()
        return True


    def run_ixia_throughput_tests(self,proto,script_name):
        for id in range(0,len(self.encap_type)):
            if proto == 'TCP':
                if not self.start_ixia_rfc_tests(script_name):
                    self.logger.error("ERROR in TCP throughput test")
                    return False
            if proto == 'UDP':
                if not self.start_ixia_rfc_tests(script_name):
                    self.logger.error("ERROR in TCP throughput test")
                    return False
        return True 
 
    def start_ixia_rfc_tests(self,script_name):
        #cmd='(nohup python /root/scripts/qt.py > results 2>&1 &); sleep 5'
        cmd='(nohup python /root/scripts/qt.py  /root/scripts/profiles/%s  > results 2>&1 &); sleep 5' %(script_name)
        result = self.inputs.run_cmd_on_server(self.ixia_linux_host, cmd,username='root',password='contrail123')
        self.logger.info("RFC Test Running: %s "%result)
        while True:
            if self.verify_ixia_test(script_name):
               self.logger.info("RFC Test FINISHED")
               break 
            time.sleep(60)
            self.logger.info("RFC Test Running")
        return True

    def verify_ixia_test(self,script_name):
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
            self.update_results(script_name+ " : " + result)
            return True 

    def update_url_list(self, web_server_password, web_server_username, web_server, script_name):
        url_list=self.get_ip_list()
        cmd = "cp /root/spirent/tests/%s/data/urls/TP_KVM_Left_template /root/spirent/tests/%s/data/urls/TP_KVM_Left" %(script_name,script_name)
        result = self.inputs.run_cmd_on_server(self.spirent_linux_host, cmd, web_server_username, web_server_password)
        i=1
        list_len=len(url_list)/2
        url_left=url_list[0:list_len]
        url_right=url_list[-list_len:]
        for ip in url_left:
           cmd = "sed -i 's/left_IP_%s/%s/' /root/spirent/tests/%s/data/urls/TP_KVM_Left" %(i, ip, script_name)
           result = self.inputs.run_cmd_on_server(self.spirent_linux_host, cmd, web_server_username, web_server_password)
           i=i+1
        i=1
        cmd = "cp /root/spirent/tests/%s/data/urls/TP_KVM_Left_2_template /root/spirent/tests/%s/data/urls/TP_KVM_Left_2" %(script_name,script_name)
        result = self.inputs.run_cmd_on_server(self.spirent_linux_host, cmd, web_server_username, web_server_password)
        for ip in url_right:
           cmd = "sed -i 's/right_IP_%s/%s/' /root/spirent/tests/%s/data/urls/TP_KVM_Left_2" %(i, ip, script_name)
           result = self.inputs.run_cmd_on_server(self.spirent_linux_host, cmd, web_server_username, web_server_password)
           i=i+1
        return True

    def verify_spirent_test(self, username, password):
        cmd='cat results'
        result = self.inputs.run_cmd_on_server(self.spirent_linux_host, cmd,username ,password )
        if not re.findall('Finished running',result):
           return False
        elif re.findall('ERROR',result):
            self.logger.info("Spirent Test ERROR%s"%result)
            return True
        else:
            self.logger.info("Spirent Test FINISHED%s"%result)
            cmd='cat results | grep ResultPath'
            result = self.inputs.run_cmd_on_server(self.spirent_linux_host, cmd,username ,password)
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
        self.detach_policy(self.vn1_policy_fix)
        self.detach_policy(self.vn2_policy_fix)
        self.unconfig_policy(self.svc_policy_fixture)
        self.delete_si_st(self.perf_si_fixtures, self.perf_st_fixture)
        return True

    def remove_from_cleanups(self, fix):
        for cleanup in self._cleanups:
            if fix.cleanUp in cleanup:
                self._cleanups.remove(cleanup)
                break


    def get_cpu_core_virt(self,cpu_id):
        if len(cpu_id):
            return cpu_id.pop(0) 
        else:
            return False

    def set_task_pin_virt(self,host,cpu_id,pid,cpu_cores):
        cpu_core = self.get_cpu_core_virt(cpu_id) 
        cpu_core1 = cpu_core
        if not cpu_core:
            self.logger.error("Not able to get cpu core")
            return False
        if cpu_cores > 1 :
            for i in range(1,(cpu_cores)) :
                cpu_core1 = self.get_cpu_core_virt(cpu_id)
        cmd = 'taskset -a -pc %s-%s %s'%(cpu_core,str(cpu_core1),pid)
        task_out = self.inputs.run_cmd_on_server(host, cmd)
        cmd = 'taskset -pc %s'%pid
        task_out = self.inputs.run_cmd_on_server(host, cmd)
        task_out=task_out.split(" ")
        self.logger.info("cpu mask :%s "%task_out[5])
        return True 

    def update_txquelen(self,host):
        cmd = 'for i in $(ifconfig | grep tap | awk {\'print $1\'}) ; do ifconfig $i txqueuelen 1000000 ; done'
        res = self.inputs.run_cmd_on_server(host, cmd)
        return True

    def update_mtu(self,host,mtu):
        cmd = 'for i in $(ifconfig | grep vhost | awk {\'print $1\'}) ; do ifconfig $i mtu %s ; done'%(mtu)
        res = self.inputs.run_cmd_on_server(host, cmd)
        cmd = 'for i in $(ifconfig | grep bond0 | awk {\'print $1\'}) ; do ifconfig $i mtu %s ; done'%(mtu)
        res = self.inputs.run_cmd_on_server(host, cmd)
        return True

    #This is hardcoded. Need to fix it
    def set_perf_mode_jumbo(self,host):
        cmd='for intf in p1p2 p2p2 ; do for i in $(grep $intf /proc/interrupts | awk {\'print $1\'} | sed s/://g);  do echo "8,80" > /proc/irq/"$i"/smp_affinity ; done ; done'
        #cmd='for intf in p1p2 p2p2 ; do for i in $(grep $intf /proc/interrupts | awk {\'print $1\'} | sed s/://g);  do echo "0,300" > /proc/irq/"$i"/smp_affinity ; done ; done'
        out = self.inputs.run_cmd_on_server(host, cmd)
        cmd='for intf in p1p1 p2p1 ; do for i in $(grep $intf /proc/interrupts | awk {\'print $1\'} | sed s/://g);  do echo "4,40" > /proc/irq/"$i"/smp_affinity ; done ; done'
        #cmd='for intf in p1p1 p2p1 ; do for i in $(grep $intf /proc/interrupts | awk {\'print $1\'} | sed s/://g);  do echo "0,C00" > /proc/irq/"$i"/smp_affinity ; done ; done'
        out = self.inputs.run_cmd_on_server(host, cmd)
        return True

    def update_process_cpu_virt(self,host,name):
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

            if re.findall("28-41",task_out[5]):
               if not self.set_task_pin_virt(host,self.cpu_id_10,id,self.set_cpu_cores):
                    self.logger.error("Error in pinnng cpu :%s "%cmd)
        #        del self.cpu_id_10[0]
            elif re.findall("24-31",task_out[5]):
                if not self.set_task_pin_virt(host,self.cpu_id_11,id,self.set_cpu_cores):
                    self.logger.error("Error in pinnng cpu :%s "%cmd)
                    return False 
        #        del self.cpu_id_11[0]
            elif re.findall("0-11",task_out[5]):
                if not self.set_task_pin_virt(host,self.cpu_id_00,id,self.set_cpu_cores):
                    self.logger.error("Error in pinnng cpu :%s "%cmd)
                    return False 
            elif re.findall("16-23",task_out[5]):
                if not self.set_task_pin_virt(host,self.cpu_id_0,id,self.set_cpu_cores):
                    self.logger.error("Error in pinnng cpu :%s "%cmd)
                    return False 
            elif re.findall("0-31|0-55",task_out[5]):
                if name == 'qemu':
                    if not self.set_task_pin_virt(host,self.cpu_id_0,id,self.set_cpu_cores):
                        self.logger.error("Error in pinnng cpu :%s "%cmd)
                        return False 
                if name == 'vhost':
                    if not self.set_task_pin_virt(host,self.cpu_id_0,id,1):
                        self.logger.error("Error in pinnng cpu :%s "%cmd)
                        return False 
        #        del self.cpu_id_0[0]
        return True


    def configure_mx(self,encap,handle):
        cmd = []
        if encap == 'MPLSoUDP':
            if handle.host  == self.mx1_ip: 
                cmd.append('set groups ixia_flow routing-options dynamic-tunnels contrail udp')
                cmd.append('set groups ixia_flow protocols bgp group contrail export test1-export')
            elif handle.host == self.mx2_ip: 
                cmd.append('set groups __contrail__ routing-options dynamic-tunnels __contrail__ udp')
                cmd.append('set groups __contrail__ protocols bgp group __contrail__ export test1-export') 

        elif encap == 'MPLSoGRE':
            if handle.host  == self.mx1_ip: 
                cmd.append('set groups ixia_flow routing-options dynamic-tunnels contrail gre')
                cmd.append('delete groups ixia_flow protocols bgp group contrail export test1-export')
            elif handle.host == self.mx2_ip: 
                cmd.append('set groups __contrail__ routing-options dynamic-tunnels __contrail__ gre')
                cmd.append('delete groups __contrail__ protocols bgp group __contrail__ export test1-export') 

        cli_output = handle.config(stmts = cmd,ignore_errors=True,timeout = 120) 

        return True


    def restart_control(self):
        with settings(
            host_string='%s@%s' % (
                self.inputs.username, self.inputs.cfgm_ips[0]),
                password=self.inputs.password, warn_only=True, abort_on_prompts=False, debug=True):
            run('service contrail-control restart')
        '''
        for host in self.host_list:
            username = self.inputs.host_data[self.inputs.openstack_ip]['username']
            password = self.inputs.host_data[self.inputs.openstack_ip]['password']
            cmd='(echo sleep 10 > /root/restart.sh) ; (echo  \'service supervisor-vrouter restart\' >> /root/restart.sh) ; chmod +x /root/restart.sh ; (nohup /root/restart.sh >/dev/null 2>&1 &) ; sleep 5'
            out = self.inputs.run_cmd_on_server(host, cmd)
        time.sleep(600)
        '''
        return True

    def get_ip_list(self):
        vm_ips = []
        vm_objs = self.perf_si_fixtures[0].svm_list
        for obj_id in range(0,len(vm_objs)):
            vm_ips = vm_ips + vm_objs[obj_id].vm_ips  
        vm_ips.sort()
        return vm_ips


    def start_dpdk_mq_app(self):
        vm_objs = self.perf_si_fixtures[0].svm_list
        vm_objs[0].vm_username = 'root'
        vm_objs[0].vm_password = 'c0ntrail123'
        cmd = 'cd /root/vrouter-pktgen-tests/ ; (nohup ./dpdk_l3fwd.sh >/dev/null 2>&1 &) ; sleep 5'
        ret = vm_objs[0].run_cmd_on_vm(cmds=[cmd],as_sudo=True, timeout=self.timeout)
        return True

    def create_startup_script_queues(self,queues):
        return True
        text = """#!/bin/sh
ethtool -L eth0 combined %s  
ethtool -L eth1  combined %s 
ethtool -l eth0 >> /tmp/out.txt
ethtool -l eth1 >> /tmp/out.txt"""%(queues,queues)
        text = """#!/bin/sh
echo "Hello World.  The time is now $(date -R)!" | tee /tmp/output.txt
               """
        try:
            with open ("/tmp/metadata_script.txt" , "w") as f:
                f.write(text)
        except Exception as e:
            self.logger.exception("Got exception while creating"
                                  " /tmp/metadata_script.txt as %s"%(e))
        return True
