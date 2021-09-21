# coding: utf-8

# ************************************************************
# Import Libraries
# ************************************************************

import os
import sys
import json
import logging
import logging.config
import docker

# Libraries for Debugging
import pdb
from see import see

# Custom Module
from scripts.exceptions import *


# ************************************************************
# Configuration
# ************************************************************

# Global Variables
CONFIG_FILEPATH = "config.json"

# Instantiate
client = docker.from_env()

with open(CONFIG_FILEPATH, "r") as f_config:
    config = json.load(f_config)

msg_fmt_for_fn_invoke = lambda fn_name: f"Function '{fn_name}()' invoked."
msg_fmt_for_fn_end = lambda fn_name: f"Function '{fn_name}()' ended."

# General Configuration
general_config = config["GENERAL"]
base_image_name = general_config["BASE_IMAGE_NAME"]
dockerfile_location = general_config["DOCKERFILE_LOCATION"]
my_image_name = general_config["MY_IMAGE_NAME"]

# Logging Configuration
logging_config = config["LOGGING"]
logging_config_file_location = logging_config["CONFIG_FILE_LOCATION"]
logging_separator_char = logging_config["SEPARATOR_CHAR"]
logging_separator_repeat_num = logging_config["SEPARATOR_NUM_REPEAT"]

logging_separator = logging_separator_char * logging_separator_repeat_num
logging.config.fileConfig(logging_config_file_location)

# General Configuration
client = docker.from_env()
with open(CONFIG_FILEPATH, "r") as f_config:
    config = json.load(f_config)


# ************************************************************
# Functions
# ************************************************************

def _logging_fn_invoke(fn_name):
    logging.info(logging_separator)
    logging.info(msg_fmt_for_fn_invoke(fn_name))
    return None

def _logging_fn_end(fn_name):
    logging.info(msg_fmt_for_fn_end(fn_name))
    return None

def _get_existing_image_name_list():

    existing_image_name_list = list()
    for image in client.images.list():
        for image_name_with_tag in image.tags:
            existing_image_name_list.append(image_name_with_tag)

    return existing_image_name_list


def _get_latest_version(image_name=my_image_name):

    latest_major_version = 0
    latest_minor_version = 0

    for image in client.images.list():
        for image_name_with_tag in image.tags:
            image_name_no_tag, image_tag = image_name_with_tag.split(":")

            if image_name_no_tag == image_name:    
                existing_major_version, existing_minor_version = [int(v) for v in image_tag.lstrip("v").split(".")]

                if (existing_major_version >= latest_major_version) and (existing_minor_version >= latest_minor_version):
                    latest_major_version = existing_major_version
                    latest_minor_version = existing_minor_version

    latest_version = f"v{latest_major_version}.{latest_minor_version}"
    return latest_version


def _validate_image_version(new_image_version, latest_image_version):

    valid_flag_image_version = True

    new_major_version, new_minor_version = [int(v) for v in new_image_version.lstrip("v").split(".")]
    latest_major_version, latest_minor_version = [int(v) for v in latest_image_version.lstrip("v").split(".")]

    if new_major_version < latest_major_version:
        valid_flag_image_version = False
    elif new_major_version == latest_major_version:
        if new_minor_version <= latest_minor_version:
            valid_flag_image_version = False

    return valid_flag_image_version


def _login_to_docker_hub():

    docker_hub_secret = config["DOCKER_HUB_SECRET"]

    username = docker_hub_secret["USERNAME"]
    password = docker_hub_secret["PASSWORD"]
    email = docker_hub_secret["EMAIL"]
    registry = docker_hub_secret["REGISTRY"]

    try:
        result = client.login(
            username=username, 
            password=password, 
            email=email, 
            registry=registry)
        logging.debug(result)
        logging.info("Logged in to Docker Hub successfully")
    except Exception as e:
        msg = f"Error occured while logging in to Docker Hub.: {e}"
        logging.error(msg)
        # raise WhileLoggingInToDockerHubError(msg)
        return False
    
    return True

def pull_image(image_name=base_image_name):
    _logging_fn_invoke(fn_name=sys._getframe().f_code.co_name)

    existing_image_name_list = _get_existing_image_name_list()

    if image_name in existing_image_name_list:
        logging.info("Image already exists, skip pulling the image.")
        image = client.images.get(image_name)
    
    else:
        try: 
            logging.info("Image not found, pulling the image...")
            image = client.images.pull(image_name)
            logging.info("Image successfully pulled.")
        except Exception as e: 
            msg = f"Error occured while pulling image.: {e}"
            raise WhilePullingImageError(msg)
    
    _logging_fn_end(fn_name=sys._getframe().f_code.co_name)
    return image


