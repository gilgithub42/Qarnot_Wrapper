#!/usr/bin/env python

import argparse
from config import keys

import sys
import qarnot
import os

from os import walk

class Qarnot_Wrapper():
	def __init__(self, args):
		self.conn = qarnot.Connection(client_token=keys['token'])
		self.args = args
		self.name = "Test_Wrapper"
		# print(self.conn.profiles())
		self.task = self.conn.create_task(self.name, 'docker-network', 1)
		error_happened = False

	def import_folder(self, path, py_only=False):
		f = []
		for (dirpath, _, filenames) in walk(path):
			# print(dirnames)
			if "/.git" in dirpath or "/__pycache__" in dirpath:
				continue
			for filename in filenames:
				if not py_only or filename[-3:] == ".py":
					f.append(dirpath + "/" + filename)
		print(f)
		try:
			f.remove("./config.py")
		except:
			pass
		bucket_name = self.name + '-input'
		input_bucket = self.conn.create_bucket(bucket_name)
		input_bucket.sync_directory('input')
		for e in f:
			input_bucket.add_file(e)
			print("File " + e + ' has been added to ' + bucket_name)

		# Attach the bucket to the task
		self.task.resources.append(input_bucket)
		output_bucket = self.conn.create_bucket('pytorch-output')
		self.task.results = output_bucket
		pass

	def launch(self, command):
		self.task.constants['DOCKER_REPO'] = "ezalos/donkey_qarnot:1.00"
		self.task.constants['DOCKER_TAG'] = "v1"
		self.task.constants['DOCKER_CMD'] = "/bin/sh -c \"pwd && ls -la . && ls -la .. && pip install sklearn && python3 Genetic_HP_Opti.py\""
		self.task.snapshot(5)
		self.task.submit()

		last_state = ''
		done = False
		while not done:
			# Update task state changes
			if self.task.state != last_state:
				last_state = self.task.state
				print("** {}".format(last_state))

			# Wait for the task to complete, with a timeout of 5 seconds.
			# This will return True as soon as the task is complete, or False
			# after the timeout.
			done = self.task.wait(5)

			# Display fresh stdout / stderr
			new = self.task.fresh_stdout()
			if new:
				sys.stdout.write("\n" + "-" * 10 + "stdout" + "-" * 10 + "\n")
				sys.stdout.write(new.replace("0>", "\n0>"))
				sys.stdout.write("\n" + "-" * 10 + "------" + "-" * 10 + "\n")
			new = self.task.fresh_stderr()
			if new:
				sys.stderr.write("\n" + "-" * 10 + "stderr" + "-" * 10 + "\n")
				sys.stderr.write(new.replace(" \\n", "\n"))
				sys.stderr.write("\n" + "-" * 10 + "------" + "-" * 10 + "\n")

		# Display errors on failure
		if self.task.state == 'Failure':
			print("** Errors: %s" % self.task.errors[0])
			error_happened = True

		# Download results from output_bucket into given folder
		self.task.download_results('output')


# total 20
#  0 > drwxrwxrwx  4 root  115 4096 Mar  3 09: 43 .
#  0 > drwxr-xr-x 64 root root  160 Mar  3 09: 43 ..
#  0 > -rwxrwxrwx  3 root root 2700 Mar  3 09: 41 files_example.py
#  0 > -rwxrwxrwx  2 root root 2437 Mar  3 09: 42 main.py
#  0 > -rwxrwxrwx  3 root root 2304 Mar  3 09: 41 pytorch_example.py
#  0 > -rwxrwxrwx  3 root root  521 Mar  3 09: 41 wesh.py


