# coding: utf-8

# ************************************************************
# Exceptions
# ************************************************************

class WhilePullingImageError(Exception):
    pass

class WhileBuildingImageError(Exception):
    pass

class WhileRunningContainerError(Exception):
    pass

class WhileLoggingInToDockerHubError(Exception):
    pass

class WhilePushingImageError(Exception):
    pass

class InvalidImageVersionError(Exception):
    pass

class ContainerNameConflictError(Exception):
    pass


