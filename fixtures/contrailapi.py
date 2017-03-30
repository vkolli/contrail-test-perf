import uuid
import logging

from tcutils.util import *
from vnc_api.vnc_api import *

class ContrailVncApi:

    def __init__(self, vnc, logger=None):
        self._vnc = vnc
        self._log = logger or logging.getLogger(__name__)

    def __getattr__(self, name, *args, **kwargs):
        # Call self._vnc method if no matching method exists
        method = getattr(self._vnc, name)
        return method(*args, **kwargs)

    def get_policy(self, fq_name, **kwargs):
        return self._vnc.network_policy_read(fq_name=fq_name)

    def get_floating_ip(self, fip_id, **kwargs):
        fip_obj = self._vnc.floating_ip_read(id=fip_id)
        return fip_obj.get_floating_ip_address()

    def create_floating_ip(self, pool_obj, project_obj, **kwargs):
        fip_obj = FloatingIp(get_random_name('fip'), pool_obj)
        fip_obj.set_project(project_obj)
        self._vnc.floating_ip_create(fip_obj)
        fip_obj = self._vnc.floating_ip_read(fq_name=fip_obj.fq_name)
        return (fip_obj.get_floating_ip_address(), fip_obj.uuid)

    def delete_floating_ip(self, fip_id, **kwargs):
        self._vnc.floating_ip_delete(id=fip_id)

    def assoc_floating_ip(self, fip_id, vm_id, **kwargs):
        fip_obj = self._vnc.floating_ip_read(id=fip_id)
        vm_obj = self._vnc.virtual_machine_read(id=vm_id)
        vmi = vm_obj.get_virtual_machine_interface_back_refs()[0]['uuid']
        vmintf = self._vnc.virtual_machine_interface_read(id=vmi)
        fip_obj.set_virtual_machine_interface(vmintf)
        self._log.debug('Associating FIP:%s with VMI:%s' % (fip_id, vm_id))
        self._vnc.floating_ip_update(fip_obj)
        return fip_obj

    def disassoc_floating_ip(self, fip_id, **kwargs):
        self._log.debug('Disassociating FIP %s' % fip_id)
        fip_obj = self._vnc.floating_ip_read(id=fip_id)
        fip_obj.virtual_machine_interface_refs=None
        self._vnc.floating_ip_update(fip_obj)
        return fip_obj

    def add_security_group(self, vm_id, sg_id, **kwargs):
        sg = self.get_security_group(sg_id)
        vnc_vm = self._vnc.virtual_machine_read(id=vm_id)
        vmis = [vmi['uuid'] for vmi in vnc_vm.get_virtual_machine_interface_back_refs()]
        vmis = [self._vnc.virtual_machine_interface_read(id=vmi) for vmi in vmis]
        for vmi in vmis:
            sg_lst = vmi.get_security_group_refs()
            if not sg_lst:
                sg_lst = []
            sg_lst.append({'uuid': sg.uuid, 'to':sg.fq_name})
            vmi.set_security_group_list(sg_lst)
            self._vnc.virtual_machine_interface_update(vmi)

    def remove_security_group(self, vm_id, sg_id, **kwargs):
        sg = self.get_security_group(sg_id)
        vnc_vm = self._vnc.virtual_machine_read(id=vm_id)
        vmis = [vmi['uuid'] for vmi in vnc_vm.get_virtual_machine_interface_back_refs()]
        vmis = [self._vnc.virtual_machine_interface_read(id=vmi) for vmi in vmis]
        for vmi in vmis:
            sg_lst = vmi.get_security_group_refs()
            if not sg_lst:
                return
            for i, sg_ref in enumerate(sg_lst):
                if sg_ref['uuid'] == sg.uuid:
                     break
            else:
                return
            sg_lst.pop(i)
            vmi.set_security_group_list(sg_lst)
            self._vnc.virtual_machine_interface_update(vmi)

    def create_security_group(self, sg_name, parent_fqname, sg_entries, **kwargs):
        sg = SecurityGroup(sg_name, parent_type='project',
                           fq_name=parent_fqname+[sg_name])
        sg.security_group_entries = PolicyEntriesType(sg_entries)
        self._vnc.security_group_create(sg)
        sg = self._vnc.security_group_read(fq_name=sg.get_fq_name())
        return sg.uuid

    def delete_security_group(self, sg_id, **kwargs):
        self._vnc.security_group_delete(id=sg_id)

    def get_security_group(self, sg_id, **kwargs):
        try:
            return self._vnc.security_group_read(id=sg_id)
        except:
            try:
                return self._vnc.security_group_read(fq_name=sg_id)
            except:
                return None

    def get_security_group_rules(self, sg_id, **kwargs):
        sg_info = self._vnc.security_group_read(id=sg_id)
        return sg_info.get_security_group_entries().exportDict()['PolicyEntriesType']['policy_rule']

    def delete_security_group_rules(self, sg_id, **kwargs):
        sg = self._vnc.security_group_read(id=sg_id)
        sg.set_security_group_entries(None)
        self._vnc.security_group_update(sg)

    def set_security_group_rules(self, sg_id, sg_entries, **kwargs):
        sg = self._vnc.security_group_read(id=sg_id)
        sg.set_security_group_entries(PolicyEntriesType(sg_entries))
        return self._vnc.security_group_update(sg)

    def get_vn_list(self, **kwargs):
       return self._vnc.virtual_networks_list(kwargs['parent_id'])['virtual-networks'] 

    def create_forwarding_class(self, name, fc_id, parent_obj=None,
                                dscp=None, dot1p=None, exp=None, queue_uuid=None):
        fc_obj = ForwardingClass(name=name,
                                 parent_obj=parent_obj,
                                 forwarding_class_id=fc_id,
                                 forwarding_class_dscp=dscp,
                                 forwarding_class_vlan_priority=dot1p,
                                 forwarding_class_mpls_exp=exp)
        if queue_uuid:
            queue_obj = self._vnc.qos_queue_read(id=queue_uuid)
            fc_obj.add_qos_queue(queue_obj)
        fc_uuid = self._vnc.forwarding_class_create(fc_obj)
        self._log.info('Created FC %s, UUID %s' % (self._vnc.id_to_fq_name(fc_uuid),
                         fc_uuid))
        return fc_uuid
    # end create_forwarding_class

    def update_forwarding_class(self, uuid, fc_id=None, dscp=None, dot1p=None,
                                exp=None, queue_uuid=None):
        self._log.info('Updating FC %s: fc_id: %s, dscp: %s, dot1p: %s, exp: %s,'
                         'queue: %s' % (uuid, fc_id, dscp, dot1p, exp, queue_uuid))
        fc_obj = self._vnc.forwarding_class_read(id=uuid)
        if fc_id:
            fc_obj.set_forwarding_class_id(fc_id)
        if dscp:
            fc_obj.set_forwarding_class_dscp(dscp)
        if dot1p:
            fc_obj.set_forwarding_class_vlan_priority(dot1p)
        if exp:
            fc_obj.set_forwarding_class_mpls_exp(exp)
        if queue_uuid:
            queue_obj = self._vnc.qos_queue_read(id=queue_uuid)
            fc_obj.set_qos_queue(queue_obj)
        self._vnc.forwarding_class_update(fc_obj)
        return fc_obj
    # end update_forwarding_class

    def delete_forwarding_class(self, uuid):
        fq_name = self._vnc.id_to_fq_name(uuid)
        self._log.info('Deleting FC %s, UUID: %s' %(fq_name, uuid))
        return self._vnc.forwarding_class_delete(id=uuid)
    # end delete_forwarding_class
        
    def create_qos_config(self, name,
                          parent_obj=None,
                          dscp_mapping=None,
                          dot1p_mapping=None,
                          exp_mapping=None,
                          qos_config_type=None,
                          default_fc_id=0):
        '''
            dscp_mapping , dot1p_mapping and exp_mapping is a
            dict of code_points as key and ForwardingClass id as value

            qos_config_type: One of vhost/fabric/project
        '''

        dscp_entries = self._get_code_point_to_fc_map(dscp_mapping)
        dot1p_entries = self._get_code_point_to_fc_map(dot1p_mapping)
        exp_entries = self._get_code_point_to_fc_map(exp_mapping)

        qos_config_obj = QosConfig(name=name,
                                   parent_obj=parent_obj,
                                   dscp_entries=dscp_entries,
                                   vlan_priority_entries=dot1p_entries,
                                   mpls_exp_entries=exp_entries,
                                   qos_config_type=qos_config_type,
                                   default_forwarding_class_id=default_fc_id)
        uuid = self._vnc.qos_config_create(qos_config_obj)
        self._log.info('Created QosConfig %s, UUID: %s' % (
                         self._vnc.id_to_fq_name(uuid), uuid))
        return uuid
    # end create_qos_config

    def set_qos_config_entries(self, uuid, dscp_mapping=None, dot1p_mapping=None,
                               exp_mapping=None):
        ''' If the user wants to clear the entries, {} needs to be passed
        '''
        self._log.info('Updating qos-config:%s, dscp_mapping: %s,'
                         'dot1p_mapping: %s, exp_mapping: %s' % (
                         uuid, dscp_mapping, dot1p_mapping, exp_mapping))
        qos_config_obj = self._vnc.qos_config_read(id=uuid)
        if dscp_mapping is not None:
            dscp_entries = self._get_code_point_to_fc_map(dscp_mapping)
            qos_config_obj.set_dscp_entries(dscp_entries)
        if dot1p_mapping is not None:
            dot1p_entries = self._get_code_point_to_fc_map(dot1p_mapping)
            qos_config_obj.set_vlan_priority_entries(dot1p_entries)
        if exp_mapping is not None:
            exp_entries = self._get_code_point_to_fc_map(exp_mapping)
            qos_config_obj.set_mpls_exp_entries(exp_entries)
        self._vnc.qos_config_update(qos_config_obj)
        return qos_config_obj
    # end set_qos_config_entries
    
    def set_default_fc_id(self, uuid, default_fc_id=0):
        ''' Updates the default FC ID associated with this qos config
        '''
        self._log.info('Updating qos-config: Default_FC_Id: %d,'
                          % (default_fc_id))
        qos_config_obj = self._vnc.qos_config_read(id=uuid)
        qos_config_obj.set_default_forwarding_class_id(default_fc_id)
        self._vnc.qos_config_update(qos_config_obj)

    def _get_code_point_to_fc_map(self, mapping_dict=None):
        if not mapping_dict:
            return None
        new_map = QosIdForwardingClassPairs()
        for k, v in mapping_dict.iteritems():
            pair = QosIdForwardingClassPair(k, v)
            new_map.add_qos_id_forwarding_class_pair(pair)
        return new_map
    # end _get_code_point_to_fc_map

    def _add_to_entries(self, qos_config_obj, dscp_mapping=None,
                        dot1p_mapping=None, exp_mapping=None):
        self._log.debug('Adding FC entries to Qos Config %s, dscp:%s, '
            'dot1p: %s, exp: %s' % (qos_config_obj.uuid, dscp_mapping,
            dot1p_mapping, exp_mapping))
        if dscp_mapping:
            for k, v in dscp_mapping.iteritems():
                entry = QosIdForwardingClassPair(k, v)
                qos_config_obj.dscp_entries.add_qos_id_forwarding_class_pair(
                    entry)
                qos_config_obj.set_dscp_entries(qos_config_obj.dscp_entries)
        if dot1p_mapping:
            for k, v in dot1p_mapping.iteritems():
                entry = QosIdForwardingClassPair(k, v)
                qos_config_obj.vlan_priority_entries.add_qos_id_forwarding_class_pair(
                    entry)
                qos_config_obj.set_vlan_priority_entries(
                    qos_config_obj.vlan_priority_entries)
        if exp_mapping:
            for k, v in exp_mapping.iteritems():
                entry = QosIdForwardingClassPair(k, v)
                qos_config_obj.mpls_exp_entries.add_qos_id_forwarding_class_pair(
                    entry)
                qos_config_obj.set_mpls_exp_entries(
                    qos_config_obj.mpls_exp_entries)
        self._vnc.qos_config_update(qos_config_obj)
        return qos_config_obj
    # end _add_to_entries

    def add_qos_config_entries(self, uuid, dscp_mapping=None,
                               dot1p_mapping=None,
                               exp_mapping=None):
        ''' Add one or more code-point to fc mappings to existing qos-config entries
        '''
        qos_config_obj = self._vnc.qos_config_read(id=uuid)
        if dscp_mapping:
            self._add_to_entries(qos_config_obj, dscp_mapping=dscp_mapping)
        if dot1p_mapping:
            self._add_to_entries(qos_config_obj, dot1p_mapping=dot1p_mapping)
        if exp_mapping:
            self._add_to_entries(qos_config_obj, exp_mapping=exp_mapping)
        return qos_config_obj
    # end add_qos_config_entries

    def get_code_point_entry(self, qos_config_obj, dscp=None, dot1p=None,
                             exp=None):
        ''' Return QosIdForwardingClassPair object for the argument
        '''
        entries = None
        value = dscp or dot1p or exp
        if dscp:
            entries = qos_config_obj.dscp_entries
        if dot1p:
            entries = qos_config_obj.vlan_priority_entries
        if exp:
            entries = qos_config_obj.mpls_exp_entries

        if entries:
            pairs = entries.get_qos_id_forwarding_class_pair()
            entry = [x for x in pairs if x.key == value]
            if entry:
                return entry[0]
    # end get_code_point_entry

    def del_qos_config_entry(self, uuid, dscp=None, dot1p=None, exp=None):
        ''' Remove the entry from qos config which has the code-point
        '''
        qos_config_obj = self._vnc.qos_config_read(id=uuid)
        self._log.info('In Qos config %s, Removing entry for key dscp:%s, '
            'dot1p:%s, exp:%s' % (uuid, dscp, dot1p, exp))

        dscp_entry = self.get_code_point_entry(qos_config_obj, dscp=dscp)
        if dscp_entry:
            qos_config_obj.dscp_entries.delete_qos_id_forwarding_class_pair(
                dscp_entry)
            qos_config_obj.set_dscp_entries(
                self.qos_config_obj.dscp_entries)
        dot1p_entry = get_code_point_entry(qos_config_obj, dot1p=dot1p)
        if dot1p_entry:
            qos_config_obj.dscp_entries.delete_qos_id_forwarding_class_pair(
                dot1p_entry)
            qos_config_obj.set_vlan_priority_entries(
                qos_config_obj.vlan_priority_entries)
        exp_entry = self.get_code_point_entry(qos_config_obj, exp=exp)
        if exp_entry:
            qos_config_obj.dscp_entries.delete_qos_id_forwarding_class_pair(
                exp_entry)
            qos_config_obj.set_mpls_exp_entries(
                qos_config_obj.mpls_exp_entries)
        self._vnc.qos_config_update(qos_config_obj)
        return qos_config_obj
    # end del_qos_config_entry

    def update_virtual_router_type(self,name,vrouter_type):
        vr_fq_name = ['default-global-system-config', name]
        vr = self._vnc.virtual_router_read(
            fq_name=vr_fq_name)
        vr.set_virtual_router_type(vrouter_type)
        self._vnc.virtual_router_update(vr)

    def create_virtual_machine(self,vm_uuid=None):
        vm = VirtualMachine()
        if vm_uuid:
            vm.set_uuid(vm_uuid)
        self._vnc.virtual_machine_create(vm)
        return vm
    #end create_virtual_machine

    def delete_virtual_machine(self,vm_uuid):
        self._vnc.virtual_machine_delete(id=vm_uuid)
    #end delete_virtual_machine

    def disable_policy_on_vmi(self, vmi_id, disable=True):
        '''
        Disables the policy on the VMI vmi_id
        '''

        log_str = 'DISABLED' if disable else 'ENABLED'

        vmi_obj = self._vnc.virtual_machine_interface_read(id=vmi_id)
        vmi_obj.set_virtual_machine_interface_disable_policy(disable)
        self._vnc.virtual_machine_interface_update(vmi_obj)
        self._log.info("Policy %s on VMI %s" % (log_str, vmi_id))

        return True
    # end disable_policy_on_vmi

    def add_fat_flow_to_vmi(self, vmi_id, fat_flow_config):
        '''vmi_id: vmi id where Fat flow config is to be added
           fat_flow_config: dictionary of format {'proto':<string>,'port':<int>}
        '''
        proto_type = ProtocolType(protocol=fat_flow_config['proto'],
                        port=fat_flow_config['port'])

        vmi_obj = self._vnc.virtual_machine_interface_read(id=vmi_id)
        fat_config = vmi_obj.get_virtual_machine_interface_fat_flow_protocols()
        if fat_config:
            fat_config.fat_flow_protocol.append(proto_type)
        else:
            fat_config = FatFlowProtocols(fat_flow_protocol=[proto_type])
        vmi_obj.set_virtual_machine_interface_fat_flow_protocols(
                                                fat_config)
        self._vnc.virtual_machine_interface_update(vmi_obj)
        self._log.info("Fat flow added on VMI %s: %s" % (
                            vmi_id, fat_flow_config))

        return True
    #end add_fat_flow_to_vmi

    def remove_fat_flow_on_vmi(self, vmi_id, fat_flow_config):
        '''
        Removes the first matching Fat flow configuration
        vmi_id: vmi id
        fat_flow_config: dictionary of format {'proto':<string>,'port':<int>}
        '''
        vmi_obj = self._vnc.virtual_machine_interface_read(id=vmi_id)
        fat_config_get = vmi_obj.get_virtual_machine_interface_fat_flow_protocols()
        if fat_config_get:
            for config in fat_config_get.fat_flow_protocol:
                if config.protocol == fat_flow_config['proto'] and \
                    config.port == fat_flow_config['port']:
                    fat_config_get.fat_flow_protocol.remove(config)
                    vmi_obj.set_virtual_machine_interface_fat_flow_protocols(
                                                            fat_config_get)
                    self._vnc.virtual_machine_interface_update(vmi_obj)
                    self._log.info("Fat flow config removed from VMI %s: %s" % (
                                        vmi_id, vars(config)))
                    break

        return True
    #end remove_fat_flow_on_vmi

    def add_proto_based_flow_aging_time(self, proto, port=0, timeout=180):
        '''
        Adds protocol based flow aging timeout value.
        proto: <string>, port: <int>, timeout: <int-in-seconds>
        '''

        fq_name = [ 'default-global-system-config',
                    'default-global-vrouter-config']
        gv_obj = self._vnc.global_vrouter_config_read(fq_name=fq_name)
        flow_aging = gv_obj.get_flow_aging_timeout_list()

        flow_aging_add = FlowAgingTimeout(protocol=proto, port=port, timeout_in_seconds=timeout)
        if flow_aging:
            flow_aging.flow_aging_timeout.append(flow_aging_add)
        else:
            flow_aging = FlowAgingTimeoutList([flow_aging_add])
        gv_obj.set_flow_aging_timeout_list(flow_aging)
        self._vnc.global_vrouter_config_update(gv_obj)

        self._log.info('Added global flow aging configuration: %s' % (vars(flow_aging_add)))

        return True
    #end add_proto_based_flow_aging_time

    def delete_proto_based_flow_aging_time(self, proto, port=0, timeout=180):
        '''
        Remove protocol based flow aging timeout value.
        proto: <string>, port: <int>, timeout: <int-in-seconds>
        '''

        fq_name = [ 'default-global-system-config',
                    'default-global-vrouter-config']
        gv_obj = self._vnc.global_vrouter_config_read(fq_name=fq_name)
        flow_aging = gv_obj.get_flow_aging_timeout_list()

        if not flow_aging:
            return
        for aging in flow_aging.flow_aging_timeout:
            values = vars(aging)
            if values['timeout_in_seconds'] == timeout and \
                values['protocol'] == proto and values['port'] == port:
                flow_aging.flow_aging_timeout.remove(aging)

                gv_obj.set_flow_aging_timeout_list(flow_aging)
                self._vnc.global_vrouter_config_update(gv_obj)

                self._log.info('Deleted the flow aging configuration: %s' % (vars(aging)))

                return True
    #end delete_proto_based_flow_aging_time

    def create_interface_route_table(self, name, parent_obj=None, prefixes=[]):
        '''
        Create and return InterfaceRouteTable object

        Args:
            prefixes : list of x.y.z.a/mask entries
        '''
        route_table = RouteTableType(name)
        nw_prefixes = [ IPNetwork(x) for x in prefixes]
        route_table.set_route([])
        intf_route_table = InterfaceRouteTable(
                                interface_route_table_routes = route_table,
                                parent_obj=parent_obj,
                                name=name)
        if prefixes:
            rt_routes = intf_route_table.get_interface_route_table_routes()
            routes = rt_routes.get_route()
            for prefix in prefixes:
                rt1 = RouteType(prefix = prefix)
                routes.append(rt1)
            intf_route_table.set_interface_route_table_routes(rt_routes)
        uuid = self._vnc.interface_route_table_create(intf_route_table)
        intf_route_table_obj = self._vnc.interface_route_table_read(id=uuid)
        self._log.info('Created InterfaceRouteTable %s(UUID %s), prefixes : %s'\
            %(intf_route_table_obj.fq_name, intf_route_table_obj.uuid, prefixes))
        return intf_route_table_obj
    # end create_interface_route_table

    def add_interface_route_table_routes(self, uuid, prefixes=[]):
        '''
        Add prefixes to an existing InterfaceRouteTable object
        Args:
            uuid     : uuid of InterfaceRouteTable
            prefixes : list of x.y.z.a/mask entries
        '''
        intf_route_table = self._vnc.interface_route_table_read(id=uuid)
        nw_prefixes = [ IPNetwork(x) for x in prefixes]
        intf_route_table = self._vnc.interface_route_table_read(id=uuid)
        if nw_prefixes:
            rt_routes = intf_route_table.get_interface_route_table_routes()
            routes = rt_routes.get_route()
            for prefix in prefixes:
                rt1 = RouteType(prefix = prefix)
                routes.append(rt1)
                self._log.info('Adding prefix %s to intf route table'
                    '%s' % str((prefix)))
            intf_route_table.set_interface_route_table_routes(rt_routes)
        self._vnc.interface_route_table_update(intf_route_table)
        return intf_route_table
    #end add_interface_route_table_routes

    def delete_interface_route_table_routes(self, uuid, prefixes):
        '''
        Delete prefixes from an existing InterfaceRouteTable object

        Args:
        uuid     : uuid of InterfaceRouteTabl
        prefixes : list of x.y.z.a/mask entries
        '''
        intf_rtb_obj = self._vnc.interface_route_table_read(id=uuid)
        rt_routes = intf_rtb_obj.get_interface_route_table_routes()
        routes = rt_routes.get_route()
        for prefix in prefixes:
            prefix_found = False
            for route in routes:
                if route.prefix == prefix:
                    prefix_found = True
                    routes.remove(route)
                if not prefix_found:
                    self._log.warn('Prefix %s not found in intf route table'
                        ' %s' % (prefix, self.name))
                else:
                    self._log.info('Prefix %s deleted from intf route table'
                        ' %s' % (prefix, self.name))
        intf_route_table.set_interface_route_table_routes(rt_routes)
        self._vnc.interface_route_table_update(intf_route_table)
    # end delete_interface_route_table_routes

    def delete_interface_route_table(self, uuid):
        '''
        Delete InterfaceRouteTable object

        Args:
            uuid : UUID of InterfaceRouteTable object
        '''
        self._vnc.interface_route_table_delete(id=uuid)
        self._log.info('Deleted Interface route table %s' % (uuid))
    # end delete_interface_route_table

    def bind_vmi_to_interface_route_table(self, vmi_uuid, intf_rtb):
        '''
        Bind interface route table to a VMI

        intf_rtb : either UUID or InterfaceRouteTable object

        Returns None
        '''
        # TODO
        # Start making different modules for each object and rename methods
        # accordingly
        if is_uuid(intf_rtb):
            intf_rtb_obj = self._vnc.interface_route_table_read(id=intf_rtb)
        elif isinstance(intf_rtb, InterfaceRouteTable):
            intf_rtb_obj = intf_rtb
        vmi_obj = self._vnc.virtual_machine_interface_read(id=vmi_uuid)
        vmi_obj.add_interface_route_table(intf_rtb_obj)
        self._vnc.virtual_machine_interface_update(vmi_obj)
        self._log.info('Added intf route table %s to port %s' % (
            intf_rtb_obj.uuid, vmi_uuid))
    # end bind_vmi_to_interface_route_table

    def unbind_vmi_from_interface_route_table(self, vmi_uuid, intf_rtb):
        '''
        Unbind interface route table from a VMI

        intf_rtb : either UUID or InterfaceRouteTable object

        Returns None
        '''
        if is_uuid(intf_rtb):
            intf_rtb_obj = self._vnc.interface_route_table_read(id=intf_rtb)
        elif isinstance(intf_rtb, InterfaceRouteTable):
            intf_rtb_obj = intf_rtb
        vmi_obj = self._vnc.virtual_machine_interface_read(id=vmi_uuid)
        vmi_obj.del_interface_route_table(intf_rtb_obj)
        self._vnc.virtual_machine_interface_update(vmi_obj)
        self._log.info('Removed intf route table %s from port %s' % (
            intf_rtb_obj.uuid, vmi_uuid))
    # end unbind_vmi_from_interface_route_table
