#!/bin/bash

# for this to work, your default ssh key needs to be enabled on the remote machine
# (@dzenan: this is the case for you)

set -e
set -u

remote="engine1@tokyo.dnd.d10r.net"

if [[ -f .env.tokyo ]]; then
	echo "*** copying .env.tokyo to .env on remote..."
	scp .env.tokyo $remote:~/diversiflyengine/.env
else
	echo "*** no local .env.tokyo exists. Leaving remote .env as is"
fi

# if the deps get too heavy, we could make a copy of requirements.txt on remote and compare with it after git pull and before doing pip3 install
echo "*** getting latest version from git..."
ssh $remote "cd diversiflyengine && git pull"

# this is slow and tends to segfault. Leaving out for now.
#echo "installing dependencies..."
#ssh $remote "cd diversiflyengine && pip3 install -r requirements.txt"

echo "*** restarting systemd service..."
ssh $remote "sudo systemctl restart diversifly-engine1"

echo "*** checking the logs after restart..."
sleep 5
# gets the last 30 seconds of logs
ssh $remote "sudo journalctl -S -30s -u diversifly-engine1 | cat"
echo
echo "*** all done!"
