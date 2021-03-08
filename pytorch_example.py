## launch_pytorch.py

#!/usr/bin/env python
import sys
import qarnot
import os
from config import keys

# Edit 'MY_TOKEN' to provide your own credentials
# Create a connection, from which all other objects will be derived
token = keys['token']

conn = qarnot.Connection(client_token=token)

# Create a task
task = conn.create_task('pytorch_demo', 'docker-batch', 1)

# Store if an error happened during the process
error_happened = False
try:
    # Create a resource bucket and add input files
    input_bucket = conn.create_bucket('pytorch-input')
    input_bucket.sync_directory('input')
    input_bucket.add_file('wesh.py')

    # Attach the bucket to the task
    task.resources.append(input_bucket)

    # Create a result bucket and attach it to the task
    output_bucket = conn.create_bucket('pytorch-output')
    task.results = output_bucket

    # Set the command to run when launching the container, by overriding a
    # constant.
    # Task constants are the main way of controlling a task's behaviour
    task.constants['DOCKER_REPO'] = "qarnotlab/pytorch-gpu"
    task.constants['DOCKER_TAG'] = "v1"
    task.constants['DOCKER_CMD'] = "/bin/sh -c \"ls -la . && python3 wesh.py\""

    # Update results every 5 seconds
    task.snapshot(5)

    # Submit the task to the Api, that will launch it on the cluster
    task.submit()

    # Wait for the task to be finished, and monitor the progress of its
    # deployment
    last_state = ''
    done = False
    while not done:
        # Update task state changes
        if task.state != last_state:
            last_state = task.state
            print("** {}".format(last_state))

        # Wait for the task to complete, with a timeout of 5 seconds.
        # This will return True as soon as the task is complete, or False
        # after the timeout.
        done = task.wait(5)

        # Display fresh stdout / stderr
        sys.stdout.write(task.fresh_stdout())
        sys.stderr.write(task.fresh_stderr())

    # Display errors on failure
    if task.state == 'Failure':
        print("** Errors: %s" % task.errors[0])
        error_happened = True

    # Download results from output_bucket into given folder
    task.download_results('output')

finally:
    # Exit code in case of error
    if error_happened:
        sys.exit(1)
