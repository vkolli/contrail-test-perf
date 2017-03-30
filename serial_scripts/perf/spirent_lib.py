import sys
import os
import subprocess

def start_spirent_test (web_server_password, web_server_username, web_server, script_name):
       cmd = "sshpass -p %s ssh -o StrictHostKeyChecking=no %s@%s 'rm -rf /root/spirent/tests/%s/results; source /root/.bash_profile ;tclsh /root/spirent/tests/%s/test.tcl'" %(web_server_password, web_server_username, web_server, script_name, script_name)
       print cmd
       p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
       for line in p.stdout.readlines():
           print line,
       retval = p.wait()

def get_result_log (web_server_password, web_server_username, web_server, script_name):
       cmd = "mkdir %s ; rm -rf %s/*; sshpass -p %s scp -o StrictHostKeyChecking=no -r %s@%s:/root/spirent/tests/%s/results %s" %(script_name, script_name, web_server_password, web_server_username, web_server, script_name, script_name)
       print cmd
       p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
       for line in p.stdout.readlines():
           print line,
       retval = p.wait()

#       cmd = "sshpass -p %s ssh -o StrictHostKeyChecking=no %s@%s mkdir abc" %(web_server_password, web_server_username, web_server)
#       print cmd
#       p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#       for line in p.stdout.readlines():
#           print line,
#       retval = p.wait()

if __name__ == "__main__":
    start_spirent_test(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    get_result_log(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
