#!/bin/bash

sudo apt-get install python3 jq

cp CONFIG.dist.json CONFIG.json

# json support for Jython2.5
# https://support.xebialabs.com/hc/en-us/community/posts/201998425/comments/201058965
wget https://pypi.python.org/packages/f3/e0/8949888568534046c5c847d26c89a05c05f3151ab06728dbeca2d1621002/simplejson-2.5.2.tar.gz#md5=d7a7acf0bd7681bd116b5c981d2f7959
tar -zxvf simplejson-2.5.2.tar.gz