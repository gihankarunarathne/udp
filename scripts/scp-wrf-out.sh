#!/bin/bash

scp -r -i ~/.ssh/id_rsa  gckarunarathne@35.185.205.216:/mnt/disks/wrf-mod/OUTPUT/RF/* ../WRF/RF/
scp -r -i ~/.ssh/id_rsa  gckarunarathne@35.185.205.216:/mnt/disks/wrf-mod/OUTPUT/colombo/* ../WRF/colombo/
scp -r -i ~/.ssh/id_rsa  gckarunarathne@35.185.205.216:/mnt/disks/wrf-mod/OUTPUT/kelani-basin/* ../WRF/kelani-basin/
