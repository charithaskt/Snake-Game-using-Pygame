Snake Game: A project on Gaming in Python using Pygame and MySQL

Installation instructions:

    Software requirements:
         - Python Pygame
         - PyMySQL

         Python Pygame: Pygame is a set of Python modules designed for writing video games. 
                        Pygame adds functionality on top of the excellent SDL library. 
                        This allows you to create fully featured games and multimedia programs 
                        in the python language.

                        Pygame is highly portable and runs on nearly every platform and operating system.

                 Installation:
                        pip install pygame
                             or
                        pip3 install pygame

    	 PyMySQL: This package contains a pure-Python MySQL client library, based on PEP 249.
                  You can connect to MySQL database from python using this library.
    
                 Requirements:

                    MySQL Server – one of the following:

	                 - MySQL >= 5.5
                         - MariaDB >= 5.5

                 Installation:

                    This module does not come built-in with Python. You have to install it externally. 
         
                    To install this type the below command in the terminal.
         
                    pip install PyMySQL
                          or 
                    pip3 install PyMySQL

   
    How to install snake game?

          -   Download the snake game project zip file (python_snakegame_project-master.zip) from the git
          -   Unzip the folder 
          -   Change directory to your home folder
              cd ~
          -   Create a python virtual environment
                *  Installing Virtualenv using pip3
                   python3 -m pip install --upgrade pip
                   pip3 install virtualenv
                   which python3
                   /usr/bin/python3
                   virtualenv -p /usr/bin/python3 GAMEVENV

                *  Activating python virtual environment 'GAMEVENV' created by above command
                   cd ~/GAMEVENV
                   source ./bin/activate

                *  Deactivating virtual environment 'GAMVENV'
                   deactivate

          -   Change directory to GAMEVENV
                   cd ~ GAMEVENV
          -   Copy the unzipped snake game project source code folder 'python_snakegame_project' 
              from ~/Downloads directory to the current working directory
                   cp -r ~/Downloads/python_snakegame_project .
          -   Activate the virtual environment if not already activated
                   source ./bin/activate
          -   Move to Python_snakegame_project folder
                   cd Python_snakegame_project folder
          -   Install required python modules in the virtual environment using requirements.txt file
              [You will find requirements.txt file in this folder '~/GAMEVENV/ Python_snakegame_project']
                   pip3 install -r requirements.txt

    How to create the MySQL database needed for storing the game scores?
          -   Connect to MySQL server using root user credentials
                  myswql -uroot -p
                  Enter password: *******
                  mysql>  
          -   Create the database by ma,e 'Snake'
                  mysql>  create database Snake;
          -   Grant All Permissions on the database 'Snake' to 'snakeadmin' user with password 'admin123'
                  mysql>  use Snake
                  mysql>  grant all on Snake.* to 'snakeadmin'@'localhost' identified by 'admin123'; 
                  mysql>  flush privileges;
                  mysql>  exit;
          -   Verify the permissions by logging into MySQL as 'snakeadmin' user
              You should be able to successfully login to MySQL.
                  mysql -usnakeadmin -p
                  Enter Password: 
                  mysql>  show databases;
                  mysql>  exit;  

    How to run snake game ?
          -   Change directory to '~/GAMEVENV/ Python_snakegame_project' if it is not the 
              current directory
                 cd  ~/GAMEVENV/ Python_snakegame_project
          -   Run the game using python3
                 python3 Snake2018_v5_complete.pyw
                            or
                 python3 index.py
                 

   
           
                  
   
