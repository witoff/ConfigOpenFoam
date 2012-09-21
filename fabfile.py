from fabric.api import run, env, sudo, cd, settings, prefix
from getpass import getpass
from time import sleep


#Build for a Precise ubuntu x64 instance
def ec2():
    env.user = 'ubuntu'
    env.hosts = ['ec2-54-245-18-120.us-west-2.compute.amazonaws.com']
    env.key_filename = "/Users/witoff/.ssh/sp-one.pem"
    env.disable_known_hosts = True

def test():
    run('pwd')
    run('ls')
    run('echo $SHELL')
    run('echo $PATH')

#foam_run = '/home/ubuntu/OpenFOAM/ubuntu-2.1.1/run'
#foam_tutorials = '/opt/openfoam211/tutorials'

def setup():
    # From this tutorial: http://www.openfoam.org/download/ubuntu.php
    
    #Add OpenFoam Package to Apt
    #run('VERS=$(lsb_release -cs)')
    vers = 'precise'
    sudo('sh -c "echo deb http://www.openfoam.org/download/ubuntu %s main > /etc/apt/sources.list.d/openfoam.list"' % vers)
    
    #Refresh Package List
    sudo('apt-get -y update')
    
    #My files
    sudo('apt-get -y install git')
    run('git clone https://github.com/witoff/ConfigOpenFoam.git')
    run('cp ~/ConfigOpenFoam/bashrc ~/.bashrc')
    
    #Open Foam
    sudo('apt-get -y --force-yes install openfoam211')
    # *Need openmesa to use parareader* w/ ubuntu on EC2
    #   sudo('apt-get -y --force-yes install paraviewopenfoam3120')
    run('echo ". /opt/openfoam211/etc/bashrc" >> .bashrc')

    #Copy in Example Files
    run('. /opt/openfoam211/etc/bashrc')
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
