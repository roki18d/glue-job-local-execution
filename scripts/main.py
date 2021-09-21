# coding: utf-8

# ************************************************************
# Import Libraries
# ************************************************************

import os
import sys
import json
import argparse
import logging
import logging.config
import docker

# Libraries for Debugging
import pdb
from see import see

# Custom Module
from scripts.utils import *
from scripts.exceptions import *


# ************************************************************
# Configuration
# ************************************************************

# Global Variables
CONFIG_FILEPATH = "./config.json"

# Instantiate
client = docker.from_env()

with open(CONFIG_FILEPATH, "r") as f_config:
    config = json.load(f_config)

# General Configuration
general_config = config["GENERAL"]
base_image_name = general_config["BASE_IMAGE_NAME"]
dockerfile_location = general_config["DOCKERFILE_LOCATION"]
my_image_name = general_config["MY_IMAGE_NAME"]

# Logging Configuration
logging_config = config["LOGGING"]
logging_config_file_location = logging_config["CONFIG_FILE_LOCATION"]
logging.config.fileConfig(logging_config_file_location)


# ************************************************************
# Main Function
# ************************************************************

def main():

    # parse agguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--tag", help="")
    args = parser.parse_args()
    new_image_version = args.tag

    # pull base image, if not exists
    base_image = pull_image(image_name=base_image_name)

    # build my image
    built_image = build_image(
        my_image_name=my_image_name, 
        new_image_version=new_image_version, 
        dockerfile_location=dockerfile_location)

    # get new image tag
    new_image_tag = ":".join([my_image_name, new_image_version])

    # push my image
    push_image(my_image_name, new_image_version)

    # run container from built image
    containers = run_container(new_image_tag, restart=True)

    # end program with exit code 0
    logging.info(logging_separator)
    logging.info('This program completed successfully.')
    logging.info(logging_separator)
    sys.exit(0)


# ************************************************************
# Main Process
# ************************************************************

if __name__ == "__main__":
    main()
