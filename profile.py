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

prefixForIP = "192.168.1."

link = request.LAN("lan")

for i in range(15):
  
  if i == 0:
    node = request.XenVM("head")
    node.routable_control_ip = "true"
    #One NFS is originated from the head node, and supports a shared directory called /software.
    #One NFS is originated from the storage node, and supports a shared directory called /scratch  
    node.addService(pg.Execute(shell="sh", command="sudo mkdir -m 755 /software"))
    node.addService(pg.Execute(shell="sh", command="sudo mkdir /scratch"))   
    #nfs service
    node.addService(pg.Execute(shell="sh", command="sudo systemctl enable nfs-server.service"))
    node.addService(pg.Execute(shell="sh", command="sudo systemctl start nfs-server.service"))
    # add MPI
    node.addService(pg.Execute(shell="sh", command="sudo chmod 755 /local/repository/scripts/install_mpi.sh"))
    node.addService(pg.Execute(shell="sh", command="sudo /local/repository/scripts/install_mpi.sh"))
    
    node.addService(pg.Execute(shell="sh", command="sudo rm /etc/exports"))
    node.addService(pg.Execute(shell="sh", command="sudo cp /local/repository/exports_head /etc/exports"))
    node.addService(pg.Execute(shell="sh", command="sudo chmod 777 /etc/exports"))
    node.addService(pg.Execute(shell="sh", command="sudo exportfs -a"))
    node.addService(pg.Execute(shell="sh", command="sleep 2m"))
    
    # Mount
    node.addService(pg.Execute(shell="sh", command="sudo mount 192.168.1.3:/scratch /scratch"))
    node.addService(pg.Execute(shell="sh", command="sudo echo '192.168.1.3:/scratch /scratch nfs4 rw,relatime,vers=4.1,rsize=131072,wsize=131072,namlen=255,hard,proto=tcp,port=0,timeo=600,retrans=2,sec=sys,local_lock=none,addr=192.168.1.3,_netdev,x-systemd.automount 0 0' | sudo tee --append /etc/fstab"))
    
    
  elif i == 1:
    node = request.XenVM("metadata")
    

  elif i == 2:
    node = request.XenVM("storage")   
    node.addService(pg.Execute(shell="sh", command="sudo mkdir -m 755 /scratch"))
    
    # nfs service
    node.addService(pg.Execute(shell="sh", command="sudo systemctl enable nfs-server.service"))
    node.addService(pg.Execute(shell="sh", command="sudo systemctl start nfs-server.service"))
     
    node.addService(pg.Execute(shell="sh", command="sudo rm /etc/exports"))
    node.addService(pg.Execute(shell="sh", command="sudo cp /local/repository/exports_storage /etc/exports"))
    node.addService(pg.Execute(shell="sh", command="sudo chmod 777 /etc/exports"))
    node.addService(pg.Execute(shell="sh", command="sudo exportfs -a"))

  else:
    node = request.XenVM("compute-" + str(i-2))
    node.cores = 4
    node.ram = 4096   
    
  node.disk_image = "urn:publicid:IDN+emulab.net+image+emulab-ops:CENTOS7-64-STD"
  
  iface = node.addInterface("if" + str(i))
  iface.component_id = "eth1"
  iface.addAddress(pg.IPv4Address(prefixForIP + str(i + 1), "255.255.255.0"))
  link.addInterface(iface)
  
  node.addService(pg.Execute(shell="sh", command="sudo chmod 755 /local/repository/passwordless.sh"))
  node.addService(pg.Execute(shell="sh", command="sudo /local/repository/passwordless.sh"))  
  node.addService(pg.Execute(shell="sh", command="sudo chmod 755 /local/repository/ssh_setup.sh"))
  node.addService(pg.Execute(shell="sh", command="sudo -H -u DT882578 bash -c '/local/repository/ssh_setup.sh'"))
  node.addService(pg.Execute(shell="sh", command="sudo systemctl disable firewalld"))
  node.addService(pg.Execute(shell="sh", command="sudo su DT882578 -c 'cp /local/repository/source/* /users/DT882578'"))
  
   node.addService(pg.Execute(shell="sh", command="sudo mkdir /scratch"))
   node.addService(pg.Execute(shell="sh", command="sudo mkdir /software"))
   node.addService(pg.Execute(shell="sh", command="sudo chmod 777 /scratch"))
   node.addService(pg.Execute(shell="sh", command="sudo chmod 777 /software"))
    
  # Mount 
   node.addService(pg.Execute(shell="sh", command="sudo mount 192.168.1.3:/scratch /scratch"))
   node.addService(pg.Execute(shell="sh", command="sudo su DT882578 -c \"echo '192.168.1.3:/scratch /scratch nfs defaults 0 0' >> /etc/fstab\""))

    # Mount
   node.addService(pg.Execute(shell="sh", command="sudo mount 192.168.1.1:/software /software"))
   node.addService(pg.Execute(shell="sh", command="sudo su DT882578 -c \"echo '192.168.1.1:/software /software nfs defaults 0 0' >> /etc/fstab\""))

    # Add MPI to mpi_path
   node.addService(pg.Execute(shell="sh", command="sudo chmod 777 /local/repository/scripts/mpi_path_setup.sh"))
   node.addService(pg.Execute(shell="sh", command="sudo -H -u DT882578 bash -c '/local/repository/scripts/mpi_path_setup.sh'"))
      

  
 
    

      
    
  
  
# Print the RSpec to the enclosing page.
pc.printRequestRSpec(request)