# " 0> total 88
#  0> drwxrwxrwx   4 root  114  4096 Mar  5 16:27  .
#  0> drwxr-xr-x 141 root root   160 Mar  5 16:27  ..
#  0> -rwxrwxrwx   5 root root  2541 Mar  5 15:01 'CuteNet copy.py'
#  0> -rwxrwxrwx   5 root root 15218 Mar  5 15:01  CuteNet.py
#  0> -rwxrwxrwx   5 root root  1028 Mar  5 15:01  Genetic_HP_Opti.py
#  0> -rwxrwxrwx   5 root root  6093 Mar  5 15:01  HyperParamsOpti.py
#  0> -rwxrwxrwx   5 root root  2421 Mar  5 15:01  ModelsManager.py
#  0> -rwxrwxrwx   5 root root  5814 Mar  5 15:01  Q.py
#  0> -rwxrwxrwx   5 root root  8134 Mar  5 15:01  cartpole.py
#  0> -rwxrwxrwx   5 root root  3161 Mar  5 15:01  config.py
#  0> -rwxrwxrwx   5 root root   589 Mar  5 15:01  dataloader.py
#  0> -rwxrwxrwx   5 root root  2643 Mar  5 15:01  llenotre.py
#  0> -rwxrwxrwx   5 root root  1187 Mar  5 15:01  plot_data.py
#  0> -rwxrwxrwx   5 root root  4604 Mar  5 15:01  ref.py
#  0> -rwxrwxrwx   5 root root   523 Mar  5 15:01  test_gym.py
#  0> -rwxrwxrwx   5 root root   389 Mar  5 15:01  utils.py
#  0>
#  0> CartPole <3 :   0% 0/1500 [00:00<?, ?episode/s]\n 
#  0> CartPole <3 :   0% 0/1500 [00:00<?, ?episode/s, cmb=0, eps=89, scr=0, trn=21]\n 
#  0> CartPole <3 :   0% 0/1500 [00:00<?, ?episode/s, cmb=0, eps=89, scr=0, trn=17]\n 
#  0> CartPole <3 :   0% 0/1500 [00:00<?, ?episode/s, cmb=0, eps=88, scr=0, trn=15]\n 
#  0> CartPole <3 :   0% 0/1500 [00:00<?, ?episode/s, cmb=0, eps=88, scr=0, trn=15]\n 
#  0> CartPole <3 :   0% 0/1500 [00:00<?, ?episode/s, cmb=0, eps=87, scr=0, trn=17]\n 
#  0> CartPole <3 :   0% 5/1500 [00:00<00:32, 45.73episode/s, cmb=0, eps=87, scr=0, trn=17]\n 
#  0> CartPole <3 :   0% 5/1500 [00:00<00:32, 45.73episode/s, cmb=0, eps=87, scr=0, trn=16]
#  /usr/local/lib/python3.7/site-packages/torch/autograd/__init__.py:132: 
#  	UserWarning: CUDA initialization: Found no NVIDIA driver on your system. Please check that you have an NVIDIA GPU and installed a driver from http://www.nvidia.com/Download/index.aspx (Triggered internally at  /pytorch/c10/cuda/CUDAFunctions.cpp:100.)\n 
#  0>   allow_unreachable=True)  # allow_unreachable flag"

# [Profile(name=docker-batch, constants=(('DOCKER_SRV', 'https://registry.hub.docker.com'), ('DOCKER_REPO', 'library/ubuntu'), ('DOCKER_TAG', 'latest'), ('DOCKER_REGISTRY_LOGIN', ''), ('DOCKER_REGISTRY_PASSWORD', ''), ('DOCKER_USER', ''), ('DOCKER_HOST', ''), ('DOCKER_CMD', ''), ('DOCKER_SHUTDOWN_CMD', '/bin/true'), ('DOCKER_PROGRESS1', ''), ('DOCKER_PROGRESS2', ''), ('DOCKER_PROGRESS3', ''), ('RESOURCES_PATH', '/job'), ('DOCKER_WORKDIR', '${DOCKER_WORKDIR}'))}, 
# Profile(name=docker-batch, constants=(('DOCKER_SRV', 'https://registry.hub.docker.com'), ('DOCKER_REPO', 'library/ubuntu'), ('DOCKER_TAG', 'latest'), ('DOCKER_REGISTRY_LOGIN', ''), ('DOCKER_REGISTRY_PASSWORD', ''), ('DOCKER_USER', ''), ('DOCKER_HOST', ''), ('DOCKER_CMD', ''), ('DOCKER_SHUTDOWN_CMD', '/bin/true'), ('DOCKER_PROGRESS1', ''), ('DOCKER_PROGRESS2', ''), ('DOCKER_PROGRESS3', ''), ('RESOURCES_PATH', '/job'), ('DOCKER_WORKDIR', '${DOCKER_WORKDIR}'))}, 
# Profile(name=python, constants=(('PYTHON_SCRIPT', 'undefined'), ('PYTHON_PROGRESS', ''), ('DOCKER_SSH', ''), ('DOCKER_DEBUG', ''))}, 


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-d", "--directory", help="Directory to upload")
	args = parser.parse_args()
	if args.directory:
		qw = Qarnot_Wrapper(args)
		qw.import_folder(args.directory, True)
		qw.launch("Yo")



