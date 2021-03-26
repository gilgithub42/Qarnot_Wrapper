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

		if args.list:
			for t in self.conn.tasks():
				print(str(t))
			return

		task = self.conn.retrieve_task(args.uuid)
		if task:
			print(GREEN + "Task found `" + YELLOW + task.uuid + RESET + "`!" + RESET)
		else:
			print(RED + "Error: no task found" + RESET)
			# TODO Exit with status 1
			return

		if args.abort:
			task.abort()
			print("Aborted task `" + YELLOW + task.uuid + RESET + "`")
		elif args.stdout:
			self.fetch_fresh_output(task)
		elif args.retrieve:
			dir = 'output-' + args.uuid
			print("\tDownloading results from task in " + YELLOW + dir + RESET + " directory...")
			task.results.get_all_files(dir)
		elif args.command:
			self.prepare_task(task)
			self.prepare_docker(task)
			if args.directory:
				self.import_folder(args.directory, True)
			self.launch(task)
		else:
			print(RED + "Please specify an action to perform" + RESET)
			# TODO Exit with status 1
		# TODO Exit with status 0

	def prepare_task(self, task):
		profile = 'docker-network' if args.internet else 'docker-batch'
		task = self.conn.create_task(self.name, profile, self.args.multi_core)
		print("Task " + BLUE + self.name + RESET + ":")
		print("\tProfile:\t" + YELLOW + profile + RESET)
		print("\tNb cores:\t" + YELLOW + str(self.args.multi_core) + RESET)

	def prepare_docker(self, task):
		task.constants['DOCKER_REPO'] = self.args.docker
		task.constants['DOCKER_TAG'] = "v1"
		cmd = "/bin/sh -c \"" + self.args.command + "\""
		task.constants['DOCKER_CMD'] = cmd
		print("\tDocker repo:\t" + YELLOW +
		      task.constants['DOCKER_REPO'] + RESET)
		print("\tDocker cmd:\t" + YELLOW + task.constants['DOCKER_CMD'] + RESET)

	def import_folder(self, path, task, py_only=False):
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
		task.resources.append(input_bucket)
		bucket_out_name = self.name + '-output'
		output_bucket = self.conn.create_bucket(bucket_out_name)
		print("\tOutput bucket has been created: " + YELLOW + bucket_out_name + RESET)
		task.results = output_bucket

	def launch(self, task):
		# error_happened = False
		task.snapshot(5)
		task.submit()

		last_state = ''
		done = False
		while not done:
			# Update task state changes
			if task.state != last_state:
				last_state = task.state
				print(GREEN + "** {}".format(last_state) + RESET)

			# Wait for the task to complete, with a timeout of 5 seconds.
			# This will return True as soon as the task is complete, or False
			# after the timeout.
			done = task.wait(5)
			self.fetch_fresh_output()

		# Display errors on failure
		if task.state == 'Failure':
			print(RED + "** Errors:" + RESET + " %s" % task.errors[0])
			# error_happened = True

		# Download results from output_bucket into given folder
		task.download_results('output')

	def fetch_fresh_output(self, task):
		# Display fresh stdout / stderr
		new = task.fresh_stdout()
		search = r"(\d+>)"
		replace = r"\n\1"
		if new:
			new = re.sub(search, replace, new)
			sys.stdout.write("\n" + BLUE + "-" * 10 + "stdout" + "-" * 10 + RESET + "\n")
			sys.stdout.write(new)
			sys.stdout.write("\n" + BLUE + "-" * 10 + "------" + "-" * 10 + RESET + "\n")
		new = task.fresh_stderr()
		if new:
			sys.stderr.write("\n" + RED + "-" * 10 + "stderr" + "-" * 10 + RESET + "\n")
			sys.stderr.write(new)
			sys.stderr.write("\n" + RED + "-" * 10 + "------" + "-" * 10 + RESET + "\n")

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument(
			"-d",
			"--directory",
			help="The task's directory")
	parser.add_argument(
			"-n",
			"--name",
			default="Cute_unnamed_task",
			help="Task name")
	parser.add_argument(
            "-u",
			"--uuid",
   	        help="The UUID of an existing task")
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

	action_group = parser.add_mutually_exclusive_group()
	action_group.add_argument(
            "-l",
			"--list",
			action="store_true",
   	        help="Lists every tasks")
	action_group.add_argument(
            "-a",
			"--abort",
			action="store_true",
   	        help="Aborts the task")
	action_group.add_argument(
            "-s",
			"--stdout",
			action="store_true",
   	        help="Retrieves fresh stdout and stderr")
	action_group.add_argument(
            "-r",
			"--retrieve",
			action="store_true",
   	        help="Downloads the task's files (even if the task is running)")
	parser.add_argument(
			"-c",
			"--command",
			help="Command to execute in docker. It will be put between double quotes: \"xxx\" ")


	args = parser.parse_args()
	qw = Qarnot_Wrapper(args)



