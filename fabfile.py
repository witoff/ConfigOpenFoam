from fabric.api import run, env, sudo, cd, settings, prefix
from getpass import getpass
from time import sleep

"""
Fabfile for openfoam deployments
Usage:
1. setup your hosts and keys
2. configure your sever with `fab ec2 preconfig`
3. after reboot, continue configuration with `fab ec2 setup`
4. Go to town on examples with `fab ec2 [example, damBreak, damBreakFine]
"""

#Build for a Precise ubuntu x64 instance
def ec2():
    env.user = 'ubuntu'
    env.hosts = ['54.243.138.71']
    env.key_filename = "/Users/witoff/.ssh/aws-east.pem"
    env.disable_known_hosts = True

def test():
    run('pwd')
    run('ls')
    run('echo $SHELL')
    run('echo $PATH')

#foam_run = '/home/ubuntu/OpenFOAM/ubuntu-2.1.1/run'
#foam_tutorials = '/opt/openfoam211/tutorials'

def preconfig():
    # From this tutorial: http://www.openfoam.org/download/ubuntu.php
    
    #Add OpenFoam Package to Apt
    #run('VERS=$(lsb_release -cs)')
    vers = 'precise'
    sudo('sh -c "echo deb http://www.openfoam.org/download/ubuntu %s main > /etc/apt/sources.list.d/openfoam.list"' % vers)
    
    #Refresh Package List
    sudo('apt-get -y update')
    sudo('apt-get -y upgrade')
    sudo('shutdown -r now')

def setup():
    #My files
    sudo('apt-get -y install git')
    run('git clone https://github.com/witoff/ConfigOpenFoam.git')
    run('cp ~/ConfigOpenFoam/bashrc ~/.bashrc')
    
    #Open Foam
    sudo('apt-get -y --force-yes install openfoam211 paraviewopenfoam3120')
    # *Need openmesa to use parareader* w/ ubuntu on EC2
    #   sudo('apt-get -y --force-yes install paraviewopenfoam3120')
    run('echo ". /opt/openfoam211/etc/bashrc" >> .bashrc')
    run('echo "PS1=\'$: \'" >> .bashrc')
    run('. /opt/openfoam211/etc/bashrc')
    
    #Enable ubuntu drivers
    sudo('apt-add-repository -y ppa:ubuntu-x-swat/x-updates')
    sudo('apt-get update')
    sudo('apt-get install -y nvidia-current nvidia-settings')
    sudo('apt-get install -y --reinstall libgl1-mesa-glx')

    # Setup Paraview
    run('wget http://downloads.sourceforge.net/foam/ThirdParty-2.1.1.tgz')
    run('tar xzf ThirdParty-2.1.1.tgz')
    sudo('apt-get -y install build-essential flex bison cmake zlib1g-dev qt4-dev-tools libqt4-dev gnuplot libreadline-dev libncurses-dev libxt-dev')
    sudo('apt-get -y install libscotch-dev libopenmpi-dev')
    sudo('apt-get -y mesa-utils')
    sudo('mv ThirdParty-2.1.1 /opt/')
    with cd('$WM_THIRD_PARTY_DIR'):
        run('./makeParaView')
    
    ## Exports thef following params
    # export ParaView_DIR=/opt/ThirdParty-2.1.1/platforms/linux64Gcc/paraview-3.12.0
    # export PATH=$ParaView_DIR/bin:$PATH
    # export PV_PLUGIN_PATH=$FOAM_LIBBIN/paraview-3.12

    # Setup VNC 
    #   via: http://coddswallop.wordpress.com/2012/05/09/ubuntu-12-04-precise-pangolin-complete-vnc-server-setup/
    sudo('apt-get install linux-headers-$(uname -r)')
    sudo('dpkg-reconfigure nvidia-current')
    
    sudo('apt-get -y install gnome-core gnome-session-fallback')
    sudo('apt-get -y install vnc4server')
    sudo('apt-get -y install expect')

    #setup vnc passwd
    passwd = 'password'
    run('echo -e "spawn vncpasswd\nexpect Password:\nsend %s\\r\nexpect Verify:\nsend %s\\r" > vnc.txt' % (passwd, passwd))
    run('expect vnc.txt')
    
    run('vncserver')
    run('vncserver -kill :1')

    sudo('cp ~/ConfigOpenFoam/xstartup ~/.vnc/xstartup')

    #Start vnc
    run('vncserver')
    
    
    #Copy in Example Files
    run('mkdir -p $FOAM_RUN')
    with cd('$FOAM_RUN'):
        run('cp -r $FOAM_TUTORIALS $FOAM_RUN')

    #Create extra fine mesh dambreak case
    with cd('$FOAM_RUN/tutorials/multiphase/interFoam/laminar'):
        run('mkdir damBreakFine')
        run('cp -r damBreak/0 damBreakFine')
        run('cp -r damBreak/system damBreakFine')
        run('cp -r damBreak/constant damBreakFine')
        run('cp ~/ConfigOpenFoam/blockMeshDict damBreakFine/constant/polyMesh/blockMeshDict')
    
def example():
    #Simple incompressible flow example
    with cd('$FOAM_RUN/tutorials/incompressible/icoFoam/cavity'):
        run('blockMesh')
        run('icoFoam')
        # If compiled properly, can then visualize output data in the parareader
        # run('paraFoam')

def damBreak():
    # http://www.openfoam.org/docs/user/damBreak.php#x7-500002.3
    with cd('$FOAM_RUN/tutorials/multiphase/interFoam/laminar/damBreak'):

        #input is here: vi constant/polyMesh/blockMeshDict 
        run('blockMesh')
        #outputs are here: constant/polyMesh 
    
        #set surface tension vals to zero
        run('cp 0/alpha1.org 0/alpha1')
        run('setFields')
        run('interFoam | tee log.txt')
    
def damBreakFine():
    # http://www.openfoam.org/docs/user/damBreak.php#x7-500002.3
    with cd('$FOAM_RUN/tutorials/multiphase/interFoam/laminar/damBreakFine'):

        #input is here: vi constant/polyMesh/blockMeshDict 
        run('blockMesh')
        #outputs are here: constant/polyMesh

        run('cp 0/alpha1.org 0/alpha1')
        run('setFields')
        
        #Decompose into different sets for each processor
        # Number of segments can be updated in system/decomposeParDict
        run('decomposePar')

        #Run in separate process
        run('mpirun -np 4 interFoam -parallel > log.txt')