def build_image(my_image_name=my_image_name, new_image_version=None, dockerfile_location=dockerfile_location):
    _logging_fn_invoke(fn_name=sys._getframe().f_code.co_name)

    latest_image_version = _get_latest_version()
    valid_flag_image_version = _validate_image_version(new_image_version=new_image_version, latest_image_version=latest_image_version)
    
    if not valid_flag_image_version:
        msg = f"Invalid image version '{new_image_version}' given, new version should be higher than the latest one '{latest_image_version}'."
        raise InvalidImageVersionError(msg)

    try:
        new_image_tag = ":".join([my_image_name, new_image_version])
        image = client.images.build(path=dockerfile_location, tag=new_image_tag)
        logging.info("Image successfully built.")

    except Exception as e:
        msg = f"Error occured while building image.: {e}"
        raise WhileBuildingImageError(msg)

    _logging_fn_end(fn_name=sys._getframe().f_code.co_name)
    return image


def tag_image(repository, image_version):
    _logging_fn_invoke(fn_name=sys._getframe().f_code.co_name)

    image_name = repository.split("/")[1]
    image_tag = ":".join([image_name, image_version])

    result = client.api.tag(
        image=image_tag, 
        repository=repository, 
        tag=image_version)

    logging.debug(result)

    _logging_fn_end(fn_name=sys._getframe().f_code.co_name)
    return None
    

def push_image(image_name, image_version):
    _logging_fn_invoke(fn_name=sys._getframe().f_code.co_name)

    logging.info("Logging in to Docker Hub...")
    login_succeeded = _login_to_docker_hub()

    if login_succeeded:

        try:
            docker_hub_secret = config["DOCKER_HUB_SECRET"]
            username = docker_hub_secret["USERNAME"]
            password = docker_hub_secret["PASSWORD"]
            
            image_tag = ":".join([image_name, image_version])
            repository = "/".join([username, image_name])
            logging.debug(repository)
            tag_image(repository, image_version)

            result = client.images.push(
                repository=repository, 
                tag=image_version, 
                stream=True, 
                auth_config={"username": username, "password": password}
            )
            logging.debug(see(result))
            logging.info("Image successfully pushed.")

        except Exception as e:
            msg = f"Error occured while pushing the image.: {e}"
            logging.error(msg)
            WhilePushingImageError(msg)
            # return False

    else:
        logging.info("Error occured while logging in to Docker Hub, skip pushing the image.")
        return False

    _logging_fn_end(fn_name=sys._getframe().f_code.co_name)
    return True


def stop_and_remove_container(container_name):
    _logging_fn_invoke(fn_name=sys._getframe().f_code.co_name)

    container_list = client.containers.list()
    target_container = [container for container in container_list if container.name == container_name][0]
    target_container.stop()
    target_container.remove()

    logging.info("Container successfully stopped and removed.")

    _logging_fn_end(fn_name=sys._getframe().f_code.co_name)
    return None


def run_container(tag, restart=True):
    _logging_fn_invoke(fn_name=sys._getframe().f_code.co_name)

    docker_container_config = config["DOCKER_CONTAINER_CONFIG"]

    container_name = docker_container_config["NAME"]
    port_jupyter_notebook = docker_container_config["PORT_ON_HOST_JUPYTER_NOTEBOOK"]
    port_spark_ui = docker_container_config["PORT_ON_HOST_SPARK_UI"]

    container_name_list = [container.name for container in client.containers.list()]
    if container_name in container_name_list:
        msg = f"Specified container name '{container_name}' is in use."
        if restart:
            logging.info(msg)
            logging.info("Stopping and removing the container...")
            stop_and_remove_container(container_name)
        else:
            logging.error(msg)
            raise ContainerNameConflictError(msg)

    try: 
        containers = client.containers.run(
            image=tag, 
            ports={
                "8888/tcp": ("localhost", port_jupyter_notebook), 
                "4040/tcp": ("localhost", port_spark_ui)
            }, 
            volumes=[
                f"{os.environ['HOME']}/.aws:/root/.aws:ro", 
            ], 
            name=container_name, 
            stdin_open=True, 
            tty=True, 
            detach=True, 
            command="/home/jupyter/jupyter_start.sh", 
        )
    except Exception as e:
        msg = f"Error occured while running container.: {e}"
        raise WhileRunningContainerError(msg)

    _logging_fn_end(fn_name=sys._getframe().f_code.co_name)
    return containers
