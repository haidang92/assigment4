# Import the Portal object.
import geni.portal as portal
# Import the ProtoGENI library.
import geni.rspec.pg as pg
import geni.rspec.igext as IG

# Create a portal context.
pc = portal.Context()

# Create a Request object to start building the RSpec.
request = pc.makeRequestRSpec()


tourDescription = \
"""
This profile provides the template for a full research cluster with head node, scheduler, compute nodes, and shared file systems.
First node (head) should contain: 
- Shared home directory using Networked File System
- Management server for SLURM
Second node (metadata) should contain:
- Metadata server for SLURM
Third node (storage):
- Shared software directory (/software) using Networked File System
Remaining three nodes (computing):
- Compute nodes  
"""

#
# Setup the Tour info with the above description and instructions.
#  
tour = IG.Tour()
tour.Description(IG.Tour.TEXT,tourDescription)
request.addTour(tour)


link = request.LAN("lan")

for i in range(6):
  if i == 0:
    node = request.XenVM("head")
    node.routable_control_ip = "true" 
  elif i == 1:
    node = request.XenVM("metadata")
  elif i == 2:
    node = request.XenVM("storage")
  else:
    node = request.XenVM("compute-" + str(i-2))
    node.cores = 2
    node.ram = 4096
    
  node.disk_image = "urn:publicid:IDN+emulab.net+image+emulab-ops:CENTOS7-64-STD"
  
  iface = node.addInterface("if" + str(i-3))
  iface.component_id = "eth1"
  iface.addAddress(pg.IPv4Address("192.168.1." + str(i + 1), "255.255.255.0"))
  link.addInterface(iface)
  
  #setup automatic ssh permissions
  node.addService(pg.Execute(shell="sh", command="sudo chmod 755 /local/repository/passwordless.sh"))
  node.addService(pg.Execute(shell="sh", command="sudo /local/repository/passwordless.sh"))
  node.addService(pg.Execute(shell="sh", command="sudo chmod 755 /local/repository/ssh_setup.sh"))
  node.addService(pg.Execute(shell="sh", command="sudo -H -u DT882578 bash -c '/local/repository/ssh_setup.sh'"))
  node.addService(pg.Execute(shell="sh", command="sudo systemctl disable firewalld"))
 
  #make directories and set permissions
  if i != 1 and i != 2:
    node.addService(pg.Execute(shell="sh", command="sudo mkdir /software"))
    node.addService(pg.Execute(shell="sh", command="sudo chmod 777 /software"))
  if i != 1:
    node.addService(pg.Execute(shell="sh", command="sudo mkdir /scratch"))
    node.addService(pg.Execute(shell="sh", command="sudo chmod 777 /scratch"))

  #setup storage node
  if i == 2:
    node.addService(pg.Execute(shell="sh", command="sudo su DT882578 -c 'sudo cp /local/repository/source/* /scratch'"))
    node.addService(pg.Execute(shell="sh", command="sudo rm /etc/exports"))
    node.addService(pg.Execute(shell="sh", command="sudo su DT882578 -c 'sudo cp /local/repository/export_scratch/exports /etc/exports'"))
    node.addService(pg.Execute(shell="sh", command="sudo systemctl restart nfs-server"))
    
    
  #install mpi on the head node in /software and mount /scratch
  if i == 0:
    node.addService(pg.Execute(shell="sh", command="sudo chmod 755 /local/repository/install_mpi.sh"))
    node.addService(pg.Execute(shell="sh", command="sudo /local/repository/install_mpi.sh"))
    node.addService(pg.Execute(shell="sh", command="sudo rm /etc/exports"))
    node.addService(pg.Execute(shell="sh", command="sudo su DT882578 -c 'sudo cp /local/repository/export_software/exports /etc/exports'"))
    node.addService(pg.Execute(shell="sh", command="sudo systemctl restart nfs-server"))
    node.addService(pg.Execute(shell="sh", command="sleep 7m"))
    node.addService(pg.Execute(shell="sh", command="sudo mount -t nfs 192.168.1.3:/scratch /scratch"))
    
  if i == 3 or i == 4 or i == 5:
    node.addService(pg.Execute(shell="sh", command="sleep 8m"))
    node.addService(pg.Execute(shell="sh", command="sudo mount -t nfs 192.168.1.3:/scratch /scratch"))
    node.addService(pg.Execute(shell="sh", command="sleep 15m"))
    node.addService(pg.Execute(shell="sh", command="sudo mount -t nfs 192.168.1.1:/software /software"))
    node.addService(pg.Execute(shell="sh", command="sudo chmod 755 /local/repository/mpi_path_setup.sh"))
    node.addService(pg.Execute(shell="sh", command="sudo -H -u DT882578 bash -c '/local/repository/mpi_path_setup.sh'"))   

# Print the RSpec to the enclosing page.
pc.printRequestRSpec(request)
