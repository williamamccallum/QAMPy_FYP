# QAMPy_FYP

QAMpy Installation
Python/Visual Basic Installation
1.	Install Visual Studio Basic, 2017 or later from https://visualstudio.microsoft.com/vs/	
a.	When installing, make sure that python development and desktop development for c++ packages are ticked.
2.	Python should be installed with Visual Studio and can be run from the command line.  Check by opening command line and running ‘python --version’. If this does not work, go to “Edit the system Environment Variables” in control panel and click on advanced->environment variables.
a.	Open the start page and type in ‘python’, right click on the app and go the file location, this will take you to the shortcut to the program. Once there, right click on the python 3.x shortcut and open file location, which will take you to the python program files.
b.	Copy the path to the python files and in environment variables under user variables click on ‘PATH’ and click edit, which will open a new window. Once there, click on new and add the path to the python files. Then, back in the python program files click on the scripts folder and copy the path, then add the path same as the python program files.
c.	Back in environment variables, under system variables go to ‘path’ and click on edit. Then add the paths to python and python\scripts, same as with 2.b. 
d.	Python and pip should now be working with command line, test by running ‘python --version’ and ‘pip --version’
Anaconda Installation
3.	Install anaconda by going to https://www.anaconda.com/products/individual and downloading and running the exe file. Make sure when installing to check the ‘add Anaconda to my PATH environment variable’ checkbox under advanced installation options, otherwise you will have to repeat step 2 for Anaconda program files.
QAMpy Build/Install
4.	Download QAMpy from https://github.com/ChalmersPhotonicsLab/QAMpy and unzip contents into desired folder.
5.	Open an Anaconda prompt and check that its working by running ‘conda --version’. Then create a conda environment by running ‘conda create --name environment_name python=3.x’ where environment_name is the name of the environment you are creating and 3.x is the version of python that the environment will run. Note that the python version must be 3.6 or later
6.	Activate the virtual environment by running ‘conda activate environment_name’. The environment will allow for packages to be installed and different python versions to be used without affecting the rest of your system. It can be deactivated using ‘conda activate’ with no environment specified, which will return you to the base environment, and can be reactivated using ‘conda activate environment_name’.
7.	Download a numpy+mkl wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/
a.	The wheel which should be downloaded depends on the computer and Python version specifications. Ex, if using Python 3.9 and 64 bit Windows, use numpy‑1.22.3+mkl‑cp39‑cp39‑win_amd64.whl
b.	Move to the folder where the wheel was downloaded using ‘cd folder_location’ and use ‘pip install wheel_name’
c.	(ex. Pip install numpy‑1.22.3+mkl‑cp39‑cp39‑win_amd64.whl)
8.	Install other packages using ‘pip install scipy sphinx pythran clang’
a.	Note that ‘conda install …’ should not be used, as it will attempt to overwrite the 
9.	In conda environment, go to folder where you unzipped QAMpy into using ‘cd’ command and run ‘python setup.py build’ then ‘python setup.py install’.
Additional Packages
There are several additional packages that, while not necessary for QAMpy to run, provide functionality that helps with communication with other devices and representing the data at output, and so are highly recommended to be used in conjunction with QAMpy. These include:
Bokeh – Used to plot constellation diagrams
Matplotlib – Used to plot fft of signals and symbol error rates
Pyvisa – Used to communicate between computers and AWG & oscilloscope
Socket – Used to communicate between host and server computers via TCP/IP
They can be installed by going into anaconda prompt while the virtual environment is activated and running ‘pip install bokeh matplotlib pyvisa socket’.
Running QAMpy
1.	Open up Visual Studio, then either create or open a python repository, then in the solution explorer, right-click on python environments and click on ‘add environments’
a.	In Add environments, go to Existing environments, and click on the environment drop-down list. The virtual environment you previously created should be in the list. Select it and click add. The repository should now be using your virtual environment
2.	Test that it is working by running one of the scripts provided under QAMpy\Scripts. Recommended test case is ‘64_qam_equalisation.py’.
