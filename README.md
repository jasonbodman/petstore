# Pet Store - Item Catalog
## Project Description

This is a project within the third section of Udacity's Full-Stack Nanodegree program and focused on working within an SQLlite database from Python and utilizing Flask to display various items, organized by item type.
This project was built using Python, the Flask framework, HTML, CSS, JSON, and Google and Facebook OAuth2 clients. 

## Dependencies/Pre-Requirements:
You will need to have the following installed and setup on your computer:
- Oracle's VirtualBox (https://www.virtualbox.org/)
- Vagrant (https://www.vagrantup.com/)

## Setup
1. Install VirtualBox and Vagrant.
2. Download the [fullstack-nanodegree-vm folder](https://github.com/udacity/fullstack-nanodegree-vm)
3. Download, clone, or fork this repository within the downloaded fullstack-nanodegree-vm folder. 

## Usage
1. Navigate to the downloaded petstore folder via terminal
2. Launch Vagrant
   - Execute `vagrant up` within terminal
   - Execute `vagrant ssh` within terminal
3. Execute `python application.py` within terminal
4. Navigate to `localhost:8000` within web browser

## JSON Endpoints
The following JSON Endpoints are accessible to the public:
- `/types/JSON` - lists all animal types and details
- `/types/<int:type_id>/pets/JSON` - lists all pets and their details for a specific animal type
- `/types/<int:type_id>/pets/<int:pet_id>/JSON` - list details about a specific pet

## Known Issues
Currently, due to changes in Facebook's policy for applications, applications that do not utilize a secure connection are unable to utilize the Facebook Login feature. Currently, users can only login via Google's OAuth2 login function.

## Future Plans
In the future, I'd like to get the Facebook login working again as well as create a general login option for users to setup a new account using their own email and creating their own unique password.

## License
This application is released under the MIT License

Copyright (c) 2018 Jason Bodman

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
