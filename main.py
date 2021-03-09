#!/usr/bin/env python

import argparse
from config import keys

import sys
import qarnot
import os

import re

from os import walk

PURPLE = '\033[95m'
BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'


class Qarnot_Wrapper():
	def __init__(self, args):
		self.conn = qarnot.Connection(client_token=keys['token'])
		self.args = args
		self.name = args.name
		# print(self.conn.profiles())
		profile = 'docker-network' if args.internet else 'docker-batch'
		self.task = self.conn.create_task(self.name, profile, args.multi_core)
		print("Task " + BLUE + self.name + RESET + ":")
		print("\tProfile:\t" + YELLOW + profile + RESET)
		print("\tNb cores:\t" + YELLOW + str(args.multi_core) + RESET)
		self.prepare_docker()

	def import_folder(self, path, py_only=False):
		bucket_in_name = self.name + '-input'
		input_bucket = self.conn.create_bucket(bucket_in_name)
		input_bucket.sync_directory('input')
		print("\tInput bucket has been created: " + YELLOW + bucket_in_name + RESET)
		if path:
			f = []
			for (dirpath, _, filenames) in walk(path):
				if "/.git" in dirpath or "/__pycache__" in dirpath:
					continue
				for filename in filenames:
					if not py_only or filename[-3:] == ".py":
						f.append(dirpath + "/" + filename)
			try:
				f.remove("./config.py")
			except:
				pass
			for e in f:
				input_bucket.add_file(e)
				print("\tFile " + YELLOW + e + RESET + ' has been added to ' + bucket_in_name)
			# Attach the bucket to the task
		self.task.resources.append(input_bucket)
		bucket_out_name = self.name + '-output'
		output_bucket = self.conn.create_bucket(bucket_out_name)
		print("\tOutput bucket has been created: " + YELLOW + bucket_out_name + RESET)
		self.task.results = output_bucket

	def prepare_docker(self):
		self.task.constants['DOCKER_REPO'] = self.args.docker
		self.task.constants['DOCKER_TAG'] = "v1"
		cmd = "/bin/sh -c \"" + self.args.command + "\""
		self.task.constants['DOCKER_CMD'] = cmd
		print("\tDocker repo:\t" + YELLOW +
		      self.task.constants['DOCKER_REPO'] + RESET)
		print("\tDocker cmd:\t" + YELLOW + self.task.constants['DOCKER_CMD'] + RESET)


	def launch(self):
		# error_happened = False
		self.task.snapshot(5)
		self.task.submit()

		last_state = ''
		done = False
		while not done:
			# Update task state changes
			if self.task.state != last_state:
				last_state = self.task.state
				print(GREEN + "** {}".format(last_state) + RESET)

			# Wait for the task to complete, with a timeout of 5 seconds.
			# This will return True as soon as the task is complete, or False
			# after the timeout.
			done = self.task.wait(5)
			self.fetch_fresh_output()

		# Display errors on failure
		if self.task.state == 'Failure':
			print(RED + "** Errors:" + RESET + " %s" % self.task.errors[0])
			# error_happened = True

		# Download results from output_bucket into given folder
		self.task.download_results('output')

	def fetch_fresh_output(self):
		# Display fresh stdout / stderr
		new = self.task.fresh_stdout()
		search = r"(\d+>)"
		replace = r"\n\1"
		if new:
			new = re.sub(search, replace, new)
			sys.stdout.write("\n" + BLUE + "-" * 10 + "stdout" + "-" * 10 + RESET + "\n")
			sys.stdout.write(new)
			sys.stdout.write("\n" + BLUE + "-" * 10 + "------" + "-" * 10 + RESET + "\n")
		new = self.task.fresh_stderr()
		if new:
			sys.stderr.write("\n" + RED + "-" * 10 + "stderr" + "-" * 10 + RESET + "\n")
			sys.stderr.write(new)
			sys.stderr.write("\n" + RED + "-" * 10 + "------" + "-" * 10 + RESET + "\n")

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument(
			"-d",
			"--directory",
			help="Directory to upload")
	parser.add_argument(
			"-n",
			"--name",
			default="Cute_unnamed_task",
			help="Task name")
	parser.add_argument(
			"-c",
			"--command",
			help="Command to execute in docker. It will be put between double quotes: \"xxx\" ")
	parser.add_argument(
			"-o",
			"--docker",
			default="ezalos/qarnot_1stdqn:2.00",
			help="Docker container to use, ie: ezalos/qarnot_1stdqn: 2.00")
	parser.add_argument(
			"-m",
			"--multi_core", 
			default=1,
			type=int,
	        help="Number of cores to use")
	parser.add_argument(
			"-i", 
			"--internet", 
			default=False, 
			action='store_true',
	        help="To have internet in the container")


	args = parser.parse_args()
	if args.command:
		qw = Qarnot_Wrapper(args)
		qw.import_folder(args.directory, True)
		qw.launch()



